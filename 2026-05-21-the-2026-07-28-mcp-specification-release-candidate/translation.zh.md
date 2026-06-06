# 2026-07-28 MCP 规范发布候选版

> 原文：[The 2026-07-28 MCP Specification Release Candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)
> 作者：David Soria Parra, Den Delimarsky
> 发布日期：2026-05-21
> 说明：以下为覆盖全文结构的详细中文译述。为尊重原文版权，它不是逐字全文翻译；完整英文原文请阅读来源链接。

## 开篇：这是 MCP 发布以来最大的一次规格修订

文章介绍的是 MCP `2026-07-28` 规范的 release candidate。虽然 URL 和标题里出现 `2026-07-28`，但这不是文章发布时间，而是目标规范版本和预计最终发布时间。文章发布于 2026-05-21，release candidate 也在这一天锁定，最终规范计划在 2026-07-28 发布。

作者把这次修订称为 MCP 发布以来最大的一次规格变化。它集中解决几个问题：协议核心改为无状态，Extensions 框架正式化，Tasks 和 MCP Apps 成为官方扩展，授权规范更贴近 OAuth 与 OpenID Connect 的实际部署，弃用策略正式化，工具 schema 升级，并补上更清晰的治理和一致性验证机制。

从生产部署角度看，最直接的变化是远程 MCP server 不再需要依赖 sticky session、共享 session store 或网关里的深度请求体检查。请求本身会携带足够的信息，普通 round-robin 负载均衡、按 header 路由、按 TTL 缓存工具列表、分布式 trace 串联等实践都会更自然。

## 协议层转向无状态

文章最重要的主题是：MCP 在协议层变成无状态。

在旧版本里，使用 Streamable HTTP 调用工具时，客户端通常要先发送 `initialize` 请求，服务端返回一个 `Mcp-Session-Id`。之后的请求都要带上这个 session ID。这样一来，客户端就被绑定到某个服务端实例，或者部署层必须维护共享 session 状态。

在 `2026-07-28` release candidate 中，`initialize` / `initialized` 握手被移除，协议级 session 也被移除。协议版本、客户端信息、客户端能力等过去只在初始化阶段交换一次的信息，现在会放进每个请求的 `_meta`。如果客户端需要提前了解服务端能力，可以调用新的 `server/discover` 方法。

这个变化的含义很大：任何 MCP 请求都应该能落到任意服务端实例上处理。对水平扩展的远程 MCP server 来说，这比基于 session 的模型简单很多。

## 无状态协议不等于无状态应用

作者特别澄清：协议层无状态，不代表应用不能维护状态。

如果一个服务端确实需要跨多次工具调用保留状态，它可以像普通 HTTP API 那样返回显式 handle。例如某个工具创建购物篮后返回 `basket_id`，后续工具调用把这个 ID 当作普通参数传回来。浏览器自动化、长流程任务、购物车、数据分析会话等场景也可以用类似方式。

这种模式和隐藏在 transport metadata 里的 session 有一个关键差异：状态 handle 对模型是可见的。模型可以把它作为上下文来推理、传递、组合或转交给下一步工具，而不是让状态存在于模型看不见的协议层。

换句话说，MCP 不再替应用管理状态，但它允许应用以显式、可移植、可追踪的方式管理状态。

## 服务端向客户端请求的流程被重构

无状态协议仍然需要处理一种场景：服务端在处理某个客户端请求时，需要向客户端追加提问或请求输入。例如执行一个删除操作前，需要用户确认。

这次 release candidate 对这类 server-to-client request 做了两个重要限制。

第一，服务端只能在正在处理某个客户端发起的请求时向客户端请求东西。也就是说，用户不会在没有上下文的情况下突然收到服务端发来的 prompt；每次 elicitation 都必须追溯到某个用户或 agent 主动开始的动作。

第二，多轮交互不再依赖一直打开的 SSE stream。服务端可以返回一个 input-required 类型的结果，里面包含需要用户回答的问题，以及可以恢复原调用的 `requestState`。客户端收集答案后，把原调用、用户回答和 `requestState` 一起重新发送。因为恢复所需的状态都在 payload 里，所以任意服务端实例都能接手处理。

这个设计把多轮交互从“长连接上的持续会话”改成了“可重试、可路由、带状态 payload 的请求序列”。

## 更容易路由、缓存和追踪

为了让 MCP 更好地跑在普通 HTTP 基础设施上，这次还引入了几个看似小但很关键的操作性变化。

首先，Streamable HTTP transport 要求请求包含 `Mcp-Method` 和 `Mcp-Name` 等 header。这样负载均衡器、API 网关、限流系统就可以根据 header 判断这是 `tools/call`、`tools/list` 还是别的操作，而不必解析 JSON body。服务端也需要校验 header 和 body 是否一致，避免路由信息与真实请求不匹配。

