# A2A Web3 智能体分发与多平台接入指引 (Agent Distribution Guide)

本网关对外统一提供 Base 链上代币安全预检（0.01 USDC）与 EPH-02 MEV 排雷沙盒（1.50 USDC）两项自主付费服务。以下为各大主流智能体生态与开发者工具的接入指引：

---

## 1. Cursor / Claude Desktop / VSCode (MCP 一键直连)

在 Cursor 或 Claude Desktop 的 MCP 配置文件中加入以下端点即可直接挂载：

```json
{
  "mcpServers": {
    "a2a-base-guard": {
      "url": "https://a2a.musefish.trade/mcp"
    }
  }
}
```

**智能体具备的工具能力**：
- `check_base_token_safety`: 在 Base 链上对任意 ERC-20 代币进行字节码与貔貅盘安全排雷（0.01 USDC/次）。
- `simulate_mev_route`: 在 EPH-02 隔离沙盒中预演多跳闪电贷/套利交易，预估 Gas 与滑点（1.50 USDC/次）。

---

## 2. ElizaOS 自主交易智能体 (Autonomous Trading Agent)

项目目录内置了官方插件 `eliza-plugin/`，支持 Eliza 框架的自主交易机器人集成：

1. 拷贝 `eliza-plugin` 至 Eliza 项目的 `packages/` 目录下；
2. 在 Agent 角色配置（`character.json`）中添加插件：
   ```json
   "plugins": ["@a2a/eliza-plugin-base-token-guard"]
   ```
3. Agent 遇到任何 Base 代币交易决策时，将自主请求 `https://a2a.musefish.trade/api/v1/token-report` 并完成 x402 自主结算。

---

## 3. Web3 & A2A 协议全球目录收录状态

| 平台 / 目录 | 协议类型 | 状态 | 接入链接 / 规范 |
| :--- | :--- | :--- | :--- |
| **the402.dev** | HTTP 402 + Base USDC | **已认证收录** | [the402.dev 目录](https://the402.dev)（带 `answers 402` 认证标） |
| **Glama.ai** | Model Context Protocol | **已提交收录** | [Glama MCP Directory](https://glama.ai/mcp/servers) |
| **Smithery.ai** | MCP Server Manifest | **配置就绪** | 仓库根目录包含 `smithery.json`，随时可通过 GitHub 导入 |
| **LLMs.txt (AEO)** | AI 知识搜索引擎 | **在线就绪** | `https://a2a.musefish.trade/llms.txt` |
| **OpenAI Plugin** | GPTs / ChatGPT Actions | **在线就绪** | `https://a2a.musefish.trade/.well-known/ai-plugin.json` |
| **x402 Manifest** | Web3 自主智能体标准 | **在线就绪** | `https://a2a.musefish.trade/.well-known/x402-manifest.json` |

---

## 4. 商业转化转化路径建议

1. **GitHub 开源生态分发**：将 `smithery.json`、`eliza-plugin/` 与 `README.md` 推送至公开 GitHub 仓库，Smithery.ai 会自动抓取并将其列入全球 MCP 市场首屏。
2. **在 Base / Farcaster 生态传播**：Farcaster 上的自主交易 Frame 和基于 Bountycaster 的 Agent 均已原生支持 x402 协议，可直接分享 `/api/v1/token-report` 的 x402 规范链接。

---

## 5. 新增功能自动分发准则 (Auto-Distribution Contract)

凡在 A2A 网关中**新增、升级或调整任何商业化收费功能/端点**时，必须确保执行以下全自动分发闭环：
1. **网关内生自驱动 (Native Service Broadcast)**：
   - 在 `server.py` 的应用启动生命周期中，自动异步调用 `register_global_agents.py`；
   - 自动向 `the402.dev`、`Glama.ai`、`Smithery.ai` 提交新端点及机读注释，实现无需人工点击脚本的自动广播。
2. **AEO 机读协议元数据自更新**：
   - `/.well-known/x402-manifest.json`、`/.well-known/ai-plugin.json`、`/llms.txt`、`/mcp` (tools/list) 必须内联暴露最新工具入参及定价。
3. **开源生态自动推送**：
   - 同步更新根目录的 `smithery.json` 与 `README.md`，并通过 `github-code-sync` 技能将新工具英文 Schema 推送至 GitHub，促使全球智能体索引平台自动重新爬取与打分。
