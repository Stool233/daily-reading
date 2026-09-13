# 阅读笔记

> 来源：[The Agent Access Model](https://blog.cloudflare.com/the-agent-access-model/)，Matt Silverlock，2026-08-05。

## 精读 Trust Ratchet

关键时序：暂存受保护响应 → 各执行点确认新状态 → 向模型释放。并发调用和旧连接也须受约束；缺失确认则不交付响应。新任务若携带敏感输入，仍须按来源分类初始化，不能靠更换任务绕过限制。

这是一份参考架构；多用户共享上下文的端到端权限问题仍未解决。以上概括对应原文的 Trust Ratchet 与 multiplayer 两节。

## 两处协议核对

**委托链提供哪些信息？** RFC 8693 的顶层 `act` 标识当前执行者，嵌套 `act` 记录此前的执行者。规范要求访问控制只考虑 token 的顶层声明与当前执行者；历史执行者仅供信息追溯。因此，不能把记录了委托链理解为自动完成逐跳权限计算。见 [RFC 8693 §4.1](https://www.rfc-editor.org/rfc/rfc8693.html#section-4.1)。

**DPoP 保护哪些请求内容？** DPoP 将 token 与客户端密钥绑定。证明中的 `htm` 对应 HTTP 方法，`htu` 对应去除 query 和 fragment 的目标 URI。它不保证请求正文及一般请求头的完整性。阅读时要分别检查持钥证明、传输保护和业务授权。见 [RFC 9449 §4.2](https://www.rfc-editor.org/rfc/rfc9449.html#section-4.2) 与 [§11.7](https://www.rfc-editor.org/rfc/rfc9449.html#section-11.7)。

## 带着问题继续读

以下是阅读时提出的问题，不是作者已经给出的实现或实验证据。

- 如果同一份数据在两个系统中被标成不同等级，应由谁裁决？如何发现错标？
- 即使输出只允许数值汇总，多次合法查询是否仍可能推算出单条记录？
- 权限收紧频繁中断正常任务时，应该调整任务拆分、数据分类，还是输出接口？如何比较三者的代价？

## 我的想法

待阅读讨论后补充。
