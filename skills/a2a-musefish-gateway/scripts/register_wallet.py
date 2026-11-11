#!/usr/bin/env python3
"""Register a wallet with the A2A Gateway membership.

    pip install eth-account requests
    python register_a2a.py                      # generate, securely save, and register
    PRIVATE_KEY=0x... python register_a2a.py    # register an existing wallet
    python register_a2a.py --inviter CODE       # use someone's referral code
    python register_a2a.py --resume FILE        # retry the exact saved request

Generated keys and signed requests are saved before registration is posted.
Keep the credential file private; --resume retries its exact nonce and payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
import subprocess
import tempfile
from pathlib import Path

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

DEFAULT_BASE = os.environ.get("A2A_BASE_URL", "https://a2a.musefish.trade")
A2A_UA = os.environ.get("A2A_UA", "OMP-A2A-Agent/1.0 (registration)")
HEADERS = {"User-Agent": A2A_UA, "Accept": "application/json"}
DOMAIN = "a2a.musefish.trade"
POW_PREFIX = "a2a-registration-pow-v1:"


def protocol(base: str) -> dict:
    r = requests.get(f"{base}/api/v1/invitations/protocol", timeout=20, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def message(wallet: str, inviter: str | None, chain_id: int, nonce: str, expires: int) -> str:
    return (
        "A2A Membership Registration\n"
        f"Domain: {DOMAIN}\n"
        f"Wallet: {wallet}\n"
        f"Inviter code: {inviter if inviter else 'none'}\n"
        f"Chain ID: {chain_id}\n"
        f"Nonce: {nonce}\n"
        f"Expires: {expires}\n"
        "Sign this message to register this wallet."
    )


def solve_pow(message_hash: str, signature_hash: str, bits: int, max_rounds: int = 1 << 32) -> str:
    """Find the counter whose digest has at least `bits` leading zero bits."""
    counter = 0
    while counter < max_rounds:
        digest = hashlib.sha256(f"{POW_PREFIX}{message_hash}:{signature_hash}:{counter}".encode()).digest()
        if int.from_bytes(digest, "big") >> (256 - bits) == 0:
            return str(counter)
        counter += 1
    raise RuntimeError("proof-of-work budget exhausted")


def save_private_json(path: Path, data: dict) -> None:
    """Atomically save credentials with owner-only access; fail closed on Windows."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        if os.name == "nt":
            username = os.environ.get("USERDOMAIN", "") + "\\" + os.environ.get("USERNAME", "")
            if username.strip("\\") == "":
                raise OSError("current Windows account could not be identified")
            os.close(fd)
            fd = -1
            result = subprocess.run(["icacls", temporary, "/inheritance:r", "/grant:r", f"{username}:F"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
            if result.returncode:
                raise OSError("could not set owner-only Windows file permissions")
            fd = os.open(temporary, os.O_WRONLY | os.O_TRUNC)
        else:
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = -1
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            os.chmod(path, 0o600)
    except Exception:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def report_response(resp) -> int:
    if resp.status_code != 200:
        print(f"registration failed [{resp.status_code}]; credentials and exact request remain in the saved file", file=sys.stderr)
        return 1
    try:
        data = resp.json()
    except ValueError:
        print("registration returned an unreadable response; retry only with the same saved request", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2))
    print(f"\nfree points credited: {data.get('points_awarded', 0)}")
    print(f"your invite link: {data.get('referral_link')}")
    print("next: call a paid tool with _meta x402/payment method=points, or read /quickstart")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Register a wallet with the A2A Gateway.")
    ap.add_argument("--resume", metavar="FILE", help="retry the exact signed request saved in FILE")
    ap.add_argument("--inviter", default=os.environ.get("A2A_INVITER"), help="inviter referral code")
    ap.add_argument("--chain-id", type=int, default=8453)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()

    if args.resume:
        try:
            saved = json.loads(Path(args.resume).expanduser().read_text(encoding="utf-8"))
            if not isinstance(saved, dict) or not isinstance(saved.get("payload"), dict):
                raise ValueError
            payload, wallet, base = saved["payload"], saved["wallet_address"], saved["base_url"]
        except Exception:
            print("could not read a valid saved registration request", file=sys.stderr)
            return 1
        try:
            resp = requests.post(f"{base}/api/v1/invitations", json=payload, timeout=30, headers=HEADERS)
        except requests.RequestException:
            print(f"registration response unavailable; retry with --resume {args.resume}", file=sys.stderr)
            return 1
        print(f"wallet: {wallet}\nsaved request: {Path(args.resume).expanduser()}")
        return report_response(resp)

    private_key = os.environ.get("PRIVATE_KEY")
    if private_key:
        acct = Account.from_key(private_key)
        new_wallet = False
    else:
        acct = Account.create()
        new_wallet = True

    wallet = acct.address.lower()
    proto = protocol(args.base_url)
    bits = int(proto["pow"]["bits"])
    expires = int(time.time()) + int(proto.get("expiration_max_seconds", 300)) - 60
    nonce = secrets.token_hex(32)

    signed = message(wallet, args.inviter, args.chain_id, nonce, expires)
    signature = Account.sign_message(encode_defunct(text=signed), acct.key).signature.hex()
    if not signature.startswith("0x"):
        signature = "0x" + signature

    msg_hash = hashlib.sha256(signed.encode()).hexdigest()
    sig_hash = hashlib.sha256(signature.encode()).hexdigest()
    started = time.time()
    counter = solve_pow(msg_hash, sig_hash, bits)
    elapsed = time.time() - started

    payload = {
        "wallet_address": wallet,
        "chain_id": args.chain_id,
        "nonce": nonce,
        "expires_at": expires,
        "signature": signature,
        "pow_counter": counter,
    }
    if args.inviter:
        payload["inviter_code"] = args.inviter

    saved_path = Path(f"a2a-registration-{wallet}.json")
    saved = {"wallet_address": wallet, "base_url": args.base_url, "pow_bits": bits, "payload": payload}
    if new_wallet:
        saved["private_key"] = acct.key.hex()
    try:
        save_private_json(saved_path, saved)
    except Exception:
        print("could not securely save registration request; registration was not sent", file=sys.stderr)
        return 1
    print(f"wallet: {acct.address}")
    print(f"signed request saved securely: {saved_path.resolve()}")
    print(f"proof-of-work: {bits} bits solved in {elapsed:.1f}s (counter {counter})")
    try:
        resp = requests.post(f"{args.base_url}/api/v1/invitations", json=payload, timeout=30, headers=HEADERS)
    except requests.RequestException:
        if saved_path:
            print(f"registration response unavailable; retry the same request with --resume {saved_path}", file=sys.stderr)
        return 1
    return report_response(resp)


if __name__ == "__main__":
    sys.exit(main())
