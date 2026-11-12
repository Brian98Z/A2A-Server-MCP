# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Empty body or Cloudflare page instead of JSON | default library `User-Agent` challenged | send `user-agent: your-agent/1.0` and `accept: application/json` |
| `tools/list` works, paid call returns invoice | expected: first call is unpaid | settle with points, USDC, or Alipay |
| `400 payment metadata must be objects` | `_meta["x402/payment"]` is not an object | wrap it as an object |
| `403 Signature does not match` | signed the wrong wallet or wrong text | sign the exact `challengeToSign`/`challenge.message` with the payer key |
| `409` on settlement | earlier settlement attempt uncertain | check balance first; create a new invoice only if nothing settled |
| `429 Daily promotional-points redemption limit` | 3 promo redemptions today (UTC) | wait for the next UTC day or pay with purchased points/USDC |
| `isError: true` with `status: "warming"` | model cold; warm-up started, no invoice | wait `retry_after_s`, repeat the identical call |
| `isError: true` with `status: "offline"` | daemon temporarily unreachable (model switch/restart) | retry after ~20 s; no invoice exists |
| `503` on `fast_code_audit`/`deep_protocol_reasoning` | gateway maintenance only | honor `Retry-After`, then retry |
| Intermittent `503` outside Monday–Friday 11:00–22:00 (UTC+8) | outside the advisory service window; maintenance is more likely | retry inside the window; no payment is involved |
| Registration `400` | nonce/expiry/pow mismatch | request a fresh protocol document; rebuild message with the same values |
| PoW takes minutes | difficulty raised by operator | read `pow.bits` from the protocol instead of assuming 20 |
| Alipay `401` | wallet session cookie missing | run the login step again |
| Arcade `409 This arcade auth nonce was already used` | the nonce was already spent | sign a fresh nonce for every arcade call |
| Arcade `400 expires_at must be within the next 300 seconds` | stale or far-future expiry | request a new message and sign within five minutes |
| Arcade `402 Insufficient game points` | balance is empty and today's relief point is spent | wait for the next UTC day; granted points never pay for services |
| `429 Too many remote image fetches` | more than 6 remote image fetches a minute from one IP | back off for a minute or send inline Base64 |
| Alipay `403 Register this wallet` | wallet not a member | run `scripts/register_wallet.py` first |

Health probes:

```bash
curl -s https://a2a.musefish.trade/status.json
curl -s https://a2a.musefish.trade/health
```
