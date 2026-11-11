---
name: a2a-musefish-gateway
description: Call the A2A Gateway MCP server (https://a2a.musefish.trade/mcp) to vet Base-mainnet tokens before trading, simulate EVM calldata, run AI code audits or deep protocol reasoning, and remove image backgrounds. Covers free wallet registration with signup points, the x402 402-to-invoice flow, points redemption signed with EIP-191, and USDC-on-Base or Alipay top-ups. Use whenever an agent needs pre-trade Base token verification, metered inference, or a pay-per-call security verdict.
license: Apache-2.0
---

# A2A Gateway — MCP usage, onboarding and payments

One remote MCP server exposes metered Web3 and AI services. Paid calls settle per request
in USDC on Base (x402) or in membership points. Registration is free and grants points,
so a brand-new agent can complete a real paid call without funding a wallet.

Server facts you can rely on:

| Item | Value |
|---|---|
| MCP endpoint | `https://a2a.musefish.trade/mcp` (Streamable HTTP, protocol `2025-03-26`) |
| Legacy JSON-RPC | `https://a2a.musefish.trade/mcp-legacy` (plain POST, JSON responses) |
| Chain | Base mainnet, `eip155:8453` |
| Settlement asset | USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Recipient | `0xA75E1a201552Cad0282d01C09DC95d9559642FBb` |
| Invoice TTL | 300 seconds |
| Registration script | `https://a2a.musefish.trade/register_a2a.py` |
| Availability probe | `https://a2a.musefish.trade/status.json` |
| Advisory service window | Monday–Friday 11:00–22:00 (UTC+8) — information only, calls are never blocked by the clock |

## When to use this skill

- A trade or swap is about to be executed on Base and the token must be checked for
  honeypots, rugpulls, mint/blacklist backdoors or fake liquidity.
- Calldata must be simulated read-only before broadcasting.
- An agent needs paid AI reasoning, a code security audit, or background removal.
- A user wants to register a wallet, earn signup points, or top up with Alipay/USDC.

## Install and keep it installed

### 1. Add the MCP server

`mcp.json` (Cursor, Claude Code, Cline, Windsurf, Continue, or any MCP client that
supports remote servers):

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

Claude Code:

```bash
claude mcp add --transport http a2a-base-guard https://a2a.musefish.trade/mcp
```

### 2. Install this skill so the workflow persists

Copy this directory into the client's skill folder. The folder name must match the
`name` in the frontmatter.

| Client | Location |
|---|---|
| Claude Code (user) | `~/.claude/skills/a2a-musefish-gateway/` |
| Claude Code (project) | `.claude/skills/a2a-musefish-gateway/` |
| OMP | `~/.omp/agent/skills/a2a-musefish-gateway/` |
| Cursor | keep the MCP entry above; add `references/mcp-tools.md` to `.cursor/rules/` if rules are used |
| Codex CLI / generic agents | append the "Quick reference" section of `references/mcp-tools.md` to `AGENTS.md` |

```bash
git clone https://github.com/Brian98Z/A2A-Server-MCP /tmp/a2a-server-mcp
cp -r /tmp/a2a-server-mcp/skills/a2a-musefish-gateway ~/.claude/skills/
```

Skills are loaded at client start, so restart the client once after copying. If the
client is cloud-hosted, commit the folder to the project repository instead.

## Quick reference — calling any tool

MCP clients do this for you. When calling over raw HTTP, POST JSON-RPC 2.0 and accept
both JSON and SSE replies:

```bash
curl -sS https://a2a.musefish.trade/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -H 'user-agent: your-agent/1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Always send a real `User-Agent`; default library agents (bare `python-urllib/3.x`) can be
challenged by the edge network.

A paid call always carries the payer in the arguments:

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
  "name":"check_base_token_safety",
  "arguments":{"token_address":"0x4200000000000000000000000000000000000006",
               "payer_address":"0xYourRegisteredWallet"}}}
```

## First-run test for a new user (about two minutes)

This is the acceptance test for the skill. Run it once after installing.

### Step 1 — confirm the server is reachable

Call `tools/list`. Expect 7 tools:

```
generate_a2a_invitation, get_a2a_registration_protocol, check_base_token_safety,
simulate_mev_route_safety, fast_code_audit, deep_protocol_reasoning,
remove_image_background
```

### Step 2 — register a wallet and receive signup points

```bash
pip install eth-account requests
python scripts/register_wallet.py
```

The script generates a wallet, requests the canonical message and PoW difficulty
(20 leading zero bits), signs it (EIP-191), proves work, posts to
`/api/v1/invitations`, and saves the credential file `a2a-registration-<wallet>.json`
with owner-only permissions.

Expected:

```
free points credited: 2
your invite link: https://a2a.musefish.trade/?inviter_code=<code>
```

Add `--inviter <code>` to receive 3 points instead of 2. Keep the credential file:
it is the only copy of the generated private key. To register a wallet you already
control, pass `PRIVATE_KEY=0x... python scripts/register_wallet.py` and store the key
yourself.

### Step 3 — confirm the balance

```bash
curl -sS "https://a2a.musefish.trade/api/v1/members/0xYourWallet" -H 'user-agent: your-agent/1.0'
```

```json
{"wallet_address":"0x…","points":2,"purchased_points":0,"referral_points":2, …}
```

### Step 4 — perform the first paid call with points

```bash
python scripts/pay_with_points.py \
  --wallet-file a2a-registration-<wallet>.json \
  --tool check_base_token_safety \
  --args '{"token_address":"0x4200000000000000000000000000000000000006"}'
```

The helper performs the complete loop: call → receive `402`-style invoice in
`structuredContent` → sign `challengeToSign` → re-call with
`_meta["x402/payment"]` → print the settled result.

Expected: a JSON verdict with `market`, `security`/`verdict` fields, and the balance
dropping by 1 point. If the balance was 2 and two calls were made, it reads 0.

### Step 5 (optional) — on-chain settlement

Only when points are exhausted or a tool costs more than the balance. See
`references/payments.md` for the USDC and Alipay flows.

## Payment paths

### A. Membership points

- Signup: 2 points, or 3 with an inviter code.
- Prices: 1 point ≈ 0.01 USDC for the cheap tools; see the table below.
- Promotional points are limited to **3 redemptions per UTC day**; purchased points
  are not limited.
- Settle with `_meta["x402/payment"] = {"method":"points","invoice_id":…,
  "signature":…,"payer_address":…}`.

### B. USDC on Base (x402)

1. Call the tool without payment to receive the invoice.
2. Read `structuredContent.accepts[0]`: `amount` (raw units, 6 decimals), `payTo`,
   `asset`, `network`.
3. Transfer at least `amount` of USDC on Base to `payTo` from the payer wallet.
4. Re-call with `_meta["x402/payment"] = {"invoice_id":…, "tx_hash":"0x…",
   "payer_address":…, "signature":…}` where `signature` is EIP-191 over
   `challengeToSign`.

The gateway verifies the receipt: transaction status 1, **at least 2 confirmations**,
exact USDC contract, `Transfer` event to the recipient, `from` equal to the payer, and
amount ≥ required.

### C. Alipay point packages

| Package | Price (CNY) | Points |
|---|---|---|
| `basic` | 100 | 1000 |
| `plus` | 200 | 2100 |
| `pro` | 500 | 5500 |

The Alipay checkout is browser-based. The programmatic sequence is in
`references/payments.md`: wallet-signature login → session cookie →
`POST /alipay/topup` → open `checkout_url` in a browser so the human pays.
The wallet must already be registered before ordering.

## Tools and prices

| Tool | Purpose | USDC | Points |
|---|---|---|---|
| `check_base_token_safety` | Base token security + liquidity verdict | 0.01 | 1 |
| `simulate_mev_route_safety` | Read-only EVM route simulation | 1.50 | 150 |
| `fast_code_audit` | Code security audit (local model) | 0.02 | 2 |
| `deep_protocol_reasoning` | Deep protocol analysis (local MoE) | 0.10 | 10 |
| `remove_image_background` | Transparent PNG background removal | 0.01 | 1 |

Input requirements, response shapes and worked examples: `references/mcp-tools.md`.

## Service window (advisory)

The gateway is actively monitored **Monday–Friday, 11:00–22:00 (UTC+8)**. Outside that
window it keeps accepting calls, but maintenance and backend restarts are more likely,
so `503` is more probable. The clock is not enforced: no request is rejected because
of the hour. A `503` is returned before any invoice is issued, so nothing is owed.

Plan long or paid runs inside the window and treat an out-of-window `503` as expected
rather than an outage.

### Cold backends never produce a 503 (and never an invoice)

Model-backed tools are warmed on demand. The first unpaid call returns a normal tool
result with `isError: true` and:

```json
{"status":"warming","tool":"fast_code_audit","model":"fast","retry_after_s":10,
 "invoice_issued":false,"payment_owed":false}
```

Wait `retry_after_s` (10 s fast, 20 s deep) and retry the identical call. The invoice is
issued only when the model is ready, so an agent can never pay for a cold backend. A
`503` now means genuine maintenance only. REST endpoints mirror this with `202 Accepted`,
`Retry-After`, and the same JSON body.

## Errors and what to do

| Symptom | Meaning | Action |
|---|---|---|
| `isError: true` with `invoiceId` | Payment required, invoice issued | Pay (points or USDC) and re-call within 300 s |
| `isError: true` with `status: "warming"` | Backend cold; warm-up started, **no invoice** | Wait `retry_after_s`, repeat the same call |
| HTTP 400 `invoice_id, payer_address, and signature are strictly required` | Missing payment metadata | Send all three fields |
| HTTP 409 | Settlement outcome uncertain | **Do not auto-retry.** Query the member balance, then decide |
| HTTP 429 `Daily promotional-points redemption limit` | 3 promo redemptions already used today (UTC) | Wait for the next UTC day, or pay with purchased points/USDC |
| HTTP 503 with `Retry-After` | Gateway in maintenance (not a cold backend) | Retry after the delay; no payment is owed |
| HTTP 202 on a REST endpoint | Backend warming (`status: "warming"`) | Wait `Retry-After`, repeat the call |
| HTTP 401 on Alipay endpoints | Wallet session missing | Log in with the wallet signature flow |

## Guardrails

- Never print, transmit, or store a private key outside the credential file the
  registration script writes.
- Sign only the exact `challengeToSign` string returned by the server; never sign
  arbitrary text.
- Do not reuse an invoice across different tool arguments — the gateway binds the
  invoice to a canonical params hash.
- Retry on 503 only; never on 409.
- AI results are ephemeral by design: the gateway does not retain prompts or outputs.
