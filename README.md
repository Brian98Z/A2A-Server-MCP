# A2A Web3 Server MCP

Remote MCP server for Base token security, EVM route simulation, AI code audits, image background removal, and an arcade. Paid calls settle in USDC on Base (x402) or membership points.

This repository publishes the MCP interface only — endpoint contract, tool reference, client configs and registry manifests — plus the skill package under `skills/`. Product, marketing and operations material is not published here.

## Connect

Streamable HTTP, MCP protocol `2025-03-26`:

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

Legacy JSON-RPC: `https://a2a.musefish.trade/mcp-legacy`. Call `tools/list` for live input schemas.

## First call

Call `check_base_token_safety` with only `token_address`. The response is a free market preview, with no wallet, invoice, or payment.

### Availability

The gateway runs on actual runtime availability, not office hours: there is no weekday or weekend cutoff. `GET /status.json` reports `open`, `maintenance` and backend health. If the gateway is put into explicit maintenance, paid endpoints return `503` with `Retry-After` **before any invoice is issued**, so no payment is expected.

Free endpoints (registration, member lookup, catalog, `/status.json`) stay available.

Re-call with `payer_address` to receive the invoice for the full report. Other paid tools require `payer_address` when you want an invoice.

```json
{
  "token_address": "0x4200000000000000000000000000000000000006"
}
```

## Tools

| Tool | Purpose | Price |
|---|---|---|
| `check_base_token_safety` | Base token security and liquidity report; free preview first | 0.01 USDC or 1 point |
| `simulate_mev_route_safety` | Read-only EVM route and flashloan simulation | 1.50 USDC or 150 points |
| `fast_code_audit` | AI code security audit | 0.02 USDC or 2 points |
| `deep_protocol_reasoning` | AI protocol and contract reasoning | 0.10 USDC or 10 points |
| `remove_image_background` | Transparent RGBA background removal | 0.01 USDC or 1 point |
| `generate_a2a_invitation` | Register a wallet; returns referral code and SVG | Free |
| `get_a2a_registration_protocol` | Registration message and proof-of-work difficulty | Free |
| `get_arcade_auth_message` | EIP-191 message for arcade access | Free |
| `slots_state` | Arcade balance, pity meter, stats, recent spins | Free |
| `slots_spin` | One spin for 1 game point; prizes 1/2/5/10/100 | Free |

## Payment

1. Call the tool with `payer_address` and no payment metadata. Read `invoiceId`, `challengeToSign`, recipient, and amount from `_meta["x402/payment-required"]`.
2. Sign the exact `challengeToSign` text with EIP-191. Never send a private key.
3. For USDC, transfer the exact amount on Base and keep the transaction hash. For points, skip the transfer.
4. Retry the same call with the same arguments and:

```json
{
  "x402/payment": {
    "method": "points",
    "invoice_id": "<invoiceId>",
    "payer_address": "<wallet>",
    "signature": "<EIP-191 signature>"
  }
}
```

For USDC, omit `method` and use `"tx_hash": "<hash>"`. Never combine `tx_hash` with `method: "points"`. Invoices expire after 300 seconds. Do not pay twice.

REST calls use the same fields; send points payments with `X-A2A-Payment-Method: points`.

## Registration and points

```bash
pip install eth-account requests
curl -fsSLo register_a2a.py https://a2a.musefish.trade/register_a2a.py
python3 register_a2a.py
```

The script creates a wallet, signs the EIP-191 message, solves the SHA-256 proof of work, and registers in one request. It saves the private key and signed request in an owner-only file; protect it like a password. Resume a lost response with `--resume`.

New members receive 2 points; an invite code gives 3, and the inviter earns 1 point (lifetime cap 200). Registration is also available through `generate_a2a_invitation`; fetch the exact message and difficulty from `get_a2a_registration_protocol`.

Promotional points are limited to 3 service calls per wallet per UTC day. Purchased points are not.

## Errors and availability

- No hardcoded business hours. A `503` means maintenance or a downstream outage; it is returned before any invoice is issued.
- `429` means admission contention. Honor `Retry-After`.
- MCP settlement errors set `isError` and expose the status in `_meta["x402/payment-error"].status_code`.
- A `409` uncertain outcome must not be retried automatically. Keep the invoice and transaction identifiers; never send a second payment.

Status: `https://a2a.musefish.trade/status.json`

## Links

- Gateway: https://a2a.musefish.trade/
- MCP: https://a2a.musefish.trade/mcp
- Agent discovery: https://a2a.musefish.trade/llms.txt
- x402 manifest: https://a2a.musefish.trade/.well-known/x402-manifest.json
- License: [Apache-2.0](LICENSE)
