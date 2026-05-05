# Reiner Pope：LLM 训练与服务背后的数学

> 原文：[Reiner Pope - The math behind how LLMs are trained and served](https://www.youtube.com/watch?v=xmkSf5IS-zw)  
> 官方发布页：https://www.dwarkesh.com/p/reiner-pope  
> 文稿来源：https://gist.githubusercontent.com/dwarkeshsp/79100f0fdeed69d76241903bb0604dbe/raw/b5810c077e8ca37fe7dfd917f75a883b4c6ff688/reiner-dwarkesh-transcript.md  
> 相关练习卡片：https://reiner-flashcards.vercel.app/  
> 主持人：Dwarkesh Patel  
> 嘉宾：Reiner Pope  
> 发布日期：2026-04-29

## 说明

本文件是 [original.en.md](original.en.md) 中英文文稿的完整中文翻译。译文尽量保留原文时间戳、说话人、链接、技术术语和口语推进方式；个别变量名用代码格式表示，以避免不同 Markdown/LaTeX 渲染器把下划线误解析为数学错误。

## 时间戳

- (00:00:00) - batch size 如何影响 token 成本和速度
- (00:32:09) - MoE 模型如何布局在 GPU rack 上
- (00:47:12) - pipeline parallelism 如何让模型层跨 rack 移动
- (01:03:37) - Ilya 为什么说：“现在我们知道，pipelining 并不明智。”
- (01:18:59) - 由于 RL，模型可能比 Chinchilla-optimal 多训练 100 倍
- (01:33:02) - 从 API 定价推断长上下文内存成本
- (02:04:02) - 神经网络与密码学之间的趋同演化

## 文稿

### 00:00:00 - batch size 如何影响 token 成本和速度

**Dwarkesh Patel**

今天我采访的是 [Reiner Pope](https://reiner.org/)。他是 [MatX](https://matx.com/) 的 CEO，[MatX 是一家新的芯片创业公司](https://techcrunch.com/2026/02/24/nvidia-challenger-ai-chip-startup-matx-raised-500m/)。在此之前，他在 Google 做过 [TPU](https://en.wikipedia.org/wiki/Tensor_Processing_Unit) 架构，以及很多其他工作。这一期和我平时的访谈形式非常不同，会是一场黑板课。我们一会儿就会站起来。事实上，我们专门为了这种形式搭了这个新演播室，所以能和你一起启用它让我很高兴。

我们会聊 [model architecture](https://huggingface.co/blog/ProCreations/the-mega-article)、[ML infra](https://www.sei.cmu.edu/blog/a-hitchhikers-guide-to-ml-training-infrastructure/) 以及很多其他东西。我认为这个话题重要，是因为一旦你理解了 [training](https://www.ibm.com/think/topics/model-training) 和 [inference](https://cloud.google.com/discover/what-is-ai-inference) 在一个集群里是如何工作的，很多事情就开始说得通了：为什么 AI 是现在这个样子，为什么 AI 架构是现在这个样子，为什么 API 价格是现在这个样子，以及从根本上说，为什么 AI 进展是现在这个样子。要理解这些，你必须理解细节；而理解这些细节，需要一块黑板。Reiner，非常感谢你来做这期。

**Reiner Pope**

很高兴来到这里。

**Dwarkesh Patel**

先披露一下，我是 MatX 的天使投资人，但这和本期播客无关。Reiner，开场我想问这个问题。现在有一些公司，比如 Claude、Codex 和 Cursor，会提供类似 Fast Mode 的东西：你付 6 倍价格，它们以 2.5 倍速度向你流式输出 [tokens](https://blogs.nvidia.com/blog/ai-tokens-explained/)。从机制上说，我很好奇这里发生了什么。为什么你可以通过付更多钱获得更低延迟？

第二，能不能继续往上走？你能不能付 100 倍价格，然后以某种方式获得快得多的速度？第三，能不能反过来？是否可以有类似 Claude Code “Slow Mode”的东西：如果你愿意等好几分钟，能不能拿到更便宜的价格？也许这能帮助引出你接下来要做的分析。

**Reiner Pope**

很好。先稍微剧透一下结论：最大的效应是 [batch](https://cloud.google.com/discover/what-is-batch-inference) size。我们现在要做的，是定量说明它到底是什么样子，以及它对延迟和成本有什么影响。还有另一个效应，可以叫做 [speculative decoding](https://pytorch.org/blog/hitchhikers-guide-speculative-decoding/) 或 [multi-token prediction](https://arxiv.org/abs/2404.19737)。我们也许稍后会回到它，但首先讨论 batch size。

我想先介绍两条分析原则。第一，我们会对一个 [transformer](https://en.wikipedia.org/wiki/Transformer_\(deep_learning\)) 模型在芯片集群上运行的方式做 [roofline analysis](https://en.wikipedia.org/wiki/Roofline_model)。我们可以拿一个 [Blackwell NVL72](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) 集群作为例子，也就是一个有 72 个 [GPU](https://en.wikipedia.org/wiki/Graphics_processing_unit) 的 rack。roofline analysis 的意思是，我们看 memory bandwidth 和 compute performance。另一侧，我们只看模型的两个简单因素：操作 [weights](https://www.geeksforgeeks.org/deep-learning/the-role-of-weights-and-bias-in-neural-networks/) 所需的时间，以及操作上下文，也就是 [KV cache](https://huggingface.co/blog/not-lain/kv-caching) 所需的时间。

我们开始吧。我们要估算运行某种形态的 inference 需要多长时间。我们不会完全准确，不能精确预测时间，所以我们做近似。我们会说，这个时间必须大于等于某个量。我们考虑两个方面：做 memory fetch 需要的时间，以及做 compute 需要的时间。事实会证明，即使用一个简单模型，这也有很强的预测能力。

逐项来看，做 compute 需要多长时间？在 compute 里，我真正要做两件事：第一，要乘以所有 active [parameters](https://www.ibm.com/think/topics/model-parameters)；第二，要对 [attention](https://en.wikipedia.org/wiki/Attention_\(machine_learning\)) 做一些工作。乘以所有 active parameters 时，我有一个正在运行的 batch size，还有模型里的 active parameters 数量。然后我把它除以 compute throughput，也就是芯片的 [FLOPs](https://en.wikipedia.org/wiki/Floating_point_operations_per_second)。这是硬件层面的因素。

这涵盖了所有权重矩阵乘法的 compute time。这里有个小 caveat：我们忽略了 attention 计算本身的时间，但一般来说，和这一项相比它会相当小。所以我们先忽略它。

**Dwarkesh Patel**

我会不时插进来问一些非常基础的问题，或者澄清一些基本点。对听众来说，你并不是一次只服务一个用户。batch 指的是你同时服务很多不同用户，整个就是一个 batch。

**Reiner Pope**

我可以至少稍微解释一下 batch 的动机。我们会看到为什么 batch 是一种非常有利的优化。结果会是，如果你不把许多用户 batch 在一起，成本和经济性可能比 batch 在一起差一千倍。我们会非常明确地看到这一点。

然后是 active parameters 的数量。比如看 [DeepSeek](https://en.wikipedia.org/wiki/DeepSeek) 模型，[DeepSeek V3](https://api-docs.deepseek.com/news/news1226) 大约有 37B active parameters，700B total parameters。我们关注的是单个 AI token 实际 active 的那些参数。

我们在建模 compute performance。我会一直写等号，但在所有这些情况下，你都可以把这个时间理解成“至少这么多”，也许还有一些我们忽略的项。

在 memory 一侧，我们需要对内存做什么？我们需要 fetch 所有权重，所以有一个 fetch total parameters 的时间，不只是 active parameters。这里有 weight fetch time；此外还有 KV cache fetch time。它实际上取决于 batch size。对 batch 里的每个元素，我们都必须 fetch 一整个 context length 的 tokens，并且每个 token 有一个 size，也就是 one token 的 bytes。这是模型参数。

**Dwarkesh Patel**

也许先退一步，快速解释一下 KV cache 是什么。

**Reiner Pope**

当我做一次 [forward pass](https://towardsdatascience.com/neural-networks-forward-pass-and-backpropagation-be3b75a1cfcc/) 时……让我画一下 [autoregressive inference](https://en.wikipedia.org/wiki/Autoregressive_model) 是怎么工作的。这是在 decode 阶段。如果我有一堆文本 token……我画的是一个 [tensor](https://en.wikipedia.org/wiki/Tensor_\(machine_learning\))，因为 tokens 最终会被表示成某个 [embedding](https://en.wikipedia.org/wiki/Embedding_\(machine_learning\)) 维度里的 tensor。这个方向是 sequence length。

运行 decode 的工作，是让每个 token 穿过很多不同层里的大量矩阵乘法。一般来说，我必须对所有这些 tokens 做这项工作。但 decode 的一步只是在这里生成额外的这一个 token。

我要做的是，对整个模型里的所有权重矩阵做一次完整 forward pass。但接着有 attention 机制：这个 token 会看所有过去的 tokens。它具体在看什么？它看的是模型对这些 tokens 产生的某种内部表示，我们称之为 KV cache。这个单个 token attend 到所有历史 tokens 的过程，就是 attention。它主要受 memory fetch 主导，而不是矩阵乘法主导。

所以我们在这里写下要 fetch 的 memory 数量，然后当然要除以内存带宽，也就是每秒多少 memory bytes。事实上，这些方程已经足够让我们画一些拟合线了。我们想看的是对 batch 的敏感性，以及稍后单独画的对 context length 的敏感性。我们说过，batch size 能给你带来 latency 和 cost 的某种 trade-off。

我们把它画出来。我觉得我们想画的其实只有两张图。首先画 batch size 对 time。看形状时，我们有一个 max，它里面有 sum，还有另一项。我们逐项看看这些项如何 scale：compute 和 memory 的时间，以及它们如何出现。

先看 compute time。它对 batch size 是纯线性的，没有 offset，所以是一条这样的曲线。这是 `t_compute`。在 memory 一侧，有一部分只是一个常数 base offset，也就是 weight fetch。最后还有 KV fetch 这一项，它也相当线性地依赖 batch size，所以看起来像这样。这一项加上这一项，然后和 compute 取 max……先至少画出 sum。两个 memory times 加起来会变成这样的斜线。然后总体的 maximum 是，我画粗一点，就是这两条曲线的最大值。

这是什么意思？这是一张 latency plot。如果我增加 batch size，起初它对 batch size 的依赖并不强，所以这里有一个 latency 下界。这已经部分回答了问题。对于给定硬件配置，我们也可以谈改变硬件配置，latency 有一个下界。原因很简单：我需要把所有 total parameters 从内存读进芯片，而这需要一定时间。如果我用满了全部 memory bandwidth，就不能比这更快。

**Dwarkesh Patel**

看起来你画的 compute time 的斜率，以及 KV 如何增长，还有 KV 对 memory time 的影响……

**Reiner Pope**

如果它在上面或者下面会怎样？

**Dwarkesh Patel**

对，这一定是这样吗？如果这永远成立，那么 batch size 增长时，compute 总是会压过 KV，这似乎意味着只要 batch size 足够大，memory 可能永远不是问题。

**Reiner Pope**

这对 [context length](https://www.ibm.com/think/topics/context-window) 非常敏感，所以我觉得我们应该稍后回到这个问题并展开。随着 context length 变化，KV fetch time 会越来越高，导致从 compute-limited 转向 memory-limited。

**Dwarkesh Patel**

斜率刚好等于 compute time 的斜率，有什么特别重要的含义吗？

**Reiner Pope**

每当我们有 balance point，它就表示你刚好做对了。对于某个特定 context length，如果斜率匹配，就说明我同时 memory-bound 和 compute-bound，这是一个非常理想的位置。

**Dwarkesh Patel**

这是一个很简单的代数问题，但假设最优点是 100K context length，而你走到 200K context length。你的 [MFU](https://www.glennklockwood.com/garden/MFU) 会降到 50% 吗？稍微偏离最优 context length 区间，也就是 Goldilocks zone，会不会对 MFU 有巨大影响？

**Reiner Pope**

对。按这里的模型确实如此。这里有一个关键点：我把 memory fetch 建模成和 context length 线性相关。这取决于模型架构。对于所有 dense attention 的模型架构，这是真的。[Sparse attention](https://medium.com/@aadishagrawal/the-evolution-of-attention-mechanisms-scaling-transformers-smartly-73cb96f991cf) 的 scaling 会好得多。

**Dwarkesh Patel**

明白。sparse attention 是大家实践中都在用的吗？

**Reiner Pope**

我对 sparse attention 很感兴趣。很难知道各个 lab 实际在用什么。DeepSeek 发表过一种 [sparse attention mechanism](https://arxiv.org/abs/2512.02556)。我顺便提一句，DeepSeek 一些发表了 sparse attention 的论文，会让这一项里出现平方根。

到目前为止，我们看的是 latency。从这里很难直接读出 cost。如果我思考 cost 意味着什么……为了运行这次 inference，我会使用 GPU 若干秒，比如 1 毫秒或 20 毫秒。我必须为这段时间支付租用成本，比如每 GPU 每小时 2 美元之类。

这就是这次 inference 的成本。但在这次 inference 期间，我处理了多少 token？那就是 batch size。我们真正想画的是 cost versus batch size，也就是 `t / B` 对 batch size。这是每 token 成本。我们要想象把这三条曲线都除以 `B`，也就是乘以 reciprocal。结果是：compute curve 原来是线性的，除以 `B` 后就变成一个常数。这是 `t_compute`。KV fetch 原来也是线性的，现在也变成常数。weight fetch 原来是常数，现在除以 `B`，所以变成双曲线。

同样，我们要对 sum 和 max 做计算。这两项的 sum 会把双曲线上移。KV fetch 和 weight fetch 的 sum 给出更高的一条双曲线，像这样。然后我们和 compute 取 max。最终得到的就是我们关心的总体形状。

我们再次看到一些极限行为。batch size 为 1 时，成本一开始非常高。它几乎走向无穷大，因为有太多 weight fetch 没有在大 batch size 上摊薄。但随着 batch size 增加，weight fetch 会被许多不同 batch elements 摊薄，它的成本变得很小，最终 compute time 驱动成本。所以 cost 有一个下界，也就是这条线。

**Dwarkesh Patel**

所以 Claude Code Slow 或 Codex Slow 之类会落在这条线上。它不会有太大帮助，因为你没法把 KV values 在更大 batch 上摊薄。

**Reiner Pope**

它们对每个 batch 都是独有的。compute 对每个 batch 也是独有的。所以问题是，在把其他东西都摊掉之后，你对每个 batch 最少要做多少工作？

**Dwarkesh Patel**

你不再 memory bandwidth bound 的那个点，在实践里需要多大的 batch？frontier models 实际 batch 大概多大？

**Reiner Pope**

你可以直接解出来。它甚至对模型架构不是特别敏感。我们来做一下。

我们讨论的是 memory time 等于 compute time 的时候。这就是那个问题。因为我们关注 batch size，本质上也是问 weights 什么时候被矩阵乘摊薄，所以我会聚焦比较 weight fetch time 和 weight multiply time。为了简化分析，得到一个干净答案，我会暂时忽略 KV fetch 项。我们把这两个时间相等。

写出来就是：`N`，total parameters 的数量，除以 memory bandwidth，等于 batch size 乘以 active parameters 数量，再除以 compute performance。看这里，上面都是模型参数，下面都是硬件参数。把它们整理成一边是硬件参数会比较好。

这等价于 FLOPs 除以 memory bandwidth，等于 batch size 乘以 active parameters 数量，再除以 total parameters 数量。这个硬件参数最终会变成一个无量纲常数。如果按 FLOPs 看……它的量纲是什么？这是每秒多少次乘法，这是每秒多少字节。所以还不完全无量纲。但你可以说，每秒多少 [FP4](https://towardsdatascience.com/16-8-and-4-bit-floating-point-formats-how-does-it-work-d157a31ef2ef/) 乘法，再乘以每个 FP4 是半个字节，最后就能把它变成无量纲。在大多数 GPU 上，这大约是 300。

**Dwarkesh Patel**

从一代模型到下一代模型，FLOPs 不断增加，这个比率有没有变化？

**Reiner Pope**

这是一个硬件参数。硬件变化到什么程度？从 [A100](https://www.nvidia.com/en-us/data-center/a100/) 到 [H100](https://www.nvidia.com/en-us/data-center/h100/) 再到 [B100](https://www.exxactcorp.com/blog/hpc/comparing-nvidia-tensor-core-gpus)，FLOPs 大幅增加，memory bandwidth 也大幅增加，所以这个比率保持得相当稳定。

我们也可以表达这一项。这是一个 sparsity parameter。我甚至可能换一种说法。我们直接解 batch size。把它移到另一边，得到 batch size 需要大于大约 300 乘以 sparsity。比如 DeepSeek 里，我激活 256 个 experts 中的 32 个，所以 DeepSeek 的这个倍率是 8。

这个给出的 ballpark 和实践非常吻合。一般来说，人们会比这个稍微大一些。他们不想刚好卡在 balance point 上，因为真实世界效率没有 roofline analysis 说的那么好。但拿这个数再乘 2 到 3 倍就差不多。

**Dwarkesh Patel**

所以 batch 里是两三千个 token。但如果把 KV cache 包括进去，意思是 optimal batch size……

**Reiner Pope**

应该变得更大。我们刚才解的是 compute time 等于 memory time 的等价点。如果我加入某个消耗更多 memory bandwidth 的东西，那么留给 weight loads 的 bandwidth 就更少。我需要让 memory bandwidth 增长更多，因此 batch size 也要更大。

**Dwarkesh Patel**

这看起来小得不可思议。它少于一个 sequence，对吧？

**Reiner Pope**

记住，我说的是我正在为多少个 token 各自生成下一个 token。它实际上是 2000 个独立 sequence。

**Dwarkesh Patel**

明白。我们只是在讨论这些 sequence 上的一次 forward pass。你把 batch 理解为 sequence 数量。

**Reiner Pope**

对。

**Dwarkesh Patel**

如果你有一个 frontier model，并且真的在做 inference，那肯定有超过 2000 个并发用户。是否会因为要等整个 batch 填满而增加延迟？或者只要有合理数量的用户，要填满下一个 2000 个 slot，花 100 毫秒的概率是不是非常低？

**Reiner Pope**

可以把它想成：火车什么时候发车？假设我选择了一个 batch size 来运行。顺便说一下，这里的 intersection point 和这里的是同一个。我选择这个 batch size，并知道它会花，比如 20 毫秒，这通常就是它落到的位置。

这是一条 GPU 上正在运行什么的时间线。它每 20 毫秒都会启动一个新 batch。你可以把它想成火车时刻表。每 20 毫秒发一班新车。所有准备好的乘客都上车。如果车满了，他们等下一班。如果车没满，车也照样开。

这对排队延迟意味着什么？最坏情况是一个请求刚好在火车发车后到达。它必须等下一班，所以最多等 20 毫秒，然后还要等那班车跑完。所以最坏延迟是 40 毫秒。

**Dwarkesh Patel**

20 毫秒是怎么来的？

**Reiner Pope**

这是一个经验法则，但它来自哪里还没有完全解释。到目前为止，我们关注 memory bandwidth 和 compute time。看 memory 时，另一个考虑是我们想用满所有 memory capacity。一般来说，我们会用全部 memory capacity 存 weights 或 KVs。在一次 forward pass 的时间内，我们想把所有 memory capacity 都读进芯片。也就是 capacity 除以 bandwidth。在许多不同代的 [HBM](https://en.wikipedia.org/wiki/High_Bandwidth_Memory) 上，这通常会落在 20 毫秒左右。

**Dwarkesh Patel**

单位是对的。一个 byte 除以 bytes per second。

**Reiner Pope**

例如在 [Rubin](https://www.nvidia.com/en-us/data-center/technologies/rubin/) 代，大概是 288 GB 除以 20 TB/s，算出来大约 15 毫秒。

**Dwarkesh Patel**

我确认一下我理解了这句话。单位分析我懂。它的意思是，我们可以在这段时间内把 HBM 排空并替换掉。所以我们不希望 HBM 小到不能写入或取出所有想要的东西；也不希望读写能力相对……

**Reiner Pope**

有两种情况。为什么不选择一个大于 15 毫秒的 latency？想想这意味着什么：我实际上有时间把 HBM 读两遍。顺便说一句，大多数 HBM 访问是读，不是写。几乎全是读，因为权重矩阵是只读的，KV cache 访问也几乎全是读。大约 30 毫秒里，我可以把整个 HBM 读两遍，但这么做有什么意义？我不想把权重矩阵读两遍，也不想把 KVs 读两遍。

**Dwarkesh Patel**

非常合理。几个快速问题。如果 optimal batch size 大概是 2000，而且它完全取决于 sparsity，不取决于模型大小或其他东西。

**Reiner Pope**

sparsity 会体现在模型大小中，但除此之外，它只取决于 sparsity，不取决于 scale。

**Dwarkesh Patel**

这是一个很有意思的结果。一个问题是：inference batching 带来的规模经济，会在多大程度上推动中心化？但看起来没那么夸张。2000 个同时用户多吗？听起来不算很多。

**Reiner Pope**

我们可以稍微分析一下。你可以按用户数来想，但更有用的方式是按 tokens per second 来想。这个 batch size 对系统的 tokens per second 意味着什么？

tokens per second 等于 batch size。我们运行一个 batch 的 tokens，每隔一个时间间隔运行一次，这个间隔等于 15 毫秒或 20 毫秒。最后就是 batch size 乘以大约 60，也就是 64 乘以 `B`。大约是 2000 乘以 64，也就是 128,000 tokens per second。这是更容易消化的单位。

并发用户很难推理，但一个系统的全球流量是多少？看一些公告时，API providers 有时会炫耀他们有多少流量。我记得去年 Gemini 的一些公告里，数字是全球每秒数亿 tokens。这只是它的一千分之一。

**Dwarkesh Patel**

Gemini 很大。Gemini 的一千分之一也很多。要真正在规模上有竞争力，至少要能服务 Gemini 的一千分之一。很有意思。

sparsity 越高，需要的 compute 越少。按照这个分析，batch size 越大时，compute 最终会成为瓶颈。那么问题是，sparsity 能推到多高？随着 sparsity ratio 增加，也就是 active parameters 相对 total parameters 变少，模型性能会下降多少？它下降的速度会不会比你通过增加 sparsity factor 省下 compute 的速度更快？

**Reiner Pope**

你是说模型质量，而不是模型速度。不幸的是，我们不能用解析方式回答。那是模型质量的经验问题。我最多能拉出一篇论文，从经验上回答。

**Dwarkesh Patel**

我们现在拉论文吗？

**Reiner Pope**

这篇论文叫做 “[Unified Scaling Laws for Routed Language Models](https://arxiv.org/abs/2202.01169)”。到现在它已经有点老了，但他们看的其中一件事是，如果我持续增加 sparsity，对模型质量有什么影响？这个答案对实际选择的 [mixture of experts](https://huggingface.co/blog/moe) 非常敏感。Mixture of experts 已经存在很久了，也许早在 2017 年就有，但技术变化很大。DeepSeek 的 mixture of experts 对工作方式做了很大改变。更早的论文还有 “[GShard](https://arxiv.org/abs/2006.16668)” 和 “[Switch Transformer](https://arxiv.org/abs/2101.03961)”。实际经验结果会依赖所有这些因素。

（原文此处引用了论文图表 `image1`。）

在这里展示的一种较早技术中，你可以看到，如果我把 active parameters 的数量固定在某个大小，然后增加 sparsity，也就是他们所说的 expert count，质量会持续提升。你可以想象从 1.3B dense 画一条水平线过去，会看到在这个例子里，64-expert、370M activated parameter 的模型和一个 dense 1.3B 模型一样好。

**Dwarkesh Patel**

所以从某种意义上说，回报其实没那么惊人：你需要把 total parameters 增加 100 倍，才相当于 active parameters 增加 10 倍。

**Reiner Pope**

实际上甚至更夸张。为了一个适度的 efficiency 提升，要大幅增加 parameter count。

**Dwarkesh Patel**

所以这个例子里其实是 4 倍？

**Reiner Pope**

64 倍换 4 倍。

**Dwarkesh Patel**

所以，虽然提高 sparsity 确实能节省 compute time，直觉上看这似乎是值得做的 trade-off。但如果每次 sparsity 翻倍，你把这一项降 2 倍，同时另一项涨 8 倍……

**Reiner Pope**

这到底好还是坏？即使从 memory 角度看……记住，你是在翻倍 memory fetch 的这一部分，而它是可以被 batch 摊薄的。所以只要继续运行更大的 batch size。从我们这里做的分析角度看，这是纯收益。基本上一直做下去，直到你没有足够用户为止。

这里有一种等价关系：如果我有很多用户，就可以使用更稀疏的模型。从这个角度看，这是合理 trade-off。另一个出现的 trade-off 是，它也会消耗 memory capacity。我们这里只分析了 memory bandwidth，但它也消耗 memory capacity。

**Dwarkesh Patel**

我明白了。我确认一下理解。你是说，我们想少花时间 compute，所以增加 sparsity。要让它有效，需要更大的 batch size。这意味着我们需要更多 memory capacity 来支持更高 sparsity。

**Reiner Pope**

也许现在正好可以聊聊 mixture of experts layer 通常如何布局在一个 GPU rack 上。

### 00:32:09 - MoE 模型如何布局在 GPU rack 上

**Dwarkesh Patel**

好，合理。我们刚才到哪了？

**Reiner Pope**

Sparse mixture of experts。也许是我们如何把它放在 GPU 上。

先放大 mixture of experts layer，画一下它长什么样。通常会有某种 router layer，它决定把 tokens 路由到哪里。tokens 从这里进来，经过 router layer，然后我们有许多不同的 experts。我再多画几个，让它们排成一排。

router 会决定要路由到哪些 experts，而且只会是其中一小部分，比如 32 个里选 1 个。它可能决定路由到这个、这个，也可能到这个。每个 expert 本身就是一个普通 [MLP](https://en.wikipedia.org/wiki/Multilayer_perceptron)。它有一个 up projection，然后中间有 nonlinearity，再有一个 down projection。

最后，我们做反向操作。前面我们把东西 broadcast 出去，现在要把它们收回来并求和。像这样收回来。最后还有 residual connections。token 也会从这里穿过去，并加到 MoE layer 的结果上。这就是普通的 MoE layer。

我想讲的是它如何映射到一个 GPU rack，以及这对 communication 意味着什么，因为我觉得这会开始显示我们能稀疏到什么程度的限制。这里的标准做法，也是最好的解法，是使用 [expert parallelism](https://nvidia.github.io/TensorRT-LLM/advanced/expert-parallelism.html)。这意味着不同 experts 放在不同 GPU 上。如果我们拿 DeepSeek 这样的模型来说，它们有 256 个 experts。假设我们想在一个 [Blackwell](https://en.wikipedia.org/wiki/Blackwell_\(microarchitecture\)) rack 上跑它。这里有 72 个 GPU。

我们会遇到整除问题。72 不是 2 的幂。我们先简化，假设只用其中 64 个。忽略另外 8 个，不是什么大事。于是每个 GPU 放 4 个 experts。非常简单。为了画图，实际上我们就说每个 GPU 放 2 个 experts。于是我们画出这些 GPU boundaries。每一对 experts 都在自己的 GPU 上。

然后我们可以看 communication cost。我们有一些 centrally stored tokens。它们被路由到所有这些 experts，这里会付出一些 communication cost。在 output 上也会付同样的 communication cost。希望是，这不要变成 communication limited。

这里的 traffic pattern 是什么？它是：任何 GPU 都会和任何其他 GPU 通信，取决于模型做出的路由决策。这是一个 [all-to-all traffic pattern](https://www.dell.com/en-us/blog/understanding-llm-gpus-clusters-fabrics-traffic-for-networkers/)。

**Dwarkesh Patel**

你说 any GPU 的时候，router 不止一个 GPU 吗？

**Reiner Pope**

我画成一个 router。现实中，你实际上会有很多 router 的副本，事实上 router 数量会和 GPU 数量一样多。

**Dwarkesh Patel**

就像 incoming traffic 那样。

**Reiner Pope**

对。这边是 64 个 GPU，这边也是 64 个 GPU。实际上是同一批 GPU，只是我们画成分开的，因为它们服务不同目的。所以在这个点，任何 GPU 都可能发给任何其他 GPU。

这种 all-to-all communication pattern，以及 Blackwell racks 的配置，正好完美匹配 MoE 实际需要的 communication pattern。然而，如果你觉得一个 rack 太慢，想用两个 rack，那么就会遇到挑战：也许我在外面画一个 rack boundary，像这样，于是我不再拥有两个 rack 中所有 GPU 之间的 all-to-all communication。rack-to-rack communication 会成为一个实质性瓶颈。

这里的根本点是，一个 rack 限定了你能做的 expert layer 的大小。这也是推动 interconnect domain 变得越来越大的原因之一。

**Dwarkesh Patel**

继续之前，也许值得解释一下 rack 到底是什么。rack 内和 rack 间 bandwidth 的差异，以及 rack 内外 all-to-all 与非 all-to-all communication 的差异。

**Reiner Pope**

这里开始会在 Nvidia、Google 和其他公司，包括我们之间，变得很不一样。一般来说，rack 是一个物理结构。它有几米高，取决于配置，一两米宽，里面放若干 GPU 或 [XPU](https://semiengineering.com/what-is-an-xpu/)，通常大约 64 个。

限制它大小的是供电、重量和冷却能力。在许多情况下，由于这些物理约束，它最终就是这个尺寸。当我部署一个 data center 时，一个 data center 可能有成千上万个这样的 rack。我有一个高高的 rack，里面有一堆 GPU 等等。然后我在旁边再放另一个 rack。

**Dwarkesh Patel**

你说得好像很容易。

**Reiner Pope**

对，我就把它们放进去。在 Nvidia 的情况下，communication topology 是这样……他们其实把 GPU 放在 rack 外侧，然后把 switches 放在 rack 内侧。结果是这里有一组 switches。这些是 [NV switches](https://www.nvidia.com/en-us/data-center/nvlink/)。然后他们拉很多 cable。每个 GPU 都有 cable 连到中间的 switches。switches 连接所有 GPU。所有 GPU 可以在两跳内和所有其他 GPU 通信：先到 switch，再到另一个 GPU。

现在，如果我要离开 rack，就会走另一条路径。GPU 还有一种慢得多的 connectivity，通常大约慢 8 倍。我刚才在 GPU 情况下用绿色画的是 NVLink。更一般地，它叫 [scale-up network](https://naddod.medium.com/understanding-scale-up-vs-scale-out-in-ai-infrastructure-584723afb94d)。通常你还会有一个 [scale-out network](https://naddod.medium.com/understanding-scale-up-vs-scale-out-in-ai-infrastructure-584723afb94d)，允许你连接到某个 [data center switch](https://www.lanaotek.com/what-is-a-switch-in-a-data-center.html)。所有 GPU 都会有某种连接通向某个 data center switch。这就是 scale-out，它的 bandwidth 往往大约慢 8 倍。

如果你想把一个 mixture of experts layer 布局到两个 rack 上，挑战是这里一半 GPU 会想和这里的 GPU 通信。平均来看，当我看这些 GPU 上的 tokens 想去哪里时，一半 tokens 想留在 rack 内。这很好，它们可以用快速的 scale-up network。但另一半 tokens 会想离开 rack，去另一个 rack，这就没那么好。它们需要用慢得多的网络，于是这会成为 all-to-all pattern 的瓶颈。

另一种选择是，为什么不在这里放一个大 switch，把所有东西接到一个更大的 switch 上，从而把两个 rack 合起来？这个方向有很多想法，但一般来说，你之所以有这种 switch 层级，而不是一个大 switch，是为了管理 cabling congestion。你需要跑大量 cables。

**Dwarkesh Patel**

抱歉，你刚才问的问题基本上就是：为什么不是一个更大的 scale-up？

**Reiner Pope**

没错。为什么不让一百万个芯片在 scale-up 里？或者一千个芯片？

**Dwarkesh Patel**

发生了什么变化，让 Nvidia 能从 [Hopper](https://en.wikipedia.org/wiki/Hopper_\(microarchitecture\)) 的 8 个，到 Blackwell 的 72 个，再到 Rubin 将会是……500 多个吗？

**Reiner Pope**

对，500 多个。

**Dwarkesh Patel**

是什么让这件事发生的？

**Reiner Pope**

从 Hopper 到 Blackwell，主要只是决定把 form factor 从 trays 改成 racks。这是一个产品决策。那里没有重大技术障碍。

从 64 到大约 500，这里面有一点 [Jensen](https://www.dwarkesh.com/p/jensen-huang) math，但至少确实有一个真实的 4 倍提升，来自复杂得多、困难得多的 rack design。那确实是一种新的物理设计，用来跑更多 cables。

**Dwarkesh Patel**

cable 的复杂性只是弄清楚哪根 cable 连到哪里，或者哪个 signal 从哪里到哪里这种成本吗？

**Reiner Pope**

我们放大看看 wire density。我再画一次这个图，这样我们有更干净、更大的版本可以用。

假设中间有一些 switches。一开始，我每边只有两个 GPU 或两组 GPU tray。假设每个 tray 想拉出两根 cable。我实际运行垂直 cables，像这样接到 switches。现在如果我想把 rack 里的 GPU 数翻倍，就需要字面意义上两倍密度的 cables。我还需要跑这些 cable。

**Dwarkesh Patel**

一个非常幼稚的问题。如果你看物理 data center，好像 rack 里面有很多空间。我不知道，cables 真的很大吗？

**Reiner Pope**

rack 外面有空间。rack 里面……随着它们变得更优化，这些 rack 非常紧。tray 进入 rack 和 rack backplane 的 connector density 很高，backplane 本身密度也非常高。还有其他物理约束，包括 cable 的 bend radius。你不想把它们折断之类。

**Dwarkesh Patel**

所以约束它的真的是放 cable 的物理空间。我完全不知道。有意思。这很令人惊讶。rack 这么大，我们竟然不能再塞更多 cable。

**Reiner Pope**

rack design 不是我的专长，但我和相关人士聊他们面临的约束时，它是多种因素组合。你在优化哪些大的物理东西？空间、rack 的重量。它其实非常重，所以你需要足够多金属，防止下垂和倒塌。但你加更多金属，它又更重。然后是供电和冷却。所有这些都在竞争。现代 rack 正在把这些都推到非常极端的物理极限。

**Dwarkesh Patel**

[GPT-4](https://en.wikipedia.org/wiki/GPT-4) 又是什么时候发布的？2022 还是 2023？

**Reiner Pope**

2023。

**Dwarkesh Patel**

好。传闻它超过一万亿参数。看起来只是最近六个月，才有模型发布出来，参数量明显超过三年前发布的这个模型，按理说这中间应该有 scaling 才对。

原因是不是我们一直在等有足够 memory 的 rack，能容纳一个 5T parameter model，再加上足够用户、足够多 sequences 的 KV cache？或者如果你做 [RL](https://en.wikipedia.org/wiki/Reinforcement_learning)，也有类似考虑：要实际容纳你试图解决的那批问题的 KV cache。

如果看 Hopper，你有 8 个 Hopper，我想截至 2022 年大概是 640 GB。到了 Blackwell，终于……它是什么时候部署的？

**Reiner Pope**

很近。也许去年。

**Dwarkesh Patel**

去年。你终于有了 10 到 20 TB 量级的 scale-up，足够放一个 5T model 加 KV cache。

**Reiner Pope**

部署更大的 scale-up domains 是一个巨大 unlock。我这里画的是 Nvidia Blackwell deployment。Google 的 deployment 实际上很久以来就有非常大的 scale-up domains。

**Dwarkesh Patel**

这也解释了为什么 Gemini 看起来领先。Gemini 似乎比一些其他 lab 更早成功完成 pre-training。

**Reiner Pope**

我当时不在那里，所以不确定其中有多少来自成功部署更高 sparsity ratios，这有可能。也可能来自一大堆真实的 modeling things，尤其是你如何做 mixture of experts。我们看到 DeepSeek 的 mixture of experts 激活更多 experts，但 experts 更细粒度。那是一个很大的创新。我相信模型架构和训练数据上也有很多其他创新。

很难把这些因素拆开，但从能做什么的极限来看，active parameters 如我们所见受 compute cost 限制，而 total parameters 受 scale-up size 限制。

### 00:47:12 - pipeline parallelism 如何让模型层跨 rack 移动

**Dwarkesh Patel**

当你在单个 scale-up domain 内运行时，这个考虑是专门针对 forward 或 backward，还是专门针对 [prefill](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/) versus [decode](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/)？还是说不管什么 workload，无论是 pre-training run、RL generation，还是为用户 inference，最好都在一个 scale-up 里？

**Reiner Pope**

很有意思。要回答这个问题，我们需要谈 communication patterns。我们刚才谈过 mixture of experts 的 communication pattern。那是 all-to-all。all-to-all 非常强烈地偏好 full connectivity，也就是我们刚刚展示的东西，并且偏好在一个 rack 内。

除了这里展示的 expert parallelism，还有其他类型的 parallelism。文献里有 [tensor parallelism](https://huggingface.co/docs/text-generation-inference/en/conceptual/tensor_parallelism)。随着 experts 越来越小，它的重要性已经低了很多，所以可以忽略。但还有另外两个可用的东西：[data parallelism](https://en.wikipedia.org/wiki/Data_parallelism) 和 [pipeline parallelism](https://docs.pytorch.org/docs/stable/distributed.pipelining.html)。它们可能更适合使用多个 rack。

我们专门看 pipeline parallelism。这是一个 MoE layer。上面还会有一百多层。我可以在这个点，比如决定移动到另一个 rack，change rack。那么，这会不会成为 communication bottleneck？我们其实可以解出什么时候它会成为 bottleneck。在代数分析之前，先把路径可视化一下。我们会有另一个 MoE layer，这里还有另一个 MoE layer，以此类推。

假设我在这里 change rack，然后若干层后又在这里 change rack。我们用来判断 change rack 的地方是否有 communication bottleneck 的方法，是比较 scale-out bandwidth requirements 和 scale-up bandwidth requirements。我们写下来。提示是，这里有多得多的 sends。这里我们发送很多东西，而这里我们只发送一个东西，也许还会发送很多次。这就是差异。

**Dwarkesh Patel**

我能试着猜一下吗？只是出于好奇，看看我是不是真的理解。看起来你把 batch size 送进 rack。

**Reiner Pope**

这里吗？对。

**Dwarkesh Patel**

但 rack 内的 communication 是 batch size 乘以 GPU 数量。

**Reiner Pope**

乘以 activated GPUs 的数量。我根本不会发给这个 GPU。这个图里这里会膨胀 1 到 3 倍。关键是，我甚至根本不需要发给这个 GPU，所以这是一个很大的节省。

我们要讲 scale-up 相对 scale-out 在多大程度上是 bottleneck。我们直接跳到 scale-up 上花费的时间除以 scale-out 上花费的时间。我们说的就是这个量。

第一个考虑是，scale-up 通常比 scale-out 快 8 倍。在 baseline 上，如果 bandwidth 一样，我们会有这个 1/8，来自 bandwidth。但接着还有一个因素：我们发送的数据量扩张了多少。如果一个 token 进入这里，在 DeepSeek 的例子里，它可能被路由到 32 个 experts 或 16 个 experts。它被路由到某个数量的 experts。所以这是 activated experts 的数量。同样的事情适用于多层，所以也许我要跑两层。还有每个 stage 的 layer 数量倍数。

**Dwarkesh Patel**

你不需要为 all-to-all 把整个东西乘以 2 吗？

**Reiner Pope**

为了 up 和 down。对，有个 factor of two。谢谢。

我们希望 scale-up time 大于 scale-out time，因为 scale-up time 是更重要、更珍贵的资源。我们希望这个数大于等于 1。这个其实看起来并不难。我们只需要克服一个 8 的因子。所以这三个东西的乘积需要大于 8。通常 activated experts 的数量就相当大，可能自己就是 8。然后我们可以把每个 stage 的 layer 数增加很多，直到满足这个条件。

最终看起来就是，我可以有一整个 rack pipeline：一个 rack 做一层，然后移动到下一个 rack 做另一层，再移动到下一个 rack 做下一层。

**Dwarkesh Patel**

让我觉得有意思的是，实践中最好的 parallelism strategy 最后在物理上很像实际架构本身。它不是什么 galaxy brain 的东西。就是：“哦，我们有 experts，就把它们放在不同 GPU 上；我们有不同 layers，就把它们放在不同 racks 上。”我觉得这很有趣。

**Reiner Pope**

切法和模型架构相匹配。

**Dwarkesh Patel**

正是。它本可以是一些更古怪的 tensor parallelism 之类。

**Reiner Pope**

galaxy brain 的思考方式是：模型有哪些不同维度会被 scale up？它按 layers scale up，按 model dimension scale up，按 [DFF](https://en.wikipedia.org/wiki/Feedforward_neural_network) dimension scale up，按 experts 数量 scale up。每一个数字你都可以选择沿着它切。如果这些数字足够大，最终沿那里切就会变得有利可图。我们选择了其中两个。另两个，在模型通常的 sizing 方式下，不划算。

**Dwarkesh Patel**

[Ilya 有一个 talk，他说：“今天我们知道不要做 pipeline parallelism。”](https://youtu.be/1yvBqasHLZs) 然后 [Horace He](https://horace.io/) 给我和朋友们……我讨厌这听起来像 Dr. Seuss 的引用。但他给我们讲过这些不同 parallelism。他说 pipeline parallelism 的问题是，除了 bubbles 之外，它还会制造架构约束。比如 [Kimi](https://en.wikipedia.org/wiki/Kimi_\(chatbot\)) 有这些 [residuals](https://go281.user.srcf.net/blog/research/residual-streams/)，attention 会 attend 到前面几层，所以用这种方式实现会变得困难。

**Reiner Pope**

我觉得我们还没有完整说清楚 pipelining 给我们带来的好处是什么。这些复杂性是真实的。pipelining 非常麻烦，但它确实带来一些好处。然后你可以决定这些好处是否值得付出成本。它在 inference 中有一些好处，在 training 中也许有更大好处。对 inference 来说，我们节省的是什么？节省 memory time 还是 compute time？其实不是。我们只是把 memory time 从一个 chip 移到另一个 chip，或者从一个 rack 移到另一个 rack。runtime 上没有实际收益。

不过，我们节省的是 memory capacity。如果我们认为一个 rack 的 memory 是瓶颈，那么它会限制我们能跑多快。pipelining 允许我们大幅降低这个瓶颈。

**Dwarkesh Patel**

这件事的另一面……访谈前，我和 [Axel](https://feldmann.nyc/) 聊过，他是 [Jane Street](https://en.wikipedia.org/wiki/Jane_Street_Capital) 的 GPU performance engineer。他解释说，要做 pipelining，就必须用 micro-batches，而不是 full batches。如果用 micro-batches，那么按定义你就没法在所有 users 或所有 sequences 上摊薄加载 weights 的成本。它的正面含义是，你不需要用那么多 memory。负面含义是，我们没法在所有这些 users 上摊薄加载 weights。也许值得解释一下为什么必须用 micro-batches。

**Reiner Pope**

我们来画 pipeline bubble 吗？pipeline parallelism 里出现的 micro-batching 是什么？

我先关注 inference。这是稍微简单的问题。我画 time，以及我们在哪个 rack 上。想法是也许我有 4 个 rack。一个 inference 会在某个时间里穿过这 4 个 rack。这个是 inference number zero。它以某个 batch size 运行，并像这样穿过所有 pipeline stages。

现在，如果我们说：“那我们在这里运行 inference number one”，这显然是巨大的浪费。比如每个 rack 四分之三的时间都什么也不做。我们实际上不会在这里运行 inference one，而是一旦可以运行就立刻运行，也就是 inference zero 结束后马上运行。然后继续。如果没有填上这些，我们就会称之为 pipeline bubble。在 inference context 里，我画的是只做 forward pass，这一点很明显。为什么要做这种蠢事？在 training context 里，它也许没那么明显。但在 inference context 里，这个改变非常自然。

**Dwarkesh Patel**

哦，有意思。这有点显然，但 micro-batch 和 batch 的区别在 inference 里完全不重要，因为你想怎么叫都行。它只在 training 中重要，因为那里有 optimal batch size。

**Reiner Pope**

对。

**Dwarkesh Patel**

在做完整 backward step 之前，你想积累整个 batch 里的所有 sequences。如果想在 training 里做 pipelining，为了避免 bubble，你需要……

**Reiner Pope**

要不要画带这个的 training diagram？我们来画。这是 inference diagram，我把它叫 forward，避免误解。现在做 training 的同一个图。我们有一个 forwards pass，但某个阶段必须切换到 backwards pass。

我们在 forwards pass 里做若干 batches，然后要让所有人一次性切换到 backwards pass。inference 部分在这里是一样的，但接着在这个点 hard stop，然后所有人 transition 到 backwards pass，编号也类似。

**Dwarkesh Patel**

也许值得澄清一下，那里有 hard stop 的原因是，你想对 backward step 一次做完整 batch。然后这个 batch 应该多大有一个 optimal size。

**Reiner Pope**

从 [ML convergence rate](https://www.cs.ubc.ca/~schmidtm/Courses/540-W18/L5.pdf) 角度看，其实越小总是越好，因为你从 [gradient descent](https://www.geeksforgeeks.org/machine-learning/gradient-descent-algorithm-and-its-variants/) 得到的是最新鲜的信息。

**Dwarkesh Patel**

但从总 training time 角度呢？

**Reiner Pope**

从总 training time 角度，系统层面更小更差。最优点是两者之间的 trade-off。

所以你选择一个 batch size，对这个 batch size 做一些 forwards，再做一些 backwards。你问为什么那里甚至有 hard stop。pipeline parallelism 因为这里有 idle time，也就是 bubble，文献里有很多技术试图用不同布局避免它。有一些更复杂的方案叫 [zero bubble](https://arxiv.org/abs/2401.10241) 或 [one-forward-one-backward](https://arxiv.org/abs/2406.03488)，会用复杂方式交错 forwards 和 backwards。

**Dwarkesh Patel**

你可以在那个 bubble 里挖比特币。

**Reiner Pope**

对。更有用的是，你可以做 weight gradient step，不过也可以挖比特币。

在 inference 中，pipelining 对你关心的任何东西，比如 batch size 或 latency，效果是中性的。它不会改善，也不会变差。看这个 inference 的 latency，如果它是 pipelined，和它全部在一个 rack 上运行相比……如果都在一个 rack 上，我们只是把所有 boxes 向下滑，仍然排成一列，latency 是一样的。

pipelining 对 latency 既不更好也不更差。它确实意味着每个 rack 使用更少 memory capacity。因为现在不需要整个模型，只需要四分之一模型，然后可以扩展。

**Dwarkesh Patel**

非常合理。所以 inference 期间使用 pipelining 是 no-brainer，但 training 期间会有更难的 trade-off。

**Reiner Pope**

即使在 inference 中，其实它也不是大量使用。它降低 memory capacity requirements，但实际上 capacity 有很大富余。我记得你说 Blackwell 一个 rack 有几十 TB。这比 trillion parameter model 大得多。trillion parameter model 只需要 1 TB，所以已经能放下。pipelining 没有巨大收益，因为它减少的是一个已经相当小的数字。

但这确实说明，理论上也许那里有太多 memory。你可以建不同硬件，配更少 memory。如果你在设计硬件，可以说：“我不需要那么多 memory，因为不需要让 weights 放进一个 rack。我可以让 weights 放进 8 个 rack，所以可以造 HBM per GPU 没那么多的硬件。”

### 01:03:37 - Ilya 为什么说：“现在我们知道，pipelining 并不明智。”

**Dwarkesh Patel**

一个宏观问题：现在大家都在谈 [memory wall](https://ayarlabs.com/glossary/memory-wall/)。[Memory 变得特别贵](https://www.theverge.com/news/839353/pc-ram-shortage-pricing-spike-news)。内存不够。智能手机出货量会下降 30%，因为内存不够。这很震撼，[Dylan](https://www.dwarkesh.com/p/dylan-patel) 说 hyperscalers 今年 50% 的 CapEx 花在 memory 上。

**Reiner Pope**

这可信。

**Dwarkesh Patel**

hyperscaler CapEx 是什么规模？高几千亿，也许一万亿，而他们一半花在 memory 上？这是一个巨大约束。这就是为什么今年我们不会有新 laptop 和 phone。

但同时，我们 memory 又太多了？人们愿意往这些系统里放太多 memory。既然你不需要，为什么 Jensen 要把这么多 memory 塞进这些 racks？

**Reiner Pope**

在我们擦掉之前写的方程里，我们有 memory time、memory bandwidth 和 compute bandwidth。现在开始看 memory capacity。

先看 memory capacity，不考虑任何 parallelism scheme。对 memory 的需求是 total parameters 的数量。这是我们使用的某个系统里需要容纳 weights 的东西。然后还需要容纳 KVs。KVs 按 batch size 乘以 context length 乘以 bytes per token 增长。

我刚才在这个 context 里关于 pipelining 做的论证，是有一些技术允许我们解决这个问题。考虑在某个数量的 GPU 上运行。我们有一个 extent，也就是 `E`，expert parallelism。当我们把一个 expert layer shard 到很多 GPU 上时，shard 的程度是多少？多少 GPU？我们可以说比如 64。然后 `P` 是 pipelining 的 extent。也就是 rack 数，比如我们选 4 之类。

这是整个系统上的 total memory requirement，但现在我要计算 per GPU 的 memory requirement。我用小写 `c_mem`。显然，我们只是把所有这些数字除以 `E` 和 `P`。很简单。就是这个 `N_total` 加上 batch 乘以 context length 乘以 bytes per token，全部除以 `E * P`。

为什么这样除是对的？我们知道参数在一个 rack 的所有 GPU 间被完美切分。layers 在不同 racks 间被完美切分。所以这部分成立。然后不知怎么，我们会安排，我会暂时略过细节，让 contexts 在一个 rack 的 GPU 间也同样完美 sharding，并且基于 layer 在 racks 间切分。

**Dwarkesh Patel**

抱歉，4 是 rack 的数量？

**Reiner Pope**

对，例如。

这里是我们实际需要回头分析 batch size `B` 的地方。你刚才提到 micro-batching versus global batching。我们回到这个 pipelining diagram。

有一个 batch 往前走，然后按我刚才画的，它好像就消失了。这其实不对。如果想想 decode 如何工作，我已经生成了一堆 tokens。做一次 forwards pass，生成一个新 token，然后写入 KV cache。然后再做一次 forwards pass，生成下一个 token。我实际上会让这个 batch zero 在一个 loop 里运行。事实上，它 forward 完成后，就可以在这里启动下一轮 loop。我们把它填上。有 two、three、two、three、two、three。

我们把这个 batch 拆开。这个 batch 是 global batch size。`B` 等于 micro-batches 数量乘以每个 micro-batch 的 batch size。我们需要多少 micro-batches？在这张图里 micro-batches 的数量是 4：zero、one、two、three。micro-batch size 仍然是大约 2000 的那个数。抱歉，不是，它是 300 乘以 sparsity。

**Dwarkesh Patel**

这就是每 20 毫秒出发的那班火车的大小。

**Reiner Pope**

对。这就是 20 毫秒火车。global batch size 是 micro-batches 数量乘以 local batch size。local batch size 由这个硬件参数设定。

micro-batches 的数量应尽可能小，但要足以绕回来而不留下 idle time。如果更少，绕回来时就会有 idle time。你可以从视觉上看到，它等于 pipeline stages 的数量。这里是一个视觉证明。它是 4，这边也是 4。你可以看见它沿着这里走，然后绕回 pipeline stages 的数量。

**Dwarkesh Patel**

抱歉，非常基础的问题。这是实际做法吗？今天的 frontier model 在 inference 期间会有 pipelining？

**Reiner Pope**

在 massive scale training 里肯定这么做。inference 也可以做。我其实要说明为什么它没那么有吸引力。它对 weights 有用，但对 KVs 没那么有用。

大挑战是……我们把它填进去。这里的 micro-batch size 最后等于 pipeline stages 的数量。当我们回去把所有这些代入这里，会看到 pipeline stages 数量乘以这个小写 `b` 出现在这里。当我们把它 factor out，会把这个加法拆成两项。

这一项仍然完整除以 `E * P`。另一项这里也还有除以 `E * P`，但 `P` 会抵消。我们发现，如果增加 pipeline stages 数量，weights 的 memory footprint 会不断下降，但 activations 的 memory footprint 保持不变。所以它实际上不起作用。

你的大部分 memory……一旦做了足够 pipelining，实际上不需要很多，常常两个就足够，这一项会变得很小。KV cache 会成为主导项。

**Dwarkesh Patel**

我知道这不对。我只是想弄清楚我的逻辑哪里错了。如果你通过很多不同 stages 做 pipelining，KV values 在 layers 间不是共享的。为什么跨多个 layers pipelining 不会有帮助？因为那样你就不必存……

**Reiner Pope**

你只需要存一层而不是两层 KVs。从这个角度看，你说得对。与之竞争的是，你需要让所有 racks 在同一时间都有用地忙起来，所以 simultaneously in flight 的 sequences 数量上升了。

**Dwarkesh Patel**

啊，这就合理了。

**Reiner Pope**

它们正好抵消，最后 per GPU 没有节省。

**Dwarkesh Patel**

对。这从根本上回到了你无法跨 KV caches 摊薄的点。

**Reiner Pope**

首先，我们确认你不能跨 batch size 摊薄 KV caches。现在我们说，你也不能跨 pipeline stages shard 它。从这两个角度看都很糟。

**Dwarkesh Patel**

有意思。那么 inference 期间实际会怎么做？

**Reiner Pope**

DeepSeek 论文报告了他们的做法，就是做大量 expert parallelism。实际上，你应该把 expert parallelism 增加到 scale-up domain size，然后做很少 pipelining。也许完全不做，也许做 2 个，刚好让 weight storage 不至于太成问题。

真正有意义的 parallelism 只有这两种。过去有 tensor parallelism，也就是在 expert 内部切分，但现在 experts 太小了，这不是一个划算优化。

**Dwarkesh Patel**

这是否意味着 frontier labs 在做 inference 时，基本都只在单个 scale-up 内？

**Reiner Pope**

是的。你可以看它如何依赖 model size。可能有一个非常大的模型，超过一个 rack 的 memory。那就应该做一点 pipelining。也许它极端稀疏，这也会是一个理由。

**Dwarkesh Patel**

这回到讲座开头的承诺：这实际上也会告诉你 AI progress。就 model size scaling 直到最近一直很慢而言……

我确认一下我理解的 claim。claim 不是说你本可以跨更多 racks 训练。只是说在以前，这么做没意义，因为我们没有能力轻松地为更大的模型做 inference。

**Reiner Pope**

其实，pipelining 对 context length 没帮助。它完全有助于 model size。因为有 pipelining 的能力，至少一个 rack 不应该限制你放下模型参数。

你问的另一个考虑是，为什么还没有 scale up 更多，为什么更大的 scale-up domains 有帮助。我们已经讲过一个方面：它不是因为 memory capacity。我们对 memory capacity 至少有解决方案，针对 model size 是这样，针对 KV cache size 不是，但至少针对 model size 是这样。另一个问题是 latency。

**Dwarkesh Patel**

我正要问，从 rack 到 rack，每一跳的 latency cost 是多少？

**Reiner Pope**

这非常依赖硬件。我不能很权威地说。我觉得大概是几毫秒量级，但这里可能有一个数量级的误差。

**Dwarkesh Patel**

4 是你可能有多少 pipeline stages 的现实数字吗？

**Reiner Pope**

是。

**Dwarkesh Patel**

所以不算太多。

**Reiner Pope**

在少量 pipeline stages 上，这不是巨大的 latency impact。

**Dwarkesh Patel**

但我猜每 token 10 毫秒。

**Reiner Pope**

对。

**Dwarkesh Patel**

大概 2 乘以 4，或者我不知道你刚说多少……每 token 10 毫秒其实很多。

**Reiner Pope**

如果它从 20 变成 30，或者类似……

只是画一下它经过的路径：这里你从 GPU 或 TPU 到 network card，然后到 top-of-rack switch，然后跳到另一个 rack，再反过来走同样路径。你必须把这些不同环节的 latencies 加起来。

**Dwarkesh Patel**

抱歉，这是和 data center switch 同一个东西吗？

**Reiner Pope**

它事实上可能会上到 data center switch 再回来。取决于 deployment configuration。

**Dwarkesh Patel**

明白。因为这是 decode，而且是 sequential，它们会跨 stages 叠加。不能同时做。

**Reiner Pope**

对。

**Dwarkesh Patel**

那么这把我们带回问题：scale-up 的大小，是否和过去几年 AI 模型大小为什么是现在这个样子有关，无论是通过 training 还是 inference？

**Reiner Pope**

我们谈了 hop 的 latency。还有 `t_mem` latency。memory time latency 实际上会被更大的 scale-up domains 大幅改善。我把 `t_mem` 写回来。weights 的 `t_mem` 等于 total parameters 数量除以 memory bandwidth。这里说的是哪个 memory bandwidth？只是一个 GPU 吗？它是我可以并行用来加载这些 weights 的 GPU 数量。我不能并行使用不同 pipeline stages，因为它们不是同时运行的，但我可以并行使用 scale-up domain 里的所有 GPU 来加载 weights。这非常有效。基本上，这里的 memory bandwidth 项本身等于 scale-up size……

**Dwarkesh Patel**

乘以每 GPU 的 memory bandwidth。

**Reiner Pope**

对。乘以 GPU bandwidth。这个项不会增加很多。每代可能增加 1.5 或 2 倍，但这个 scale-up size 从 Hopper 起增加了 8 倍。

**Dwarkesh Patel**

所以更大的 scale-up 重要，不是因为整个 scale-up 的 memory capacity，而是真正因为 memory bandwidth。

**Reiner Pope**

对。pipelining 完全解决 capacity problem，但 scale-up size 有助于解决 bandwidth problem。

**Dwarkesh Patel**

而 bandwidth problem 有助于做更长 context lengths，随着模型越来越 agentic，这越来越相关。

**Reiner Pope**

首先，它让你能以更低 latency 运行模型。如果我只是做一个非常稀疏的模型，而且它在一个小 H100 box 上，latency 会很高。

### 01:18:59 - 由于 RL，模型可能比 Chinchilla-optimal 多训练 100 倍

**Dwarkesh Patel**

一个很跑题的问题。有 [Chinchilla scaling](https://arxiv.org/abs/2203.15556)，它告诉你模型应该多大，相对于你要在多少数据上训练它。但现在显然你不只是试图优化“用训练 compute 得到的最高质量模型”。你想要的是用户通过 training compute 和 inference compute 的混合能得到的最好结果。

所以问题是，你应该把模型 over-train 到什么程度，使得为了达到某个 performance，摊到 training 和 inference 上的 compute 被最小化。现在有了 RL，又有另一个考虑：你会做一定量 pre-training。这个 pre-training 会同时用于 RL generation，然后也用于最终用户的 inference。我这里说 over-training，是指从纯 training compute 角度看，也许更高效的做法是用一个更大模型、训练更短时间，因为它学得更快；但也许你会用一个更小模型，花比原本更多的 compute 去训练它，因为这样给用户服务更便宜。

让我把问题问得更具体。基本上，模型比 Chinchilla optimal 多训练了多少？这是否因为 RL generation 而改变？

**Reiner Pope**

这里我们必须做一些猜测，因为更新后的 scaling laws 和 model traffic 没有公开，所以只能猜。一种看法是……

先说一个一般性的 heuristic claim。如果我有某些 cost，总成本是 cost `A` 和 cost `B` 的和，也许一个是 training cost，一个是 inference cost，而我想最小化这个和……

对很多曲线来说，最小值往往出现在 costs 被 equalize 的地方。这是某种 heuristic claim，但有很多例子是真的。比如一个是 `1/x`，另一个是 `x`，它们往往在彼此相等的点最小化。`e^x` 和 `e^-x` 以及很多其他东西也类似。基本上，我有一条下降的曲线，另一条上升的曲线，它们往往在这个相等点最小化。

我会启发式地猜测，你描述的 setup 也是这样。真正证明这是真的，需要看 scaling laws，并拟合这些奇怪指数，但遵循 power laws 的东西往往有这个性质。所以我先提出这个 claim，然后继续。

我们会说，想让 training cost 和 inference cost equalize。可以全部一般化。pre-training 的 cost 是 active params 数量乘以 pre-training data。外面有一个 factor of 6，也就是 FLOPs 数量。有著名的 [6ND formula](https://www.adamcasson.com/posts/transformer-flops)。然后在 RL 里，大致也是同样的东西。active parameters 数量相同，但现在 data amount 是 RL data。这里有一个额外 efficiency multiplier，或者 inefficiency……

**Dwarkesh Patel**

也就是你不会在所有 rollouts 上训练这个事实。

**Reiner Pope**

有这一点，还有另一个，也许更大的 inefficiency：它涉及大量 decode。decode 的 MFU 通常低于 training。

**Dwarkesh Patel**

好。所以如果你对 RL 中每一次 generation 都做 backward pass，那就是 6ND。

**Reiner Pope**

所以这可能是一个更小的数，对吧？

**Dwarkesh Patel**

至少是 2，因为那是下界……

**Reiner Pope**

在 2 到 6 的范围内。我们就说在 2 到 6 的范围内，并停在这里。然后可以加入 inference cost。inference cost 是 2 乘以 active parameters 数量，再乘以 inference data。

**Dwarkesh Patel**

抱歉，我刚才说得特别混乱。给听众解释一下，forward plus backwards per parameter 是 6。forward alone 是 2。这就是为什么 RL 中，你肯定会生成所有 trajectories，但可能会或不会训练所有 trajectories，所以是 2 到 6。

**Reiner Pope**

对，谢谢。然后 inference 就只是 2。我们要解的是这三项大致相等。那就是人们会处在的大致区域。各个 labs 对多做 RL versus 多做 pre-training 哪个更有用，有更多信息。我没有这些信息，但我认为一个不错的 ballpark 是三者各占 33%。

**Dwarkesh Patel**

我不确定我理解这个直觉。另一个 naive model 可能是 RL 加 pre-training 占 50%，inference 占 50%。

**Reiner Pope**

那也是一个有效答案。因为这是 heuristic，我无法真的证明哪个更对。它们差得不多。33 和 25 只差一个小 factor。

我们选其中一个。全都相等足够简单，所以解它们相等。非常直接。我们马上可以看到 activated parameters 数量完全消失，所以把它 factor out。我们就说 pre-training data，我决定按你的方式做，这样稍微好一点，加上……哦，我这里也没有 inefficiency。pre-training data 加上某个 `alpha` 倍的 RL data，最后会等于某个 `beta` 倍的 inference data。

粗略估一下 `alpha`。这个 `alpha` 大概在 2 到 6 除以 6 的范围内，也就是把这一项和这一项比较。然后还有一个 inefficiency 项，我会说也许在 30% 的范围。所以这个 alpha 大概是 1/10。这里的 `beta` 其实也一样。它是三分之一乘以 30%。所以也等于 1/10。

**Dwarkesh Patel**

如果两个都是十分之一，这有点暗示 RL 上从来没有 backward pass？

**Reiner Pope**

对。好吧，我们可以把这个设成 2/10。让它大一点。再写一次，这个是 2/10，这个是 1/10。

你有多少 inference tokens，只是每秒几亿 tokens 乘以模型部署两个月、下一版本发布前的时间的函数。这应该决定 RL 和 pre-training 的 token 数量。

我想我们还没做 pre-training 和 RL 的等价，所以在这里做。pre-training data 应该等于 2/10 RL data，才让它们 cost equivalent。抱歉，1/10。我弄反了。如果 inefficiency 更高，我们为每个 token 付出更多 cost，所以为了等时间，这里需要是 1/10。追溯回来……这个东西按这里写出来，其实像 1.5，而这个是 1。

**Dwarkesh Patel**

数十亿美元的 compute 刚刚流向另一个方向了。

**Reiner Pope**

对吧？我觉得如果你用 spreadsheet 实际建模，也许会注意到钱正在流进下水道。按这里的模型，这些最后都很接近。这个 30% 可能有点太慷慨。所以我们就说这里是 1.5，然后这里保持 1。

我觉得到这里，你几乎可以直接读出来：inference tokens 数量应该和 pre-training tokens 数量差不多，也应该和 RL tokens 数量差不多，差异在我们无法推理的 factors 内。

**Dwarkesh Patel**

抱歉我犯了一个基础代数错误。看起来 RL tokens 应该比 pre-training tokens 更少？

**Reiner Pope**

一般来说对。因为 RL 在机器时间上效率更低，如果你想让 RL 和 pre-training time equalize，那么你应该用更少 tokens，才能有相同 wall time。

**Dwarkesh Patel**

这都很有意思。我从没想过可以从 equalizing data 的角度看。

**Reiner Pope**

我觉得从 equalizing cost 开始是对的，但取决于你如何建模 cost，它会接近 equalizing data。

**Dwarkesh Patel**

所以为了让 GPT 被 optimal 地训练，每一个使用 GPT-5 的用户，他们 stream 的 total tokens 应该等于 pre-training 中输入的 total tokens。pre-training 的 total tokens 是所有人类知识的总和。每个模型应该在它得到的 input/output 上生成总量等于人类知识总和的 tokens。

**Reiner Pope**

对。人们会在哪边犯错？如果你认为人的预测能力并不完美，而且还冒着一个风险：你做出一个不是 frontier model 的模型，然后直接扔掉，那么这会改变 cost trade-off，因为 inference 那边要乘以某个概率。你应该把 inference tokens 按某个量打折。

**Dwarkesh Patel**

对。我们能不能反推出，对于给定大小的模型，它比 Chinchilla optimal 多了多少 compute？

**Reiner Pope**

我觉得要做这个，我们必须做一些 real-world assumptions。

inference tokens，我们应该完全能数，对吧？假设每秒几亿。也许现在是每秒 5 亿 tokens，我真的不知道。5 亿 tokens 每秒乘以……一个模型在过时前部署两个月？

这个我心算不了。你能输入电脑算一下吗？

**Dwarkesh Patel**

2.6 乘以 10^15。

**Reiner Pope**

好，2.6 乘以 10^15。这个数可能太大，因为这会是一个 model family 里的多个模型。我们把它缩小 5 倍或 10 倍之类。所以我们估算每个具体模型也许是每秒 5000 万 tokens。模型 live 两个月。算出来大约是 200T tokens。然后我们想把它和 frontier model 的 active parameters 比较。我实际上不知道最新传闻。你知道吗？

**Dwarkesh Patel**

有人告诉我 150T。

**Reiner Pope**

active parameters？

**Dwarkesh Patel**

抱歉，我是说 tokens。

**Reiner Pope**

在 150T tokens 上训练。有意思。

**Dwarkesh Patel**

这差不多。

**Reiner Pope**

确实差不多。所以 pre-training data。

**Dwarkesh Patel**

这个引用不严谨，但没关系。

**Reiner Pope**

我觉得 active parameters 的数量通常可能在 100B 左右，诸如此类。也许更大一点。所以乘以 20 得到 Chinchilla token count。因此 Chinchilla 的 `D_Chinchilla` 大概是 2T。我们看到实际大约比它大 100 倍。

**Dwarkesh Patel**

`D_Chinchilla` 实际上是什么意思？

**Reiner Pope**

我猜是 Chinchilla scaling law 推荐的 pre-training token count。

**Dwarkesh Patel**

哦，我明白了。所以 over-trained 多少。懂了。

**Reiner Pope**

这个 200T 或 100T parameters，抱歉 tokens，相对于 Chinchilla optimal 的 2T 的 ratio，就是它 over-trained 的程度。也就是 over-trained 100 倍。

**Dwarkesh Patel**

100。所以如果考虑这里，只要这个 ballpark 大体对，只是想想你希望所有东西在 compute 上相等……如果 OpenAI 也意识到了这一点，而且他们服务某个 tokens per second，这就告诉你 GPT-5 的 pre-training 用了多少 data。即使错 50% 之类，也很疯狂：你能从 first principles 推出这些数字。

**Reiner Pope**

这就是为什么你应该到处做 approximation，因为这里有很大的 error bars。但只是把 `A` 设为 `B` 然后算出来，感觉很 empowering。

### 01:33:02 - 从 API 定价推断长上下文内存成本

**Dwarkesh Patel**

这太酷了。好，按这种试图推断东西的精神，我们可以公开查这些模型的 API prices，也许能从中学到一些东西。

首先，longer context 方面，[Gemini 3.1](https://ai.google.dev/gemini-api/docs/pricing) 如果超过 200k tokens，会比低于 200k tokens 贵 50%。高层看，我理解为什么可能这样，但为什么具体是 50%？

**Reiner Pope**

为什么具体是 50%？高层上，首先是 context length 增加会带来某种 cost increase。我们可以把它重新写出来。那是 memory time versus compute time。

我们把之前的同样方程放上来：memory fetch 的时间，也就是 weights 和 KV cache；以及 compute 的时间，也就是 weights 的矩阵乘。我也会画 cost curve，但这次把它画成 context length 的函数，而不是 batch size 的函数。所以这是 cost curve as a function of context length。我们画 compute。compute 的 cost 实际上对 context length 是常数。这里没有 context length dependence。现实里有一些 dependence，但非常轻微，所以忽略。这就是 compute time。

然后也画 memory fetch 对 context length 的依赖。它从 weights 的一个大数字开始，然后随着 context length 缓慢增长。也许从这里开始，然后随 context length 增长。于是取 maximum，你会看到这里有一个 inflection point。

这可能就是 Gemini 支付的 cost。然后想一想，你会如何在上面放 pricing structure？你想确保无论 context length 是多少，仍然有利润。所以有一个 two-tier pricing structure。也许到某个程度之前是这样。

我觉得，因为 bump 在 200k，这说明它可能和这个 crossover point 某种程度对齐。也许不完全对齐。我们其实大概可以把这个计算做完，看看落到哪里。

如果对 active parameters 数量做一些假设，我们可以解出每 token bytes 数。解 bytes per token 时，我们假设 memory time 和 compute time equalize 的点在，比如 200k tokens。所以让这两个相等。

还假设 batch size 足够大，以至于花在 weights 上的 memory time 可以忽略。因此忘掉这一项，关注真正花在 KV cache 上的 memory time。把这一项搬过来，就是 batch 乘以 context length 乘以 bytes per token，再除以 memory bandwidth，等于 activated params 数量除以 FLOPs。然后解 bytes per token。batch size 这里漏了。它在这里出现，到这里会抵消。我还漏掉了 context length。

所以可以代入数字。这是我们之前看到那个数字的倒数。也就是 1/300，它在许多不同硬件平台上相当稳定。我们猜测 activated parameters 数也许是 100B。context length 说的是 200k。不过这里有点错。context length 应该在分母，不是在分子。

**Dwarkesh Patel**

1667。差不多 2 KB。

**Reiner Pope**

这其实是 plausible 的。你说大约 2 KB。我们做个 sanity check，看它可能是什么。人们用少量 bytes per token 做 attention 有两种机制。一种是 dense attention，但跨 layers 有大量 reuse。[Character AI](https://en.wikipedia.org/wiki/Character.ai) 有一篇 [blog post 谈这个，交替 long 和 short context](https://blog.character.ai/optimizing-ai-inference-at-character-ai-2/)。在 Character AI 这种模型里，也出现在 [Gemma](https://en.wikipedia.org/wiki/Gemma_\(language_model\)) 模型里，global context，也就是我们这里真正讨论的东西，是跨所有 layers 共享的。

要得到 KB 级别，比如可以来自 `d_head` 为 128，这是典型值。然后 bytes 数通常是 attention layers 数乘以 2，乘以 `d_head`，再乘以 KV heads 数。这是每 layer unique contexts 的数量。

你是跨许多 layers 共享 context，还是只使用一次？在 Character AI 类似模型里，这个数是 1。我们说这是 128。这是一个通常从 1 到……抱歉，这是 KV heads，我是这个意思。

**Dwarkesh Patel**

head 和 KV head 的区别是……？

**Reiner Pope**

KV heads 是存储在 memory 里的 heads，存储之前 tokens 的内容。Q heads 是 retrieval heads。它们只临时使用，并由正在 attend 的 token 使用。在这个 autoregressive context 里，我有和所有 contexts 关联的 KV heads，然后有和这个新 token 关联的 Q heads。

**Dwarkesh Patel**

但这个 head，128。

**Reiner Pope**

哦，抱歉。这个 `d_head` 是 vector 的 dimension。KV heads 数通常在 1 到 8 之间。比如有 8 个 KV heads 和 `d_head` 为 128，就完全可能得到这个数。或者也可以有更少 KV heads，但更多 layers。

这是通过 dense attention 得到这个量级的一种方式。还有一种通过 sparse attention 的方式：你增加所有这些数字，但再乘一个 `1/sparsity` 项。我觉得这个数字是 plausible 的，也许稍微有点小。

**Dwarkesh Patel**

有趣的是，他们会通过 API pricing 泄露这么多信息。

**Reiner Pope**

我是说，你有动机把价格设得接近成本，否则别人会抢走你的市场。

**Dwarkesh Patel**

也许我们可以从 input 和 output prices 的差异里学点东西，它能告诉我们这些模型中 decode 和 prefill 的差别。我记得上次看是 output 贵 50% 还是类似？

**Reiner Pope**

我不记得了。我过去看到的是贵 3 到 5 倍。

**Dwarkesh Patel**

好，那更合理。假设贵 5 倍。这是 decode 中处理下一个 token 的 compute。假设你在做 prefill，不只是处理最近一个 token，而是并行处理所有 tokens。我想说它会是这个乘以 prefill length？

**Reiner Pope**

或者一般来说 pass length。如果我们把 decode 看成 length 为 1 的 pass，把 prefill 看成 length 很大的 pass。

**Dwarkesh Patel**

好。也许叫 prefix？好，memory。你不会为 prefill tokens 存 KV cache。

**Reiner Pope**

让我实际画一下 prefill 如何出现，也许可以澄清。我们做一点 decode，像这样。然后可能实际上回头做更多 prefill。如果你把这想成一个 chat session，用户说了一些话，AI 生成回应，然后用户又说了一些话，我们会 prefill 这段。也许这是 general case，而不是这个。

**Dwarkesh Patel**

事实上，这就像你 read a file 之类。

**Reiner Pope**

read a file，或者 AI 正在响应用户 input、tool call，或任何不是 AI-generated 的东西。

**Dwarkesh Patel**

好，假设我们在这里。你之前已经计算了所有这些。所以只是之前所有东西的 KV。但这段的 memory cost 是什么？我是说 memory bandwidth cost。如果你在做 [flash attention](https://modal.com/blog/flash-attention-article)，它会……

**Reiner Pope**

基本上是 temporary。它甚至不会进 main memory。忽略它。

**Dwarkesh Patel**

正是。所以那就只是之前所有东西。不是就这样吗？

**Reiner Pope**

memory time 实际上完全不用调整。

**Dwarkesh Patel**

好。很好。所以 accommodate 这个变化非常 trivial。这一项让它贵 5 倍。那么为什么？这实际上告诉我们什么？这个变量能帮我们 clamp 什么？唯一可能改变的是，compute 因此贵了 5 倍。

**Reiner Pope**

这是 one pass 的时间，但实际 token 数量大了那么多。我们事实上想看 per token cost，或者 per token time。

**Dwarkesh Patel**

我不确定我理解了。这是 processing the next token in prefix 吗？

**Reiner Pope**

其实是 processing the entire batch。以这个 cost，我们处理了这么多 tokens，也就是 prefill length。或者 pass length。不是这个 prefix，而是这个 cost。

**Dwarkesh Patel**

好。我们就做这个 pass。所以这是贵 5 倍。input 贵 5 倍。

**Reiner Pope**

事实上 output 更贵。

**Dwarkesh Patel**

output 贵 5 倍。

**Reiner Pope**

我们想得到的结果是：prefill 是 compute-limited，而 decode 是 memory bandwidth-limited。

**Dwarkesh Patel**

我们这样做吧。我们把 len-pass 画在 X 轴，把 `t` 画在 Y 轴。

**Reiner Pope**

我们想看 per token cost，所以应该是 `t` 除以 pass length。这样才对。

**Dwarkesh Patel**

我想我被这里搞糊涂了。Len-pass 是……看起来 prefill 时它应该更高。

**Reiner Pope**

prefill 有更大的 pass length。对。

**Dwarkesh Patel**

但为什么它更便宜？

**Reiner Pope**

为什么 cost 更高？因为要除以 pass length。这会除掉这一项，而这些 memory costs 都会除以 pass length，使 memory costs 变便宜。

**Dwarkesh Patel**

好，让我想一下。基本上我们会有四条不同线。先做 prefill……其实先做 decode。

**Reiner Pope**

pass length 等于 1 时，就是 decode。更大时，就是 prefill。

**Dwarkesh Patel**

哦，好，我明白了。回到这个。所以 `t_compute`，如果基本上只是这一项除以 len-pass，就是这个量。它实际上不会随 `t` 变化，所以就是某个平坦值，像这样。这是 `t_compute`。这是……

**Reiner Pope**

那是 decode。

**Dwarkesh Patel**

decode。对。现在 `t_mem`，我们把整个东西除以 len-pass。上面是什么其实不重要，它会看起来像这样。假设这是 `t_mem`。这还是 decode。

所以随着 prefix 或 pass 的长度增加，你的 memory bandwidth time 下降。这意味着，只要你原来 bottlenecked on memory bandwidth，就可以避免这个 bottleneck。

他们对 prefill 收费比 decode 低 5 倍，确实表明他们在很大程度上 bottlenecked on memory bandwidth，以至于对他们来说，至少因为 `t` 等同于 cost，也就是租 compute 的成本，这里会是 1，这里会是 5。

**Reiner Pope**

对。

**Dwarkesh Patel**

所以它事实上极其 memory bandwidth bottlenecked。真实图大概像这样。

**Reiner Pope**

它还是会交叉，但对。

**Dwarkesh Patel**

正是。我这样画。这是 decode 上 memory 和 compute time 之间的 gap。好，有意思。

另一个有意思的问题是为什么 cache hits 便宜这么多。如果我没记错，cache hits 大概便宜 10 倍……根据所有这些模型的定价，写入 cache 更贵。但如果 hit cache，就是 10 倍。想必这是把某个东西保留在 HBM 而不是把它清空的成本。但如果你确实把它保留在 HBM，那再次加载就更便宜？

**Reiner Pope**

对。你可以用两种方式为一个 token 产生 KV cache。你可以直接从 underlying token IDs 从零开始 compute 出来，而 token IDs 本身很小。或者你之前已经产生过它，并把它存到某个 memory 里。

cost ratio 其实讲的是这两种产生它的机制之间的 ratio。cache miss 意味着你已经把它从所有 memories 里删掉了，必须直接从 tokens 重新 compute。你甚至可以再进一步想，你把它存在哪一层 memory tier。可以存在 HBM。还有比 HBM 更慢、更便宜的 memory，比如 host 上的 [DDR](https://en.wikipedia.org/wiki/DDR_SDRAM)，也有 [flash](https://en.wikipedia.org/wiki/Flash_memory)。你可以做的事情之一，是计算在每个 memory tier 里待着何时有意义，这和你要存多久相关。

我们想看在几个不同 memory tiers 中的 storage cost，以及 rematerialization cost。Remat 指的是你删除后，从零重新构建所有 KV cache 的成本，也就是 rematerialize。基本上，这会 cost context length。实际上，我们看 per token cost，所以不需要到处带着 context length。

为了 rematerialize 一个 token 的 KV cache，我只需要对整个模型跑一次 forward pass。这就是 compute time。我必须按 GPU 的速度重新运行 compute，然后乘以 GPU dollars per second。

**Dwarkesh Patel**

抱歉，一个幼稚问题。为什么没有 quadratic term？

**Reiner Pope**

有 quadratic term。它体现在 compute 里。作为近似，我选择去掉它。我快速展示一下它长什么样。如果看 per token cost，或者 per token FLOPs 数，有一部分 FLOPs 来自做 weight matrix multiplies，作为……

**Dwarkesh Patel**

这是 flat。

**Reiner Pope**

……context length 的函数。然后还有一部分 multiplies 来自做 KV cache，它会随着你 attend 的东西数量线性上升。这条线的 slope 很低，所以像这样画时，非常接近一条 flat line。你在上到几百万 tokens 左右时才会开始注意 quadratic 或 linear 项的影响。所以它不是特别相关。

**Dwarkesh Patel**

如果这是真的，为什么没有哪家公司有超过一百万 token context length？

**Reiner Pope**

long context 有两种成本。一种是 memory bandwidth cost，我们花了很多时间分析。就是这个东西。另一种是 compute cost。compute cost 几乎总是被基本原则迫使成为比 memory bandwidth cost 小得多的 slope。限制你做到特别大 contexts 的主要东西是 memory bandwidth 和 memory capacity，也就是这个效应。

**Dwarkesh Patel**

[Dario 在播客里说过](https://www.dwarkesh.com/p/dario-amodei-2)，其他人也说过一个想法：“AGI 不需要 [continual learning](https://www.ibm.com/think/topics/continual-learning)，[in-context learning](https://www.lakera.ai/blog/what-is-in-context-learning) 就够了。”如果你相信这个，那么你必须认为我们需要达到一亿 token context length，才能有一个相当于和你一起工作一个月的员工。现在，也许有 sparse attention 或其他东西后，这不再是真的。但如果你这样想，那么某个 ML infra 东西必须改变，允许一亿 token，比如 memory bandwidth 要允许一亿 token context lengths。

**Reiner Pope**

sparse attention 肯定给你一条出路，因为你得到平方根。它带来很大改善。但如果看模型 context lengths 的历史，从 GPT-3 这样的早期模型，到 GPT-4，我不记得具体什么时候转变，它们从大约 8K 一下升到 100-200K。然后过去一两年，它们基本都徘徊在那里。我觉得这说明这里是相当 balanced 的 cost point，大幅超过这个点会 cost-prohibitive。

**Dwarkesh Patel**

不是因为 compute cost，而是因为 memory bandwidth……

**Reiner Pope**

因为 memory bandwidth cost，对。我其实看不到很好的解决路径。HBM 就是这样，不会有巨大改善。

**Dwarkesh Patel**

为什么 sparse attention 没解决它？

**Reiner Pope**

sparse attention 是很大改善。也许它已经被 price in 了。它不是无限改善，因为如果太 sparse，就会损失太多质量。

经验结果是 context lengths 没有继续大幅增加。我觉得原因是这里没有 memory wall 的解法。太 sparse 只是意味着你 attend 到 tokens 的一个很小子集，质量会变差。

**Dwarkesh Patel**

合理。

**Reiner Pope**

这些重新合成 KV cache 的不同方式，成本是什么？从零 compute 基于我的 GPU time。我必须做一定数量的 multiplies，花费 GPU time 来产生它。

存到 HBM。它其实按 bytes per token 走。我只需要每 token 某个 bytes 数，然后把它存进 HBM。它会占用一些 HBM capacity。一个思考方式是，如果太多这些东西坐在我的 HBM 里，如果我用没在使用的 KV caches 填满 HBM，我就不能用那个 GPU。

怎么定价？也许我说它的成本和我使用的 HBM fraction 成正比。还要乘以 GPU dollars。我们再加一个 memory tier，假设存到 DDR。flash 和 DDR 也有同类东西。

我把这些放错列了。本来想做两列。我想区分的是 retrieve 的成本，以及 hold on 的成本。一个是 per second 的成本，另一个是 instantaneous cost。Rematerialization 有 retrieve cost，store cost 是 0，因为我们删掉了它。这是我放错位置的一项。这其实是 hold on 的成本，所以我重写一下。

如果只是存到 HBM，它有这种 cost profile。如果存到 DDR，实际上会花一些时间。这里得到同样东西：bytes per token 除以 DDR capacity，乘以 DDR cost per second。但现在它还有一个 retrieve cost，比 HBM 更高，因为需要把它 copy 进 HBM。所以这是 bytes per token 除以 DDR bandwidth。然后它也会消耗一些 DDR。

**Dwarkesh Patel**

每个 scale-up 都有 DDR 和 flash 吗？

**Reiner Pope**

这真的是 deployment question，所以你可以选择。Nvidia 确实以这种形式部署，它两者都有。

**Dwarkesh Patel**

为什么 retrieve HBM 的成本不是 bytes 除以 memory bandwidth？

**Reiner Pope**

取决于你如何定义 retrieve。这里我把 retrieve 定义为：把它移入 HBM，这样你就可以开始实际对它做 inference。

**Dwarkesh Patel**

因为如果它已经在 HBM 里，你可以在从 HBM 到 SRAM 拿它的同时做 compute？有意思。

**Reiner Pope**

对，比如这样。这是三种东西，我猜我排序错了。一般来说，如果你在平衡两个 costs，而且 memory hierarchy 里有不同 tiers，你应该预期随着这个 cost 上升，另一个 cost 下降。你可以看见 zeros 在哪里。我应该把它们排成这个第一、这个第二、这个第三。

如果你只会 hold 很短时间，那么所有这些都要乘以 hold time。这个是，这个也是。

**Dwarkesh Patel**

有意思的是，它们写入价格也不同。你在 API 里指定 5 分钟还是 1 小时？这暗示 5 分钟是 HBM，1 小时是 DDR。

**Reiner Pope**

我觉得这是相当不错的假设。如果看数字，也可能结果是往下一层，是 DDR versus flash。

**Dwarkesh Patel**

有意思。我查一下价格差异。base input tokens 是每百万 tokens 5 美元。

**Reiner Pope**

base，也就是 remat。这个是 5 美元。

**Dwarkesh Patel**

那是 5 美元用于“retrieve”。然后写入，想必是 HBM，5 分钟是 6.25。

**Reiner Pope**

我们也许可以通过 durations 判断它是哪一层 memory tier。

**Dwarkesh Patel**

5 分钟 versus 1 小时。

**Reiner Pope**

正是。我觉得这可能最终会是你所在 memory tier 的 drain time。意思是，既然我知道要 hold 某个东西 5 分钟，我希望选择一个每 5 分钟可以读一遍的 memory。我可以每 5 分钟读完整个 memory 一次，大致如此。这就是 memory 的 drain time。所以如果我拿 storage capacity 除以 storage bandwidth，希望它等于 5 分钟。

我们对 HBM 做过这个计算。对 HBM，我们知道这个数字是 20 毫秒。所以 HBM 太小了。DDR 可能和这个差一两个数量级，所以可能在 seconds 量级，比如 1 到 10 秒。我没有背这些数字，但一般来说，越往慢 tier 走，flash 可能是一分钟量级。然后 spinning disk 是完全不同的东西，大概是一小时量级。所以这可能真的识别出 flash 和 [spinning disk](https://en.wikipedia.org/wiki/Disk_storage) 这两个 tier。

**Dwarkesh Patel**

抱歉，为什么是这个计算？storage capacity 除以 bandwidth？

**Reiner Pope**

你有一堆不同 memory tiers，我们列了四个。选择哪个 memory tier，是关于最小化 cost。你用了设备的多少 fraction？你用设备的一部分来 hold 它，然后用设备的一部分来 retrieve 它。假设我用了设备的 10%。我想 equalize 这两个 fractions。这是一个信号，说明我选到了正确的东西。

假设这里有一个 runtime。我会 hold 这么长时间，所以这是 time-hold。然后这里会有某个时间，也就是 time-retrieve。基本上，要 equalize 这两个 costs，我希望 retrieval time 等于 hold time 乘以 capacity fraction。因为这是 retrieval time，这是我可以同时 hold 多少其他东西。

**Dwarkesh Patel**

基本上，你想把东西存在那里足够久，以至于它待在那里的时间，等于把所有东西装进去和拿出来的时间。

**Reiner Pope**

基本上是这样。我觉得这大概说明这两个 tiers 是 flash 和 spinning disk。我有点震惊竟然会用 spinning disk，因为它是如此古老的技术。

**Dwarkesh Patel**

有意思。它慢到要花一小时才能把完整 capacity 读进来，也很疯狂。

**Reiner Pope**

这是一种非常没有吸引力的技术，但在某些地方有用。

### 02:04:02 - 神经网络与密码学之间的趋同演化

**Dwarkesh Patel**

我们坐下来，是因为我想问你一些不需要黑板的问题。你有一篇[极其有意思的博客文章](https://reiner.org/neural-net-ciphers)，谈到从高层看，不同 cryptographic protocols 的架构看起来很像 neural networks。这里有一种 convergent evolution：两者都需要在所有输入之间混合信息。对 cryptographic protocols 来说，是为了确保进入 [hash function](https://en.wikipedia.org/wiki/Hash_function) 的每个新 input 都会完全扰乱结果。对 neural networks 来说，当然是它们需要考虑这一条信息如何改变你对另一条信息的理解。

我觉得这是一个非常有意思的点。从高层看，在某种意义上它们试图做相反的事情。cryptographic protocols 试图把有结构的信息变成看起来和 randomness 不可区分。neural networks 试图把看起来随机的东西，比如 protein sequences、DNA、garbled text，提取出更高层结构。它们有相似的高层机制，但实际上是在做相反的事情。我想知道你怎么看。

**Reiner Pope**

我也会寻找 mixing 和 scrambling 出现的其他例子。几乎有一个物理例子：你在做蛋糕，想搅拌面糊。字面上说，先这样搅，再那样搅，其实不是一个很差的方法。

除此之外，回到 digital world，它们有一些差异，而你指出的是一个很强的差异。它的表现方式是，如果你随机初始化一个 neural network，也许它也是一个合理的 cipher，因为 random initialization 会用复杂方式打乱东西。它甚至可能做到你想要的事。谁知道？

让它变得可解释的是 gradient descent。你可以 differentiate 一个 neural network，并得到有意义的 derivative。我们做了很多工作，避免 derivative 过度复杂，所以 residual connection 会把它控制在简单范围内。我们做的 [LayerNorm](https://docs.pytorch.org/docs/stable/generated/torch.nn.LayerNorm.html) 也有这个作用。

攻击 cryptographic ciphers 的最大方式之一，也是 differentiate 这个 cipher。ciphers 运行在不同的 number field 里。它们运行在 two elements 的 field，也就是 binary，而 neural nets 理论上运行在 real numbers 的 field。你必须对 binary numbers 求导，但你绝对可以 differentiate 一个 cipher。这叫 [differential cryptanalysis](https://en.wikipedia.org/wiki/Differential_cryptanalysis)。

基本上，它说的是，如果你对 input 做一个很小的 difference，很难让 output 的 difference 也很小。设计良好的 cipher 的整个工作，就是让 output difference 非常大。区别在于，那时 optimization goals 是让它复杂化。它们没有同样的 residual connections，比如 LayerNorms。

**Dwarkesh Patel**

我想两者汇合的一个地方是 backdoors。在 [LLM](https://en.wikipedia.org/wiki/Large_language_model) 里的 backdoor，你试图隐藏……你会把它看作 input 吗？它不是进入 forward pass 的 input，但它是进入 backward pass 的 input。你试图隐藏一个进入 backward pass 的 input。

**Reiner Pope**

这是 adversarial context 吗？这里实际上正好有 ciphers 也有的 [avalanche property](https://en.wikipedia.org/wiki/Avalanche_effect)。对 image classification models 的 adversarial attacks，是寻找 image 的一个非常小 perturbation，使 classification 完全改变，output 完全改变。这在 ciphers 里是常态，而在 neural nets 里是不希望出现的情况。

**Dwarkesh Patel**

好，所以我问你，neural networks 是否真的被用于 cryptography？然后我们意识到也许最好还是在黑板上讲。它们真的在 cryptography 里使用吗？

**Reiner Pope**

用 neural nets 做 cryptography……一般来说，创造一种新的 cipher 是非常危险的主张。几乎所有新 cipher 都会被破。99% 都会被破，所以这大概不是一个好的起点。但另一个方向，至少在一个非常明确的案例里，非常有成效。

ciphers 里有一种 construction，后来被引入 neural nets，叫 [Feistel cipher](https://en.wikipedia.org/wiki/Feistel_cipher#:~:text=In%20cryptography%2C%20a%20Feistel%20cipher,known%20as%20a%20Feistel%20network.)，或 Feistel network。想法是，你可能有某个 function *f*，它不可逆，但你喜欢这个 function，因为它做了一些有意思的事情，比如做一个 MLP，或者用有意思的方式混合。

你想用它构造出某个 invertible 的东西。我们要做的 construction 会是一个 two-input function，而不是 one-input function。我们会应用 *f*(*x*)。我们需要实际记住 *x* 是什么，所以把 *x* 放在这里，这样可以向后工作；同时也不能丢掉 *y*。我们会记住 *y*，并把它们加在一起形成这个 tuple。

反过来如何 invert？如果我有这个 output，想 recover *x* 和 *y*，我可以很容易 recover *x*。它就在这里，我直接读出来。要 recover *y*，如果这个东西叫 *z*，我可以通过 *z* minus *f*(*x*) recover *y*，因为我已经 recover 了 *x*。这意味着这个 construction 是 invertible 的。

这在 ciphers 里大量使用，现在仍在使用。它是构造 ciphers 的主要机制之一。你通常希望 ciphers 是 invertible，尤其是 ciphers 的 layers，因为那有更好的 cryptographic properties。

这实际上已经被移植到 neural nets 里。有一篇 2017 年的论文叫 [RevNets](https://arxiv.org/abs/1707.04585)，也就是 reversible networks。它做的是让整个 network invertible。你可以把它应用到任何 network，比如 transformer network。我做 forwards pass，但随后也可以把整个 pass 向后运行。整个 neural network 通过这个 exact construction 变成 invertible。

这篇论文把它应用到某个 layer，比如 transformer layer。我们有这个 function *f*，也就是我们的 transformer layer。通常我们只有一个 input，然后有一个 residual connection 出来，并在这里加上。现在这个变体是，我们有两个 inputs，*x* 和 *y*。*x* 经过 function，加到 *y* 上，然后这成为新的 *x*，也就是 output *x*。然后这个 *x* 成为 output *y*。

如果往前看两层，它真正做的就是你之前提到的东西。它做的是来自两层之前的 residual connection。这个 *y* 来自上一层，是那里的 residual connection。因为这个 construction，整个东西是 invertible。

我为什么关心这个？invertible 有什么用？它可能有趣的主要地方是 training。如果我考虑 training 的 forward pass……假设我有 4 层，并按 0、1、2、3 的顺序运行它们。我必须把所有 activations 写到 HBM。这里得到的 HBM footprint 会大致和 layers 数量线性相关。

这实际上可能是 training 期间最大的 memory footprint。这是普通 training，然后我运行 backwards pass，并按反方向读取它。forward pass 往前走，backward pass 往后走。我必须把它们读回来。

RevNets 论文的想法是，因为它是 invertible，我根本不需要存这些。我可以完全 rematerialize 它。我运行 forwards pass，然后在运行 backwards pass 时，同时 lockstep 地 undo 我做过的所有 forwards pass steps，以便拿到这里需要的 activations。这会节省 memory，是个不错的想法。

**Dwarkesh Patel**

有意思。从某种意义上说，你是在花更多 compute 来节省 memory。

**Reiner Pope**

对。

**Dwarkesh Patel**

有意思。这和 KV cache 做的事情相反。KV cache 是花更多 memory 来节省 compute。

**Reiner Pope**

对。考虑到硬件现在的状态，花更多 memory 来节省 compute 通常是有利可图的。

**Dwarkesh Patel**

有意思。这太好玩了。Reiner，非常感谢你来做这期。我觉得它真的证明了这个演播室和黑板背后的设想是对的。

**Reiner Pope**

嗯。

**Dwarkesh Patel**

好，非常感谢你来。
