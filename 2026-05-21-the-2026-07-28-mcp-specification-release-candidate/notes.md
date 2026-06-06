# 阅读笔记

## 一句话总结

MCP `2026-07-28` release candidate 的本质，是把 MCP 从依赖协议级 session 的交互模型，重构为更接近普通 HTTP API 的无状态、可路由、可缓存、可追踪协议。

## 关键概念

- **协议层无状态**：请求本身携带协议版本、方法、名称、客户端信息和能力等上下文，不再依赖 `initialize` 后建立的 session。
- **显式状态 handle**：应用需要跨调用保留状态时，由工具返回 `basket_id`、`browser_id`、`task_id` 等 handle，并让模型在后续调用中作为普通参数传回。
- **Server-to-client request 约束**：服务端只能在处理客户端发起的请求时要求补充输入，避免无上下文地打扰用户。
- **Multi Round-Trip Requests**：服务端返回需要输入的中间结果，客户端收集输入后带着 `requestState` 重试原调用。
- **HTTP 可操作性**：`Mcp-Method`、`Mcp-Name`、cache metadata 和 W3C Trace Context 让网关、缓存、限流和分布式 tracing 更容易工作。
- **Extensions Track**：新能力可以作为扩展独立演进，不必都塞进核心规范。
- **生命周期策略**：功能从 Active 到 Deprecated 再到 Removed，有明确窗口和 SEP 过程。

## 文章主张

1. MCP 需要摆脱协议级 session，才能更自然地跑在横向扩展的 HTTP 基础设施上。
2. 协议无状态不会削弱应用状态，反而会迫使状态显式化、参数化、可追踪化。
3. 长连接和隐藏会话不适合作为所有交互能力的基础，多轮交互可以用可恢复请求表达。
4. MCP 的下一阶段不是只增加能力，而是建立扩展、弃用、授权和一致性测试的治理框架。
5. Apps、Tasks 这类能力更适合作为官方扩展独立演进，而不是直接固定在核心协议里。
6. 授权规范必须贴近 OAuth/OIDC 现实部署，否则多 server、多 issuer 场景容易出错。
7. Breaking changes 是这次基础重构的代价，但之后应该通过生命周期和扩展机制降低破坏性升级频率。

## 我的理解

这篇文章的核心不是“又加了几个 MCP feature”，而是 MCP 开始认真处理自己作为开放协议的部署问题。

早期协议为了让能力跑起来，session 是一个自然选择：初始化一次，后面在同一个上下文里继续通信。但一旦 MCP server 变成远程服务、进入企业网关、负载均衡、可观测性系统和多租户基础设施，session 就会变成运维负担。你需要粘性路由、共享状态、特殊网关逻辑，还很难把每个请求独立缓存或追踪。

无状态核心把 MCP 拉回 HTTP 的长处：每个请求自描述，任何实例都能处理，基础设施可以根据 header 决策，trace 可以贯穿全链路。代价是客户端和服务端实现要把过去藏在 session 里的东西显式放回请求、`_meta` 或工具参数里。

我觉得最值得注意的是“显式 handle”这个思路。它不仅是 session 的替代物，也更适合 agent。模型能看见 `task_id`、`basket_id` 或 `browser_id`，就能在计划里引用它、传递它、解释它。隐藏 session 对传统程序方便，但对模型来说是一块不可见状态。

## 对实现者的影响

- 旧的 `initialize` / `initialized` 流程需要迁移，客户端不能假设每次会先建立 protocol session。
- 依赖 `Mcp-Session-Id` 的远程 server 需要重新设计状态管理，把状态转为显式 handle 或应用层存储。
- 网关和服务端要处理并校验 `Mcp-Method`、`Mcp-Name` 这类 header，避免 header 与 body 不一致。
- 如果客户端缓存 `tools/list` 或资源读取结果，需要理解 `ttlMs` 和 `cacheScope`。
- 长任务实现要关注新的 Tasks extension，尤其是 `tasks/list` 被移除后的任务可见性和作用域设计。
- 如果使用 Roots、Sampling、Logging，要开始规划替代路径，但不需要在这个版本立刻删掉。
- 如果工具 schema 依赖更复杂的 JSON Schema，验证器要处理 `$ref`、组合、条件和性能边界。
- 如果客户端按旧的 `-32002` 缺失资源错误码分支处理，需要改为标准 JSON-RPC `-32602`。

## 对 MCP 生态的启发

- 核心协议应该尽量小而稳定，复杂能力放到 extensions 中独立试验。
- MCP Apps 的价值不只是 UI，而是让服务端能表达交互，同时 host 继续掌握 sandbox、consent 和 audit。
- Tasks 作为扩展比作为核心更合理，因为长任务生命周期会因场景而变化。
- Conformance suite 会变得越来越重要，否则不同 SDK 对“无状态请求”“多轮输入”“缓存语义”的实现可能分叉。
- 对企业部署来说，authorization hardening 可能比新功能更重要，因为 MCP 客户端面对多个 server 和 authorization server 是常态。

## 可延伸思考

- 无状态 MCP 是否会改变 host 对 tool list 和 resource list 的刷新策略？
- 显式 handle 会不会增加 prompt 泄漏或权限混淆风险？需要怎样的 handle 设计和过期策略？
- MCP Apps 的 sandbox、template prefetch 和 consent 流程会如何影响 UI 组件生态？
- `tasks/list` 移除后，用户如何在 host 里查看长期任务？是由 host 自己维护，还是由具体 server 暴露资源？
- Roots、Sampling、Logging 的弃用会如何影响现有 SDK 和开发者体验？
- 完整 JSON Schema 2020-12 会不会让工具 schema 过度复杂，从而增加模型选择工具和填写参数的难度？

## 待补充问题

- 需要对照 draft specification 看 `server/discover` 的精确定义。
- 需要确认当前主流 MCP SDK 对 `2026-07-28` release candidate 的支持进度。
- 需要看 Tasks extension 仓库中的 lifecycle 细节，特别是 task handle、取消语义和错误恢复。
- 需要看 MCP Apps 的安全模型：iframe sandbox 权限、资源加载、消息传递和审计记录。
