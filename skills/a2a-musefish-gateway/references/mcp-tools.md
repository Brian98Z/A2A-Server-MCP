# A2A Gateway — MCP tool reference

Endpoint: `POST https://a2a.musefish.trade/mcp` (Streamable HTTP, `2025-03-26`).
Legacy: `POST https://a2a.musefish.trade/mcp-legacy` (same JSON-RPC bodies, plain JSON replies).
Always send `accept: application/json, text/event-stream` and a real `User-Agent`.

Discovery:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

Every paid tool requires `payer_address` (the registered wallet) in `arguments`.
Unpaid calls never error out — they return `result.isError = true` plus the invoice in
`result.structuredContent` and `result._meta["x402/payment-required"]`.

## Paid tools

### check_base_token_safety — 0.01 USDC / 1 point

```json
{"name":"check_base_token_safety",
 "arguments":{"token_address":"0x4200000000000000000000000000000000000006",
              "payer_address":"0xYourWallet"}}
```

`token_address` must be a 40-hex Base ERC-20 address. The first call returns an invoice
with a freemium preview; after settlement the same call returns the full report:
`market` (price, liquidity, 24h volume, buy/sell counts), bytecode-level checks
(honeypot, mint, ownership, blacklist) and a verdict.

### simulate_mev_route_safety — 1.50 USDC / 150 points

```json
{"name":"simulate_mev_route_safety",
 "arguments":{"target_address":"0xRouter…","calldata":"0x…","value":0,
              "payer_address":"0xYourWallet"}}
```

`target_address` required; `calldata` optional hex; `value` optional wei integer.
Runs a read-only trace and reports reverts, slippage traps, fee-on-transfer hooks and
gas bombs.

### fast_code_audit — 0.02 USDC / 2 points

```json
{"name":"fast_code_audit",
 "arguments":{"prompt":"<Solidity code or security question>",
              "system_prompt":"optional role",
              "payer_address":"0xYourWallet"}}
```

Backed by a local Qwen model. If the model daemon is cold, the gateway returns 503
with `Retry-After` **before** issuing an invoice.

### deep_protocol_reasoning — 0.10 USDC / 10 points

Same schema as `fast_code_audit`, backed by a larger MoE model. Longer latency
(20–60 s); keep the MCP client timeout above 120 s.

### remove_image_background — 0.01 USDC / 1 point

```json
{"name":"remove_image_background",
 "arguments":{"image":"data:image/png;base64,… or https://…",
              "rem_mode":"RMBG-1.4",
              "add_background":"none",
              "payer_address":"0xYourWallet"}}
```

Returns a Base64 transparent PNG. Input may be a data URI or a public HTTPS URL.

## Free tools

### get_a2a_registration_protocol

```json
{"name":"get_a2a_registration_protocol","arguments":{}}
```

Returns `domain`, `message_template`, `nonce_bytes`, `expiration_max_seconds` and the
`pow` block (`algorithm`, `bits`, `format`). Current difficulty is 20 leading zero bits.

### generate_a2a_invitation

```json
{"name":"generate_a2a_invitation",
 "arguments":{"wallet_address":"0x…","chain_id":8453,"nonce":"<64 hex>",
              "expires_at":1790000000,"signature":"0x…","pow_counter":"123456",
              "inviter_code":"optional"}}
```

Equivalent to `POST /api/v1/invitations`. Returns the member snapshot, awarded points
and the referral link. The message that must be signed:

```
A2A Membership Registration
Domain: a2a.musefish.trade
Wallet: {wallet_lower}
Inviter code: {exact_code_or_none}
Chain ID: {chain_id}
Nonce: {64_lowercase_hex}
Expires: {unix_seconds}
Sign this message to register this wallet.
```

Proof of work: `SHA-256("a2a-registration-pow-v1:" + sha256(message) + ":" + sha256(signature) + ":" + counter)`
must have `bits` leading zero bits. `sha256()` values are lowercase hex.

## Response envelope

Settled call:

```json
{"jsonrpc":"2.0","id":11,"result":{
  "content":[{"type":"text","text":"{…}"}],
  "_meta":{"x402/payment-response":{"status":"settled","method":"points",
                                   "invoice_id":"inv-…","tx_hash":null}}}}
```

Payment required:

```json
{"jsonrpc":"2.0","id":10,"result":{
  "isError":true,
  "structuredContent":{
    "x402Version":2,
    "invoiceId":"inv-chec-…",
    "amountDisplay":"0.01 USDC",
    "accepts":[{"scheme":"exact","network":"eip155:8453","amount":"10000",
                "asset":"0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "payTo":"0xA75E1a201552Cad0282d01C09DC95d9559642FBb",
                "maxTimeoutSeconds":300}],
    "challengeToSign":"A2A Payment Settlement Authorization\nInvoice: inv-…\nTool: …\nPayer: 0x…\nChainID: 8453 (Base)",
    "free_preview":{"..." : "partial data"}},
  "_meta":{"x402/payment-required":{ …same object… }}}}
```

Sign `challengeToSign` verbatim with EIP-191 `personal_sign` using the payer wallet.
The recovered address must equal `payer_address`.

## Cold-backend warming (not a 503)

`fast_code_audit` and `deep_protocol_reasoning` run on an on-demand model. If the unpaid
call arrives while the model is stopped or another model is loaded, the gateway starts
the request's model in the background and returns:

```json
{"jsonrpc":"2.0","id":3,"result":{
  "isError":true,
  "structuredContent":{"status":"warming","tool":"deep_protocol_reasoning",
    "model":"deep","retry_after_s":20,"invoice_issued":false,"payment_owed":false,
    "detail":"The model backend is starting. No invoice was issued and no payment is owed."},
  "content":[{"type":"text","text":"{…same object…}"}]}}
```

Retry the identical call after `retry_after_s`; the invoice appears only when the model
answers `is_running: true` on the daemon. No payment, hold, or invoice is created while
warming.

## Settlement error semantics

| Status | Where | Meaning |
|---|---|---|
| 400 | `error.message` | Invalid arguments or missing `invoice_id`/`signature` |
| 403 | `error.message` | Signature does not match payer |
| 409 | `_meta["x402/payment-error"].status_code` | Settlement outcome uncertain; do not retry blindly |
| 429 | `error.message` | Promotional-points daily cap (3 per UTC day) |
| 503 | `error.message` | Gateway maintenance only; no invoice issued |
