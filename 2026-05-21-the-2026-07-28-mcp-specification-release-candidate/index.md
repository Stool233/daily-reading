---
title: "The 2026-07-28 MCP Specification Release Candidate"
title_zh: "2026-07-28 MCP 规范发布候选版"
author: "David Soria Parra, Den Delimarsky"
source: "https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/"
published: "2026-05-21"
recorded: "2026-06-06"
tags:
  - daily-reading
  - mcp
  - protocol
  - specification
  - release-candidate
  - stateless
  - extensions
---

# The 2026-07-28 MCP Specification Release Candidate / 2026-07-28 MCP 规范发布候选版

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文详细译述](translation.zh.md)
- [英文来源结构图](original.en.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- 作者：David Soria Parra, Den Delimarsky
- 发布日期：2026-05-21
- 记录日期：2026-06-06

## 摘要

这篇文章介绍 MCP `2026-07-28` 规范的 release candidate。它的核心变化是把 MCP 协议层改为无状态：移除初始化握手和协议级 session，让每个请求都携带足够的协议版本、客户端信息、方法和名称等上下文，从而更适合普通 HTTP 基础设施、负载均衡、缓存和追踪。

文章同时把 Extensions 机制正式化，MCP Apps 和 Tasks 成为官方扩展；授权规范也进一步贴近 OAuth 2.0 和 OpenID Connect 的真实部署方式。Roots、Sampling、Logging 被标记为弃用但暂不移除，工具 schema 升级到完整 JSON Schema 2020-12。整体看，这次 release candidate 是一次偏基础设施和治理层面的破坏性升级，为 MCP 之后的长期演进建立更清晰的扩展、弃用和一致性验证机制。
