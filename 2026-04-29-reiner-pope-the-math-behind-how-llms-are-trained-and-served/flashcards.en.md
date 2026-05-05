# Flashcards for Reiner Pope on Dwarkesh Podcast — Practice Questions

- YouTube: https://youtu.be/xmkSf5IS-zw
- Substack: https://www.dwarkesh.com/p/reiner-pope
- Interactive site: https://reiner-flashcards.vercel.app/
- Archived with reading note: 2026-05-05
- Total cards: 27

Wrote some practice problems to help myself and my audience retain Reiner's blackboard lecture.

---

## (00:00:00) — How batch size affects token cost and speed

### Q1. Equation for time of one forward pass (hint — it's the result of two different quantities)

$$T = \max(t_{\mathrm{compute}},\ t_{\mathrm{mem}})$$

### Q2. Equation for $t_{\mathrm{compute}}$

$$t_{\mathrm{compute}} = \frac{B \cdot N_{\mathrm{active}}}{\mathrm{FLOPs}}$$

where $B$ is batch size, $N_{\mathrm{active}}$ is active parameters, and FLOPs is the compute throughput of the hardware.

### Q3. Equation for $t_{\mathrm{mem}}$ (hint — there's a contribution from the weights, and from the KV cache)

$$t_{\mathrm{mem}} = \frac{N_{\mathrm{total}} + B \cdot \mathrm{len}_{\mathrm{ctx}} \cdot \mathrm{KV}_{\mathrm{bytes/token}}}{\mathrm{mem}_{\mathrm{bw}}}$$

### Q4. Sketch out (in your head) what the graph with batch size on the x-axis and latency on the y-axis looks like — draw the lines for $t_{\mathrm{compute}}$, KV fetch, and weight fetch, then bold the line that corresponds to total latency given a certain batch size.

![Latency vs. batch size](/images/latency-vs-batch.png)

### Q5. Where does the lower bound on latency come from? Why can't you just keep decreasing batch size and have infinitesimal total time to process a token?

Because you still have to load all the active parameters into memory.

### Q6. Why doesn't the time cost of a token keep decreasing indefinitely as you increase batch size? What two things cannot be amortized over the batch?

Compute time, and memory time for KV cache fetches, cannot be amortized with batch size.

### Q7. On modern hardware, what is the typical ratio of FLOPs / memory bandwidth?

$\sim 300$ FLOPs / byte.

### Q8. Work through the math that shows that optimal batch size ought to be at least $300 \times$ your sparsity ratio (active / total parameters) to maximize throughput. Ignore KV cache.

Set compute time = memory time (at equality, both resources are fully saturated):

$$\frac{B \cdot N_{\mathrm{active}}}{\mathrm{FLOPs}} = \frac{N_{\mathrm{total}}}{\mathrm{mem}_{\mathrm{bw}}}$$

Solve for $B$:

$$B = \frac{\mathrm{FLOPs}}{\mathrm{mem}_{\mathrm{bw}}} \cdot \frac{N_{\mathrm{total}}}{N_{\mathrm{active}}} = 300 \cdot \frac{1}{\mathrm{sparsity}}$$

So $B \geq 300 / \mathrm{sparsity}$.

**Why:** compute scales with $B$ (each token needs its own matmul), but weight fetches don't (load once, reuse across batch). Need enough tokens to amortize the fetch.

**DeepSeek V3:** $32/256$ active → $B \geq 300 \times 8 = 2{,}400$.

### Q9. Picture a GPU cluster as a train station: every $\sim$20ms, a "train" departs carrying a batch of sequences through one forward pass (producing one new token per sequence). Why 20ms specifically? What goes wrong if you schedule trains more frequently? How about less frequently?

20ms is the HBM drain time — memory capacity ÷ memory bandwidth. E.g. Rubin: $288\text{ GB} / 20\text{ TB/s} \approx 15\text{ms}$.

