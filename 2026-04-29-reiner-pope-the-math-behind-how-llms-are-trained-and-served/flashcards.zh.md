# Reiner Pope 在 Dwarkesh Podcast 上的访谈 flashcards - 练习题

- YouTube: https://youtu.be/xmkSf5IS-zw
- Substack: https://www.dwarkesh.com/p/reiner-pope
- 互动网站：https://reiner-flashcards.vercel.app/
- 归档日期：2026-05-05
- 卡片总数：27

这些练习题用于帮助自己和读者记住 Reiner 的黑板课内容。

---

## (00:00:00) - batch size 如何影响 token 成本和速度

### Q1. 一次 forward pass 所需时间的公式是什么？提示：它由两个不同量共同决定。

$$T = \max(t_{\text{compute}},\ t_{\text{mem}})$$

### Q2. $t_{\text{compute}}$ 的公式是什么？

$$t_{\text{compute}} = \frac{B \cdot N_{\text{active}}}{\text{FLOPs}}$$

其中 $B$ 是 batch size，$N_{\text{active}}$ 是 active parameters，FLOPs 是硬件的计算吞吐。

### Q3. $t_{\text{mem}}$ 的公式是什么？提示：它既包含权重读取，也包含 KV cache 读取。

$$t_{\text{mem}} = \frac{N_{\text{total}} + B \cdot \text{len}_{\text{ctx}} \cdot \text{KV}_{\text{bytes/token}}}{\text{mem\_bw}}$$

### Q4. 在脑中画出横轴为 batch size、纵轴为 latency 的图：画出 $t_{\text{compute}}$、KV fetch 和 weight fetch 的曲线，然后把给定 batch size 下对应总延迟的曲线加粗。

![Latency vs. batch size](/images/latency-vs-batch.png)

### Q5. latency 的下界来自哪里？为什么不能一直减小 batch size，从而让处理一个 token 的总时间趋近于 0？

因为你仍然必须把所需参数加载进内存。

### Q6. 为什么随着 batch size 增加，一个 token 的时间成本不会无限下降？哪两件事不能通过 batch 摊薄？

计算时间和 KV cache fetch 的内存时间，不能通过 batch size 摊薄。

### Q7. 在现代硬件上，FLOPs / memory bandwidth 的典型比值是多少？

$\sim 300$ FLOPs / byte。

### Q8. 推导为什么为了最大化吞吐，最优 batch size 至少应达到 $300 \times$ 稀疏度倍率。忽略 KV cache。

令计算时间 = 内存时间。在相等点，两个资源都被充分饱和：

$$\frac{B \cdot N_{\text{active}}}{\text{FLOPs}} = \frac{N_{\text{total}}}{\text{mem\_bw}}$$

解出 $B$：

$$B = \frac{\text{FLOPs}}{\text{mem\_bw}} \cdot \frac{N_{\text{total}}}{N_{\text{active}}} = 300 \cdot \frac{1}{\text{sparsity}}$$

因此 $B \geq 300 / \text{sparsity}$。这里的 $\text{sparsity}$ 按 active / total parameters 计算；如果用 total / active 表示稀疏度倍率，则是 $300 \times$ 稀疏度倍率。

**原因：**计算随 $B$ 增长，因为每个 token 都需要自己的 matmul；但权重读取不会随 $B$ 增长，因为权重读一次即可在 batch 内复用。你需要足够多 token 来摊薄权重读取。

**DeepSeek V3：**激活比例为 $32/256$，所以 $B \geq 300 \times 8 = 2{,}400$。

### Q9. 把 GPU cluster 想象成火车站：每隔约 20ms，一班“火车”出发，载着一个 batch 的序列完成一次 forward pass，每个序列生成一个新 token。为什么具体是 20ms？如果调度更频繁会怎样？更不频繁又会怎样？

20ms 是 HBM drain time，也就是内存容量除以内存带宽。例如 Rubin：$288\text{ GB} / 20\text{ TB/s} \approx 15\text{ms}$。

快于 20ms 不可行，因为在带宽限制下，你无法在更短时间内从 HBM 物理读取所有权重。

