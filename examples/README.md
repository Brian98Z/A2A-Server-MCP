# Examples

Three runnable calls against the live gateway. Each one is copy-paste; no API key.

## 1. REST: free preview inside the 402

```bash
curl -s -X POST https://a2a.musefish.trade/api/v1/token-report \
  -H 'Content-Type: application/json' \
  -d '{"token_address":"0x4200000000000000000000000000000000000006"}' | jq '{invoiceId, amountDisplay, preview: .free_preview}'
```

The response is a real `402`. Read `free_preview` as data, not as a failure. Add `payer_address` to receive the full-report invoice.

## 2. MCP: initialize, list tools, call one

```bash
curl -s -X POST https://a2a.musefish.trade/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"example","version":"1"}}}'

curl -s -X POST https://a2a.musefish.trade/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

curl -s -X POST https://a2a.musefish.trade/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"check_base_token_safety","arguments":{"token_address":"0x4200000000000000000000000000000000000006"}}}'
```

Responses are single JSON-RPC objects; the server does not emit SSE framing.

## 3. Membership: one command, then settle with points

```bash
curl -fsSL https://a2a.musefish.trade/register_a2a.py | python3 -
```

Registration signs an EIP-191 message, solves the SHA-256 proof of work, and credits 2 points (3 with an inviter code). Settle a paid tool with the returned wallet:

```bash
curl -s -X POST https://a2a.musefish.trade/api/v1/token-report \
  -H 'Content-Type: application/json' \
  -H 'x-a2a-payment-method: points' \
  -d '{"token_address":"0x4200000000000000000000000000000000000006","invoice_id":"<from the 402>","payer_address":"<wallet>","signature":"<EIP-191 over challengeToSign>"}'
```

Protocol details: `GET /api/v1/invitations/protocol`. Error shapes: every failure returns `error`, `detail`, `hint` and, where relevant, `missing_fields` / `retry_after_s`.
