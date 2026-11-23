# A2A Gateway — MCP Integration

One remote MCP server exposes eleven tools: five metered services that settle in USDC on Base (x402) or
membership points, and six free tools for registration and the arcade.

| Item | Value |
|---|---|
| MCP endpoint | `POST https://a2a.musefish.trade/mcp` |
| Transport | Streamable HTTP, JSON-RPC 2.0, protocol `2025-03-26` |
| Legacy JSON-RPC | `POST https://a2a.musefish.trade/mcp-legacy` |
| Chain | Base mainnet, `eip155:8453` |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Invoice TTL | 300 seconds |
| Status | `https://a2a.musefish.trade/status.json` |

## 1. Transport requirements

Every POST must send:

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |
| `Accept` | `application/json, text/event-stream` |

Responses are one JSON-RPC object per request. The server does not emit SSE event framing, so parse
the JSON body even when you accept `text/event-stream`. Missing or wrong `Accept` is the most common
cause of a `406` before any tool runs.

Discovery:

- `GET /mcp` — endpoint metadata: version, methods, required headers, streaming notes, catalog link.
- `GET /api/v1/mcp-catalog` — machine-readable tool catalog with input schemas.
- `tools/list` — the live catalog over JSON-RPC.

## 2. Configure

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

## 3. First call: free preview

`check_base_token_safety` with only `token_address` returns a free market preview. No wallet, invoice,
or payment is needed, and no default token is assumed.

- Over MCP the preview arrives in a normal `200` result (`structuredContent.free_preview`).
- Over REST (`POST /api/v1/token-report`) the same token-only call answers `HTTP 402` whose body
  already contains `free_preview` — read that body as data, not as a failure.

Add `payer_address` to receive the invoice for the full bytecode report.

## 4. Tools

### Paid

| Tool | Price | Arguments |
|---|---|---|
| `check_base_token_safety` | 0.01 USDC / 1 point | `token_address`; add `payer_address` for the invoice |
| `simulate_mev_route_safety` | 1.50 USDC / 150 points | `target_address`; optional `calldata`, `value`, `payer_address` |
| `fast_code_audit` | 0.02 USDC / 2 points | `prompt` (≤16k chars); optional `system_prompt`, `payer_address` |
| `deep_protocol_reasoning` | 0.10 USDC / 10 points | `prompt` (≤16k chars); optional `system_prompt`, `payer_address` |
| `remove_image_background` | 0.01 USDC / 1 point | `image` (URL or Base64); optional `rem_mode`, `add_background`, `payer_address` |

### Free

| Tool | Purpose |
|---|---|
| `register_a2a_agent` | One-call registration for clients that cannot sign or solve PoW: the gateway generates a burner wallet and returns the private key once |
| `generate_a2a_invitation` | One-call wallet registration with SHA-256 proof of work; returns referral code and SVG |
| `get_a2a_registration_protocol` | Canonical signed message, request fields and current PoW difficulty |
| `get_arcade_auth_message` | EIP-191 message for arcade access |
| `slots_state` | Arcade balance, pity meter, stats, recent spins |
| `slots_spin` | One spin for 1 game point; prizes 1/2/5/10/100 |

## 5. Payment

1. Call a paid tool with `payer_address` and no payment metadata. Read `invoiceId`, `challengeToSign`,
   recipient and amount from `_meta["x402/payment-required"]` (also mirrored in
   `structuredContent.payment_required`).
2. Sign the exact challenge with EIP-191. Never transmit a private key.
3. Settle one of two ways:
   - **USDC:** transfer the exact amount on Base to the recipient and keep the transaction hash.
   - **Points:** skip the transfer; the signed challenge redeems points from the same wallet.
4. Retry the same call with identical arguments and `_meta["x402/payment"]`:

```json
{
  "method": "points",
  "invoice_id": "<invoiceId>",
  "payer_address": "<wallet>",
  "signature": "<EIP-191 signature>"
}
```

For USDC, omit `method` and send `"tx_hash": "<hash>"`. Never combine both fields. Invoices expire
after 300 seconds; a settled invoice executes at most once. Successful results report
`settled_via: points | onchain`.

A `409` means the outcome is uncertain. Do not retry automatically, keep the invoice and transaction
identifiers, and never pay twice for the same invoice.

## 6. Registration and points

```bash
pip install eth-account requests
curl -fsSLo register_a2a.py https://a2a.musefish.trade/register_a2a.py
python3 register_a2a.py
```

The script signs the canonical EIP-191 message, grinds the SHA-256 proof of work (20 leading zero bits
by default), and registers in one call. New members receive 2 points; an invite code adds 1 to the
invitee (3 total) and pays the inviter 1 point, capped at 200 lifetime. Registration also grants 10
arcade game points, which are a separate currency.

Retrying an identical registration nonce returns `replayed: true` with `points_awarded_now: 0` instead
of paying a second bonus. The script stores the private key in an owner-only file; treat it as a
password.

Balance lookup: `GET https://a2a.musefish.trade/api/v1/members/{wallet_address}`.

## 7. Errors and limits

| Condition | Response |
|---|---|
| Maintenance or downstream outage | `503`, before any invoice is issued |
| Admission contention or rate limit | `429` with `Retry-After` and `retry_after_s` |
| Bad payment signature | `401 payment_signature_invalid` |
| Uncertain settlement outcome | `409`, do not retry automatically |
| MCP settlement failure | `isError: true` and `_meta["x402/payment-error"].status_code` |

Rate limits per IP: registration 20/min; free previews and preview-invoice issuance 60/hour, shared by
MCP and REST. Server-generated agent wallets add three layers, all returning `429` with `retry_after_s`:
1/hour and 2/24h per IP (`A2A_AGENT_IP_HOURLY_CAP`, `A2A_AGENT_REGISTRATION_DAILY_CAP`), 6/24h per /24
or /64 (`A2A_AGENT_SUBNET_DAILY_CAP`), and a global 10/hour + 50/24h budget
(`A2A_AGENT_GLOBAL_HOURLY_CAP`, `A2A_AGENT_GLOBAL_DAILY_CAP`). `A2A_AGENT_REGISTRATION_ENABLED=0`
disables the path entirely. Server-generated wallets receive no arcade points
(`A2A_AGENT_SIGNUP_GAME_POINTS`, default 0). The private key returned by `register_a2a_agent` is
generated in memory, never stored or logged, and the wallet should never be funded. Every failure body
carries `error`, `detail`, `hint` and `docs`; MCP transport errors use `error.message` plus
`error.data.hint`.

## 8. More

- Human quickstart: `https://a2a.musefish.trade/quickstart`
- Integration page: `https://a2a.musefish.trade/mcp-docs`
- For agents: `https://a2a.musefish.trade/llms.txt`
- Machine catalog: `https://a2a.musefish.trade/api/v1/mcp-catalog`
- x402 manifest: `https://a2a.musefish.trade/.well-known/x402-manifest.json`
- OpenAPI: `https://a2a.musefish.trade/openapi.json`