其次，列表和资源读取结果可以携带 `ttlMs` 和 `cacheScope`。这类似 HTTP 世界里的缓存控制。客户端可以知道某个 `tools/list` 结果在多久内仍然新鲜，以及这个缓存能否跨用户共享。这样一来，客户端不必完全依赖长连接来得知列表变化。

第三，规范文档明确了 W3C Trace Context 在 `_meta` 中的传播方式，包括 `traceparent`、`tracestate` 和 `baggage` 等 key。这样一次从 host application 发起的工具调用，可以穿过客户端 SDK、MCP server 以及下游服务，并在 OpenTelemetry 兼容后端里串成一棵完整 trace。

这三个变化共同服务于同一个目标：让 MCP 流量变得可路由、可缓存、可观测。

## Extensions 成为一等机制

上一版规范里已经有 extensions，但缺少正式过程。这次 release candidate 给 extensions 补上了制度：扩展使用 reverse-DNS ID，通过 client 和 server capability 里的 `extensions` map 协商，放在独立的 `ext-*` 仓库中，由委托维护者维护，并且可以独立于核心规范进行版本演进。

更重要的是，SEP 流程里新增了 Extensions Track。扩展可以从 experimental 走向 official，而不必一开始就进入核心规范。这让 MCP 可以在不频繁破坏核心协议的情况下加入新能力。

这次包含两个官方扩展：MCP Apps 和 Tasks。

## MCP Apps：由服务端提供的交互式 UI

MCP Apps 让服务端可以提供交互式 HTML 界面，由 host 在沙盒 iframe 中渲染。工具可以提前声明 UI template，host 因而能够提前拉取、缓存并做安全审查。

关键点在于，这些 UI 并不是绕过 MCP 协议的旁路。UI 触发的动作仍然通过 MCP 的 JSON-RPC 基础协议回到 host，并经过与直接工具调用相同的审计和用户同意路径。

这个设计把“工具调用”和“工具界面”连接起来：服务端可以表达更丰富的交互，而 host 仍然保留治理、审计和 consent 控制。

## Tasks 从实验性核心能力变成扩展

Tasks 在 `2025-11-25` 版本里是实验性的核心功能。生产使用暴露出足够多的重构需求，所以这次把它移出核心规范，作为官方扩展维护。

新的 Tasks 生命周期更贴合无状态协议。服务端可以在 `tools/call` 的结果里返回一个 task handle，客户端再用 `tasks/get`、`tasks/update` 和 `tasks/cancel` 驱动任务。任务是否被创建由服务端决定：客户端声明支持这个扩展，服务端判断某次调用是否应该作为任务运行。

`tasks/list` 被移除，因为没有协议级 session 后，很难安全地定义它应该列出哪些任务。任何已经基于 `2025-11-25` 实验 Tasks API 构建的实现，都需要迁移到新的扩展生命周期。

## 授权规范加固

文章接着介绍授权相关的变化。这部分目标是让 MCP 授权更贴近 OAuth 2.0 和 OpenID Connect 在真实环境中的部署方式。

客户端现在必须校验授权响应里的 issuer 信息，以缓解 mix-up attack。MCP 的部署模式常常是一个客户端面对许多 server，这种场景下，客户端更容易把不同授权服务器的响应混在一起，所以 issuer 校验尤其重要。

Dynamic Client Registration 也会声明 OpenID Connect 的 `application_type`，避免桌面或 CLI 客户端被授权服务器默认当成 web 应用，从而拒绝 localhost redirect URI。客户端还要把注册凭据绑定到对应 authorization server 的 issuer；如果资源迁移到另一个授权服务器，就需要重新注册。

此外，规范还澄清了如何向 OpenID Connect 风格的授权服务器请求 refresh token、step-up 过程中的 scope accumulation，以及 `.well-known` discovery suffix 的细节。

整体看，这部分是在减少“规范能跑，但和真实 OAuth/OIDC 基础设施有缝隙”的问题。

## Roots、Sampling、Logging 被弃用

这次 release candidate 根据新的 feature lifecycle policy，把 Roots、Sampling 和 Logging 标记为 deprecated。

这里的 deprecated 是注解性质的弃用，不是立刻删除。相关方法、类型和 capability flag 在这个版本里仍然可用，并且在此后一年内发布的规范版本里也会继续可用。如果未来真的要移除这些能力，还需要单独的 SEP。

文章也给出了替代方向：Roots 可以由工具参数、资源 URI 或服务端配置替代；Sampling 更适合由应用直接集成 LLM provider API；Logging 对 stdio transport 可以走 `stderr`，结构化可观测性则可以走 OpenTelemetry。

这一节真正重要的是治理含义：MCP 开始用清晰的生命周期来告诉实现者什么是活跃能力、什么进入弃用窗口、什么可能在未来被移除。

