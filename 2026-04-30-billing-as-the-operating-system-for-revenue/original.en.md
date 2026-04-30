# Billing as the Operating System for Revenue

> Source: https://metronome.com/whitepaper/billing-as-the-operating-system-for-revenue  
> Author/Organization: Metronome  
> Subtitle: A modern approach to pricing, billing and growth in the AI Era

## Key excerpts and structured outline

### Introduction

Businesses have entered into a new era in product delivery, where AI and cloud technologies are changing how products are built, deployed, used, and valued by end-users. This has resulted in continuous delivery of new features, and the impact is more measurable than ever before.

Yet the infrastructure most companies use to price and bill their customers for these features was built for a past era. Then, software shipped quarterly, or even annually. At best, a company’s pricing would update annually, and a “seat” subscription meant the same thing for every customer.

### Legacy platforms can’t keep pace

When the limitations of CPQ became apparent, many companies adopted usage-based billing solutions—accounts receivable automation platforms and ERP billing modules that claim to handle consumption pricing.

But these tools apply CPQ’s architecture to usage billing’s computational problem, creating a fundamental mismatch. They can ingest usage data and generate invoices on schedules, but they have fundamental flaws:

- Rates are stored in plan-level configurations, with no centralization across customers.
- Usage is processed in batch jobs, with no real-time computation.
- Manual intervention is required for mid-cycle pricing changes.
- Granular invoice breakdowns are not possible at event or line-item level.

### The solution: Billing must become a runtime system

Modern monetization requires billing to evolve from a record-keeper into a runtime system that continuously computes pricing, invoicing, and revenue as products, costs, and customer behavior evolve.

This is powered by two engines working in tandem:

- **The pricing engine** translates multidimensional product usage into prices using a centralized, versioned rate card.
- **The invoice-compute engine** continuously aggregates usage, applies contract logic such as credits, commits, and overages, and produces invoice-ready data in real time.

A runtime system is the execution layer that continuously processes the logic required to convert customer activity into revenue. It ingests usage events, applies pricing and entitlement rules, executes rating and metering workflows, and produces accurate charges continuously.

### Why pricing needs its own system

CPQ continues to serve an essential role in defining what is sold and under what terms. It governs quoting accuracy, approval workflows, and deal structure. However, modern pricing models have introduced two structural shifts that extend beyond CPQ’s design: multidimensional pricing and credit-based monetization.

#### Multidimensional pricing logic

Traditional CPQ implementations assume a single primary metric, such as seats or licenses, with optional add-ons or volume tiers. Modern monetization models break that assumption. AI and usage-based pricing introduce multiple concurrent metrics such as API calls, GPU hours, inference tokens, or storage volume, each with distinct rates and aggregation rules.

As a result, pricing cannot be expressed by a single metric or static SKU. It must reflect multiple dimensions: usage type, output complexity, region, and model cost, all of which change over time.

#### Credit-based monetization

Instead of charging customers separately for each feature or usage metric they consume, companies are now anchoring on a single unit of value. They sell prepaid credit packages that customers draw down from as they use various capabilities over time.

This model introduces flexibility for customers and predictability for finance teams, but changes how systems run pricing and revenue processes. In credit-based models, procurement and revenue recognition are treated as separate processes.

### Downstream platforms are not runtime systems

Downstream revenue platforms, including AR automation solutions and some billing modules within ERP platforms, may offer basic pricing tables and batch invoicing to support usage-based monetization. But these are narrow tools, not runtime systems. They can store rates and trigger invoice workflows, yet they cannot compute or orchestrate pricing and invoicing as live, continuous processes.

Traditional billing systems lack:

1. A true pricing engine that computes charges dynamically based on multiple dimensions.
2. An invoice-compute engine that continuously calculates billing state in real time.

### The new architecture of monetization

In the modern technology stack, billing sits at the center of both procurement and revenue flows. Upstream, CPQ and contracting systems define commercial intent. Downstream, ERP and BI systems record financial outcomes. Between these layers, billing operates as the runtime system, powered by the pricing engine and invoice-compute engine.

### Modern monetization powered by a runtime system

The runtime system enables four foundational use cases:

1. **Dimensional and granular pricing**: Pricing depends on usage type, AI feature, task, model, input source, output complexity, region, and other factors.
2. **Prepaid and credit-based monetization**: Credits simplify procurement while allowing flexible feature-level usage.
3. **Continuous pricing evolution**: Teams can introduce features and adjust rates without contract amendments or CPQ updates.
4. **Cross-system orchestration**: The rate card becomes the authoritative configuration source, with changes propagated to metering, billing, ledgers, and revenue recognition.

### Conclusion

Modern billing is no longer a passive system of record. Companies processing billions of usage events monthly cannot wait weeks for CPQ updates or manually reconcile invoices when model costs change. The pricing engine and invoice-compute engine together form the foundation of this new model, turning every product event into financial truth.

The litmus test is simple: Can you launch a new AI feature tomorrow with dimensional pricing—charged by tokens, model, region, and complexity—without touching CPQ, without creating new SKUs, and without manual invoice adjustments? If not, you’re running monetization on legacy architecture.