Faster than 20ms is impossible because you physically can't read all the weights from HBM in less time than bandwidth allows.

Slower than 20ms means you're just leaving the FLOPs idle, because there's nothing left to read.

## (00:32:09) — How MoE models are laid out across GPU racks

### Q1. Why is one rack a natural boundary for an MoE layer?

MoE communication is all-to-all (any GPU's tokens may route to any other GPU's experts).

Within a rack, NVLink connects every GPU to every other at full bandwidth, which is a perfect fit for all-to-all. Across racks, scale-out is $\sim 8\times$ slower and bottlenecks the all-to-all.

## (00:47:12) — How pipeline parallelism moves model layers across racks

### Q1. Why do "bubbles" emerge when pipeline parallelism is used during training?

At the beginning of the batch, the GPUs dedicated to the final layers are not being used, and conversely at the end of the batch, the GPUs dedicated to the first layers are not being used.

![Pipeline bubbles diagram](/images/pipeline-bubbles.png)

### Q2. Why can't you overlap batches in training to solve pipeline bubbles?

You need to consolidate gradients and update the model before you process the next batch.

### Q3. Pipeline parallelism across $P$ stages divides model weights by $P$ per device. Why doesn't it also divide the KV cache by $P$?

Keeping $P$ stages busy requires $P$ micro-batches in flight, so concurrent sequences scale with $P$.

Given that KV cache often dominates memory at long context lengths, pipelining's value is limited.

## (01:03:37) — Why Ilya said, "As we now know, pipelining is not wise."

### Q1. Why did Ilya say, "As we now know, pipelining is not wise."