## 工具 schema 升级到完整 JSON Schema 2020-12

工具的 `inputSchema` 和 `outputSchema` 升级到完整 JSON Schema 2020-12。

输入 schema 仍然要求根节点是 object，但现在可以使用 `oneOf`、`anyOf`、`allOf`、conditionals、`$ref` 和 `$defs`。输出 schema 则不再限制为 object，`structuredContent` 可以是任意 JSON value。

这让工具契约可以表达更复杂的数据结构，但也带来实现风险。文章提醒实现者不要自动 dereference 外部 `$ref` URI，并且应该限制 schema 深度和验证耗时，避免复杂 schema 造成性能或安全问题。

另外，缺失资源的错误码从 MCP 自定义的 `-32002` 改为 JSON-RPC 标准的 `-32602` Invalid Params。如果客户端依赖旧错误码做判断，需要更新。

## 协议之后如何演进

作者承认这次 release candidate 包含 breaking changes，但也强调这不应该成为常态。

新的治理机制有三层保护。

第一是 feature lifecycle policy。功能会经历 Active、Deprecated、Removed 等状态，从弃用到最早可移除之间至少有十二个月窗口。

第二是 Extensions framework。新能力可以作为 opt-in extension 单独发布和稳定，只有在合适时才考虑进入核心规范。

第三是 conformance suite。Standards Track SEP 想达到 Final 状态，必须有对应的一致性测试场景。这个测试套件也会用于评估官方 SDK 的 tier。

这些机制意味着，MCP 以后不必每次新增能力都修改核心协议，也不必让实现者在没有测试支撑的情况下猜测兼容性。

## 时间线与验证窗口

这篇文章发布时，release candidate 已在 2026-05-21 锁定。最终规范计划在 2026-07-28 发布。中间大约十周是验证窗口，SDK 维护者和客户端实现者应该用真实工作负载测试这些变化。

文章指出，Tier 1 SDK 预计应在这个窗口内支持新规范。完整 release candidate 可以在 draft specification 中查看，changelog 会列出相对 `2025-11-25` 的全部变化。

如果实现者发现问题，应在 specification repository 中开 issue；实现问题则可以去相应 Working Group channel 或 contributor Discord 讨论。

## 结尾：这是一场基础设施层面的重构

文章最后把这次 release candidate 描述为 MCP 的长期基础：无状态协议让 MCP 更适合普通 HTTP 基础设施，extensions framework 让 Apps 和 Tasks 这类能力可以按自己的节奏演进，lifecycle policy 让实现者能更清楚地知道哪些能力会继续存在、哪些能力会进入迁移窗口。

这不是一次只改几个 API 字段的小版本，而是一次面向部署、扩展、授权、安全、可观测性和治理的系统性重构。对 MCP 实现者来说，最需要关注的不是单个 headline，而是从“session 驱动的协议”转向“每个请求都自描述、可路由、可缓存、可追踪”的整体设计。

## 术语对照

- **Release candidate**：发布候选版
- **Stateless protocol**：无状态协议
- **Protocol-level session**：协议级会话
- **Sticky session**：粘性会话 / 会话亲和
- **Shared session store**：共享会话存储
- **Server-to-client request**：服务端向客户端发起的请求
- **Elicitation**：向用户请求补充输入
- **Multi Round-Trip Requests**：多轮往返请求
- **Extensions framework**：扩展框架
- **MCP Apps**：MCP 应用扩展
- **Tasks extension**：任务扩展
- **Authorization hardening**：授权加固
- **Dynamic Client Registration**：动态客户端注册
- **Feature lifecycle policy**：功能生命周期策略
- **Conformance suite**：一致性测试套件

## 核心脉络

1. MCP `2026-07-28` release candidate 是一次破坏性但基础性的协议升级。
2. 最大变化是移除初始化握手和协议级 session，让每个请求都携带必要上下文。
3. 应用仍然可以有状态，但状态要以显式 handle 的形式进入工具参数和模型上下文。
4. 服务端向客户端请求输入的流程改为可恢复、可重试、可跨实例处理的多轮请求。
5. `Mcp-Method`、`Mcp-Name`、缓存 metadata 和 trace context 让 MCP 更容易接入 HTTP 网关、缓存和 observability 系统。
6. Extensions 机制正式化，MCP Apps 和 Tasks 成为官方扩展。
7. 授权规范向 OAuth/OIDC 实践靠拢，降低多 server 场景下的 issuer 混淆风险。
8. Roots、Sampling、Logging 进入弃用窗口，但不会在这个版本立即消失。
9. Tool schema 升级到完整 JSON Schema 2020-12，表达力增强，同时要求实现者注意验证风险。
10. 新的 lifecycle、extensions 和 conformance suite 说明 MCP 正在从快速扩张走向更成熟的标准治理。
