# 执行记忆，而不是语义召回

> 原文：[Execution Memory，而不是 Semantic Recall](https://tommy0103.github.io/project_silica/)  
> 作者：tommy0103  
> 发布日期：2026-06  
> 说明：原文为中文。以下为覆盖全文结构的详细中文读书稿，不是逐字转载或全文重排；完整原文请阅读来源链接。

## 文章要解决的问题

这篇文章表面上是在复盘 Obelisk，实际讨论的是 coding agent 的长期记忆到底应该长什么样。

作者最初的问题来自递归 agent 结构：当主 agent 调用 subagent 或 workflow 时，中间上下文不能全部塞回主 agent 的上下文窗口，否则上下文会迅速爆掉；但如果完全不可见，主 agent 又会丢失做判断所需的关键证据。于是问题变成：能否设计一层结构化历史，让 agent 在需要时自己查询？

这个问题看起来像 memory 问题，但作者给出的答案不是“做一个更聪明的语义召回系统”，而是把 coding-agent session 当作执行数据库来处理。也就是说，agent 不应该只是被动接收相似片段，而应该可以主动查询历史中的任务、消息、工具调用、文件路径、workflow、subagent、summary 和 memory。

## 为什么 URI/CLI 式检索不够好

作者早期想过用 URI/CLI 语义来组织 session 历史：先通过命令搜索，再返回某种可定位的结构，例如 session、message、tool result 的地址。这个方向的问题在于，它看起来结构清楚，但实际交给 agent 用时会有明显摩擦。

第一，检索频繁时会导致大量工具调用。每次只拉一点信息，agent 要在多轮工具结果之间维持注意力，效率低，也容易偏离原本问题。

第二，它等于让 agent 学一套 DSL。即便这套 DSL 对人类来说很规整，也会增加模型的遵循成本。检索任务的难点不应放在“让 agent 学会某套命令语法”上，而应放在“让 agent 能自然表达它想查什么，并拿到合适规模的证据”上。

## Dynamic workflow 为什么放大了这个问题

Dynamic workflow 的出现让中间上下文问题更突出。Workflow 通过脚本编排多个 agent，中间过程不会自动进入主 agent 的上下文；这本来就是它能扩展复杂任务的原因。

但这也带来一个新的要求：主 agent 必须能按需回到 workflow 内部，查看某个子任务如何推进、某个结论从哪里来、某个失败发生在哪一步。随着交互结构从单线对话变成树，再变成 DAG，传统 chat history 或简单 transcript 已经不够用了。

因此，Obelisk 的目标不是“给 agent 加一块模糊记忆”，而是给这种树/DAG 式执行历史建立可查询的索引层。

## 为什么用 CodeAct/JavaScript 做检索语言

Obelisk 的关键选择是让 agent 写 JavaScript 查询脚本，也就是用 CodeAct 作为检索语言。

这个选择同时解决了两个问题。首先，agent 可以一次执行脚本，批量拉取、过滤、组合和汇总多种信息，而不是进行多轮零散工具调用。其次，JavaScript 对 LLM 更自然；相比自定义 DSL，它更接近模型已有的代码能力。

更重要的是，CodeAct 允许组合。Agent 可以先查 session，再按文件路径过滤，再展开相关 message，再查看 tool failure，再汇总证据。这种检索过程不是线性管道，而是可以根据数据形状动态调整的程序。

作者把这点和 bash native 区分开来：bash pipeline 擅长线性组合，而 CodeAct 更适合操作结构化对象、分支逻辑和多步聚合。

## Helper function 的真正价值是控制 overfetch

Obelisk 早期提供了 search、sessions、messages、workflows 等 helper function，但 agent 仍然会使用 raw SQL。Raw SQL 不是不能用，尤其当 SQLite 只是 raw trace 的可查询视图时，写 SQL 是合理的后备能力。

问题在于，raw SQL 对 agent 不够稳。它容易猜错字段、忽略结构关系、一次取回过量数据。更深层的问题是 token budget：结构化数据库不太会漏掉信息，但非常容易取回太多信息。

因此，helper function 不只是 SQL wrapper。它们的核心价值是渐进披露：先给轻量 summary，需要时再展开 detail；先沿主干检索，必要时再进入 tool result、subagent、workflow 或 raw JSONL。

SkillOpt 暴露出的 overfetch 问题强化了这个判断。如果一个 helper 默认返回完整 workflow tree 或大量 message，就会把模型上下文淹没。好的 agent-facing API 应该帮助 agent 把证据拉到刚好够用，而不是把数据库内容倾倒出来。

## 为什么 execution memory 不等于 semantic recall

文章最重要的理论转折是：coding-agent session 和普通聊天记录不是同一种记忆材料。

普通 IM session 更像社交情景记忆，话题可能跳跃，回复链可能发散，很多信息依靠人的语境和关系理解。Coding-agent session 则更像执行记忆：它围绕任务推进，有明确主干，有文件、命令、测试、diff、错误输出等外部锚点，也有 project、branch、时间线和 memory 等自然组织方式。

这导致两类检索需求完全不同。对 IM session，你可能要找“语义上相关的聊天片段”；对 coding-agent history，你经常要找更具体的问题：

- 哪次 session 改过这个文件？
- 哪个工具调用产生了这个错误？
- 当时为什么没有采用某个方案？
- 哪个 summary 支撑了现在的判断？
- 某个 workflow 里的 subagent 到底做了什么？

这些问题更适合明确检索、结构化索引和证据展开，而不是默认向量召回。

## 对 RAG 和 memory 叙事的反思

作者认为，人们过去太容易把 memory 问题交给向量检索。这背后有两层路径依赖。

一层是 RAG 叙事：系统先猜测模型可能需要哪些相关片段，再把它们塞进上下文。这个方案在许多文档问答场景里有价值，但它不一定适合 agent 自己查执行历史。Agent 对当前任务、错误、文件、上下文缺口的感知，往往比外部召回器更具体。

另一层是拟人化记忆：人们希望 memory 像人脑一样无感召回。但即便是人类处理长工作记录，也不会只靠脑内回忆，而会使用搜索、日志、版本控制和笔记。对 agent 来说，显式搜索 execution history 反而更贴近日常工程实践。

因此，Obelisk 的立场不是否定向量检索，而是反对让向量检索默认定义所有 memory 问题。

## Tool result 为什么是证据后备层

文章里有一个很关键的设计判断：tool result 不应该默认成为语义检索层。

原因是 coding agent 在正常工作中会复述自己的观察：它读了哪些文件、命令输出了什么、测试为什么失败、下一步准备怎么改。这些复述构成 session 主干的语义状态。直接检索 tool result 当然更原始，但也更冗长、更噪声、更容易 overfetch。

所以，Obelisk 默认检索主干消息；当需要审计、验证原始输出、追查误读或补证据时，再展开 tool result。Subagent、workflow 和 raw JSONL 也类似：默认折叠，按需展开。

这个设计和 execution memory 的性质相匹配。主干是语义层，外部结构是证据层；好的检索系统应该能在两者之间切换，而不是把所有内容平铺给模型。

## 文章的最终判断

Obelisk 的创新不是 SQLite、FTS5、JSONL 或 JavaScript 沙箱本身。这些技术都很普通。真正的创新是重新定义了 coding-agent memory 的问题边界。

如果把 coding-agent history 看成聊天记录，就会自然走向语义相似召回；如果把它看成自带结构的执行轨迹，就会自然走向可查询索引、证据锚点、渐进披露和审计链。

这篇文章的结论可以压缩成一句话：coding-agent transcripts 不是 chat logs，而是自我叙述的 execution traces。Obelisk 之所以有效，是因为它没有把这种历史压成泛化的“记忆”，而是保留了它作为执行数据库的结构。

## 术语对照

- **Execution memory**：执行记忆
- **Semantic recall**：语义召回
- **Coding-agent history**：编码智能体历史 / coding agent 历史
- **Session**：会话 / 执行会话
- **Trace**：执行轨迹
- **Tool result**：工具结果
- **Subagent**：子智能体
- **Workflow**：工作流
- **Dynamic workflow**：动态工作流
- **CodeAct**：以代码作为行动和查询语言的 agent 交互方式
- **Overfetch**：过量取回 / 检索过量
- **Progressive disclosure**：渐进披露
- **Evidence anchor**：证据锚点

## 核心脉络

1. 递归 agent 和 workflow 会制造大量中间上下文，主 agent 需要按需查询。
2. URI/CLI/DSL 式检索会增加工具调用和模型遵循成本。
3. CodeAct/JavaScript 更适合作为 agent 查询结构化历史的语言。
4. Helper function 的价值不仅是封装 SQL，更是控制 token budget 和渐进披露。
5. Coding-agent session 是 execution memory，不是普通聊天记录。
6. Execution memory 有任务中心、主干明确、外部可验证、跨 session 自然结构等特征。
7. 对这类历史，明确检索和证据展开往往比默认语义召回更合适。
8. Tool result、subagent、workflow 和 raw JSONL 应作为按需展开的证据层。
9. Obelisk 的创新在于重新定义 memory 问题，而不是发明新技术。
