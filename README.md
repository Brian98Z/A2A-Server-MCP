# A2A Web3 Server MCP — Autonomous Agent Security Gateway

[![MCP Version](https://img.shields.io/badge/MCP-2024--11--05-blue.svg)](https://modelcontextprotocol.io/)
[![Protocol](https://img.shields.io/badge/Web3-x402%20Autopay-green.svg)](https://the402.dev)
[![Network](https://img.shields.io/badge/Chain-Base%20(8453)-orange.svg)](https://base.org)
[![Endpoint Status](https://img.shields.io/badge/Gateway-ONLINE-brightgreen.svg)](https://a2a.musefish.trade)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

A production-grade Model Context Protocol (MCP) server providing real-time Web3 security, pre-execution simulation, and zero-retention uncensored AI inference on Base Mainnet (ChainID `8453`). Built for autonomous AI agents, automated trading swarms, security auditors, and decentralized quant workflows.

The gateway exposes five primary agent tools backed by micro-settlement via the **HTTP 402 (x402)** protocol:
1. **`check_base_token_safety`**: Pre-trade token bytecode audit, liquidity depth verification, and honeypot risk assessment (0.01 USDC).
2. **`simulate_mev_route_safety`**: Ephemeral in-memory EVM trace simulation (EPH-02 sandbox) for flashloans and multi-hop swaps without on-chain broadcast (1.50 USDC).
3. **`fast_code_audit`**: Lightning-fast (93 t/s) uncensored smart contract and security audit powered by local Qwen3.5-9B (0.02 USDC).
4. **`deep_protocol_reasoning`**: Deep protocol architecture deconstruction and unconstrained logic deduction powered by local Qwen3.6-35B MoE (0.10 USDC).
5. **`remove_image_background`**: One-click high-precision image matting and background removal powered by local native PyTorch RMBG-1.4 CUDA model (0.01 USDC). Returns transparent RGBA PNG (Base64). Completely standalone, zero ComfyUI dependency.

---

## ⚡ Quick Start & 1-Click Integration

### 1. Cursor IDE

Add the MCP server directly in Cursor via **Settings** -> **Features** -> **MCP** -> **Add new MCP server**:
- **Name**: `a2a-base-guard`
- **Type**: `HTTP / SSE`
- **Server URL**: `https://a2a.musefish.trade/mcp`

Or drop the following config into `.cursor/mcp.json` at your project root:

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

---

### 2. Claude Desktop

Add the endpoint to your `claude_desktop_config.json`:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

---

### 3. Smithery.ai & Open MCP Registries

Install directly into your local agent runtime using the Smithery CLI:

```bash
npx -y @smithery/cli install a2a-base-guard --client claude
```

---

## 🛠️ Tool Specifications

This server strictly conforms to the **Model Context Protocol (2024-11-05)** specification, supporting `initialize`, `ping`, `tools/list`, and `tools/call`.

### Tool 1: `check_base_token_safety`

Performs an on-chain bytecode safety assessment and liquidity dehydrator report for any token contract on Base.

- **Pricing**: 0.01 USDC ($0.01)

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "token_address": {
      "type": "string",
      "description": "Base ERC-20 contract hex address (e.g. 0x4200000000000000000000000000000000000006 for WETH)"
    }
  },
  "required": ["token_address"]
}
```

#### Example Response
```json
{
  "status": "SAFE",
  "token_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "symbol": "USDC",
  "security_report": {
    "honeypot_risk": false,
    "buy_tax_bps": 0,
    "sell_tax_bps": 0,
    "ownership_renounced": true,
    "has_blacklist_privilege": false
  },
  "market_snapshot": {
    "liquidity_usd": 482500000,
    "volume_24h": 128400000,
    "fdv": 482500000
  }
}
```

---

### Tool 2: `simulate_mev_route_safety`

Executes multi-call routes in a clean, read-only EVM sandbox (EPH-02) to detect sandwich attacks, state discrepancies, reentrancy traps, and slippage anomalies before transaction broadcasting.

- **Pricing**: 1.50 USDC ($1.50)

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "target_address": {
      "type": "string",
      "description": "Smart contract address on Base"
    },
    "calldata": {
      "type": "string",
      "description": "Hex encoded calldata (e.g. 0x06fdde03)"
    },
    "value": {
      "type": "integer",
      "description": "Native ETH value in wei (default 0)"
    }
  },
  "required": ["target_address"]
}
```

#### Example Response
```json
{
  "status": "SUCCESS",
  "gas_used": 142850,
  "reverted": false,
  "state_diff_summary": {
    "transfers_detected": 2,
    "intermediate_balance_loss": false,
    "slippage_protected": true
  }
}
```

---

### Tool 3: `fast_code_audit` (New 🚀)

Zero-refusal, lightning-fast smart contract and code security audit powered by local Qwen3.5-9B (throughput ~93 t/s on RTX 5070 Ti). Identifies honeypots, malicious backdoors, reentrancy vulnerabilities, transfer tax traps, and hidden mints with zero moralizing refusal.

- **Pricing**: 0.02 USDC ($0.02)
- **Privacy Model**: Pure ephemeral memory execution (Zero log retention, no prompt or output persistence).

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string",
      "description": "Solidity code snippet, contract logic, or security question to audit (Max 16,384 chars)"
    },
    "system_prompt": {
      "type": "string",
      "description": "Optional customized system role prompt"
    }
  },
  "required": ["prompt"]
}
```

#### Example Response
```json
{
  "status": "SUCCESS",
  "model": "Qwen3.5-9B-Uncensored-Aggressive",
  "audit_report": "### Critical Findings:\n- [CRITICAL] Hidden Owner Backdoor: Owner can freeze any account.\n- [HIGH] Reentrancy in withdraw(): State updated after transfer.",
  "latency_ms": 22384.27,
  "tokens_consumed": 2168,
  "security_notice": "Pure ephemeral memory inference. Zero retention, no logging."
}
```

---

### Tool 4: `deep_protocol_reasoning` (New 🚀)

Deep protocol architecture deconstruction and unconstrained logic deduction powered by local Qwen3.6-35B MoE. Analyzes multi-contract cross-chain interactions, mathematical flashloan constraints, game-theoretic attack vectors, and protocol edge cases.

- **Pricing**: 0.10 USDC ($0.10)
- **Architecture**: 35B MoE with 256k context depth.

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string",
      "description": "Complex protocol architecture, mathematical arbitrage model, or system design to evaluate (Max 16,384 chars)"
    },
    "system_prompt": {
      "type": "string",
      "description": "Optional customized system role prompt"
    }
  },
  "required": ["prompt"]
}
```

#### Example Response
```json
{
  "status": "SUCCESS",
  "model": "Qwen3.6-35B-A3B-Uncensored",
  "reasoning_report": "### Mathematical Protocol Proof:\n1. Flashloan invariant Δx · Δy >= k is strictly violated when slippage exceeds 32 bps under multi-pool pool balancing...\n2. Arbitrage convergence theorem proof shows dead-lock condition at block boundary.",
  "latency_ms": 31250.40,
  "tokens_consumed": 3890,
  "security_notice": "Pure ephemeral memory inference. Zero retention, no logging."
}
```

---

## 💳 Autonomous Settlement: x402 Protocol

This server integrates the **Coinbase x402 v2 (Payment Required)** standard for machine-to-machine micropayments:

1. When calling via standard HTTP REST or MCP `tools/call`, an unauthenticated request receives a structured `HTTP 402` with an invoice ID, challenge text to sign, and exact deposit requirements.
2. The agent transfers the specified amount of native Base USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) to the designated gateway wallet (`0xA75E1a201552Cad0282d01C09DC95d9559642FBb`).
3. Resending the request with `tx_hash`, `invoice_id`, `payer_address`, and an EIP-191 cryptographic payment signature immediately clears the invoice and delivers the verified payload.

---

## 🌐 Public Discovery & Agent Metadata

- **MCP Endpoint**: `https://a2a.musefish.trade/mcp`
- **Machine Discovery (AEO)**: `https://a2a.musefish.trade/llms.txt`
- **x402 Specification**: `https://a2a.musefish.trade/.well-known/x402-manifest.json`
- **OpenAI Compatible Plugin**: `https://a2a.musefish.trade/.well-known/ai-plugin.json`
- **Verified Listing**: Indexed on [the402.dev](https://the402.dev) with verified `answers 402` status.

---

## 📄 License

Distributed under the [Apache-2.0 License](LICENSE).