You're adding architecture constraints — things like Kimi's attention-to-residuals (where each block attends to all previous layers' residuals) become very difficult when those residuals live on different pipeline stages. Similarly, interleaving sliding-window and global attention layers could cause load imbalance across stages. Dealing with all this slows down research iteration, which is the greatest sin you can commit.

## (01:18:59) — Because of RL, models may be 100× over-trained beyond Chinchilla-optimal

### Q1. Where does the 6 in the $6ND$ pre-training FLOPs equation come from?

2 FLOPs per parameter per token for the forward pass (multiply + add). Backward pass is $2\times$ forward because you compute gradients w.r.t. both input matrices. So $2 + 4 = 6$.

### Q2. Write the equation for total compute cost across pre-training, RL, and inference.

$$C_{\mathrm{total}} = C_{\mathrm{pretrain}} + C_{\mathrm{RL}} + C_{\mathrm{inference}}$$

$C_{\mathrm{pretrain}} = 6 \times N_{\mathrm{active}} \times D_{\mathrm{pretrain}}$ (the $6ND$ formula — forward + backward)

$C_{\mathrm{RL}} = (2 \,\mathrm{to}\, 6) \times N_{\mathrm{active}} \times D_{\mathrm{RL}} \times \mathrm{inefficiency}$ (2 if you don't train on the rollout and do forward only, up to 6 if you do; inefficiency from low MFU during decode)

$C_{\mathrm{inference}} = 2 \times N_{\mathrm{active}} \times D_{\mathrm{inference}} \times \mathrm{inefficiency}$ (forward pass only; lower MFU during decode)

### Q3. Why might you naively expect $C_{\mathrm{pretrain}} = C_{\mathrm{RL}} = C_{\mathrm{inference}}$?

If pre-training, RL, and inference costs trade off (more pre-training → less RL/inference needed for same quality, and vice versa), the optimum is approximately where all three are equal.

### Q4. Solve for $D_{\mathrm{pretrain}} = D_{\mathrm{RL}} = D_{\mathrm{inference}}$, with $\tfrac{1}{3}$ as much MFU from decode as prefill.

$$6 \times D_{\mathrm{pretrain}} = 3 \times D_{\mathrm{RL}} \times 3 \times \mathrm{inefficiency} = 2 \times D_{\mathrm{inference}} \times 3 \times \mathrm{inefficiency}$$

$$D_{\mathrm{pretrain}} = 1.5\, D_{\mathrm{RL}} = D_{\mathrm{inference}}$$

### Q5. If a frontier model does 50M tokens/sec globally and is deployed for 2 months, using the analysis above, how many tokens should it be pretrained on?

$$D_{\mathrm{inference}} \approx 50\text{M tokens/sec} \times 60\text{ days} \times 86{,}400\text{ sec/day} \approx 200\text{T tokens}$$

$$D_{\mathrm{pretrain}} \approx D_{\mathrm{inference}} \approx 200\text{T tokens}$$

### Q6. The Chinchilla rule is that $D_{\mathrm{optimal}} \approx 20 \times N_{\mathrm{active}}$. If a frontier model has 100B active parameters and is pretrained on 200T tokens, how much over Chinchilla-optimal is it?

$$D_{\mathrm{chinchilla}} \approx 20 \times 100\text{B} = 2\text{T tokens}$$

$$200\text{T} / 2\text{T} = 100\times$$

## (01:33:02) — Deducing inference memory costs from API pricing

### Q1. Why does Gemini charge $\sim 50\%$ more for tokens above 200K context? At a high level, what's happening?

Below this point, you're compute bound, whose cost is flat as context length increases.

Above this point, you're memory time bound, thanks to KV cache growing, and that increases linearly with context length.

### Q2. Sketch compute and memory time per token as context length increases. Then also sketch the pricing per token and how it changes at the crossover point.

![Cost vs. context length](/images/cost-vs-context.png)

### Q3. Given Gemini's 200K crossover, work out the implied bytes-per-token of KV cache. Assume 100B active parameters.

At the crossover, $t_{\mathrm{compute}} = t_{\text{KV fetch}}$:

$$\frac{B \cdot N_{\mathrm{active}}}{\mathrm{FLOPs}} = \frac{B \cdot \mathrm{len}_{\mathrm{ctx}} \cdot \mathrm{bytes/token}}{\mathrm{mem}_{\mathrm{bw}}}$$

Solve for bytes/token:

$$\mathrm{bytes/token} = \frac{\mathrm{mem}_{\mathrm{bw}}}{\mathrm{FLOPs}} \cdot \frac{N_{\mathrm{active}}}{\mathrm{len}_{\mathrm{ctx}}} = \frac{1}{300} \cdot \frac{N_{\mathrm{active}}}{\mathrm{len}_{\mathrm{ctx}}}$$

Plug in: $N_{\mathrm{active}} \approx 100\text{B}$, $\mathrm{len}_{\mathrm{ctx}} = 200\text{K}$ → $\mathrm{bytes/token} \approx 1.7\text{ KB}$.

### Q4. Output tokens are typically 3–5× more expensive than input tokens. What does that tell us? And why is that?

MFU during decode is about $\tfrac{1}{5}$ that during prefill.

This is because in prefill, you're processing the whole sequence in parallel, so the weight fetch can be amortized across lots of compute, whereas in decode, you have to load all the weights in just to process one more token, which means you're wasting FLOPs while you're waiting for the weights to show up from memory.

### Q5. Why are cached input tokens (cache hits) $\sim 10\times$ cheaper than fresh input tokens?

Loading KVs from memory is much cheaper than recomputing.

## (02:04:02) — Convergent evolution between neural nets and cryptography

### Q1. Why do cryptographic protocols have similar high-level architecture to neural networks, where they're basically jumbling information across many layers?

They've both had this convergent evolution where cryptographic protocols need every output bit to depend on every input bit in complicated ways, and similarly, NNs need output to make connections between inputs.

### Q2. One could argue that NNs and cryptographic protocols use a similar high-level architecture to opposite ends. In what sense are they doing opposite things?

Cryptographic protocols take something which has a lot of structure and make it seem indistinguishable from random. Whereas NNs take something which may look random and extract structure from it.