慢于 20ms 意味着你只是让 FLOPs 闲置，因为已经没有更多东西可读。

## (00:32:09) - MoE 模型如何布局在 GPU racks 上

### Q1. 为什么一个 rack 是 MoE layer 的自然边界？

MoE 通信是 all-to-all：任何 GPU 上的 token 都可能被路由到任何其他 GPU 上的 expert。

在一个 rack 内，NVLink 以全带宽连接每个 GPU，非常适合 all-to-all。跨 rack 时，scale-out 网络大约慢 $\sim 8\times$，会成为 all-to-all 的瓶颈。

## (00:47:12) - pipeline parallelism 如何把模型层移动到多个 rack

### Q1. 为什么训练中使用 pipeline parallelism 会出现 bubble？

在 batch 开始时，负责最后几层的 GPU 还没有输入可处理；反过来，在 batch 结束时，负责最前几层的 GPU 已经没有输入可处理。

![Pipeline bubbles diagram](/images/pipeline-bubbles.png)

### Q2. 为什么不能在训练中重叠多个 batch 来解决 pipeline bubble？

因为在处理下一个 batch 之前，你需要汇总梯度并更新模型。

### Q3. 跨 $P$ 个 stage 的 pipeline parallelism 会把模型权重按每台设备除以 $P$。为什么它不会同样把 KV cache 除以 $P$？

要让 $P$ 个 stage 保持忙碌，就需要有 $P$ 个 micro-batch 同时在 pipeline 中流动，因此并发序列数也随 $P$ 增长。

考虑到长上下文下 KV cache 经常主导内存，pipelining 的价值是有限的。

## (01:03:37) - Ilya 为什么说“现在我们知道，pipelining 并不明智”

### Q1. Ilya 为什么说：“现在我们知道，pipelining 并不明智”？

因为它会增加架构约束。例如 Kimi 的 attention-to-residuals 机制中，每个 block 会 attend 到所有前面层的 residual；如果这些 residual 分布在不同 pipeline stage 上，事情会变得很困难。类似地，把 sliding-window attention 和 global attention 层交错起来，可能会造成不同 stage 的 load imbalance。处理这些问题会拖慢研究迭代，而拖慢研究迭代是最严重的代价。

## (01:18:59) - 由于 RL，模型可能比 Chinchilla-optimal 多训练 100 倍

### Q1. 预训练 FLOPs 公式 $6ND$ 中的 6 来自哪里？

forward pass 中，每个参数每个 token 需要 2 FLOPs，即乘法加加法。backward pass 是 forward 的 $2\times$，因为要同时计算两个输入矩阵的梯度。因此 $2 + 4 = 6$。

### Q2. 写出预训练、RL 和推理的总计算成本公式。

$$C_{\text{total}} = C_{\text{pretrain}} + C_{\text{RL}} + C_{\text{inference}}$$

$C_{\text{pretrain}} = 6 \times N_{\text{active}} \times D_{\text{pretrain}}$，即 $6ND$ 公式，包含 forward + backward。

$C_{\text{RL}} = (2 \text{ to } 6) \times N_{\text{active}} \times D_{\text{RL}} \times \text{inefficiency}$。如果不在 rollout 上训练、只做 forward，则系数为 2；如果训练 rollout，最高到 6；inefficiency 来自 decode 阶段较低的 MFU。

$C_{\text{inference}} = 2 \times N_{\text{active}} \times D_{\text{inference}} \times \text{inefficiency}$。这里只做 forward pass；decode 阶段 MFU 较低。

### Q3. 为什么你可能会天真地预期 $C_{\text{pretrain}} = C_{\text{RL}} = C_{\text{inference}}$？

如果预训练、RL 和推理成本之间存在权衡，比如更多预训练可以让同等质量所需的 RL 或推理更少，反之亦然，那么最优点大致会出现在三者相等的位置。

### Q4. 假设 decode 的 MFU 只有 prefill 的 $\tfrac{1}{3}$，求解 $D_{\text{pretrain}} = D_{\text{RL}} = D_{\text{inference}}$ 的关系。

