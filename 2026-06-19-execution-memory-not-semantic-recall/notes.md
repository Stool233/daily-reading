# 阅读笔记

## 一句话总结

Obelisk 的核心不是“给 agent 加记忆”，而是承认 coding-agent history 本来就是带结构、带证据、可查询的 execution memory。

## 关键概念

- **Execution memory**：围绕任务执行形成的历史，包含消息主干、工具调用、文件路径、命令输出、diff、测试结果、workflow、subagent 和 summary。
- **Semantic recall**：基于语义相似度被动召回片段，适合部分知识问答场景，但不一定适合工程执行历史。
- **CodeAct as query language**：让 agent 写代码查询历史，而不是学习一套额外 DSL 或反复调用细碎 CLI。
- **Progressive disclosure**：先返回轻量 summary，再按需展开细节，避免数据库检索变成 token 倾倒。
- **Evidence layer**：tool result、subagent、workflow、raw JSONL 等并非默认语义层，而是需要审计或补证时展开的证据层。
- **Self-narrating trace**：coding agent 会不断复述自己的观察和决策，这些复述构成可检索主干。

## 文章主张

1. Coding-agent session 不是普通聊天记录，而是结构化执行轨迹。
2. Agent memory 不应默认等同于向量检索或语义召回。
3. 对 coding-agent history，很多真实问题需要明确检索：文件、错误、工具调用、方案取舍和证据来源。
4. CodeAct/JavaScript 比 CLI/URI/DSL 更适合作为 agent 查询语言。
5. Helper function 的关键作用是控制信息规模，而不是简单封装 SQL。
6. Tool result 应该默认折叠，作为证据后备层按需展开。
7. Obelisk 的工程价值来自对数据形态的判断，而不是某个单点技术创新。

## 我的理解

这篇文章最有价值的地方，是把 memory 从“像不像人脑”拉回到“数据本来长什么样”。

Coding agent 的历史不是均质文本。它天然包含任务边界、项目路径、git 分支、工具调用、命令结果、文件修改、测试反馈和 agent 自己的阶段性总结。把这些东西压成 embedding chunk，反而会损失最重要的关系结构。

所以 Obelisk 的方向更像一个 agent-native observability/query layer。它不是替代 summary，也不是替代 vector search，而是把 agent 的历史作为一个可操作的数据结构暴露出来。模型真正需要的是能快速从“我现在要解决什么问题”跳到“历史里哪段执行证据相关”。

这里也能看出为什么 progressive disclosure 重要。数据库会让信息变得可得，但可得不等于可用。Agent-facing API 如果默认返回过多 detail，就会把结构优势变成上下文噪声。好的检索接口应该先给目录、摘要、候选证据，再让 agent 选择要深入哪一层。

## 对工程实践的启发

- 设计 agent history 时，不应只存 message text，还要保留 tool call、tool result、file path、cwd、branch、subagent、workflow、summary 等结构。
- 给 agent 的查询接口要 helper-first，raw SQL 作为后备，而不是默认路径。
- Helper 默认返回 compact result，需要时再展开原始证据。
- Memory 层应区分 raw evidence 和 durable conclusion：前者用于审计，后者需要人类批准后沉淀。
- 对多 agent/workflow 系统，主 agent 必须能按需查询子任务上下文，否则复杂任务会变成不可追溯黑箱。
- 评估 agent memory 不应只使用 IM/chat benchmark，还需要 execution-memory 风格 benchmark。

## 可能的反驳或风险

- 明确检索依赖良好的 schema 和字段设计；如果数据模型差，agent 仍然会查错或查不到。
- FTS/SQL 更擅长已知词、文件路径、错误信息和结构化关系；对模糊意图或概念迁移，向量检索仍有价值。
- 让 agent 写查询脚本会带来安全边界问题，尤其是文件系统、数据库写入和沙箱能力。
- Progressive disclosure 的 API 设计很难：太薄会导致 agent 找不到证据，太厚会导致 overfetch。
- Agent 的复述不一定可靠，因此 tool result 作为证据后备层必须容易展开和审计。

## 和本仓库阅读流的关系

这篇文章本身也解释了为什么阅读归档需要结构化：来源、元信息、译述、笔记和摘录分开，后续检索时能按不同目的进入不同层级。

如果把每日阅读也当成 execution memory 的一种轻量形式，那么 `meta.json` 是结构索引，`index.md` 是入口，`translation.zh.md` 是压缩后的语义主干，`original.*.md` 是来源映射，`notes.md` 是人类批准后的可复用理解。

## 可延伸思考

- Obelisk 这类 execution memory 是否应该和 git commit、test run、CI result 直接绑定？
- 对 coding agent 来说，哪些信息应该进入主干，哪些应该只作为证据层保存？
- 能否构造专门评估 execution memory 的 benchmark，而不是借用 IM memory benchmark？
- Vector search 在 execution memory 中最适合承担什么角色：候选召回、概念桥接，还是 fallback？
- 如果 agent 会写查询脚本，runtime 的 read-only guard 应该如何设计，才能兼顾安全和表达能力？

## 我的摘录

> Agent transcripts are not chat logs; they are self-narrating execution traces.

## 待补充问题

- Obelisk 当前的 helper API 是否已经足够覆盖常见 coding-agent 复盘问题？
- Memory mutation 的用户批准边界具体如何在不同 agent runtime 中实现？
- 如果未来 coding agent 原生支持 execution memory，session schema 应该从一开始就包含哪些字段？
