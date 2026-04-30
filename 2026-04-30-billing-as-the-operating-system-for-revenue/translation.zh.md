# 作为收入操作系统的计费

> 原文：Billing as the Operating System for Revenue  
> 来源：https://metronome.com/whitepaper/billing-as-the-operating-system-for-revenue  
> 作者/机构：Metronome

## 导言

Metronome 认为，企业已经进入一个新的产品交付时代。AI 和云技术正在改变产品如何被构建、部署、使用和衡量价值。过去，软件可能按季度或年度发布，价格也往往一年才调整一次；而现在，新功能可以持续交付，每个功能对不同用户产生不同价值，也消耗不同资源、产生不同成本。

传统定价和计费基础设施是为旧时代设计的。它们假设产品、价格和合同是相对静态的。但在 AI 时代，这种假设会造成运营断裂：财务团队需要手工修发票，销售运营团队需要维护大量 SKU，产品团队要等 CPQ 更新才能测试新价格，客户看到的用量看板也不是实时的。

## 传统平台为什么跟不上

许多公司在 CPQ 不足后采用了 usage-based billing、AR automation 或 ERP billing module。但文章认为，这些工具往往只是把 CPQ 的静态架构套到用量计费问题上。

它们通常可以导入用量并生成发票，但存在根本限制：

- 价格存放在 plan 或 customer configuration 中，而不是集中管理。
- 用量通过批处理计算，而不是实时计算。
- mid-cycle 价格变化需要人工干预。
- 发票无法提供足够细粒度、事件级的解释。

结果是，企业不得不用自研脚本、手工流程和工程团队维护内部 billing 系统。每增加一个 AI feature，本应带来收入，却反而增加运营负担。

## 解决方案：Billing 必须成为 runtime system

现代商业化要求 billing 从记录系统演变为运行时系统。它需要随着产品、成本和客户行为变化，持续计算价格、发票和收入。

这个系统由两个核心引擎组成：

### Pricing engine

Pricing engine 把多维度产品用量转换为价格。它通过集中式、版本化 rate card 保存价格规则。例如：

- GPT-4 inference in US-East = 每 1K tokens 0.03 美元
- 一次文档摘要 = 2 credits
- 某类复杂推理任务 = 按模型、区域和输出复杂度组合计费

它既可以保证全局一致性，也可以允许特定合同 override。

### Invoice-compute engine

Invoice-compute engine 持续聚合用量，应用合同逻辑，例如 credits、commits、overages、discounts 和 expiration，并实时生成可开票数据。它不是夜间批处理，而是随着 usage events 发生持续计算。

## CPQ 和 ERP 的演变

过去的 monetization 流程相对简单：CPQ 定义报价和合同条款，ERP 处理发票和收入确认。中间几乎都是静态对象：quote、SKU、schedule。

这种模式适合 seat-based SaaS。但 AI 和 usage-based 产品引入了更频繁的功能发布、更复杂的成本结构和更多样的购买方式。定价不能再存在于静态系统里，开票也不能只是被动的会计任务。

## 为什么定价需要自己的系统

文章认为，现代 pricing model 引入了两个传统 CPQ 难以处理的结构性变化：

### 1. 多维度定价逻辑

传统 CPQ 通常假设主要计费指标是 seats 或 licenses，再加一些 add-ons 或 volume tiers。但 AI 和用量型产品可能同时有 API calls、GPU hours、inference tokens、storage volume、model type、region 和 output complexity 等多个维度。

如果用静态 SKU 表示这些组合，会出现 SKU proliferation。例如 2 种 usage type、3 个 output tier、3 个 region、2 个 model option 就可能产生 36 个 SKU，还没计算 volume tiers 和促销价格。

### 2. Credit-based monetization

越来越多公司采用 credit 模型：客户预先购买一包 credits，然后在使用不同功能时消耗 credits。

这种模型的好处是客户体验简单，采购摩擦低，销售可以只卖标准化 credit pack。但它要求 billing 系统能实时计算：

- 每个 feature 或 usage type 如何转换成 credits；
- 每次使用如何扣减余额；
- credit 使用如何映射到合同、产品和收入确认；
- rollover、expiration、bonus credits 等合同规则如何自动执行。

CPQ 可以记录购买 credit pack 这件事，但不能实时计算 credits 如何被消耗以及收入何时确认。

## 下游平台不是 runtime system

文章批评了一类“看似支持 usage-based billing”的下游平台，包括 AR automation 和 ERP billing module。它们可以保存费率、触发发票流程，但不是实时计算系统。

它们通常缺少两个能力：

1. **真正的 pricing engine**：动态计算多维度价格，而不是查静态价格表。
2. **invoice-compute engine**：实时计算 billing state，而不是定时批处理。

没有这些能力，就会出现价格分散、难以回答平均单价和收入影响问题、价格调整需要逐个客户修改、credit balance 不实时、发票细节需要事后用 spreadsheet 或 BI 重建等问题。

## 新的 monetization architecture

新的架构中，billing 位于 CPQ/contracting 与 ERP/BI 之间。

- 上游 CPQ 和合同系统定义商业意图：客户买了什么、commit 多少、有哪些条款。
- 中间 billing runtime system 执行定价和计费计算。
- 下游 ERP、revenue 和 BI 系统记录财务结果。

Billing runtime 包含 pricing engine、invoice-compute engine 和 contract encoding layer。每个 usage event、价格变化和合同更新都能实时传播到 invoice、ledger、customer dashboard 和 revenue system。

## 现代 monetization 的四个能力

### 1. 维度化和细粒度定价

通过 rate card 统一定义 usage type、AI feature、task、model、input source、output complexity、region 等维度，并由 pricing engine 计算价格。

### 2. 预付费和 credit-based monetization

客户用 credits 作为跨产品统一货币。Billing 系统实时执行 credit burn，并维护准确余额和财务账本。

### 3. 持续定价演进

价格可以随着模型成本、功能价值和客户需求变化而变化，不必每次都修改合同或 CPQ。系统支持 cohort rollout、版本控制、回滚和审计。

### 4. 跨系统编排

rate card 成为价格规则的 authoritative configuration。变化只需做一次，再自动传播到 metering、billing、ledger 和 revenue recognition。

## 结论

文章的结论是：随着产品持续演进，企业也需要能持续把用量转换成收入的基础设施。现代 billing 不再是被动记录系统，而是把每个产品事件转换成财务事实的计算层。

一个简单判断标准是：企业能否明天上线一个新的 AI feature，并按 tokens、model、region、complexity 多维度计费，同时不修改 CPQ、不创建新 SKU、不手工调整发票？如果不能，就说明当前架构仍然是 legacy monetization architecture。
