#!/usr/bin/env python3
"""Settle one A2A Gateway tool call with membership points.

    python pay_with_points.py --wallet-file a2a-registration-0xabc.json \
        --tool check_base_token_safety \
        --args '{"token_address":"0x4200000000000000000000000000000000000006"}'

The helper performs the full loop: call -> invoice -> EIP-191 signature over
`challengeToSign` -> re-call with _meta["x402/payment"]. It prints the settled JSON
and the wallet balance before/after.

Requires: eth-account. Set A2A_BASE_URL to target another deployment.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from eth_account import Account
from eth_account.messages import encode_defunct

DEFAULT_BASE = os.environ.get("A2A_BASE_URL", "https://a2a.musefish.trade").rstrip("/")
UA = os.environ.get("A2A_UA", "a2a-agent-skill/1.0")


def http(method: str, url: str, body: dict | None = None, headers: dict | None = None,
         timeout: float = 180.0) -> tuple[int, dict | str]:
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
            return exc.code, raw[:400]


def mcp(payload: dict, base: str) -> tuple[int, dict]:
    return http("POST", f"{base}/mcp", payload,
                {"accept": "application/json, text/event-stream"}, timeout=180)


def load_key(wallet_file: str | None) -> tuple[str, str]:
    if wallet_file:
        saved = json.loads(Path(wallet_file).expanduser().read_text(encoding="utf-8"))
        key = saved.get("private_key")
        wallet = saved.get("wallet_address")
        if not key:
            raise SystemExit("wallet file has no private_key; pass PRIVATE_KEY instead")
        return key, wallet.lower()
    key = os.environ.get("PRIVATE_KEY")
    if not key:
        raise SystemExit("provide --wallet-file or PRIVATE_KEY")
    return key, Account.from_key(key).address.lower()


def balance(base: str, wallet: str) -> dict:
    status, body = http("GET", f"{base}/api/v1/members/{wallet}")
    return body if status == 200 and isinstance(body, dict) else {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wallet-file", help="credential JSON written by register_wallet.py")
    ap.add_argument("--tool", required=True, help="tool name, e.g. check_base_token_safety")
    ap.add_argument("--args", default="{}", help="JSON object of tool arguments")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ns = ap.parse_args()

    base = ns.base_url.rstrip("/")
    key, wallet = load_key(ns.wallet_file)
    args = json.loads(ns.args)
    if not isinstance(args, dict):
        raise SystemExit("--args must be a JSON object")
    args.setdefault("payer_address", wallet)

    before = balance(base, wallet)
    print(f"wallet:  {wallet}")
    print(f"points:  {before.get('points')} (purchased {before.get('purchased_points')}, "
          f"promo {before.get('referral_points')})")

    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": ns.tool, "arguments": args}}
    status, first = mcp(call, base)
    result = first.get("result") if isinstance(first, dict) else None
    if result and not result.get("isError"):
        print("already settled without payment:")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:4000])
        return 0

    structured = (result or {}).get("structuredContent") or {}
    meta_payment = ((result or {}).get("_meta") or {}).get("x402/payment-required") or {}
    error_data = ((first.get("error") or {}).get("data") or {}) if isinstance(first, dict) else {}
    if structured.get("status") in ("warming", "offline"):
        print(f"backend {structured['status']}: retry after {structured.get('retry_after_s', 15)}s; "
              "no invoice was issued and nothing is owed")
        return 3
    invoice = (structured.get("invoiceId") or meta_payment.get("invoiceId")
               or error_data.get("invoiceId"))
    challenge = (structured.get("challengeToSign") or meta_payment.get("challengeToSign")
                 or error_data.get("challengeToSign"))
    if not invoice or not challenge:
        print(f"unexpected response [{status}]:", json.dumps(first, ensure_ascii=False)[:1200])
        return 1
    print(f"invoice: {invoice}  amount: {structured.get('amountDisplay')}")

    signature = Account.sign_message(encode_defunct(text=challenge), key).signature.hex()
    if not signature.startswith("0x"):
        signature = "0x" + signature
    call["id"] = 2
    call["params"]["_meta"] = {"x402/payment": {
        "method": "points", "invoice_id": invoice,
        "payer_address": wallet, "signature": signature}}
    status, paid = mcp(call, base)
    paid_result = paid.get("result") if isinstance(paid, dict) else None
    if not paid_result or paid_result.get("isError"):
        print(f"settlement failed [{status}]:", json.dumps(paid, ensure_ascii=False)[:1200])
        return 1

    after = balance(base, wallet)
    print("settled; points:", before.get("points"), "->", after.get("points"))
    text = (paid_result.get("content") or [{}])[0].get("text", "")
    try:
        print(json.dumps(json.loads(text), ensure_ascii=False, indent=2)[:6000])
    except (ValueError, TypeError):
        print(text[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
