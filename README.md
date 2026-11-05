# A2A Web3 Server MCP - 智能体安全网关与 MCP 接入协议

[![MCP Version](https://img.shields.io/badge/MCP-2024--11--05-blue.svg)](https://modelcontextprotocol.io/)
[![Protocol](https://img.shields.io/badge/Web3-x402%20Autopay-green.svg)](https://the402.dev)
[![Network](https://img.shields.io/badge/Chain-Base%20(8453)-orange.svg)](https://base.org)
[![Status](https://img.shields.io/badge/Endpoint-ONLINE-brightgreen.svg)](https://a2a.musefish.trade)

生产级 Web3 Autonomous Agent 安全网关。本 MCP 服务对外提供两项核心智能体安全能力：
1. **Base 链上代币安全预检脱水 (`check_base_token_safety`)**：0.01 USDC / 次，实时检测貔貅盘（Honeypot）、蜜罐陷阱、所有权丢弃状态与真实流动性深度。
2. **EPH-02 闪电贷与 MEV 交易排雷沙盒 (`simulate_mev_route`)**：1.50 USDC / 次，零广播纯内存 EVM 执行追踪，精准侦测重入攻击、滑点劫持与隐藏税费。

---

## 🚀 快速接入 (1-Click Integration)

### 1. Cursor IDE 一键接入

在 Cursor 的 `Settings` -> `Features` -> `MCP` 中，选择 **Add new MCP server**：
- **Name**: `a2a-base-guard`
- **Type**: `HTTP / SSE`
- **Server URL**: `https://a2a.musefish.trade/mcp`

或者在项目根目录下创建 `.cursor/mcp.json`：
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

### 2. Claude Desktop (桌面端智能体)

在 Claude Desktop 配置文件 `claude_desktop_config.json` 中添加：

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

### 3. Smithery.ai & 全球 MCP 生态接入

支持通过 Smithery CLI 一键安装至您的本地 AI 工作流：
```bash
npx -y @smithery/cli install a2a-base-guard --client claude
```

---

## 🛠️ MCP 工具定义 (Tool Definitions)

本 MCP 服务严格遵循 **Model Context Protocol (2024-11-05)** 标准规范，支持 `initialize`、`ping`、`tools/list` 与 `tools/call`：

### 工具 1: `check_base_token_safety`
在 Base 主网对任意 ERC-20 代币合约进行安全脱水排雷。

* **输入参数**:
  ```json
  {
    "token_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
  }
  ```
* **返回数据结构**:
  - `status`: 代币安全评级 (`SAFE` / `SUSPICIOUS` / `HONEYPOT_RISK`)
  - `dexscreener`: 实时流动性池深度、交易量、FDV 与代币基本面
  - `security_verdict`: 恶意税率（Buy/Sell Tax）、增发后门与转账限制分析

---

### 工具 2: `simulate_mev_route`
在只读隔离沙盒中执行多跳路由 / 闪电贷调用的 EVM 执行追踪，返回全量排雷日志。

* **输入参数**:
  ```json
  {
    "calls": [
      {
        "target": "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24",
        "call_data": "0x...",
        "value": "0"
      }
    ]
  }
  ```
* **返回数据结构**:
  - `simulation_status`: 模拟结果 (`SUCCESS` / `REVERTED`)
  - `gas_used`: 实际消耗 Gas 总量
  - `state_diff`: 链上状态差异追踪（排查中间偷代币或滑点劫持风险）

---

## 💳 Web3 x402 自主支付结算机制

本服务全面支持 **HTTP 402 Payment Required** 自主微支付协议：
1. 智能体发起调用时，若无付款凭证，网关将返回包含发票信息的 `402` 响应；
2. 智能体可直接向结算网关指定的 Base 原生收款钱包转账对应金额的 USDC（Base USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`）；
3. 携带交易哈希 `X-TX-Hash` 与签名回传，网关秒级放行并交付深度排雷数据。

---

## 🌐 官方端点与元数据

- **MCP 服务端点**: `https://a2a.musefish.trade/mcp`
- **Agent 知识发现**: `https://a2a.musefish.trade/llms.txt`
- **x402 规范清单**: `https://a2a.musefish.trade/.well-known/x402-manifest.json`
- **OpenAI 兼容插件**: `https://a2a.musefish.trade/.well-known/ai-plugin.json`
- **the402 目录收录**: [the402.dev/a2a-base-guard](https://the402.dev)

---

## 📄 License
MIT License
