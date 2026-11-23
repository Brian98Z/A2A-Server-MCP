---
name: a2a-gateway-mcp
description: "A2A Gateway MCP integration: six free tools and five paid tools settled over x402 USDC or points, with signing, wallet registration, payment, error handling, and arcade rules."
tags: code,mcp
---

# A2A Gateway — MCP Integration

Endpoint: `POST https://a2a.musefish.trade/mcp` (Streamable HTTP, JSON-RPC 2.0).
Discovery: `tools/list`, then `tools/call`. Legacy protocol version: `2025-03-26` (also negotiates `2025-06-18`); `server/discover` is supported for modern clients.
Every POST must send `Content-Type: application/json` and `Accept: application/json, text/event-stream`; responses are a single JSON-RPC object with no SSE framing.

## 1. Configure

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

Legacy JSON-RPC endpoint: `https://a2a.musefish.trade/mcp-legacy`.

## 2. First call

`check_base_token_safety` with only `token_address` returns a free market preview. No wallet, invoice, or payment is needed, and no default token is assumed. This is not the full report.

- Over MCP the preview arrives in a normal `200` result (`structuredContent.free_preview`).
- Over REST (`POST /api/v1/token-report`) the same call answers `HTTP 402` whose body already carries `free_preview`; read it as data.

Re-call with `payer_address` to receive the invoice for the full bytecode report.

## 3. Tools

### Paid

| Tool | Price | Arguments |
|---|---|---|
| `check_base_token_safety` | 0.01 USDC / 1 point | `token_address`; add `payer_address` for the invoice |
| `simulate_mev_route_safety` | 1.50 USDC / 150 points | `target_address`; optional `calldata`, `value`, `payer_address` |
| `fast_code_audit` | 0.02 USDC / 2 points | `prompt`; optional `system_prompt`, `payer_address` |
| `deep_protocol_reasoning` | 0.10 USDC / 10 points | `prompt`; optional `system_prompt`, `payer_address` |
| `remove_image_background` | 0.01 USDC / 1 point | `image` (URL or Base64); optional `rem_mode`, `payer_address` |

### Free

| Tool | Purpose |
|---|---|
| `generate_a2a_invitation` | Register a wallet; returns referral code and SVG |
| `register_a2a_agent` | Server-generated burner wallet (no signature/PoW); one-time key + 2 points |
| `get_a2a_registration_protocol` | Registration message and proof-of-work difficulty |
| `get_arcade_auth_message` | EIP-191 message for arcade access |
| `slots_state` | Arcade balance, pity meter, stats, recent spins |
| `slots_spin` | One spin for 1 game point; prizes 1/2/5/10/100 |

## 4. Payment flow

1. Call a paid tool with `payer_address` and no payment metadata. Read `invoiceId`, `challengeToSign`, recipient, and amount from `_meta["x402/payment-required"]`.
2. Sign the exact challenge with EIP-191. Never send a private key.
3. For USDC, transfer the exact amount on Base and keep the hash. For points, skip the transfer.
4. Retry the same call with identical arguments and `_meta["x402/payment"]`:

```json
{
  "method": "points",
  "invoice_id": "<invoiceId>",
  "payer_address": "<wallet>",
  "signature": "<EIP-191 signature>"
}
```

For USDC, omit `method` and use `"tx_hash": "<hash>"`. Never combine both. Invoices expire after 300 seconds.
Clients that can only submit tool arguments (no `_meta`, e.g. a UI form) may attach the
payment fields directly to the retried call instead:

```json
{
  "payment_method": "points",
  "invoice_id": "<invoiceId>",
  "payer_address": "<wallet>",
  "signature": "<EIP-191 signature>"
}
```

Use `"payment_method": "onchain"` with `"tx_hash": "<hash>"` for USDC. Both transports are verified identically.


## 5. Registration

```bash
pip install eth-account requests
curl -fsSLo register_a2a.py https://a2a.musefish.trade/register_a2a.py
python3 register_a2a.py
```

New members receive 2 points; an invite code gives 3, and the inviter earns 1 point (cap 200). The script saves the private key in an owner-only file. Protect it like a password.

## 6. Errors

- `503`: maintenance or downstream outage; no invoice was issued.
- `429`: admission contention or a rate limit; honor `Retry-After` (`retry_after_s` in the body).
- `401 payment_signature_invalid`: the EIP-191 signature does not match the challenge or payer.
- Settlement failures set `isError` and `_meta["x402/payment-error"].status_code`.
- `409`: uncertain outcome; do not retry automatically and never pay twice.

Rate limits per IP: registration 20/min; free previews and preview-invoice issuance 60/hour, shared by MCP and REST.

Status: `https://a2a.musefish.trade/status.json`.
