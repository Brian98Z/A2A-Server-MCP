#!/usr/bin/env python3
"""Read-only health check for the A2A Gateway skill.

    python selfcheck.py                 # endpoint, tools, protocol, packages, wallet challenge
    python selfcheck.py --register      # also registers a throwaway wallet and spends 1 point

--register creates a real membership account on the server. Use it once per install.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("A2A_BASE_URL", "https://a2a.musefish.trade").rstrip("/")
UA = os.environ.get("A2A_UA", "a2a-agent-skill/1.0")


def http(method: str, url: str, body: dict | None = None, headers: dict | None = None,
         timeout: float = 60.0) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"user-agent": UA, "accept": "application/json"}
    if data is not None:
        hdrs["content-type"] = "application/json"
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw[:1] in "{[" else raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, raw[:300]


def mcp(payload: dict, base: str) -> tuple[int, dict]:
    return http("POST", f"{base}/mcp", payload,
                {"accept": "application/json, text/event-stream"}, timeout=120)


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    return ok


def live_flow(base: str) -> bool:
    from eth_account import Account
    from eth_account.messages import encode_defunct

    status, proto = http("GET", f"{base}/api/v1/invitations/protocol")
    if not check("registration protocol", status == 200 and isinstance(proto, dict), str(status)):
        return False
    bits = int(proto["pow"]["bits"])

    acct = Account.create()
    wallet = acct.address.lower()
    nonce = secrets.token_hex(32)
    expires = int(time.time()) + 240
    message = (f"A2A Membership Registration\nDomain: a2a.musefish.trade\n"
               f"Wallet: {wallet}\nInviter code: none\nChain ID: 8453\n"
               f"Nonce: {nonce}\nExpires: {expires}\nSign this message to register this wallet.")
    signature = Account.sign_message(encode_defunct(text=message), acct.key).signature.hex()
    if not signature.startswith("0x"):
        signature = "0x" + signature
    msg_hash = hashlib.sha256(message.encode()).hexdigest()
    sig_hash = hashlib.sha256(signature.encode()).hexdigest()
    counter = 0
    while True:
        digest = hashlib.sha256(f"a2a-registration-pow-v1:{msg_hash}:{sig_hash}:{counter}".encode()).digest()
        if int.from_bytes(digest, "big") >> (256 - bits) == 0:
            break
        counter += 1
    status, reg = http("POST", f"{base}/api/v1/invitations", {
        "wallet_address": wallet, "chain_id": 8453, "nonce": nonce,
        "expires_at": expires, "signature": signature, "pow_counter": str(counter)})
    if not check("register wallet", status == 200, f"points={reg.get('points_awarded') if isinstance(reg, dict) else reg}"):
        return False

    status, member = http("GET", f"{base}/api/v1/members/{wallet}")
    if not check("member balance", status == 200 and member.get("points", 0) >= 2, f"points={member.get('points')}"):
        return False

    status, first = mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "check_base_token_safety",
        "arguments": {"token_address": "0x4200000000000000000000000000000000000006",
                      "payer_address": wallet}}}, base)
    structured = (first.get("result") or {}).get("structuredContent") or {}
    if not check("invoice issued", bool(structured.get("invoiceId")), structured.get("amountDisplay", "")):
        return False

    sig2 = Account.sign_message(encode_defunct(text=structured["challengeToSign"]), acct.key).signature.hex()
    if not sig2.startswith("0x"):
        sig2 = "0x" + sig2
    status, paid = mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "check_base_token_safety",
        "arguments": {"token_address": "0x4200000000000000000000000000000000000006",
                      "payer_address": wallet},
        "_meta": {"x402/payment": {"method": "points", "invoice_id": structured["invoiceId"],
                                   "payer_address": wallet, "signature": sig2}}}}, base)
    ok = bool(paid.get("result")) and not paid["result"].get("isError")
    if not check("points settlement", ok, f"wallet={wallet}"):
        return False
    status, after = http("GET", f"{base}/api/v1/members/{wallet}")
    return check("points deducted", after.get("points") == 1, f"{member.get('points')} -> {after.get('points')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--register", action="store_true",
                    help="register a throwaway wallet and spend 1 point (creates real data)")
    ns = ap.parse_args()
    base = ns.base_url.rstrip("/")
    print(f"base: {base}")
    passed = []

    status, status_body = http("GET", f"{base}/status.json")
    passed.append(check("status.json", status == 200 and isinstance(status_body, dict),
                        str(status_body.get("status") if isinstance(status_body, dict) else status)))

    status, listing = mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, base)
    names = [t["name"] for t in (listing.get("result", {}).get("tools", []) if isinstance(listing, dict) else [])]
    arcade = {"get_arcade_auth_message", "slots_state", "slots_spin"}
    passed.append(check("tools/list", status == 200 and len(names) >= 10 and arcade <= set(names),
                        ", ".join(names)))

    status, proto = http("GET", f"{base}/api/v1/invitations/protocol")
    passed.append(check("registration protocol", status == 200 and "pow" in (proto or {}),
                        f"bits={proto.get('pow', {}).get('bits') if isinstance(proto, dict) else status}"))

    status, packages = http("GET", f"{base}/alipay/packages")
    passed.append(check("alipay packages", status == 200 and isinstance(packages, list) and len(packages) == 3,
                        str([p.get("id") for p in packages]) if isinstance(packages, list) else str(status)))

    status, challenge = http("GET", f"{base}/api/v1/wallet/challenge?wallet_address="
                                     "0x0000000000000000000000000000000000000001")
    passed.append(check("wallet challenge", status == 200 and isinstance(challenge, dict) and "message" in challenge,
                        "ok" if status == 200 else str(status)))

    if ns.register:
        passed.append(live_flow(base))

    ok = all(passed)
    print("\nSELF-CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
