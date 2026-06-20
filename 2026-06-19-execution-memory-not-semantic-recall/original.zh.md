# Execution Memory，而不是 Semantic Recall

> 来源：https://tommy0103.github.io/project_silica/  
> 作者：tommy0103  
> 发布日期：2026-06  
> 说明：原文为中文。本文档只记录来源元信息、短摘录和非逐字来源结构图；完整文章请阅读来源链接。

## 短摘录

> Agent transcripts are not chat logs; they are self-narrating execution traces.

> It was here all along.

## 来源结构图

### 文章开场

作者从 Obelisk 的开发复盘说起：让 Codex 使用 Obelisk skill 综合 Obelisk 开发轨迹后，生成结果不仅质量高，而且每个可复盘点都能回到对应证据。这让作者重新思考 Obelisk 为什么有效。

文章展示了一份 Obelisk 技术复盘素材，里面按候选主题列出大量开发线索和证据锚点，包括从 session-journal skill 到 Obelisk、反 wiki 化、索引完整性、查询 API、schema 文档、SKILL.md 重写、indexer hardening、Electron app、workflow/subagent、recap、memory layer、Claude/Codex 多源索引、产品边界、发行策略、SkillOpt 评估和 Electron 打包等。

### 递归 agent 结构里的中间上下文

作者回到 5 月中旬的问题：在递归 agent 结构中，主 agent 不应该把所有中间上下文拍平塞进自己的上下文窗口，但也不能完全丢失这些信息。最初的方向是通过更好的 session 存储结构让 agent 查询上下文。

当时的想法偏向 URI/CLI 语义，例如通过命令搜索再返回某种可定位结构。作者后来意识到，这种方式有两个明显问题：频繁检索会制造太多工具调用，降低效率并造成注意力漂移；同时，它要求 agent 学会一套额外 DSL，遵循效果和检索质量都不稳定。

### Dynamic workflow 的启发

Anthropic dynamic workflow 让中间上下文问题更加明显。Workflow 通过脚本编排多个 agent，中间结果不直接进入主 agent 上下文，这正是子 agent 能成立的前提。

但这也意味着，主 agent 需要一个按需拉取中间结果的检索层。随着交互结构从单一对话流扩展成树，再进一步扩展成 DAG，检索层的重要性被放大。

### CodeAct 作为检索语言

Obelisk 的核心解法受到 dynamic workflow 的启发：用 JavaScript/CodeAct 作为检索语言。相较于多轮 CLI 调用，agent 可以在一次脚本执行中拉取、组合和聚合多类信息，再把结果作为一个整体返回。

作者认为，CodeAct 对 LLM 来说更自然，也比自定义 DSL 更容易组合。它的优势不只是封装查询，而是允许 agent 直接操作结构化数据，并把多个 API 组合成高阶检索逻辑。

### 从 raw SQL 到渐进披露

Obelisk 早期提供了 search、sessions、messages、workflows 等 helper，但 agent 仍然经常直接写 raw SQL。Raw SQL 可以作为后备手段，因为数据库只是 raw trace 的 view，真正来源仍是 JSONL；但长期依赖 raw SQL 并不是理想形态。

作者逐渐把 helper function 理解为两件事：一是常用 SQL 的封装，二是 token budget 的控制器。设计良好的 helper 应该先返回 summary，而不是把所有原始 message 或 tool result 直接塞回模型上下文。

SkillOpt 暴露了 overfetch 问题：例如某些 helper 会返回远超当前任务需要的数据。作者由此强调，SQLite/结构化索引不太会漏信息，但非常容易取太多信息；渐进披露正是为了解决这个问题。

### 为什么 Obelisk 能工作

文章开始回答核心问题：Obelisk 有效，并不是因为 SQLite、FTS5、JSONL 或 schema 本身是新技术，而是因为 coding-agent session 的数据形态特殊。

作者认为，过去几年大家过度依赖向量检索叙事。一方面，人们倾向于让 RAG 猜测模型可能需要什么，再把相关片段喂给模型；另一方面，人们也容易把 memory 拟人化成无感召回。但对长 session 来说，人类自己也需要搜索工具来定位信息。

在 agentic AI 场景下，agent 往往比外部 RAG 更知道自己要找什么。Obelisk 的前提正是：让 agent 明确搜索结构化历史，而不是被动接收语义相似片段。

### Execution memory

作者把 coding-agent session 定义为 execution memory，而不是普通 IM session 或 social episodic memory。二者的区别在于：

- Agent session 通常围绕任务推进，主题更集中，转折也有因果关系。
- Agent session 有明确主干：用户和主 agent 的消息构成主线，subagent 和 workflow 构成子树或子图。
- Agent session 的产出可被外部验证，例如代码 diff、测试结果、命令输出和文件路径。
- Session 之间存在自然组织方式，例如 project、branch、时间线和 memory。

这些特征让明确检索在 coding-agent history 上特别有效。很多问题不是寻找语义相似片段，而是寻找某个文件何时被改过、某个错误在哪次 session 里出现过、当时为什么放弃某个方案、哪个工具结果支撑了某个结论。

### 设计判断

Obelisk 把 tool result 作为证据后备层，而不是默认语义检索层。作者认为，平时真正承载语义状态的是 agent 对工具结果的复述；只有在审计、确认原始输出或怀疑 agent 误读时，才需要展开 tool result。

这也解释了 Obelisk skill 默认检索主干、折叠其他部分的设计。主干承载大部分语义状态，而 tool result、subagent、workflow 和 raw JSONL 更像可追溯的外部证据层。

### 结论

文章的最终判断是：Obelisk 的创新不在于使用了新技术，而在于重新定义了问题。它不是用数据库模拟通用记忆系统，而是承认 coding-agent history 本身就是可查询的执行数据库。

## Copyright Note

This archive intentionally does not reproduce the full article. Use the source URL above for the complete text.
