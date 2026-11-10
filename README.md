# A2A Web3 Server MCP

An MCP gateway for Base token security, transaction simulation, AI analysis, image background removal, and wallet-based referrals.

## Connect

Use Streamable HTTP with MCP protocol version `2025-03-26`:

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

Call `tools/list` for current input schemas. The legacy JSON-RPC endpoint is `/mcp-legacy`.

### Client setup

In Cursor, add a new MCP server named `a2a-base-guard`, select Streamable HTTP, and use the URL above. In Claude Desktop, use its remote MCP connector where available; client versions differ in support for URL-based entries in `claude_desktop_config.json`. After connecting, refresh the server's tools and call `tools/list`. See the [integration guide](DISTRIBUTION_GUIDE.md) for additional discovery endpoints.

All paid tools require `payer_address` in their arguments. Common inputs:

| Tool | Inputs besides `payer_address` |
|---|---|
| `check_base_token_safety` | `token_address`: Base token contract address |
| `simulate_mev_route_safety` | `target_address`; optional hex `calldata` and integer `value` in wei |
| `fast_code_audit`, `deep_protocol_reasoning` | `prompt`; optional `system_prompt` |
| `remove_image_background` | `image` as base64 or a public URL; optional `rem_mode` and `add_background` |

For example, start a token report with `{"token_address":"0x4200000000000000000000000000000000000006","payer_address":"<your wallet address>"}`. The first call returns invoice details rather than the paid report. Follow the payment steps below; replace the example wallet with your own.

## Tools and pricing

| Tool | Purpose | Price |
|---|---|---|
| `check_base_token_safety` | Base token security and liquidity report | 0.01 USDC or 1 point |
| `simulate_mev_route_safety` | Read-only transaction route simulation | 1.50 USDC or 150 points |
| `fast_code_audit` | AI code security analysis | 0.02 USDC or 2 points |
| `deep_protocol_reasoning` | AI protocol analysis | 0.10 USDC or 10 points |
| `remove_image_background` | Transparent image background removal | 0.01 USDC or 1 point |
| `generate_a2a_invitation` | Register and generate a referral code and SVG | Free |
| `get_a2a_registration_protocol` | Get signing and proof-of-work parameters | Free |

## Membership and referrals

Register in one request through `generate_a2a_invitation` or `POST /api/v1/invitations`. Generate a random 32-byte lowercase hexadecimal nonce and an expiry no more than 300 seconds ahead; sign the registration message with EIP-191, solve the proof of work, then submit `wallet_address`, `nonce`, `expires_at`, `signature`, and `pow_counter`. `chain_id` defaults to 8453; `inviter_code` is optional. Fetch the exact message and current difficulty with `get_a2a_registration_protocol` or `GET /api/v1/invitations/protocol`.

Sign the following exact UTF-8 message with EIP-191 `personal_sign`, using LF line breaks and no trailing newline:

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

For proof of work, find a canonical nonnegative decimal counter such that SHA-256 of UTF-8 `a2a-registration-pow-v1:<message_sha256_hex>:<signature_sha256_hex>:<decimal_counter>` has the number of leading zero bits returned by the protocol endpoint. Both hashes are lowercase SHA-256 hex of the exact UTF-8 message and signature strings. Submit the resulting counter as `pow_counter`; use the exact inviter code in both message and request, or `none` in the message when omitted. Registration returns a referral code, invitation link, and SVG.

Each eligible referred registration awards the inviter one point, up to 200 lifetime referral points. Registration awards no points to the new member. Exact successful retries do not award again; existing rewards above the cap are not revoked. Check available, reserved, and total points at `GET /api/v1/members/{wallet_address}`.

Promotional points are limited to three service calls per wallet per UTC day; purchased points are not subject to that limit. Service concurrency limits still apply.

Members can purchase points through Alipay on the website. Agent service calls support Base USDC or membership points.

Registration IPs are best-effort: forwarded headers are unauthenticated and can be spoofed, while shared IPs can prevent legitimate registrations. Wallet signatures prove key control, not unique identity; the dotcode itself does not authenticate ownership.

## Payment and execution

For paid tools, provide `payer_address` and request an invoice. Sign `challengeToSign`, then resubmit the same inputs with `invoice_id` and `signature` in MCP `_meta["x402/payment"]`, plus `tx_hash` for Base USDC or `method: "points"` for eligible services. Invoice details are returned in `_meta["x402/payment-required"]`. MCP settlement failures set `isError` and expose the underlying status in `_meta["x402/payment-error"].status_code`; a tool-level error may use HTTP 200.

### Step-by-step payment

1. Call the selected tool with its normal arguments and `payer_address`. Read `invoiceId`, `challengeToSign`, network, recipient and amount from `_meta["x402/payment-required"]`.
2. Sign the exact `challengeToSign` text with the payer wallet using EIP-191 `personal_sign`. Never send your private key.
3. For USDC, transfer the invoice amount of native USDC on Base to the invoice recipient and retain the transaction hash. For points, skip the transfer and use `method: "points"` instead.
4. Call the same tool again with identical arguments and an MCP `params._meta` object like the following, replacing each placeholder:

```json
{
  "x402/payment": {
    "method": "points",
    "invoice_id": "<invoiceId>",
    "payer_address": "<payer wallet address>",
    "signature": "<EIP-191 signature>"
  }
}
```

For USDC, omit `method` and add `"tx_hash": "<transaction hash>"`. Do not combine a transaction hash with points. For the REST equivalents, request the invoice first, then repeat the same inputs with `invoice_id`, `payer_address` and `signature`; use the HTTP header `X-A2A-Payment-Method: points` for points, or include `tx_hash` for USDC. Invoices expire after five minutes. Partial points payments are not supported.

Verified on-chain and points calls share one backend execution slot per process. Up to 16 verified on-chain calls may wait for 60 seconds; points calls are rejected when the backend is busy or paid calls are waiting. A running points call is not interrupted. API and MCP request bodies have a 15-second read deadline and 15 MiB limit.

After dispatch, a failed or interrupted operation can have an uncertain outcome. Automatic redispatch is disabled, and backend admission can be quarantined until an operator confirms the remote task has stopped. The quarantine is process-local and does not survive restart; there is no automatic on-chain reconciliation or refund. Points remain reserved until an operator verifies the outcome and reconciles the hold. The queue deadline is not a backend execution deadline.

## Alipay

Alipay web payment collection is integrated. It is separate from MCP tool settlement and membership points.

## Administration

Configure `ADMIN_SESSION_TOKEN`, `CF_TURNSTILE_SITE_KEY`, and `CF_TURNSTILE_SECRET_KEY` for the admin dashboard. API clients can authenticate using `X-Admin-Token`. Existing blacklist entries require authenticated manual review and removal.

## Links

- Gateway: https://a2a.musefish.trade/
- MCP: https://a2a.musefish.trade/mcp
- Agent discovery: https://a2a.musefish.trade/llms.txt
- x402 manifest: https://a2a.musefish.trade/.well-known/x402-manifest.json
- License: [Apache-2.0](LICENSE)
