# Reiner Pope：LLM 训练与服务背后的数学

> 原文：[Reiner Pope - The math behind how LLMs are trained and served](https://www.youtube.com/watch?v=xmkSf5IS-zw)  
> 官方发布页：https://www.dwarkesh.com/p/reiner-pope  
> 文稿来源：https://gist.githubusercontent.com/dwarkeshsp/79100f0fdeed69d76241903bb0604dbe/raw/b5810c077e8ca37fe7dfd917f75a883b4c6ff688/reiner-dwarkesh-transcript.md  
> 相关练习卡片：https://reiner-flashcards.vercel.app/  
> 主持人：Dwarkesh Patel  
> 嘉宾：Reiner Pope  
> 发布日期：2026-04-29

## 说明

原始文稿是一场两小时以上的黑板访谈。本文件采用中文结构化译文：保留原文的章节、核心推导、关键公式和结论，省略部分口语重复、寒暄和中断确认。完整英文逐字稿见 [original.en.md](original.en.md)，配套练习题见 [flashcards.en.md](flashcards.en.md)。

## 时间戳

- 00:00:00 - batch size 如何影响 token 成本和生成速度
- 00:32:09 - MoE 模型如何布局在 GPU rack 上
- 00:47:12 - pipeline parallelism 如何把模型层移动到不同 rack
- 01:03:37 - Ilya 为什么说“现在我们知道，流水线并不明智”
- 01:18:59 - 由于 RL，模型可能比 Chinchilla-optimal 多训练 100 倍
- 01:33:02 - 从 API 定价反推长上下文的内存成本
- 02:04:02 - 神经网络与密码学之间的趋同演化

## 00:00:00 - batch size 如何影响 token 成本和生成速度

Dwarkesh 介绍 Reiner Pope：他是 MatX 的 CEO，过去在 Google 做过 TPU 架构。这期不是普通访谈，而是黑板课，主题是模型架构、机器学习基础设施，以及训练和推理在集群上实际如何运行。理解这些细节之后，AI 架构为什么长这样、API 价格为什么这样、AI 进展为什么受这些约束，都会更容易解释。

开场问题是：为什么 Claude、Codex、Cursor 等产品可以提供类似 Fast Mode 的模式，让用户支付更高价格以换取更快 token 流式输出？能否继续加价 100 倍来获得更快速度？反过来，是否可以提供 Slow Mode，让用户等更久以换取更低价格？

Reiner 的核心回答是：最重要的变量是 batch size。另一个变量是 speculative decoding 或 multi-token prediction，但本节先分析 batch size。

### roofline analysis 的两个资源约束

Reiner 使用 roofline analysis 来近似分析 transformer 在芯片集群上的推理时间。以 Blackwell NVL72 这样的 72 GPU rack 为例，分析只看两个硬件资源：

- 计算吞吐：FLOPs。
- 内存带宽：memory bandwidth。

模型侧也先只保留两个因素：

- 操作权重所需的时间。
- 操作上下文，也就是 KV cache 所需的时间。

一次 forward pass 的总时间可以近似写成：

$$T = \max(t_{\mathrm{compute}}, t_{\mathrm{mem}})$$

计算时间主要来自对 active parameters 的矩阵乘：

$$t_{\mathrm{compute}} = \frac{B \cdot N_{\mathrm{active}}}{\mathrm{FLOPs}}$$

其中：

- $B$ 是 batch size。
- $N_{\mathrm{active}}$ 是每个 token 实际激活的参数数。
- FLOPs 是硬件计算吞吐。

这里暂时忽略 attention 计算本身，因为在这个简化模型中，它通常小于权重矩阵乘的主项。

内存时间包括两个部分：读取模型权重，以及读取 KV cache：

$$t_{\mathrm{mem}} = \frac{N_{\mathrm{total}} + B \cdot \mathrm{len}_{\mathrm{ctx}} \cdot \mathrm{KV}_{\mathrm{bytes/token}}}{\mathrm{mem}_{\mathrm{bw}}}$$

其中：

- $N_{\mathrm{total}}$ 是模型总参数数。
- $\mathrm{len}_{\mathrm{ctx}}$ 是上下文长度。
- $\mathrm{KV}_{\mathrm{bytes/token}}$ 是每个 token 的 KV cache 字节数。
- $\mathrm{mem}_{\mathrm{bw}}$ 是内存带宽。

batch 指的是许多用户或许多序列一起被服务，而不是一次只服务一个用户。batch 很有价值，是因为权重读取可以在 batch 内摊薄。如果不 batching，推理经济性可能差几个数量级。

### KV cache 是什么

在 autoregressive decode 中，模型每次只生成一个新 token。新 token 要通过所有层的权重矩阵，同时它还要通过 attention 查看过去所有 token 的内部表示。过去 token 的 key/value 表示就是 KV cache。

对当前新 token 来说，读取 KV cache 是一次面向整个历史上下文的内存访问。它主要受内存带宽约束，而不是矩阵乘计算约束。上下文越长，KV cache 读取越重。

### batch size 与延迟

如果横轴是 batch size，纵轴是一次 forward pass 的时间：

- 计算时间随 batch size 线性增长。
- 权重读取时间是一个常数项，因为权重读一次即可被 batch 内多个 token 共用。
- KV cache 读取时间也随 batch size 线性增长，因为每个序列都有自己的上下文。

总延迟由计算曲线和内存曲线的较大者决定。即使 batch size 很小，延迟也不能无限降低，因为你仍然要从 HBM 中读取模型权重。这给了延迟一个硬件下界。

上下文长度会改变瓶颈。如果上下文变长，KV cache 读取时间增加，系统可能从 compute-bound 转向 memory-bound。对于 dense attention，KV 读取近似随上下文长度线性增长；sparse attention 可以改善这个 scaling。

### batch size 与每 token 成本

如果看成本，就要把总时间除以 batch size，即 $T / B$。这时：

- 计算项除以 $B$ 后近似成为常数。
- KV cache 项除以 $B$ 后也近似成为常数。
- 权重读取项除以 $B$ 后成为随 batch size 下降的双曲线。

因此，batch size 从 1 增大时，每 token 成本会迅速下降，因为权重读取被摊薄。但成本不会无限下降，因为计算和 KV cache 都无法继续靠 batch 摊薄。

这也解释了为什么“Slow Mode”不会无限便宜。等更久可以帮助形成更大 batch，但一旦权重读取已经被充分摊薄，剩下的计算和 KV cache 成本是每个 token 自己必须付出的。

### 最优 batch size 的粗略推导

为了估算什么时候权重读取已经被摊薄到与计算时间平衡，先忽略 KV cache，令：

$$\frac{B \cdot N_{\mathrm{active}}}{\mathrm{FLOPs}} = \frac{N_{\mathrm{total}}}{\mathrm{mem}_{\mathrm{bw}}}$$

整理得到：

$$B = \frac{\mathrm{FLOPs}}{\mathrm{mem}_{\mathrm{bw}}} \cdot \frac{N_{\mathrm{total}}}{N_{\mathrm{active}}}$$

现代 GPU 上，按 FP4 乘法和字节数换算后，$\mathrm{FLOPs}/\mathrm{mem}_{\mathrm{bw}}$ 常见量级约为 300。因此：

$$B \approx 300 \cdot \frac{N_{\mathrm{total}}}{N_{\mathrm{active}}}$$

如果把 $\frac{N_{\mathrm{total}}}{N_{\mathrm{active}}}$ 理解为稀疏度倍率，那么 MoE 越稀疏，所需 batch size 越大。例如 DeepSeek V3 每次激活 32/256 个 expert，也就是 8 倍稀疏度，粗略需要：

$$B \approx 300 \times 8 = 2400$$

实践中通常会再放大两三倍，因为真实系统达不到理想 roofline 效率，而且 KV cache 也会消耗内存带宽。

这里的 batch size 指的是一次 forward pass 中同时为多少个序列各生成一个新 token。因此 2000 不是 2000 个 token 的一个长序列，而是约 2000 个并发序列。

### 20ms 火车模型

Reiner 用火车站类比 batching：GPU 每隔约 20ms 发出一班“车”，所有准备好的序列上车，一次 forward pass 产生每个序列的下一个 token。如果请求刚错过一班车，就等下一班，再等这一班跑完，所以最坏排队延迟大约是两个间隔。

20ms 的经验值来自 HBM 容量除以内存带宽，也就是把 HBM 读一遍所需的时间。例如 Rubin 代硬件可粗略看作：

$$288\text{GB} / 20\text{TB/s} \approx 15\text{ms}$$

如果调度间隔短于这个时间，你根本来不及读完权重或 KV；如果远长于这个时间，FLOPs 会空闲，因为内存中已经没有更多有用数据可读。

### batch 对中心化的影响

推理 batching 带来规模经济，但这个门槛并不像直觉上那么夸张。一个 rack 以 2000 batch、约 20ms 一轮计算，大约对应 10 万级 token/s。相比大型 API 服务全球上亿 token/s 的吞吐，一个 rack 只是很小的一部分。因此，batching 不是无限推动中心化的理由，但确实要求服务商有足够流量来填满 batch。

### 稀疏度与模型质量

更高稀疏度可以减少每 token 激活参数，从而节省计算。但稀疏度能提高到什么程度而不损害模型质量，这是经验问题，不是单靠代数能回答。Reiner 提到 routed language model 的 scaling law 研究：在某些 MoE 技术下，保持 active parameters 不变、增加 expert count，模型质量仍可能提升。不过具体结论依赖 MoE 架构。

## 00:32:09 - MoE 模型如何布局在 GPU rack 上

MoE layer 的自然边界是一个 rack，因为 MoE routing 本质上是 all-to-all 通信：任何 GPU 上的 token 都可能被路由到任何其他 GPU 上的 expert。

在 rack 内，NVLink 可以让 GPU 之间高带宽互连，很适合 all-to-all。跨 rack 的 scale-out 网络通常慢得多，可能慢约一个数量级，因此如果把一个 MoE layer 切到多个 rack，就会让 all-to-all 成为瓶颈。

这导致一种自然布局：把同一个 MoE layer 的 experts 尽量放在同一个 rack 内，让 token 在 rack 内完成路由和聚合。跨 rack 更适合放不同层，而不是把同一层的 all-to-all 拆开。

这个视角把模型架构和数据中心网络拓扑联系起来：MoE 不只是算法选择，也是在利用特定通信结构。一个模型层到底应该铺在一个 rack、多个 rack 还是一个更小的 group 上，取决于该层的通信模式和网络带宽层级。

## 00:47:12 - pipeline parallelism 如何把模型层移动到不同 rack

pipeline parallelism 的基本做法是把模型层切成多个 stage，不同 GPU 或 rack 负责不同层。输入 token 先经过早期 stage，再传到后续 stage。

这种方法可以把模型权重分摊到多个设备上，但会产生 pipeline bubble：

- 在一个 batch 刚开始时，后面 stage 没有输入可处理，会空闲。
- 在一个 batch 快结束时，前面 stage 已经没有新输入，也会空闲。

训练时不能简单地把不同 batch 重叠起来完全消除 bubble，因为你需要先合并梯度并更新模型，再处理下一批训练数据。微批次可以缓解 bubble，但不能免费消除。

pipeline parallelism 对 inference 的问题也很关键：它确实把每个设备上的权重按 stage 数 $P$ 分摊，但 KV cache 不一定同样按 $P$ 分摊。为了让 $P$ 个 stage 都保持忙碌，需要同时有 $P$ 个 micro-batch 在 pipeline 中飞行，因此并发序列数也随 $P$ 增加。长上下文时 KV cache 往往主导内存，这会限制 pipeline parallelism 的收益。

换句话说，pipeline 可以解决“权重太大”的问题，但不一定解决“KV cache 太大”的问题。对于长上下文推理，这个区别非常重要。

## 01:03:37 - Ilya 为什么说“现在我们知道，流水线并不明智”

Ilya 的那句话指向一个研究工程权衡：pipeline parallelism 会给模型架构施加额外约束，而这些约束可能妨碍研究迭代。

如果某种新架构要求后续层 attention 到前面所有层的 residual，或者要求 global attention 与 sliding-window attention 交错出现，那么这些跨 stage 依赖会让 pipeline 变复杂。不同 stage 的计算量也可能不均衡，导致 load imbalance。

真正昂贵的不是某一次通信，而是研究速度下降。当前沿模型架构还在快速演化时，任何会限制架构探索、增加调试难度、拖慢迭代的并行化方式，都可能在整体上得不偿失。

这个观点不是说 pipeline parallelism 永远不能用，而是说它把系统优化和模型设计绑定得太紧。对研究团队而言，最大的成本可能是“不能方便地尝试下一种架构”。

## 01:18:59 - 由于 RL，模型可能比 Chinchilla-optimal 多训练 100 倍

Reiner 接着把预训练、RL 和推理统一放进一个总计算成本框架中：

$$C_{\mathrm{total}} = C_{\mathrm{pretrain}} + C_{\mathrm{RL}} + C_{\mathrm{inference}}$$

预训练的经典 FLOPs 估算是：

$$C_{\mathrm{pretrain}} = 6 \times N_{\mathrm{active}} \times D_{\mathrm{pretrain}}$$

其中的 6 来自：

- forward pass：每个参数每个 token 约 2 FLOPs，即乘法加加法。
- backward pass：约为 forward 的 2 倍，因为要计算输入和权重的梯度。
- 合计约 $2 + 4 = 6$。

RL 和 inference 可以粗略写成：

$$C_{\mathrm{RL}} = (2 \,\mathrm{to}\, 6) \times N_{\mathrm{active}} \times D_{\mathrm{RL}} \times \mathrm{inefficiency}$$

$$C_{\mathrm{inference}} = 2 \times N_{\mathrm{active}} \times D_{\mathrm{inference}} \times \mathrm{inefficiency}$$

RL 的系数取决于 rollout 是否也训练，以及训练方式。decode 阶段通常 MFU 更低，因此要乘上低效率项。

如果预训练、RL 和推理之间可以相互替代，粗略直觉是最优点会让三者边际成本相近。也就是说，一个部署后会被大量推理使用的模型，值得在预训练阶段多花更多 token，把推理期的总成本压低。

访谈中给出的数量级例子是：假设一个前沿模型部署两个月，全球吞吐 5000 万 token/s，那么两个月 inference token 数大约是：

$$50\text{M tokens/s} \times 60 \times 86400 \approx 200\text{T tokens}$$

如果用这个量级反推预训练 token 数，可能得到 200T token 级别。

而 Chinchilla rule 通常说：

$$D_{\mathrm{optimal}} \approx 20 \times N_{\mathrm{active}}$$

如果模型有 100B active parameters，那么 Chinchilla-optimal token 数约为：

$$20 \times 100\text{B} = 2\text{T tokens}$$

200T 相比 2T，就是 100 倍。这就是“由于 RL 和推理，模型可能比 Chinchilla-optimal 多训练 100 倍”的含义。

这并不是说 Chinchilla 错了，而是目标函数变了。Chinchilla 主要考虑给定训练预算下的预训练最优；前沿模型服务考虑的是预训练、RL、部署推理总成本，以及模型质量对后续使用量的影响。

## 01:33:02 - 从 API 定价反推长上下文的内存成本

Reiner 用 API 定价作为公开信号，反推长上下文推理成本。例如 Gemini 在超过某个长上下文阈值后，token 价格显著上升。高层解释是：

- 阈值以下，推理可能主要 compute-bound，随着 context length 增加，成本不明显上升。
- 阈值以上，KV cache 读取让推理变成 memory-bound，成本随 context length 近似线性增加。

在 compute 与 KV fetch 的交叉点，有：

$$\frac{B \cdot N_{\mathrm{active}}}{\mathrm{FLOPs}} =
\frac{B \cdot \mathrm{len}_{\mathrm{ctx}} \cdot \mathrm{bytes/token}}{\mathrm{mem}_{\mathrm{bw}}}$$

消去 $B$，可得：

$$\mathrm{bytes/token} =
\frac{\mathrm{mem}_{\mathrm{bw}}}{\mathrm{FLOPs}} \cdot
\frac{N_{\mathrm{active}}}{\mathrm{len}_{\mathrm{ctx}}}$$

如果 $\mathrm{FLOPs}/\mathrm{mem}_{\mathrm{bw}} \approx 300$，$N_{\mathrm{active}} \approx 100\text{B}$，交叉点 $\mathrm{len}_{\mathrm{ctx}} = 200\text{K}$，则：

$$\mathrm{bytes/token} \approx \frac{1}{300} \cdot \frac{100\text{B}}{200\text{K}} \approx 1.7\text{KB}$$

这个数量级可以用来理解为什么长上下文不是“只是窗口更大”。每增加一个上下文 token，都可能增加后续 decode 时需要反复读取的 KV memory。

### output token 为什么更贵

输出 token 常常比输入 token 贵 3 到 5 倍。原因是 prefill 和 decode 的硬件利用率不同：

- prefill 可以并行处理整段输入序列，矩阵乘更大，权重读取更容易被摊薄。
- decode 每次只生成一个新 token，需要反复读取权重和 KV，FLOPs 更容易等内存。

因此，decode 的 MFU 往往明显低于 prefill。

### cached input 为什么便宜

缓存命中的 input token 通常便宜很多，因为读取已有 KV cache 比重新计算整段输入便宜。重新 prefill 要跑完整个前向计算；cache hit 则主要是从内存加载已算好的 KV 表示。

## 02:04:02 - 神经网络与密码学之间的趋同演化

最后一部分是类比：神经网络和密码协议在高层结构上都有“多层混合”的特征。密码学希望输出的每一位都以复杂方式依赖输入的每一位，让结构看起来像随机；神经网络则希望从看似混乱的数据中提取结构和关系。

两者方向相反：

- 密码协议把有结构的信息打散，使其难以区分于随机。
- 神经网络从看似随机或高维的数据中抽取结构，使其变成有用表示。

但它们都演化出多层、混合、传播依赖关系的架构。这种类比的价值不在于说两者是同一个东西，而在于提醒我们：当系统需要让所有输入维度以复杂方式互相影响时，多层组合结构可能是一种自然解。

## 中文结论

这期访谈的主线是：LLM 的许多产品现象都能从硬件约束和系统架构中推出来。

Fast Mode、Slow Mode、output token 更贵、长上下文涨价、MoE 的 rack 布局、pipeline 的工程代价、预训练 token 数远超 Chinchilla，这些看似分散的问题，都可以放进同一个框架：计算、内存、通信、并发和总生命周期成本之间的权衡。

最重要的阅读收获是，模型不是抽象地“运行在 GPU 上”。模型架构、数据中心拓扑、HBM 带宽、KV cache、batching 策略和产品定价是同一个系统的不同外显。
