---
title: "Building cloud agent infrastructure: what's different, and what we learned"
title_zh: "构建云端 agent 基础设施：差异与经验"
author: "Peter Pang"
source: "https://x.com/i/article/2062697992814313472"
published: "2026-06-05"
recorded: "2026-07-09"
tags:
  - daily-reading
  - ai-agents
  - cloud-infrastructure
  - sandbox
  - agent-runtime
  - security
  - credentials
  - creao
---

# Building cloud agent infrastructure: what's different, and what we learned / 构建云端 agent 基础设施：差异与经验

这是一篇每日阅读记录，已拆分为多个文件，便于分别阅读、修改和补充笔记。

## 文件

- [中文详细译述](translation.zh.md)
- [英文来源结构图](original.en.md)
- [元信息](meta.json)
- [阅读笔记](notes.md)

## 来源

- 原文链接：https://x.com/i/article/2062697992814313472
- 关联动态：https://x.com/intuitiveml/status/2062699747224568212
- 作者：Peter Pang
- 发布日期：2026-06-05
- 记录日期：2026-07-09
- 对应 issue：https://github.com/Stool233/daily-reading/issues/6

## 摘要

Peter Pang 从 CREAO 构建云端 agent 基础设施的经验出发，讨论桌面 agent 与云端 agent 的根本差异。桌面框架默认一个用户、一台机器、一个进程、一个可信边界；云端 agent 则运行在共享硬件和一次性 sandbox 中，可能由定时任务、HTTP 请求或其他 agent 触发，并且用户常常不在场。

文章的两条经验非常具体：第一，要把用户控制、变化慢的环境状态，与平台控制、变化快的 runner 代码拆开；第二，长期凭证不能进入 sandbox，必须通过宿主侧 API bridge、网络边界和短期 per-run token 来完成受控访问。

最后文章把云端 agent 抽象成“带自然语言接口的函数”：用户拥有实现，平台拥有触发面、运行时和安全边界。真正的工程纪律，是让这些层各自按自己的节奏演进，并在系统接缝处主动寻找风险。
