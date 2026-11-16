---
name: a2a-musefish-gateway
description: Call the A2A Gateway MCP server (https://a2a.musefish.trade/mcp) to vet Base-mainnet tokens before trading, simulate EVM calldata, run AI code audits or deep protocol reasoning, remove image backgrounds, and play the arcade with signed wallet auth. Covers free wallet registration with signup points, the x402 invoice flow, points redemption signed with EIP-191, and USDC-on-Base or Alipay top-ups.
license: Apache-2.0
---

# A2A Gateway — MCP usage

One remote MCP server exposes metered Web3 and AI services. Paid calls settle in USDC on Base (x402) or membership points. Registration is free and grants points, so a new agent can complete a paid call without funding a wallet.

| Item | Value |
|---|---|
| MCP endpoint | `https://a2a.musefish.trade/mcp` (Streamable HTTP, protocol `2025-03-26`) |
| Legacy JSON-RPC | `https://a2a.musefish.trade/mcp-legacy` |
| Chain | Base mainnet, `eip155:8453` |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Invoice TTL | 300 seconds |
| Registration script | `https://a2a.musefish.trade/register_a2a.py` |
| Status | `https://a2a.musefish.trade/status.json` |

## Install

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

Copy this directory into the client's skill folder. OMP uses `~/.omp/agent/skills/a2a-musefish-gateway/`; Claude Code uses `~/.claude/skills/` or `.claude/skills/`.

## First call

`check_base_token_safety` with only `token_address` returns a free market preview. No wallet, invoice, or payment is required. This is not the full report.

Re-call with `payer_address` to receive the invoice for the full bytecode report. Other paid tools require `payer_address` for an invoice.

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
  "name":"check_base_token_safety",
  "arguments":{"token_address":"0x4200000000000000000000000000000000000006"}}}
```

## Tools

Paid:

| Tool | Price | Arguments |
|---|---|---|
| `check_base_token_safety` | 0.01 USDC / 1 point | `token_address`; add `payer_address` for the invoice |
| `simulate_mev_route_safety` | 1.50 USDC / 150 points | `target_address`; optional `calldata`, `value`, `payer_address` |
| `fast_code_audit` | 0.02 USDC / 2 points | `prompt`; optional `system_prompt`, `payer_address` |
| `deep_protocol_reasoning` | 0.10 USDC / 10 points | `prompt`; optional `system_prompt`, `payer_address` |
| `remove_image_background` | 0.01 USDC / 1 point | `image`; optional `rem_mode`, `payer_address` |

Free:

| Tool | Purpose |
|---|---|
| `generate_a2a_invitation` | Register a wallet; returns referral code and SVG |
| `get_a2a_registration_protocol` | Registration message and proof-of-work difficulty |
| `get_arcade_auth_message` | EIP-191 message for arcade access |
| `slots_state` | Arcade balance, pity meter, stats, recent spins |
| `slots_spin` | One spin for 1 game point; prizes 1/2/5/10/100 |

Input schemas and response shapes: `references/mcp-tools.md`.

## Register and get points

```bash
pip install eth-account requests
python scripts/register_wallet.py
```

The script creates a wallet, signs the EIP-191 message, solves the proof of work, registers, and saves an owner-only credential file. New members receive 2 points; `--inviter <code>` gives 3, and the inviter earns 1 point (cap 200). To use an existing wallet, pass `PRIVATE_KEY` as an environment variable.

## Pay

1. Call a paid tool with `payer_address` and no payment metadata.
2. Read `invoiceId`, `challengeToSign`, recipient, and amount from `_meta["x402/payment-required"]`.
3. Sign the exact challenge with EIP-191.
4. Retry the same call with identical arguments and `_meta["x402/payment"]`.

Points:

```json
{"method":"points","invoice_id":"<invoiceId>","payer_address":"<wallet>","signature":"<EIP-191>"}
```

USDC: omit `method` and add `"tx_hash":"<hash>"`. Never combine both. Invoices expire after 300 seconds. Never pay twice.

Points helper: `python scripts/pay_with_points.py --wallet-file <credential.json> --tool <tool> --args '<json>'`.

USDC and Alipay details: `references/payments.md`.

## Arcade

Sign the message from `get_arcade_auth_message`, then pass `wallet_address`, `nonce`, `expires_at`, and `signature` to `slots_state` or `slots_spin`. Each nonce is single use; generate a fresh one per call. Only won game points can pay points-rail calls. Granted points are arcade-only.

## Errors

| Symptom | Meaning | Action |
|---|---|---|
| `isError: true` with `invoiceId` | Payment required | Pay and re-call within 300 s |
| `isError: true` with `status: "warming"` | Backend cold; no invoice | Wait `retry_after_s`, repeat |
| HTTP 409 | Uncertain settlement | Do not auto-retry; keep identifiers |
| HTTP 429 | Promotional limit or contention | Honor `Retry-After` or use purchased points/USDC |
| HTTP 503 | Maintenance; no invoice issued | Retry after the delay; do not pay |

Never print or transmit a private key. Sign only the exact `challengeToSign` string. AI results are ephemeral and not retained.
