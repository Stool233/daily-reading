---
title: "Critical thinking when agents do the work"
title_zh: "当智能体替你工作时，如何保持批判性思考"
author: "Addy Osmani"
source: "https://x.com/addyosmani/status/2117512471930167377"
published: "2026-11-03"
recorded: "2026-11-09"
tags:
  - daily-reading
  - ai-agents
  - critical-thinking
  - verification
  - cognitive-offloading
---

# 当智能体替你工作时，如何保持批判性思考

作者讨论大量使用智能体以后，如何继续掌握问题、判断证据并对结果负责。重点包括认知卸载与认知投降的区别、提前设定验证标准、读懂智能体替自己作过的决定，以及保留重要技能的日常练习。

## 阅读文件

- [完整中文译文](translation.zh.md)：按附件顺序翻译全部 64 个正文段落与 8 个小标题。
- [中文 PDF](output/pdf/critical-thinking-when-agents-do-the-work.zh.pdf)：完整译文，含封面目录、书签、页码与可搜索文字。
- [阅读笔记](notes.md)：文章论证、术语解释、适用边界和可执行的阅读练习。
- [完整英文原文](original.en.md)：来自用户提供的全文，补充 Markdown 段落和标题格式。
- [原始附件文本](source.txt)：按字节保留，便于回溯。
- [元信息](meta.json)与[完整性检查记录](verification.json)。

## 来源说明

作者：Addy Osmani（@addyosmani）。原帖：[X](https://x.com/addyosmani/status/2117512471930167377)。记录与翻译日期：2026-11-09。

标题和 2026-11-03 的帖子日期依据指向同一链接的[索引资料](https://joaozinho.news/en/editions/november-3-2026-morning/addy-osmani-warns-of-cognitive-surrender-when-the-agent-s/)交叉核对；X 页面直接读取返回 HTTP 403。全文翻译以用户附件为准。附件没有保留嵌入链接和图片，本归档不补造这些元素。

## 重建译文和 PDF

逐段译文保存在 [translation.segments.json](translation.segments.json)，数组第 n 项对应 `source.txt` 的第 n 行。修改后运行 [build_pdf.py](build_pdf.py)，同步生成 Markdown 和 PDF。需要 Python、ReportLab；默认使用 macOS 的宋体与黑体，字体路径可通过脚本参数调整。

```bash
python3 build_pdf.py
```

脚本会重新生成 `translation.zh.md` 和 `output/pdf/` 下的 PDF。检查记录对应本次交付版本，重建后应重新做文字提取与页面视觉检查。
