# Payments — points, USDC on Base, Alipay

All amounts are USDC with 6 decimals unless stated otherwise. The gateway never accepts
a payment without a bound invoice: the invoice fixes the tool, the canonical argument
hash, the amount and a 300-second expiry.

## 1. Points (fastest path, no funding needed)

Signup grants 2 points (3 with an inviter code). Points are spent at these rates:

| Tool | Points | USDC equivalent |
|---|---|---|
| `check_base_token_safety` | 1 | 0.01 |
| `remove_image_background` | 1 | 0.01 |
| `fast_code_audit` | 2 | 0.02 |
| `deep_protocol_reasoning` | 10 | 0.10 |
| `simulate_mev_route_safety` | 150 | 1.50 |

Promotional (signup/referral) points: at most **3 redemptions per UTC day**.
Purchased points have no daily cap.

### Settlement payload

```json
{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{
  "name":"check_base_token_safety",
  "arguments":{"token_address":"0x4200…0006","payer_address":"0xYourWallet"},
  "_meta":{"x402/payment":{
    "method":"points",
    "invoice_id":"inv-chec-f3616222abf742df",
    "payer_address":"0xYourWallet",
    "signature":"0x<eip191 signature over challengeToSign>"}}}}
```

`scripts/pay_with_points.py` implements the whole loop (invoice → sign → settle) and
prints the settled payload. It refuses to spend when the balance is insufficient.

## 2. USDC on Base (x402)

1. Call the tool with `payer_address` and no payment metadata.
2. Read `structuredContent.accepts[0]`:
   - `amount` raw units (`10000` = 0.01 USDC)
   - `asset` `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
   - `payTo` `0xA75E1a201552Cad0282d01C09DC95d9559642FBb`
   - `network` `eip155:8453`
3. Send ≥ `amount` USDC from the payer wallet to `payTo` on Base. Any wallet can pay,
   but `payer_address` and the transfer `from` must match.
4. Re-call within 300 seconds with:

```json
{"_meta":{"x402/payment":{
  "invoice_id":"inv-…",
  "payer_address":"0xYourWallet",
  "tx_hash":"0x<transfer transaction hash>",
  "signature":"0x<eip191 over challengeToSign>"}}}
```

Verification rules enforced on-chain: receipt status 1, at least **2 confirmations**,
exact USDC contract, `Transfer` event, recipient equals `payTo`, sender equals
`payer_address`, amount ≥ invoice amount.

If the transaction is mined slowly, retry the settlement call with the same tuple; a
409 means the outcome is uncertain — reconcile the member balance before retrying.

## 3. Alipay packages (CNY, human checkout)

| Package id | Price | Points |
|---|---|---|
| `basic` | ¥100 | 1000 |
| `plus` | ¥200 | 2100 |
| `pro` | ¥500 | 5500 |

Sequence (wallet must already be registered):

```bash
# 1. Challenge
curl -s "https://a2a.musefish.trade/api/v1/wallet/challenge?wallet_address=0xYourWallet"

# 2. Sign challenge.message with EIP-191 personal_sign, then log in.
#    Origin must be exactly https://a2a.musefish.trade
curl -s -X POST https://a2a.musefish.trade/api/v1/wallet/login \
  -H 'content-type: application/json' -H 'Origin: https://a2a.musefish.trade' \
  -c cookies.txt \
  -d '{"wallet_address":"0xYourWallet","nonce":"<nonce>","signature":"0x<sig>"}'

# 3. Create the order (idempotency_key is required; reuse it for retries)
curl -s -X POST https://a2a.musefish.trade/alipay/topup \
  -H 'content-type: application/json' -H 'Origin: https://a2a.musefish.trade' \
  -b cookies.txt \
  -d '{"package_id":"basic","idempotency_key":"agent-order-001"}'
```

Response:

```json
{"order_no":"PAY-…","checkout_url":"https://a2a.musefish.trade/alipay/checkout/PAY-…",
 "amount":100,"points":1000}
```

Open `checkout_url` in a human-visible browser; the payment is completed by the user in
Alipay. Points are credited after the Alipay notification is verified. Poll
`GET /api/v1/members/{wallet}` or `GET /api/v1/wallet/session` (with the cookie) to
detect crediting.

Endpoints without a wallet session return 401; a wallet that is not registered returns
403 and must register first.

## 4. Invoice lifecycle

| State | Meaning |
|---|---|
| issued (402) | Bound to tool + params hash; expires in 300 s |
| settled | Payment verified; result returned in the same call |
| expired | Do not reuse the invoice; issue a new one |
| 409 | Uncertain; reconcile, never blind-retry |

A single invoice cannot be reused with different arguments: the canonical params hash
binds it to the first call.
