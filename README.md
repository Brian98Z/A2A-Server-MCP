# A2A Web3 Server MCP — Autonomous Agent Security Gateway

[![MCP Version](https://img.shields.io/badge/MCP-2024--11--05-blue.svg)](https://modelcontextprotocol.io/)
[![Protocol](https://img.shields.io/badge/Web3-x402%20Autopay-green.svg)](https://the402.dev)
[![Network](https://img.shields.io/badge/Chain-Base%20(8453)-orange.svg)](https://base.org)
[![Endpoint Status](https://img.shields.io/badge/Gateway-ONLINE-brightgreen.svg)](https://a2a.musefish.trade)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

A production-grade Model Context Protocol (MCP) server providing real-time Web3 security and pre-execution simulation on Base Mainnet (ChainID `8453`). Built for autonomous AI agents, automated trading swarms, and decentralized quant workflows.

The gateway exposes two primary agent tools backed by micro-settlement via the **HTTP 402 (x402)** protocol:
1. **`check_base_token_safety`**: Pre-trade token bytecode audit, liquidity depth verification, and honeypot risk assessment (0.01 USDC).
2. **`simulate_mev_route`**: Ephemeral in-memory EVM trace simulation (EPH-02 sandbox) for flashloans and multi-hop swaps without on-chain broadcast (1.50 USDC).

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

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "token_address": {
      "type": "string",
      "description": "Base ERC-20 contract address (0x...)"
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

### Tool 2: `simulate_mev_route`

Executes multi-call routes in a clean, read-only EVM sandbox to detect sandwich attacks, state discrepancies, reentrancy traps, and slippage anomalies before transaction broadcasting.

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "calls": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target": { "type": "string", "description": "Target contract address" },
          "call_data": { "type": "string", "description": "Hex-encoded transaction calldata" },
          "value": { "type": "string", "description": "ETH value in wei (default 0)" }
        },
        "required": ["target", "call_data"]
      }
    }
  },
  "required": ["calls"]
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

## 💳 Autonomous Settlement: x402 Protocol

This server integrates the **HTTP 402 (Payment Required)** standard for machine-to-machine micropayments:

1. When calling via standard HTTP REST, an unauthenticated request receives a structured `HTTP 402` with an invoice ID and exact deposit requirements.
2. The agent transfers the specified amount of native Base USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) to the designated gateway wallet (`0xA75E1a201552Cad0282d01C09DC95d9559642FBb`).
3. Resending the request with `X-TX-Hash` and an EIP-191 cryptographic payment claim immediately clears the invoice and delivers the verified payload.

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
