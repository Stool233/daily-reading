# CI at Scale: Lean, Green, and Fast

> Authors: Dhruva Juloori, Zhongpeng Lin, Matthew Williams, Eddy Shin, Sonal Mahajan\
> Affiliation: Uber Technologies, Inc., USA\
> Source: [arXiv:2501.03440v2](https://arxiv.org/html/2501.03440v2) · [Original PDF](paper.pdf)\
> First submitted: 2025-01-07 · Version used: v2, 2025-05-19 · Archived: 2026-09-05\
> License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Authors retain credit.\
> Format changes: Converted the arXiv HTML article to Markdown; math preserved as LaTeX; figures rendered from the PDF; navigation and web interface omitted. Figure 3 retains the source's prior-work attribution. For authoritative typography and any conversion discrepancy, consult the original PDF. No author endorsement is implied.

## Abstract

Maintaining a “green” mainline branch—where all builds pass successfully—is crucial but challenging in fast-paced, large-scale software development environments, particularly with concurrent code changes in large monorepos. SubmitQueue, a system designed to address these challenges, speculatively executes builds and only lands changes with successful outcomes. However, despite its effectiveness, the system faces inefficiencies in resource utilization, leading to a high rate of premature build aborts and delays in landing smaller changes blocked by larger conflicting ones.

This paper introduces enhancements to SubmitQueue, focusing on optimizing resource usage and improving build prioritization. Central to this is our innovative probabilistic model, which distinguishes between changes with shorter and longer build times to prioritize builds for more efficient scheduling. By leveraging a machine learning model to predict build times and incorporating this into the probabilistic framework, we expedite the landing of smaller changes blocked by conflicting larger time-consuming changes. Additionally, introducing a concept of speculation threshold ensures that only the most likely builds are executed, reducing unnecessary resource consumption.

After implementing these enhancements across Uber’s major monorepos (Go, iOS, and Android), we observed a reduction in Continuous Integration (CI) resource usage by approximately 53%, CPU usage by 44%, and P95 waiting times by 37%. These improvements highlight the enhanced efficiency of SubmitQueue in managing large-scale software changes while maintaining a green mainline.

## Index Terms:

Continuous Integration, Merge Queue, Monorepos, Build Time Prediction, Build Scheduling, Probabilistic Modeling, Speculative Execution, Version Control

## I Introduction

Hundreds of engineers frequently commit changes to a single repository in modern software development, particularly within large and fast-paced technology companies[[1](https://arxiv.org/html/2501.03440v2#bib.bib1)]. This scenario presents a significant challenge: efficiently managing these changes, quickly resolving conflicts, and ensuring that the mainline remains green. A mainline is considered green if all build steps—compilation, unit tests, and UI tests—are successfully executed for every commit point in the repository history. Maintaining a green mainline is critical for enabling rapid development and deployment cycles. However as highlighted in the study [[2](https://arxiv.org/html/2501.03440v2#bib.bib2)], landing changes rapidly while keeping the mainline green becomes increasingly difficult as the codebase grows in size and complexity, further compounded by the concurrency of changes submitted by numerous developers.

While systems such as GitHub’s Merge Queue [[3](https://arxiv.org/html/2501.03440v2#bib.bib3)], GitLab’s Merge Train [[4](https://arxiv.org/html/2501.03440v2#bib.bib4)], LinkedIn’s pre-merge validation [[5](https://arxiv.org/html/2501.03440v2#bib.bib5)], and Airbnb’s Evergreen [[6](https://arxiv.org/html/2501.03440v2#bib.bib6)] and similar solutions [[7](https://arxiv.org/html/2501.03440v2#bib.bib7), [8](https://arxiv.org/html/2501.03440v2#bib.bib8)] aim to maintain a green mainline, they often fall short of rapidly landing changes while keeping the mainline green. These approaches lack either speculative execution or conflict resolution, leading to high resource usage and longer land times when earlier changes in the queue fail or during periods of high change velocity.

SubmitQueue is designed to efficiently land changes while maintaining a green mainline, following the principles outlined in [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)]. At Uber, where over four thousand engineers work globally across thousands of microservices and tens of mobile apps, the system processes tens of thousands of changes each month. This scale involves managing hundreds of millions of lines of code across six major monorepos and seven programming languages. SubmitQueue facilitates hundreds of thousands of deployments and handles millions of configuration changes monthly. In this high-velocity development environment, ensuring the seamless and efficient integration of changes while landing them quickly into the mainline is crucial for maintaining service reliability, operational stability, and maximizing developer productivity.

SubmitQueue operates by speculating on the outcomes of all pending changes and constructing a speculation tree that outlines all possible builds for changes currently in the system. It uses a combination of a probabilistic model and a machine learning model to prioritize the builds most likely to succeed, executing them in parallel to minimize land times. This ensures that only changes passing all required checks are landed, thereby preserving the integrity of the mainline. Additionally, SubmitQueue performs conflict analysis between changes to prune the speculation tree, allowing independent changes to be built concurrently.

While SubmitQueue addresses many challenges in maintaining a green mainline, it still has certain limitations. As highlighted in the previous study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], SubmitQueue has a strategy where it aborts ongoing builds of changes when the builds of the newly arrived changes are predicted to have a higher likelihood of success than those already in progress. This leads to two key issues:

- High Resource Utilization: A significant number of builds are prematurely aborted, with an estimated 40-65% of builds being affected across major monorepos at Uber, which in turn leads to the need for scheduling additional builds for the changes whose builds were aborted.

- Increased Waiting Times: SubmitQueue processes changes in the order they are submitted. As a result, changes with shorter build times that arrive after a large, time-consuming change must wait for the larger change to either commit or reject before proceeding.

The introduction of Bypassing Large Diffs (BLRD) [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)] has partly addressed the issue of increased waiting times by introducing the concept of commutativity in change ordering. According to BLRD, if all the speculative builds for a smaller change, when blocked by a larger time-consuming conflicting change, have been evaluated and yield consistent outcomes, the smaller change can safely bypass the larger change and be landed or rejected based on the outcome. However, not all speculative builds for the smaller change are evaluated in most cases, as they are not prioritized. This occurs because SubmitQueue’s probabilistic model, as outlined in [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], assumes that only a single build is required to make a decision for each change and cannot distinguish between smaller and larger time-consuming changes to prioritize the builds accordingly. As a result, smaller changes continue to experience long waiting times when their speculative builds aren’t prioritized, even though they could potentially bypass the larger changes ahead in the queue.

Addressing these limitations is crucial for two key reasons. First, resource utilization directly impacts operational costs, especially in fast-paced tech companies with high development velocity. Estimates suggest that large-scale CI systems, like those at Google and Mozilla, incur costs in the millions annually [[11](https://arxiv.org/html/2501.03440v2#bib.bib11)]. Inefficient build prioritization can further escalate these costs. For companies with limited budgets, this poses a significant barrier to adopting CI practices. Additionally, long waiting times reduce system efficiency and hinder developer productivity, as engineers face delays in landing their changes.

This paper proposes a series of enhancements to the SubmitQueue system, focusing on optimizing resource usage and improving build prioritization to reduce waiting times. Specifically, we introduce a refined build prioritization strategy that leverages a machine learning model to predict build times and a novel probabilistic model to assess the eligibility of changes for bypassing to prioritize builds more effectively. Additionally, we present the concept of a speculation threshold to ensure that only the most probable builds are scheduled, further enhancing the system’s efficiency.

Following the implementation of these enhancements across Uber’s major monorepos (Go, iOS, and Android), we saw notable improvements in key metrics: CI resource usage dropped by 53%, weekly CPU hours by 44%, and p95 waiting times by 37%. These results highlight more efficient resource utilization, reduced consumption, and faster change landings, demonstrating the effectiveness of our strategy in optimizing SubmitQueue for large-scale CI environments.

The paper is structured as follows: We first discuss the background, highlighting the importance of maintaining a green mainline and the associated challenges. Next, we provide an overview of the SubmitQueue system, covering key concepts such as BLRD[[10](https://arxiv.org/html/2501.03440v2#bib.bib10)], BLRD eligibility, build completion estimation, and probabilistic build prioritization. We then explore the concept of speculation threshold and its impact on build scheduling. The paper continues with an in-depth discussion of the implementation and evaluation of these strategies, followed by conclusions and future work.

## II Background

### II-A Importance of a Stable Mainline

As discussed in Section [I](https://arxiv.org/html/2501.03440v2#S1), maintaining a green mainline—where all builds pass successfully is critical in large-scale, high-velocity development environments. A green mainline ensures stability, enabling seamless continuous integration, rapid development cycles, and consistent deployment of updates.

As highlighted in [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], When the mainline turns “red” indicating a failure, it triggers a cascade of issues that can severely impact productivity, development timelines, and overall system stability. These issues include:

- Delayed Rollouts: A red mainline delays the deployment of new features and security patches, which can result in financial losses, especially in industries where time-to-market is critical. A study [[12](https://arxiv.org/html/2501.03440v2#bib.bib12)] shows that organizations with effective CI/CD practices deploy code 46 times more frequently, have 440 times faster commit-to-deploy times, and recover from downtime 170 times faster than low-performing organizations, underscoring the impact of delayed rollouts on revenue.

- Rollback Costs: When failures occur, engineers must revert to the last stable state, often requiring complex cherry-picking and significant resource use. A study [[13](https://arxiv.org/html/2501.03440v2#bib.bib13)] on Atlassian projects (2021-2023) found that failed CI builds caused an average of 120 hours of wasted build time per project annually, resulting in substantial costs.

- Decreased Productivity: A red mainline disrupts developer workflows by causing local build failures and forcing developers to work on code that may later be reverted. A study [[14](https://arxiv.org/html/2501.03440v2#bib.bib14)] has shown that process metrics like build stability are strong indicators of developer productivity. Unstable builds and frequent reverts significantly disrupt workflow, leading to wasted effort and frustration, as developers must spend time fixing issues that might not have existed in a stable mainline environment.

### II-B Other Approaches and Their Limitations

GitHub’s Merge Queue [[3](https://arxiv.org/html/2501.03440v2#bib.bib3)] and GitLab’s Merge Train [[4](https://arxiv.org/html/2501.03440v2#bib.bib4)] both operate by sequentially testing each change before merging. While they support parallel testing, these systems only speculate the success paths. When earlier changes in the queue fail, subsequent changes must be retested without the failed ones, which causes delays, especially when the failure rate is high. Additionally, both approaches lack conflict detection based on dependency graphs, leading to unnecessary test restarts when unrelated changes fail and causing further delays for subsequent changes.

![figure-1-architecture](assets/figures/figure-1-architecture.png)

Fig. 1: SubmitQueue Architecture

Airbnb’s Evergreen system [[6](https://arxiv.org/html/2501.03440v2#bib.bib6)] addresses the serializability of changes in large monorepos by conducting conflict analysis and parallelizing the verification of independent changes. However, it falls short in scenarios with high-conflict periods or rapid change velocity. If pre-merge tests for earlier changes in the queue are lengthy, subsequent changes that have finished building must wait, limiting scalability in fast-paced environments. Additionally, if those pre-merge tests are prone to failures, it can result in repeated retesting of subsequent changes, leading to resource inefficiencies.

Aviator’s Merge Queue [[7](https://arxiv.org/html/2501.03440v2#bib.bib7)] is similar to SubmitQueue in that it speculatively executes builds of pending changes while performing conflict analysis. They introduced the concept of calculating a “cutoff score” to determine which speculation paths are worth building. While setting a cutoff score can reduce resource usage, it alone is insufficient. Under high-load conditions, smaller changes conflicting with larger changes must either wait for the larger changes to finish or face build delays if their scores fall below the cutoff, negatively impacting land times.

### II-C The Need for a Robust Change Management System

Given the limitations of other approaches, a more comprehensive solution is necessary to address the scale and concurrency of modern software development. Systems like SubmitQueue meet these demands by speculatively executing builds and landing only changes that pass all required checks, preventing mainline breakages before they occur.

By implementing systems like SubmitQueue, companies of any size can significantly enhance developer productivity, enabling faster release cycles while ensuring the highest levels of software quality. These systems help maintain a stable and reliable mainline, minimizing disruptions and reducing bottlenecks caused by concurrent changes. This paper builds on these foundations by introducing enhancements to optimize resource usage, reduce waiting times, and refine build prioritization for improved overall performance.

## III System Overview

When a change is submitted to SubmitQueue via the API service, it is added to a distributed queue for processing. The core service consists of several components responsible for executing all necessary build steps for each enqueued change. It ultimately determines whether to land or reject the change and the reason for rejection. Figure [1](https://arxiv.org/html/2501.03440v2#S2.F1) illustrates the high-level architecture of SubmitQueue.

### III-A Enumerator

The Enumerator processes the queue of pending changes by constructing a speculation tree that outlines all possible builds for changes currently in the system. Using a target analyzer to identify potential conflicts between changes, the Enumerator (1) prunes unnecessary speculations to increase the likelihood of executing the remaining ones and (2) identifies independent changes that can be built in parallel, improving throughput.

### III-B Profiler

The Profiler takes the speculation trees generated by the enumerator to create a profile for each tree, capturing information about the bypassing changes linked to each change within the tree. By predicting the build times of the nodes in the speculation tree, the build-time analyzer enables the Profiler to accurately identify the bypassing changes associated with each change.

### III-C Prioritizer

The Prioritizer calculates the probability of build needed for each node in the speculation tree by leveraging change bypassing data from the speculation tree profile and the success likelihood score of each change within SubmitQueue. It then ranks the builds based on these probabilities. The success likelihood score is predicted using a machine learning-powered success predictor, enabling the Prioritizer to make more informed build prioritization decisions.

### III-D Selector

The Selector processes the prioritized builds and performs the following actions: (1) schedules high-probability builds for execution in the CI, (2) aborts ongoing builds that do not exist in the latest set of prioritized builds, and (3) safely commits changes to the monorepo once they meet all criteria for landing.

## IV Bypassing Large Diffs (BLRD)

SubmitQueue executes builds in parallel to precompute results. However, it only decides whether to commit or reject a change once its corresponding build finishes and reaches the head of the tree. As a result, smaller changes that arrive after larger conflicting changes are often delayed, even if their builds completed earlier. Large changes affecting many build targets can conflict with nearly every subsequent change processed by SubmitQueue. As illustrated in Figure [2](https://arxiv.org/html/2501.03440v2#S4.F2), conflicts are frequent in the monorepos, and as the number of conflicts increases, the speculation tree grows deeper, further exacerbating delays.

![figure-2-conflict-rates](assets/figures/figure-2-conflict-rates.png)

Fig. 2: Monthly conflict rates across Go, iOS, and Android monorepos from January to June 2024.

As discussed in Section [I](https://arxiv.org/html/2501.03440v2#S1), BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)] can expedite the landing of smaller changes if all of their speculative builds with the conflicting larger changes ahead yield the same outcome.

![figure-3-speculation-tree](assets/figures/figure-3-speculation-tree.png)

Fig. 3: Speculation tree of builds for conflicting changes $C_{1}$, $C_{2}$, and $C_{3}$ that arrive in the mentioned order [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)].

Figure reproduced with authors’ consent from the prior study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)].

In Figure [3](https://arxiv.org/html/2501.03440v2#S4.F3), let $H$ represent the current repository HEAD, and $C_{1}$, $C_{2}$, and $C_{3}$ be conflicting changes to be committed. Here, $C_{1}$ is a large time-consuming change, while $C_{2}$ is smaller and faster. For these changes, the following build steps are defined:

- $B_{1}$ – Build steps for $C_{1}$ against $H$.

- $B_{2}$ – Build steps for $C_{2}$ against $H$.

- $B_{1.2}$ – Build steps for $C_{2}$ against $H+C_{1}$.

- $B_{1.2.3}$ – Build steps for $C_{3}$ against $H+C_{1}+C_{2}$.

- $B_{1.3}$ – Build steps for $C_{3}$ against $H+C_{1}$.

- $B_{2.3}$ – Build steps for $C_{3}$ against $H+C_{2}$.

- $B_{3}$ – Build steps for $C_{3}$ against $H$.

Let $M(S,C)$ represent the state of the mainline after applying change $C$ to state $S$. SubmitQueue tests $C_{2}$ both on the current HEAD ($B_{2}$) and against $C_{1}$ ($B_{1.2}$). If both speculative builds $B_{2}$ and $B_{1.2}$ produce identical results, then the outcome of landing $C_{2}$ is independent of whether $C_{1}$ lands before or after. In this case, $C_{2}$ can be safely landed while $C_{1}$ is still in progress, ensuring:

$$
M(M(H,C_{1}),C_{2})=M(M(H,C_{2}),C_{1}),
$$

thereby demonstrating that the order of landing $C_{1}$ and $C_{2}$ behaves commutatively. For more details and a complete proof of the BLRD concept, please refer to [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)].

![figure-4-blrd-trigger-rates](assets/figures/figure-4-blrd-trigger-rates.png)

Fig. 4: Monthly BLRD Trigger Rate for Go, Android, and iOS monorepos from January to June 2024.

The BLRD trigger rate is calculated as the ratio of the total number of changes bypassed to the total number of changes that had to wait due to conflicting builds in progress. With rates ranging from 0% to 45% across all monorepos, this suggests significant room for improvement in optimizing the bypassing of smaller changes and reducing delays caused by the builds of larger conflicting changes ahead in the speculation tree.

## V Probabilistic Model

SubmitQueue prioritizes builds based on their likelihood of being needed to optimize resource utilization. According to [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], the probability $\displaystyle P^{\text{needed}}_{B_{C}}$ denotes the likelihood that the result of build $B_{C}$ will be used to decide whether to commit or reject the change $C$. The probabilistic model proposed in the prior research was based on the following assumptions:

- Only one build is necessary to determine the fate of a change.

- Changes are landed onto the mainline in the order they arrive in the queue.

However, these assumptions no longer hold with the introduction of BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)]. As mentioned in Sections [I](https://arxiv.org/html/2501.03440v2#S1) and [IV](https://arxiv.org/html/2501.03440v2#S4), BLRD allows smaller changes to bypass larger, conflicting ones if all speculative builds of the smaller change are evaluated and produce consistent outcomes before the larger change completes. This requires SubmitQueue to evaluate multiple builds per change, ensuring smaller changes can bypass larger ones when eligible. The previous model’s assumption of a single build determining a change’s outcome is insufficient, as BLRD demands equal prioritization of all speculative builds to assess eligibility to bypass. However, evaluating all builds is expensive, because the number of builds grows exponentially with the depth of the speculation tree. Therefore, after the introduction of BLRD, the probabilistic model needs to prioritize builds to expedite the landing of the changes while optimizing resource usage.

### V-A Enhanced Probabilistic Model

The new model should focus on two key objectives:

- Prioritize speculative builds for possible bypasses: When changes can bypass larger conflicting changes ahead in the queue, all speculative builds of the eligible changes must be prioritized equally to allow smaller changes to land quickly.

- Schedule builds for most likely paths in speculation tree for non-bypassing changes: When a change’s builds are likely to finish after the conflicting changes ahead in the queue are landed or rejected, only the most necessary speculative builds should be prioritized, as one build is sufficient to determine the outcome.

Consider Figure [3](https://arxiv.org/html/2501.03440v2#S4.F3), which illustrates the new probabilistic model with multiple conflicting changes. The finish times for the changes are defined as follows:

- The finish time of $C_{1}$ ($FT_{1}$) is the time when build $B_{1}$ completes.

- The finish time of $C_{2}$ ($FT_{2}$) is the time when both $B_{1.2}$ and $B_{2}$ complete.

- The finish time of $C_{3}$ ($FT_{3}$) is the time when all builds $B_{1.2.3}$, $B_{1.3}$, $B_{2.3}$, and $B_{3}$ complete.

In this context, the expression $P(FT_{y}<FT_{x})$ represents the probability that the finish time of change $C_{y}$ occurs before the finish time of change $C_{x}$. These probabilities determine which builds are required, influencing the scheduling and prioritization of builds. This is because if $C_{y}$’s builds are unlikely to finish before $C_{x}$’s builds, there is little chance that BLRD will be used, and we only need to speculate $C_{y}$ based on most likely outcome of $C_{x}$.

- Case 1: $FT_{1}<FT_{2}<FT_{3}$

In this scenario, $C_{1}$ finishes before $C_{2}$, and $C_{2}$ finishes before $C_{3}$. Since there is no opportunity for bypassing, the root of the tree $B_{1}$ is always needed to determine the fate of $C_{1}$. The probabilities are:

$$
P^{\text{needed}}_{B_{1}}=1,\quad P^{\text{needed}}_{B_{1.2}}=P^{\text{success}}_{B_{1}},\quad P^{\text{needed}}_{B_{2}}=1-P^{\text{success}}_{B_{1}}
$$

$$
P^{\text{needed}}_{B_{1.2.3}}=P^{\text{success}}_{B_{1}}\times P^{\text{success}}_{B_{2}}
$$

This specific case was the primary focus of the probabilistic model presented in the prior study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)].

- Case 2: $FT_{2}<FT_{1}<FT_{3}$

There is a chance that all builds of $C_{2}$ finish before $C_{1}$, allowing $C_{2}$ to bypass $C_{1}$, the outcomes of both builds $B_{2}$ and $B_{1.2}$ are needed for determining whether $C_{2}$ lands before $C_{1}$. The probabilities are:

$$
P^{\text{needed}}_{B_{2}}=P^{\text{needed}}_{B_{1.2}}=P(FT_{2}<FT_{1})
$$

Since $C_{3}$ finishes last, its builds are dependent on the results of both $C_{1}$ and $C_{2}$.

- Case 3: $FT_{1}<FT_{3}<FT_{2}$

There is also a possibility that $C_{1}$ finishes before $C_{3}$, and $C_{3}$ finishes before $C_{2}$. When BLRD is used for $C_{3}$, the build outcomes of $C_{2}$ do not affect the builds for $C_{3}$. The probabilities that we need different builds for $C_{3}$ to bypass $C_{2}$ are:

$$
P^{\text{needed}}_{B_{1.2.3}}=P^{\text{success}}_{B_{1}}\times P(FT_{3}<FT_{2})
$$

$$
P^{\text{needed}}_{B_{1.3}}=P^{\text{success}}_{B_{1}}\times P(FT_{3}<FT_{2})
$$

$$
P^{\text{needed}}_{B_{2.3}}=P^{\text{failure}}_{B_{1}}\times P(FT_{3}<FT_{2})
$$

$$
P^{\text{needed}}_{B_{3}}=P^{\text{failure}}_{B_{1}}\times P(FT_{3}<FT_{2})
$$

- Case 4: $FT_{3}<FT_{2}<FT_{1}$

In this scenario, $C_{3}$ finishes before both $C_{2}$ and $C_{1}$. As a result, the build outcomes of $C_{1}$ and $C_{2}$ do not affect the builds for $C_{3}$, and similarly, the build outcome of $C_{1}$ do not affect the builds for $C_{2}$. The probabilities for $C_{3}$’s builds are:

$$
P^{\text{needed}}_{B_{1.2.3}}=P(FT_{3}<FT_{1})\times P(FT_{3}<FT_{2})
$$

$$
P^{\text{needed}}_{B_{1.3}}=P(FT_{3}<FT_{1})\times P(FT_{3}<FT_{2})
$$

$$
P^{\text{needed}}_{B_{2.3}}=P(FT_{3}<FT_{1})\times P(FT_{3}<FT_{2})
$$

$$
P^{\text{needed}}_{B_{3}}=P(FT_{3}<FT_{1})\times P(FT_{3}<FT_{2})
$$

For $C_{2}$’s builds:

$$
P^{\text{needed}}_{B_{1.2}}=P(FT_{2}<FT_{1}),\quad P^{\text{needed}}_{B_{2}}=P(FT_{2}<FT_{1})
$$

- Case 5: $FT_{3}<FT_{1}<FT_{2}$

In this scenario, $C_{3}$ finishes before $C_{1}$, and $C_{2}$ finishes last. Similar to Case 4, the builds for $C_{3}$ are unaffected by the build outcomes for $C_{1}$ and $C_{2}$, as $C_{3}$ completes first. However, unlike Case 4, $C_{2}$’s builds depend on the outcome of $C_{1}$’s builds, as $C_{1}$ finishes before $C_{2}$. As a result, the probabilities of the $C_{3}$ builds being needed remain the same as in Case 4, and the probabilities for $C_{2}$ builds remain the same as in Case 1.

### V-B Generalization

The principles outlined in the cases above can be generalized for multiple changes in the queue.

$$
P^{\text{needed}}_{B_{C}}=\prod_{C_{i}\in\mathcal{F}}P^{\text{outcome}}_{B_{C_{i}}}\times\prod_{C_{j}\in\mathcal{B}}P(FT_{C}<FT_{C_{j}})
$$

where:

- $P^{\text{needed}}_{B_{C}}$ represents the probability of a build being needed for a change $C$.

- $\mathcal{F}$ is the set of conflicting changes ahead of $C$ in the queue that $C$ does not bypass.

- $\mathcal{B}$ is the set of conflicting changes ahead that $C$ may bypass.

- $P^{\text{outcome}}_{B_{C_{i}}}$ represents the probability of the build outcome $B_{C_{i}}$ for change $C_{i}$ in $\mathcal{F}$. The estimation of this probability is explained in the prior study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)].

- $P(FT_{C}<FT_{C_{j}})$ represents the probability that the finish time of $C$ is less than the finish time of the change $C_{j}$ in $\mathcal{B}$, allowing $C$ to bypass $C_{j}$.

In extreme cases, when $\prod_{C_{j}\in\mathcal{B}}P(FT_{C}<FT_{C_{j}})\to 0$, which can occur as the speculation depth increases in the tree, the system defaults to the original probabilistic model, prioritizing the most likely build needed for the change, i.e.,

$$
P^{\text{needed}}_{B_{C}}=\prod_{C_{i}\in\mathcal{A}}P^{\text{outcome}}_{B_{C_{i}}}
$$

where $\mathcal{A}$ is the set of all changes ahead of $C$ in the queue. This ensures efficient build prioritization and resource usage while minimizing unnecessary scheduling.

## VI Evaluating BLRD Eligibility

BLRD may require an exponential number of builds to make a decision for a change, depending on its depth in the speculation tree, which can be computationally expensive. For example, in Figure 2, if the builds for $C_{2}$ finish after those for $C_{1}$, $C_{2}$ cannot bypass $C_{1}$ because $C_{1}$ would have already been accepted or rejected. In such cases, only one of $C_{2}$’s builds is necessary. To improve cost efficiency, BLRD builds are scheduled only when there is a high probability that the builds of a change will finish before those of preceding conflicting changes. In Figure [3](https://arxiv.org/html/2501.03440v2#S4.F3), if $P(FT_{2}<FT_{1})$ surpasses a predefined threshold, builds $B_{1,2}$ and $B_{2}$ for $C_{2}$ are prioritized equally, optimizing resource allocation and minimizing unnecessary builds. This threshold, determined from empirical builds data, balances the need to prioritize smaller changes while reducing the risk of scheduling unneeded builds.

## VII Estimating the Probability of Build Completion Ordering

Given two conflicting changes $C_{x}$ and $C_{y}$, arriving at times $AT_{x}$ and $AT_{y}$ ($AT_{x}<AT_{y}$), with respective finish times $FT_{x}$ and $FT_{y}$, and predicted build times $T_{x}$ and $T_{y}$, our goal is to estimate the probability that the build for $C_{y}$ will finish before the build for $C_{x}$, expressed as:

$$
P(FT_{y}<FT_{x})
$$

The predicted build times $T_{x}$ and $T_{y}$ can be approximated as normally distributed random variables. We use the NGBoost model [[15](https://arxiv.org/html/2501.03440v2#bib.bib15)], which is well-suited for probabilistic modeling, to predict build times. NGBoost learns patterns from historical builds to capture both the central tendency (mean) and variability (variance) in build times, smoothing out data irregularities and representing the predicted build times as a normal distribution. Thus,

$$
T_{x}\sim\mathcal{N}(\mu_{x},\sigma_{x}^{2}),\quad T_{y}\sim\mathcal{N}(\mu_{y},\sigma_{y}^{2})
$$

where $\mu_{x}$ and $\mu_{y}$ represent the combined mean build times, and $\sigma_{x}^{2}$ and $\sigma_{y}^{2}$ represent the combined variances of the builds for changes $C_{x}$ and $C_{y}$. The combined mean and variance are computed by averaging the individual builds’ means and variances. We seek to compute:

$$
P(FT_{y}<FT_{x})=P((T_{y}+AT_{y})<(T_{x}+AT_{x}))
$$

This expression can be rewritten as:

$$
P(T_{y}-T_{x}<AT_{x}-AT_{y})
$$

We aim to compute the probability that the difference in build times, $T_{y}-T_{x}$, is less than the difference in arrival times, $AT_{x}-AT_{y}$. The random variables $T_{x}$ and $T_{y}$ are normally distributed, so the difference $D=T_{y}-T_{x}$ is also normally distributed. The mean and variance of $D$ are given by:

$$
\mu_{D}=\mu_{y}-\mu_{x}
$$

$$
\sigma_{D}^{2}=\sigma_{x}^{2}+\sigma_{y}^{2}
$$

Thus, $D\sim\mathcal{N}(\mu_{D},\sigma_{D}^{2})$. The Z-score formula [[16](https://arxiv.org/html/2501.03440v2#bib.bib16)] is used to standardize this difference:

$$
Z=\frac{(AT_{x}-AT_{y})-(\mu_{y}-\mu_{x})}{\sqrt{\sigma_{x}^{2}+\sigma_{y}^{2}}}
$$

The Z-score measures how far the difference between arrival times is from the difference in build times, in standard deviations. Using the cumulative distribution function (CDF) of the standard normal distribution, the cumulative probability $\Phi(Z)$ gives the likelihood that $C_{y}$ finishes before $C_{x}$:

$$
P(FT_{y}<FT_{x})=\Phi(Z)
$$

where $\Phi(Z)$ represents the value of the CDF for the Z-score.

- Case 1: Close Arrival Times, Close Build Times

Request $C_{x}$ arrives at 10:00 AM ($AT_{x}=0$ minutes), with predicted build time $\mu_{x}=25$ minutes and $\sigma_{x}=5$ minutes. Request $C_{y}$ arrives at 10:05 AM ($AT_{y}=5$ minutes), with predicted build time $\mu_{y}=20$ minutes and $\sigma_{y}=4$ minutes. We compute the probability $P(FT_{y}<FT_{x})$ as follows:

$$
AT_{x}-AT_{y}=-5,\quad\mu_{y}-\mu_{x}=-5
$$

$$
\sigma_{D}^{2}=5^{2}+4^{2}=41,\quad\sigma_{D}=\sqrt{41}\approx 6.40
$$

$$
Z=\frac{-5-(-5)}{6.40}=0
$$

$P(FT_{y}<FT_{x})=\Phi(0)\approx 0.5$, meaning there is a 50% probability that $C_{y}$ finishes before $C_{x}$.

- Case 2: Large Difference in Arrival Times

Request $C_{x}$ arrives at 10:00 AM ($AT_{x}=0$ minutes), with predicted build time $\mu_{x}=20$ minutes and $\sigma_{x}=4$ minutes. Request $C_{y}$ arrives at 6:00 PM ($AT_{y}=480$ minutes), with predicted build time $\mu_{y}=5$ minutes and $\sigma_{y}=2$ minutes.

$$
AT_{x}-AT_{y}=0-480=-480,\quad\mu_{y}-\mu_{x}=5-20=-15
$$

$$
\sigma_{D}^{2}=4^{2}+2^{2}=16+4=20,\quad\sigma_{D}=\sqrt{20}\approx 4.47
$$

$$
Z=\frac{-480-(-15)}{4.47}=\frac{-465}{4.47}\approx-104.02
$$

Thus, $P(FT_{y}<FT_{x})=\Phi(-104.02)\approx 0$, meaning $C_{y}$ is almost certain to finish after $C_{x}$.

- Case 3: Small Arrival Time Difference, Large Build Time Difference

Request $C_{x}$ arrives at 10:00 AM ($AT_{x}=0$ minutes), with predicted build time $\mu_{x}=35$ minutes and $\sigma_{x}=6$ minutes. Request $C_{y}$ arrives at 10:01 AM ($AT_{y}=1$ minute), with predicted build time $\mu_{y}=15$ minutes and $\sigma_{y}=3$ minutes. The probability $P(FT_{y}<FT_{x})$ is computed as follows:

$$
AT_{x}-AT_{y}=0-1=-1,\quad\mu_{y}-\mu_{x}=15-35=-20
$$

$$
\sigma_{D}^{2}=6^{2}+3^{2}=36+9=45,\quad\sigma_{D}=\sqrt{45}\approx 6.71
$$

$$
Z=\frac{-1-(-20)}{6.71}=\frac{19}{6.71}\approx 2.83
$$

Thus, $P(FT_{y}<FT_{x})=\Phi(2.83)\approx 0.9977$, meaning there is a 99.77% probability that $C_{y}$ finishes before $C_{x}$.

## VIII Speculation Threshold

The prior study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)] did not address the implementation of a speculation threshold score for nodes in the speculation tree when selecting builds to schedule in CI. As a result, the system frequently scheduled more builds than necessary, including those with low $P^{\text{needed}}_{B_{C}}$ scores, which led to increased build cancellations and significant resource wastage.

Setting a minimum threshold of $P^{\text{needed}}_{B_{C}}$ can ensure that only the most probable nodes are selected for building. The threshold score should be informed by historical build data and adjusted based on the specific characteristics of the monorepos. However, setting the threshold too high can negatively impact land times, especially during high-load conditions. In such cases, more changes may be forced to wait for their builds, particularly if they conflict with larger changes ahead in the queue. Additionally, merely setting the speculation threshold could still leave smaller changes blocked by larger ones if the speculative builds of the smaller changes receive $P^{\text{needed}}_{B_{C}}$ score lesser than the threshold.

By leveraging the probabilistic model suggested in Section [V](https://arxiv.org/html/2501.03440v2#S5), the scores of speculative builds for smaller changes can be boosted if those changes are likely to bypass larger conflicting changes ahead. Thus, setting an appropriate speculation threshold, combined with the probabilistic model, strikes an optimal balance between resource usage and land times, ensuring efficient build scheduling without compromising throughput.

## IX Implementation

### IX-A Core Service

As outlined in the prior study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], SubmitQueue is built as a robust Java service, leveraging MySQL [[17](https://arxiv.org/html/2501.03440v2#bib.bib17)] for backend storage, Bazel [[18](https://arxiv.org/html/2501.03440v2#bib.bib18)] as a build system, Apache Helix [[19](https://arxiv.org/html/2501.03440v2#bib.bib19)] for efficient sharding of queues across multiple machines, and RxJava [[20](https://arxiv.org/html/2501.03440v2#bib.bib20)] for seamless event communication within processes. The introduction of BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)] and the incorporation of build-time prediction for build prioritization have fundamentally transformed SubmitQueue’s core algorithm. Previously, the system employed a greedy, best-first, depth-wise traversal strategy, where nodes with the highest scores were visited first, and land/reject decisions for changes were based on the outcome of a single node. With BLRD, results from multiple nodes are often required to allow smaller changes to bypass larger, conflicting changes ahead in the speculation tree. To accommodate this, we have shifted to a level-order traversal approach, which enables simultaneous exploration of multiple speculative nodes for a given change, ensuring that nodes eligible for BLRD are prioritized equally. The earlier method, relying on the outcome of a single node, proved insufficient for managing the complexities introduced by BLRD.

### IX-B Model Training

In our study, build refers to the compilation, testing, packaging, and publishing process triggered by code changes within a code repository. Each build encompasses multiple jobs that run concurrently to execute specific tasks, such as compiling different software components or executing various test suites. The parallel execution of jobs optimizes the overall build time, particularly for critical code changes that necessitate comprehensive testing.

As discussed in Section [VII](https://arxiv.org/html/2501.03440v2#S7), We trained our models separately for each monorepo using the NGBoost (NGB) Regressor [[15](https://arxiv.org/html/2501.03440v2#bib.bib15)] to predict build times and handle uncertainties. These models were trained on Uber’s native Machine Learning platform, Michelangelo [[21](https://arxiv.org/html/2501.03440v2#bib.bib21), [22](https://arxiv.org/html/2501.03440v2#bib.bib22)]. The model outputs the mean and the standard deviation for each prediction. The mean provides the expected build duration, while the standard deviation offers a measure of uncertainty around this prediction. This dual-output approach enables us to manage prediction variability effectively and make more informed decisions based on the predicted build times and their associated uncertainties.

The dataset used to train the models comprises historical builds processed by SubmitQueue over the last three months, with the models being retrained weekly. We used the same feature set mentioned in the prior study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], as these features are highly relevant and influential in predicting build times. Among all the features analyzed, the following have the highest influence on the model’s predictions, listed in order of their importance:

- Targets Changed: The number of targets modified in the change corresponding to the build.

- Targets Added: The number of new targets added in the change corresponding to the build.

- Targets Removed: The number of targets removed in the change corresponding to the build.

- Conflicts Count: The number of changes that the change corresponding to the build conflicts with.

- Speculation Height: The height of the node corresponding to the build in the speculation tree.

- Added Lines: The total number of new lines added in the change corresponding to the build.

- Removed Lines: The total number of lines removed in the change corresponding to the build.

- ChangeSet Count: The total number of files modified in the change corresponding to the build.

- Commits Count: The total number of commits in the change corresponding to the build.

- Developer Name: The author of the change corresponding to the build.

To train the model, the dataset was divided into training and validation sets, with 80% of the data allocated for training and the remaining 20% reserved for validation. This split ensures that the model is evaluated on unseen data, helping to assess its generalization capability and avoid overfitting.

To evaluate the performance of the NGB model, we used the Mean Absolute Percentage Error (MAPE) as the loss function. The MAPE is a metric that quantifies the average absolute errors as a percentage of the actual values, providing an intuitive understanding of the prediction error relative to the scale of the target variable. It is defined as:

$$
\text{MAPE}=\frac{1}{n}\sum_{i=1}^{n}\frac{\left|\hat{y}_{i}-y_{i}\right|}{y_{i}}\times 100\%
$$

where $n$ is the number of predictions, $\hat{y}_{i}$ is the predicted value, and $y_{i}$ is the actual value.

Our best-performing models across different monorepos yielded the following MAPE values: 3% for the Go monorepo, 6% for the iOS monorepo, and 3.5% for the Android monorepo. These results demonstrate that our model achieved high accuracy in predicting build times, with error rates generally falling below 5%. The use of MAPE as our evaluation metric allowed us to assess the model’s performance relative to the scale of the target values, ensuring that we could manage uncertainties effectively and make informed decisions based on the model’s predictions.

### IX-C Simulation System

Testing new strategies in SubmitQueue can be costly and may result in longer land times, negatively impacting developer productivity. To mitigate these challenges, we developed a simulation system that replicates production-level traffic for a given monorepo. This system enables us to evaluate the effectiveness of algorithms by reconstructing requests and build contexts from a specific period. By simulating the order in which requests enter the queue and applying different algorithms, we can analyze key metrics such as land times, speculation penalties, waiting times for small changes, and total resource utilization. A key difference between the simulation and production environments is that speculative builds for a change may not always precisely replicate those in production, due to variations in traffic, system load, or other environmental factors. To address this, we estimate the build times of those builds by computing the mean of available build times for that change in production. The simulator is a crucial evaluation tool, allowing us to test and refine new algorithms before deploying them to production, ensuring that any changes are effective and cost-efficient.

## X Evaluation

SubmitQueue has been in production at Uber since 2018, following the strategy outlined in a previous study [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)]. On July 22nd, 2024, we rolled out a new strategy across three of Uber’s largest monorepos—Go, iOS, and Android—which consist of hundreds of millions of lines of code and handle thousands of daily changes submitted by hundreds of developers. To evaluate the effectiveness of this strategy, we tracked key performance metrics—weekly CPU hours, build-to-changes ratio, and P95 waiting times—over a 21-week period, from May 13, 2024, to September 30, 2024, capturing both pre- and post-rollout data. While our evaluation focused on Uber’s monorepos, the techniques presented here are language-agnostic and platform-independent. The following subsections summarize the performance improvements observed for each metric across the Go, iOS, and Android monorepos.

### X-A Resource Usage

![figure-5-builds-per-change](assets/figures/figure-5-builds-per-change.png)

Fig. 5: Weekly trend of Builds-to-Changes ratio across Go, iOS, and Android monorepos.

The build-to-changes ratio is a critical metric for assessing resource efficiency in our CI pipeline. Figure [5](https://arxiv.org/html/2501.03440v2#S10.F5) illustrates the ratio trends over the 21-week evaluation period.

In the first 10 weeks, prior to the rollout, the ratio fluctuated between 3 and 6, with iOS and Android showing greater variability. The Android monorepo peaked at a ratio of 6 in Week 7, highlighting inefficiencies in resource utilization due to excessive builds per change.

After the rollout, a sharp decline in the ratio was observed across all monorepos. The Go monorepo saw a reduction of 45.45% (from a pre-rollout average of 3.39 to a post-rollout average of 1.85), iOS decreased by 47.86% (from 4.93 to 2.57), and Android achieved the largest reduction of 64.02%, dropping from 5.43 to 1.96. These results demonstrate improved resource allocation and more efficient build scheduling post-rollout.

### X-B CPU Hours Consumption

![figure-6-cpu-hours](assets/figures/figure-6-cpu-hours.png)

Fig. 6: Weekly CPU hours consumption across Go, iOS, and Android monorepos.

Figure [6](https://arxiv.org/html/2501.03440v2#S10.F6) shows the weekly CPU hours consumed across Go, iOS, and Android monorepos during the evaluation period.

Before the rollout, CPU usage was consistently high, particularly in the Go monorepo, which peaked at around 2,000 hours in Week 8. Android and iOS fluctuated between 500 and 800 hours and 400 to 600 hours, respectively.

Following the rollout, CPU hours dropped significantly across all monorepos. Go’s CPU consumption fell by 44.70% (from a pre-rollout average of 1,485 to a post-rollout average of 821 hours), iOS decreased by 34.86% (from 472 to 307 hours), and Android saw a reduction of 52.23% (from 729 to 348 hours). These reductions highlight the efficiency gains from minimizing unnecessary builds, leading to substantial cost savings and improved scalability.

### X-C P95 Waiting Times

![figure-7-p95-waiting-times](assets/figures/figure-7-p95-waiting-times.png)

Fig. 7: Weekly p95 Waiting Times for changes in Go, iOS, and Android monorepos.

CI resource usage is not the only metric to optimize in this work. Trivially, we can set the speculation threshold so high that SubmitQueue rarely speculates more than one path, which would reduce CI resource usage too. However, that would also reduce the efficiency of SubmitQueue, because BLRD, which requires multiple speculation paths, would not be used.
When the conditions for BLRD is not met, a change has to wait in SubmitQueue even though all its speculative builds finish. We monitor P95 waiting time before and after the rollout to make sure the reduction of resource usage does not reduce the efficiency. Figure [7](https://arxiv.org/html/2501.03440v2#S10.F7) illustrates the weekly P95 waiting times across the Go, iOS, and Android monorepos.

Initially, waiting times fluctuated significantly, with the Go monorepo showing peaks around weeks 5 and 10. After the new strategy was implemented in Week 11, all monorepos showed stabilization, particularly in iOS and Android, where waiting times consistently dropped to lower levels than pre-rollout. Go also demonstrated reduced variability, with more stable waiting times after Week 15.

Overall, the P95 waiting times were reduced by 44.67% for Go (from a pre-rollout average of 33.69 minutes to a post-rollout average of 18.64 minutes), 33.32% for iOS (from 14.86 minutes to 9.91 minutes), and 31.66% for Android (from 25.36 minutes to 17.33 minutes). This reduction signifies the impact of the new build prioritization strategy in expediting smaller changes landing using BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)].

## XI Related Work

### XI-A Prediction Systems in CI

BuildFast [[23](https://arxiv.org/html/2501.03440v2#bib.bib23)] and SmartBuildSkip [[11](https://arxiv.org/html/2501.03440v2#bib.bib11)] introduced systems for predicting build outcomes, while DL-CIBuild [[24](https://arxiv.org/html/2501.03440v2#bib.bib24)] used LSTM models to predict CI build failures, outperforming traditional methods. These approaches focus on predicting build outcomes rather than estimating when builds will be complete—a crucial factor in CI scheduling.

A study [[25](https://arxiv.org/html/2501.03440v2#bib.bib25)] predicted build times using the TravisTorrent dataset, with Random Forest [[26](https://arxiv.org/html/2501.03440v2#bib.bib26)] showing strong performance. We extended this by using NGBoost [[15](https://arxiv.org/html/2501.03440v2#bib.bib15)], which predicts both build times and their uncertainties, essential for handling variability in real-world CI. Our system integrates these predictions into an adaptive scheduling framework, optimizing resource allocation and reducing wait times, especially for smaller changes bypassing larger ones.

### XI-B CI Scheduling Algorithms

The study on scheduling algorithms for improved CI performance [[27](https://arxiv.org/html/2501.03440v2#bib.bib27)] demonstrated the advantages of leveraging expected processing times to improve scheduling decisions in CI environments. This study found that Shortest Processing Time (SPT) and Gupta’s algorithm [[28](https://arxiv.org/html/2501.03440v2#bib.bib28), [29](https://arxiv.org/html/2501.03440v2#bib.bib29)] significantly reduce wait times and improve system performance. Similarly, our use of NGBoost[[15](https://arxiv.org/html/2501.03440v2#bib.bib15)] not only predicts build times but also incorporates uncertainties, making it comparable to Gupta’s stochastic scheduling approach, which optimizes job uncertainty in dynamic environments. Both approaches highlight the importance of data-driven predictions in improving the efficiency of CI systems.

### XI-C Commutativity in Concurrent Systems

As demonstrated in BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)], the concept of commutativity in build operations parallels broader research on concurrent systems. A method for analyzing commutativity in concurrent programs using state-chart graph representations is presented in [[30](https://arxiv.org/html/2501.03440v2#bib.bib30)]. This work provides a formal framework for understanding when operations in a concurrent system can be safely reordered, which is conceptually similar to the commutativity property exploited by BLRD in the context of build systems.

## XII Limitations and Future Work

While our approach has significantly improved SubmitQueue, several areas for further exploration and enhancements exist. Future work could focus on:

Dynamic Speculation Thresholds: Dynamically adjusting scheduling thresholds for better resource management in speculative execution has been explored in various systems. For example, certain strategies focus on improving resource allocation by detecting task inefficiencies in real-time and minimizing unnecessary speculative tasks [[31](https://arxiv.org/html/2501.03440v2#bib.bib31)]. Similar adaptive scheduling techniques could benefit SubmitQueue, which currently uses static thresholds that may not align with real-time workload demands. Future work will explore dynamic strategies that adjust speculation thresholds based on the system’s current state to prevent inefficiencies.

Change Batching: While BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)] addresses the issue of post-build evaluation waiting, changes often face delays to begin build scheduling due to resource constraints. Recent research has explored various batching techniques to optimize this process. DynamicBatching [[32](https://arxiv.org/html/2501.03440v2#bib.bib32)] introduced a technique that adapts batch size based on the request traffic. Another approach [[33](https://arxiv.org/html/2501.03440v2#bib.bib33)] includes using weighted historical failure rates and mining historical test failures to inform batching decisions. SubmitQueue’s ability to predict build times and the likelihood of success can be further leveraged in accordance with these techniques. We can improve request throughput and optimize resource utilization by batching changes with a high probability of success and similar build durations.

## XIII Conclusion

In this paper, we introduced enhancements to SubmitQueue focused on optimizing resource usage and reducing waiting times for changes in large-scale development environments. While BLRD [[10](https://arxiv.org/html/2501.03440v2#bib.bib10)] partially addressed prolonged waiting times for changes with shorter build times, as discussed in [[9](https://arxiv.org/html/2501.03440v2#bib.bib9)], Our approach further enhances this by leveraging machine learning for build-time predictions and incorporating it into our novel probabilistic framework. These improvements tackle inefficiencies in resource consumption and delays caused by larger conflicting changes. Additionally, introducing a speculation threshold ensures that only the most probable builds are scheduled, further streamlining the process. These advancements position SubmitQueue as a highly efficient tool for managing software changes, adaptable to environments ranging from small teams to large enterprises. Adopting systems like SubmitQueue can lead to faster release cycles, reduced costs, and higher software quality, fostering more efficient industry-wide development practices. Future work will explore further optimization opportunities.

## Acknowledgment

The authors sincerely thank Chris Zhang and Akshay Utture from Uber’s Programming Systems Group for their valuable suggestions. We also appreciate the support of Shesh Patel, Matt Morgan, and Anshu Chadha, leaders of Uber’s Developer Platform, in bringing this project to fruition.

## References

- **[1]** Rachel Potvin and Josh Levenberg. Why google stores billions of lines of code in a single repository. Communications of the ACM , 59:78–87, 2016.

- **[2]** João Helis Bernardo, Daniel Alencar da Costa, and Uirá Kulesza. Studying the impact of adopting continuous integration on the delivery time of pull requests. In Proceedings of the 15th International Conference on Mining Software Repositories , MSR ’18, page 131–141, New York, NY, USA, 2018. Association for Computing Machinery.

- **[3]** Will Smythe and Lawrence Gripper. How github uses merge queue to ship hundreds of changes every day. <https://github.blog/engineering/engineering-principles/how-github-uses-merge-queue-to-ship-hundreds-of-changes-every-day/> , March 2024.

- **[4]** Veethika Mishra. How to use merge train pipelines with gitlab. <https://about.gitlab.com/blog/2020/12/14/merge-trains-explained/> , December 2020.

- **[5]** Niket Parikh. How linkedin handles merging code in high-velocity repositories. <https://www.linkedin.com/blog/engineering/optimization/continuous-integration/> , April 2020.

- **[6]** Janusz Kudelka and Joel Snyder. Evergreen: Building airbnb’s merge queue with kafka streams. <https://www.confluent.io/events/kafka-summit-london-2022/evergreen-building-airbnbs-merge-queue-with-kafka-streams/> , April 2022.

- **[7]** Ankit Jain. Merge strategies to keep builds healthy at scale. <https://www.aviator.co/blog/merge-strategies-at-scale/> , September 2023.

- **[8]** Trunk. Trunk - the fast lane for your prs. <https://trunk.io/> , 2024.

- **[9]** Sundaram Ananthanarayanan, Masoud Saeida Ardekani, Denis Haenikel, Balaji Varadarajan, Simon Soriano, Dhaval Patel, and Ali-Reza Adl-Tabatabai. Keeping master green at scale. In Proceedings of the Fourteenth EuroSys Conference 2019 , New York, NY, USA, 2019. Association for Computing Machinery.

- **[10]** Zhongpeng Lin and Matthew Williams. Bypassing large diffs in submitqueue. <https://www.uber.com/blog/bypassing-large-diffs-in-submitqueue/> , August 2023.

- **[11]** Xianhao Jin and Francisco Servant. A cost-efficient approach to building in continuous integration. In Proceedings of the ACM/IEEE 42nd International Conference on Software Engineering , ICSE ’20, page 13–25, New York, NY, USA, 2020. Association for Computing Machinery.

- **[12]** N. Forsgren, J. Humble, and G. Kim. Accelerate: The Science of Lean Software and DevOps: Building and Scaling High Performing Technology Organizations . IT Revolution Press, 2018.

- **[13]** Yang Hong, Chakkrit Tantithamthavorn, Jirat Pasuksmit, Patanamon Thongtanunam, Arik Friedman, Xing Zhao, and Anton Krasikov. Practitioners’ challenges and perceptions of ci build failure predictions at atlassian, 06 2024.

- **[14]** Foyzur Rahman and Premkumar Devanbu. How, and why, process metrics are better. In Proceedings of the 2013 International Conference on Software Engineering , ICSE ’13, page 432–441. IEEE Press, 2013.

- **[15]** Tony Duan, Anand Avati, Daisy Yi Ding, Khanh K. Thai, Sanjay Basu, Andrew Y. Ng, and Alejandro Schuler. Ngboost: Natural gradient boosting for probabilistic prediction. In Proceedings of the 37th International Conference on Machine Learning , ICML ’20, page 2690–2700. JMLR.org, 2020.

- **[16]** Stephanie Glen. Z-score: Definition, formula and calculation, 2024.

- **[17]** MySQL AB. Mysql: The world’s most popular open source database, 2024.

- **[18]** Google. Bazel - a fast, scalable, multi-language and extensible build system. <https://bazel.build/> , 2024.

- **[19]** Apache Software Foundation. Apache helix, 2024.

- **[20]** ReactiveX. Rxjava: Reactive extensions for the jvm. <https://github.com/ReactiveX/RxJava> , 2022.

- **[21]** Kai Wang, Mingshi Cai, Jingya Wang, and Eric Chen. From predictive to generative - how michelangelo accelerates uber’s ai journey. <https://www.uber.com/blog/from-predictive-to-generative-ai/> , 5 2024.

- **[22]** Jeremy Hermann and Mike Del Balso. Meet michelangelo: Uber’s machine learning platform. <https://www.uber.com/blog/michelangelo-machine-learning-platform/> , 2017. Accessed: October 4, 2024.

- **[23]** Bihuan Chen, Linlin Chen, Chen Zhang, and Xin Peng. Buildfast: History-aware build outcome prediction for fast feedback and reduced cost in continuous integration. In 2020 35th IEEE/ACM International Conference on Automated Software Engineering (ASE) , pages 42–53, 2020.

- **[24]** Islem Saidani, Ali Ouni, and Mohamed Wiem Mkaouer. Improving the prediction of continuous integration build failures using deep learning. Automated Software Engg. , 29(1), May 2022.

- **[25]** Ekaba Bisong, Eric Tran, and Olga Baysal. Built to last or built too fast? evaluating prediction models for build times. In 2017 IEEE/ACM 14th International Conference on Mining Software Repositories (MSR) . IEEE, May 2017.

- **[26]** Leo Breiman. Random forests. Machine Learning , 45(1):5–32, 2001.

- **[27]** Zacharias Faleberg Nilsson and Freddy Abrahamsson. Scheduling algorithms for improved ci performance. Master’s thesis, Chalmers University of Technology and University of Gothenburg, Gothenburg, Sweden, June 2023. Department of Computer Science and Engineering.

- **[28]** Varun Gupta, Benjamin Moseley, Marc Uetz, and Qiaomin Xie. Stochastic online scheduling on unrelated machines. CoRR , abs/1703.01634, 2017.

- **[29]** Varun Gupta, Benjamin Moseley, Marc Uetz, and Qiaomin Xie. Corrigendum: Greed works—online algorithms for unrelated machine stochastic scheduling. Math. Oper. Res. , 46(3):1230–1234, August 2021.

- **[30]** Kishore Debnath, Christina Peterson, and Damian Dechev. Analysis of commutativity with state-chart graph representation of concurrent programs, 2019.

- **[31]** Yinghang Jiang, Qi Liu, Williams Dannah, Dandan Jin, Xiaodong Liu, and Mingxu Sun. An optimized resource scheduling strategy for hadoop speculative execution based on non-cooperative game schemes, 2020.

- **[32]** Emad Fallahzadeh, Amir Hossein Bavand, and Peter C. Rigby. Accelerating continuous integration with parallel batch testing. In Proceedings of the 31st ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering , ESEC/FSE 2023, page 55–67, New York, NY, USA, 2023. Association for Computing Machinery.

- **[33]** Amir Hossein Bavand and Peter C. Rigby. Mining historical test failures to dynamically batch tests to save ci resources. In 2021 IEEE International Conference on Software Maintenance and Evolution (ICSME) , pages 217–226, 2021.
