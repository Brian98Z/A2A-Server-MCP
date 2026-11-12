---
name: a2a-gateway-mcp
description: 【代码开发·MCP接入】A2A Gateway 的 MCP 接入手册：免注册读取 4 个免费工具（注册协议、注册、街机签名/状态/转动）、按 x402 或 points 双轨结算 5 个付费工具，含签名消息、错误码与街机积分经济规则；不适用于非该域名的其他 MCP 服务。
tags: 代码开发,MCP接入
desc-en: 'MCP integration manual for A2A Gateway: call four free tools (registration protocol, registration, arcade auth message, arcade state/spin) and five paid tools settled over x402 USDC or points, with signing messages, error codes and the arcade point economy.'
globs: []
---

# A2A Gateway — MCP Integration

Canonical endpoint: `POST https://a2a.musefish.trade/mcp` (JSON-RPC 2.0 over HTTP).
Discovery: `tools/list`, then `tools/call`. Send `Accept: application/json, text/event-stream`.

## 1. Client configuration

Cursor / Claude Desktop / any MCP client that supports remote HTTP servers:

```json
{
  "mcpServers": {
    "a2a-base-guard": { "url": "https://a2a.musefish.trade/mcp" }
  }
}
```

Raw JSON-RPC example:

```bash
curl -s https://a2a.musefish.trade/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 2. Tools

### Free

| Tool | Purpose | Arguments |
|---|---|---|
| `get_a2a_registration_protocol` | Canonical EIP-191 registration message plus current proof-of-work difficulty | none |
| `generate_a2a_invitation` | One-call membership registration; returns referral code, invite link and dotcode SVG | `wallet_address`, `chain_id`, `nonce`, `expires_at`, `signature`, `pow_counter`, optional `inviter_code` |
| `get_arcade_auth_message` | Canonical EIP-191 message that authorises arcade calls | `wallet_address`, `nonce`, `expires_at` |
| `slots_state` | Arcade balance, pity meter, session stats, recent spins; applies the daily free point | `wallet_address`, `nonce`, `expires_at`, `signature` |
| `slots_spin` | One server-authoritative spin for 1 game point | same four fields |

### Paid (x402 USDC on Base, or points)

| Tool | Price | Arguments |
|---|---|---|
| `check_base_token_safety` | 0.01 USDC / 1 point | `token_address`, `payer_address` |
| `simulate_mev_route_safety` | 1.50 USDC / 150 points | `target_address`, `calldata`, `value`, `payer_address` |
| `fast_code_audit` | 0.02 USDC / 2 points | `prompt`, optional `system_prompt`, `payer_address` |
| `deep_protocol_reasoning` | 0.10 USDC / 10 points | `prompt`, optional `system_prompt`, `payer_address` |
| `remove_image_background` | 0.01 USDC / 1 point | `image` (http(s) URL or Base64), optional `rem_mode`, `add_background`, `payer_address` |

## 3. Payment flows

**Step 1 — get an invoice.** Call the paid tool with `payer_address` and no payment metadata. The response carries `structuredContent` with `invoiceId`, `amount`, `payTo`, `accepts[]` and `challengeToSign`. Never hardcode the recipient address; always read it from the invoice.

**Step 2 — pay and settle.**

- On-chain: transfer the exact USDC amount on Base to `payTo`, then re-call with
  `_meta.x402/payment = {"tx_hash": "0x…", "payer_address": "0x…"}`.
- Points: sign `challengeToSign` with EIP-191, then re-call with
  `_meta.x402/payment = {"method": "points", "invoice_id": "inv-…", "signature": "0x…", "payer_address": "0x…"}`.

The invoice binds tool name, canonical argument hash, amount and payer. Reusing it with different arguments, another payer or another rail is rejected. A 409 means the outcome is uncertain: do not retry blindly.

## 4. Arcade flow (agent-playable)

```
get_arcade_auth_message {wallet_address, nonce (64 lowercase hex), expires_at (≤300s ahead)}
  → sign the returned text with personal_sign (EIP-191)
slots_state | slots_spin {wallet_address, nonce, expires_at, signature}
```

The message is domain-bound and nonce-address-bound; every nonce is single use, and a replay returns 409. Use a fresh nonce per call.

Economy rules:

- Stake is 1 game point; prizes are 1 / 2 / 5 / 10 / 100 for three matching Cherry / Lemon / Bell / Seven / Diamond.
- The 15th consecutive miss always pays; overall hit rate is about 28.5%, RTP about 70%.
- **Granted** points (10-point welcome grant, 1 daily relief point) are arcade-only and cannot pay for gateway calls.
- **Won** points are the only game points that can pay points-rail calls; they are spent first and are exempt from the 3-per-UTC-day promotional limit.
- Game points never convert back to membership points.

## 5. Error handling

| Symptom | Meaning | Action |
|---|---|---|
| `-32602` with an argument message | Malformed argument, expired `expires_at`, or invalid signature | Rebuild the payload; keep `expires_at` within 300 seconds |
| `-32000` `status_code: 401/403` | Signature does not match the wallet, or the caller is not the payer | Sign with the same wallet you pass |
| `-32000` `status_code: 402` | No game points, points hold failed, or payment required | Read `relief`/invoice in the response; do not pay twice |
| `-32000` `status_code: 409` | Nonce replay or uncertain settlement | Sign a new nonce; for settlement, query the invoice before retrying |
| `-32000` `status_code: 429` | Rate limit (arcade 30 spins/min/IP, remote image fetch 6/min/IP) | Back off and retry after the Retry-After window |

## 6. Notes

- Paid tools are billed per call; execution failures keep the points hold reserved for the recovery loop instead of refunding automatically.
- `remove_image_background` rejects remote URLs when paying with points; supply inline Base64 instead.
- Reference implementations: `register_a2a.py` (registration) and `sms_mcp_probe.py`-style signed probes in this repository.