$$6 \times D_{\text{pretrain}} = 3 \times D_{\text{RL}} \times 3 \times \text{inefficiency} = 2 \times D_{\text{inference}} \times 3 \times \text{inefficiency}$$

$$D_{\text{pretrain}} = 1.5\, D_{\text{RL}} = D_{\text{inference}}$$

### Q5. 如果一个前沿模型全球吞吐为 50M tokens/sec，并部署 2 个月，根据上面的分析，它应该预训练多少 token？

$$D_{\text{inference}} \approx 50\text{M tokens/sec} \times 60\text{ days} \times 86{,}400\text{ sec/day} \approx 200\text{T tokens}$$

$$D_{\text{pretrain}} \approx D_{\text{inference}} \approx 200\text{T tokens}$$

### Q6. Chinchilla rule 是 $D_{\text{optimal}} \approx 20 \times N_{\text{active}}$。如果一个前沿模型有 100B active parameters，并在 200T tokens 上预训练，它比 Chinchilla-optimal 多多少？

$$D_{\text{chinchilla}} \approx 20 \times 100\text{B} = 2\text{T tokens}$$

$$200\text{T} / 2\text{T} = 100\times$$

## (01:33:02) - 从 API 定价推断推理内存成本

### Q1. 为什么 Gemini 对超过 200K context 的 token 收取约 $\sim 50\%$ 的额外费用？高层看发生了什么？

在这个点以下，你是 compute-bound；随着 context length 增加，成本基本保持平坦。

在这个点以上，由于 KV cache 增长，你变成 memory-time-bound，成本随 context length 线性增加。

### Q2. 画出随着 context length 增加，每 token 的计算时间和内存时间如何变化。然后也画出每 token 定价，并说明它在交叉点如何变化。

![Cost vs. context length](/images/cost-vs-context.png)

### Q3. 给定 Gemini 的 200K 交叉点，假设 active parameters 为 100B，求 KV cache 隐含的 bytes-per-token。

在交叉点处，$t_{\text{compute}} = t_{\text{KV fetch}}$：

$$\frac{B \cdot N_{\text{active}}}{\text{FLOPs}} = \frac{B \cdot \text{len}_{\text{ctx}} \cdot \text{bytes/token}}{\text{mem\_bw}}$$

解出 bytes/token：

$$\text{bytes/token} = \frac{\text{mem\_bw}}{\text{FLOPs}} \cdot \frac{N_{\text{active}}}{\text{len}_{\text{ctx}}} = \frac{1}{300} \cdot \frac{N_{\text{active}}}{\text{len}_{\text{ctx}}}$$

代入：$N_{\text{active}} \approx 100\text{B}$，$\text{len}_{\text{ctx}} = 200\text{K}$，得到 $\text{bytes/token} \approx 1.7\text{ KB}$。

### Q4. 输出 token 通常比输入 token 贵 3 到 5 倍。这告诉我们什么？为什么会这样？

decode 阶段的 MFU 大约是 prefill 阶段的 $\tfrac{1}{5}$。

原因是，在 prefill 中，你可以并行处理整个序列，因此权重读取可以在大量计算上摊薄；而在 decode 中，你必须为了只处理下一个 token 而加载所有权重，这意味着 FLOPs 会在等待权重从内存中出现时被浪费。

### Q5. 为什么 cached input tokens，也就是 cache hits，通常比 fresh input tokens 便宜约 $\sim 10\times$？

从内存加载 KVs 比重新计算便宜得多。

## (02:04:02) - 神经网络和密码学之间的趋同演化

### Q1. 为什么密码协议和神经网络具有相似的高层架构，也就是基本上都在很多层中混合信息？

两者出现了某种趋同演化：密码协议需要让每个输出 bit 以复杂方式依赖每个输入 bit；类似地，神经网络需要让输出在输入之间建立连接。

### Q2. 可以说神经网络和密码协议使用相似的高层架构，但目的相反。它们在哪个意义上是在做相反的事情？

密码协议拿到有大量结构的东西，并让它看起来与随机不可区分。神经网络则拿到看起来可能像随机的东西，并从中提取结构。
