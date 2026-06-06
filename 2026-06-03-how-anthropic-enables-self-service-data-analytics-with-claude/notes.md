# 阅读笔记

## 一句话总结

面向业务分析的 agent 准确率，关键不在于让模型“更会写 SQL”，而在于把业务概念、治理数据、语义层、Skills、eval 和线上纠错做成一套持续维护的系统。

## 关键概念

- **业务概念到数据实体映射**：把“活跃用户”“收入”“留存”等自然语言概念解析到唯一正确的表、字段、指标、粒度、过滤器和时间窗口。
- **Canonical dataset**：少量强治理、可发现、有人负责的数据集，用来压缩 agent 的候选空间。
- **Semantic layer first**：如果问题能映射到语义层指标，就不让 agent 手写 SQL 重新定义口径。
- **LLM-readable reference docs**：面向模型检索和判断编写的参考文档，强调粒度、范围、排除规则、使用/禁用场景和 gotchas。
- **Pairwise skills**：一个 knowledge skill 负责路由到领域文档，一个 execution skill 负责编码分析师工作流。
- **Skill maintenance**：skill 文档和数据模型同仓维护，模型变更时同步更新文档，避免上下文腐烂。
- **Eval as telemetry**：评估结果入仓，记录版本、git SHA、模型、通过率、token 和耗时，使改动效果可查询。
- **Provenance footer**：在答案中附带来源层级、数据新鲜度、owner 和 review 状态。

## 文章主张

1. LLM 可以降低业务用户提问门槛，但直接把 agent 接到仓库会制造“看起来准确”的风险。
2. 自助分析 agent 的核心问题是上下文和验证，不是 SQL 生成。
3. 大多数错误来自业务概念歧义、数据过时和检索失败。
4. 传统数据工程实践仍是基础，只是现在数据模型还要对 agent 可读、可导航、可验证。
5. 历史 SQL 的原始访问价值有限，应该被蒸馏成结构化领域文档和可复用分析模式。
6. Skills 的价值在于把资深分析师的流程、优先级和检查点变成 agent 可执行的程序性知识。
7. 没有持续维护的 skill 和 reference docs 会迅速过时，准确率会衰减。
8. Offline eval、ablation、online validation 和 correction harvesting 共同构成闭环。

## Anthropic 栈的分层

- **Data foundations**：canonical datasets、数据模型、transforms、测试、元数据、freshness、completeness、lineage。
- **Sources of truth**：语义层、血缘和转换图、蒸馏后的查询模式、业务上下文和知识图谱。
- **Skills**：把“先查语义层、再查参考文档、澄清口径、执行查询、对抗式 review、带来源交付”写进 agent 流程。
- **Validation**：离线 eval、PR 级消融、线上 provenance、数据质量检查、纠错监控和主动文档修复。

## 值得记住的数据点

- Anthropic 称其内部大部分业务分析查询已由 Claude 自动化，并达到较高总体准确率。
- 加入维护良好的 Skills 前后，analytics agent 的评估表现差异很大，说明“程序性上下文”比单纯放开工具更重要。
- 原始暴露大量历史 SQL 的消融几乎没有提升准确率，说明瓶颈不是访问更多信息，而是结构化导航。
- 对抗式 review 能提升准确率，但会增加 token 成本和延迟，因此适合按风险分层使用。
- 未维护的 skill docs 会随着数据模型变化快速腐烂，维护机制本身必须产品化。

## 我的理解

这篇文章最重要的洞见是：数据分析 agent 的“智能”很大一部分不在模型里，而在组织的数据治理与操作系统里。

一个没有治理数据层的 agent，即使 SQL 写得很漂亮，也可能只是更快地产生错误答案。反过来，如果公司已经有清晰的 canonical datasets、语义层、文档、血缘和 eval，那么模型要做的事情会变简单：按正确路径找上下文、生成查询、解释结果、暴露限制。

这也解释了为什么 Anthropic 强调 Skills。Skill 不是普通 prompt，而是把资深分析师脑子里的路线图写下来：什么情况下必须澄清，什么情况下不能用 raw table，什么过滤器绝不能忘，什么口径必须跟 dashboard 一致，答案末尾要披露哪些来源信息。

对很多团队来说，最容易犯的错可能是把问题理解成“给模型接数据库”。这篇文章的立场更接近“给模型一个受治理的分析环境”。前者让 agent 在复杂仓库里自由探索；后者把探索空间压缩到少量可信路径，并对每次路径选择做验证。

## 对产品和工程的启发

- 先做少量 canonical datasets，不要指望模型在混乱数据层上自动治理。
- 把指标定义、文档、dashboard 和 skill 维护绑定到同一套 PR/CI 流程。
- 设计 analytics agent 时，默认先走语义层；raw SQL 应该是 fallback，而不是第一选择。
- 面向 LLM 写 reference docs，要写“何时用、何时不用、粒度是什么、默认过滤是什么、常见错误是什么”。
- 把 stakeholder correction 当作高价值数据资产，自动转成 doc fix 和 eval candidate。
- 对高影响答案使用 provenance footer 和人工签核，承认 silent failure 无法完全消灭。
- 消融实验要记录负结果，避免团队在“更多上下文一定更好”的直觉里绕圈。

## 可延伸思考

- 小团队的最小可行版本是否可以是：3 个 canonical datasets + 30 个 evals + 1 个 knowledge skill？
- 如何为不同风险等级的问题决定是否启用对抗式 review？
- 如果没有成熟语义层，应该先建设语义层，还是先做 reference docs？
- Provenance footer 是否应该成为所有企业 agent 回答的默认组件？
- 历史 SQL 如何自动蒸馏成领域文档，而不是变成新的噪声库？
- Stakeholder correction 如何区分“用户偏好不同”和“agent 事实错误”？

## 待补充问题

- Anthropic 内部的 semantic layer 具体使用什么技术栈？
- Claude Code Skills 在多界面同步时如何处理权限与版本兼容？
- Offline eval 如何评估需要复杂业务判断的问题，而不仅是数字对错？
- 对 silent wrong answers，有没有比 provenance 和人工签核更系统的检测方法？
