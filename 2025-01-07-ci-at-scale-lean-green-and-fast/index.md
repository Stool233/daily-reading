---
title: "CI at Scale: Lean, Green, and Fast"
title_zh: "大规模 CI：精简、常绿且快速"
author: "Dhruva Juloori, Zhongpeng Lin, Matthew Williams, Eddy Shin, Sonal Mahajan"
source: "https://arxiv.org/abs/2501.03440"
published: "2025-01-07"
updated: "2025-05-19"
recorded: "2026-09-05"
tags:
  - daily-reading
  - continuous-integration
  - merge-queue
  - monorepo
  - speculative-execution
  - probabilistic-scheduling
  - build-time-prediction
  - submitqueue
---

# CI at Scale: Lean, Green, and Fast / 大规模 CI：精简、常绿且快速

Uber 关于 SubmitQueue 构建调度优化的论文。建议先读[阅读笔记](notes.md)中的双路径例子，再读译文第 IV–VIII 节的 BLRD 与概率模型，最后看第 X 节的生产数据。

## 文件

- [中文全文翻译](translation.zh.md)：摘要、13 节正文、致谢，以及保留原语种的 33 条参考文献。
- [英文原文](original.en.md)：由 arXiv HTML 转为 Markdown，保留公式与图表。
- [原始 PDF](paper.pdf)：11 页，保留原始排版。
- [阅读笔记](notes.md)：核心机制、数值例子、实验数据、证明前提和开放问题。
- [元信息](meta.json)：来源、版本、许可与文件信息。

## 来源

- 论文：[arXiv:2501.03440](https://arxiv.org/abs/2501.03440)，会议记录为 ICSE 2025。
- 本次版本：[v2，2025-05-19](https://arxiv.org/html/2501.03440v2)。目录日期采用首次提交日期 2025-01-07。
- 作者：Dhruva Juloori、Zhongpeng Lin、Matthew Williams、Eddy Shin、Sonal Mahajan，Uber Technologies, Inc.
- 对应 issue：[#10](https://github.com/Stool233/daily-reading/issues/10)。
- 同一 issue 提供的项目：[uber/submitqueue](https://github.com/uber/submitqueue)。
- 补充阅读：[Bypassing Large Diffs in SubmitQueue](https://www.uber.com/us/en/blog/bypassing-large-diffs-in-submitqueue/)，2023-08-31。
- 记录日期：2026-09-05。
- 论文许可：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。本归档进行了翻译、Markdown 转换与 PDF 图表裁取，保留署名和图 3 的既有来源说明，不代表原作者背书。

## 摘要

SubmitQueue 通过推测未来可能的主线状态，并行验证待合入变更，保持主线持续通过必要检查。原调度模型主要为最可能发生的路径分配资源，但 BLRD 要让短变更安全越过前面的长变更，可能需要同时拿到多条推测路径的结果；只验证高概率路径会使短变更继续等待。论文利用 NGBoost 预测构建耗时及其不确定性，估计后来的变更能否更早完成，并为具备绕过机会的构建组提高优先级，同时使用推测阈值减少无用构建。

作者在 Go、iOS 和 Android 单体仓库上线后，报告构建数与变更数之比约下降 53%、CPU 使用量约下降 44%、P95 等待时间约下降 37%。这些是生产环境上线前后的观察，指标定义、分仓库数据以及对概率近似和 BLRD 前提的分析见阅读笔记。本文的核心价值在于：调度器应估计一个验证结果对推进合入决策的价值，而不能只看对应路径是否常见。
