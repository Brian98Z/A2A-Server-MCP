# A2A Web3 Agent Distribution and Integration Guide

The gateway offers Base token safety checks and MEV route simulation alongside AI and image services. Use the MCP endpoint below to discover current tools and pricing.

Service availability: there is no hardcoded business-hours or weekend closure. Services are available whenever running; planned maintenance and downstream outages return HTTP `503`, while admission contention returns `429` with `Retry-After`. Availability is not a guarantee that every backend is healthy. For paid calls, retain invoice and transaction identifiers and retry the same payment rather than paying again.

---

## 1. Cursor / Claude Desktop / VS Code

Use `/mcp` with stateless Streamable HTTP. The legacy custom JSON-RPC endpoint is `/mcp-legacy`. Forwarded registration IP headers are not authenticated and cannot reliably prevent abuse.

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

**Selected tools:**
- `check_base_token_safety`: Base token security report (0.01 USDC).
- `simulate_mev_route_safety`: Simulate a Base transaction route (1.50 USDC or 150 points).
- `fast_code_audit`: AI code security analysis (0.02 USDC or 2 points).
- `generate_a2a_invitation`: Free EIP-191 wallet registration with SHA-256 proof of work; returns a referral code and SVG. Referral rewards are capped at 200 points per inviter. Only promotional-point redemptions are limited to three calls per wallet per UTC day; purchased-only redemptions bypass that limit. Active and uncertain promotional operations occupy a slot until released.
- `get_a2a_registration_protocol`: Retrieve the canonical signing message and current proof-of-work difficulty.
- `get_arcade_auth_message`: Return the EIP-191 arcade message to sign; same nonce/expiry rules as registration (300s TTL, nonce burned after one call).
- `slots_state`: Read arcade balance, pity meter, session stats and recent spins for the signed wallet. An empty balance is topped up with one free game point per UTC day.
- `slots_spin`: Play one server-authoritative spin for 1 game point. Prizes are 1/2/5/10/100 game points; the 15th consecutive miss always pays. Granted points (welcome grant, daily relief) are arcade-only; only won points can pay points-rail gateway calls.

Sign the following UTF-8 message with LF line separators and no trailing LF:

```text
A2A Membership Registration
Domain: a2a.musefish.trade
Wallet: <lowercase canonical address>
Inviter code: <exact referral code | none>
Chain ID: <unsigned canonical decimal>
Nonce: <64 lowercase hex chars>
Expires: <canonical Unix-seconds decimal>
Sign this message to register this wallet.
```

Exact successful requests are replayable without additional rewards; failed transactions do not consume the nonce. Each eligible referral awards one point, up to 200 lifetime referral points. Previously awarded points above this cap are not revoked. The dotcode does not prove wallet ownership.

---

## 2. ElizaOS Integration

An Eliza plugin exists in the gateway project. It can be added to an Eliza project's `packages/` directory and referenced in the character configuration:

```json
"plugins": ["@a2a/eliza-plugin-base-token-guard"]
```

The plugin targets the Base token report endpoint and its x402 payment flow.

---

## 3. Discovery Endpoints

| Service | Endpoint |
| :--- | :--- |
| MCP | `https://a2a.musefish.trade/mcp` |
| Agent discovery | `https://a2a.musefish.trade/llms.txt` |
| OpenAI plugin metadata | `https://a2a.musefish.trade/.well-known/ai-plugin.json` |
| x402 manifest | `https://a2a.musefish.trade/.well-known/x402-manifest.json` |
| Smithery manifest | `smithery.json` in this repository |

### Alipay

Alipay web payment collection is integrated separately from MCP tool settlement and membership points.

---

## 4. Distribution

Keep the published MCP schema and documentation aligned with the running gateway before sharing integration instructions.

For on-chain payments, wait for the receipt and gateway confirmation. If settlement returns HTTP 425 or its response is lost, resubmit the same invoice ID, transaction hash, and signature when the invoice remains valid; do not transfer again. On timeout, preserve both identifiers for recovery.

---

## 5. Interface Update Checklist

When adding or changing an endpoint:
1. Update the gateway's MCP tool discovery and relevant machine-readable metadata.
2. Update `smithery.json` and `README.md` with current inputs, pricing, and payment behavior.
3. Publish only the intended MCP interface and documentation files; do not publish private service source, credentials, or deployment configuration.
