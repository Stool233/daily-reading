# 从限幅理解 Verus：函数式规格、谓词和实现

> 补充讨论：2026-09-28。承接 [Verus 三种模式研究](verus-study.md)。
>
> 本文的限幅定义、逻辑改写和证明实验为独立讲解。[完整程序](examples/verus/clamp_logic.rs)已通过 Verus 检查、编译与运行，结果为 `5 verified, 0 errors`；[运行记录](examples/verus/clamp-logic-results.json)。

`spec fn` 使用熟悉的函数语法来定义数学对象。它可以返回一个值，也可以返回一个真假命题。`clamp_spec(...)` 返回整数，因而看起来像计算；当它出现在 `r == clamp_spec(...)` 或 `lo <= clamp_spec(...) <= hi` 中时，就组成了需要证明的逻辑公式。

函数、值表达式和谓词本来就可以共同组成逻辑语言。Verus 将这些概念嵌入 Rust 的语法和类型体系，并以纯数学方式解释规格代码。[官方设计概述](https://verus-lang.github.io/verus/guide/overview.html)、[规格表达式语法](https://verus-lang.github.io/verus/guide/spec-expressions.html)

## 限幅具体要求什么

设允许区间为 `[3, 10]`：

| 输入 | 输出 | 原因 |
| --- | --- | --- |
| `1` | `3` | 太小，取下界 |
| `3` | `3` | 已在区间内，保持原值 |
| `7` | `7` | 已在区间内，保持原值 |
| `10` | `10` | 已在区间内，保持原值 |
| `15` | `10` | 太大，取上界 |

前置条件 `lo <= hi` 保证区间合法，也允许两端相等。如果只要求结果在区间内，始终返回 `lo` 也能满足条件；完整的限幅还需要表达“区间内保留输入，区间外贴到相应边界”。

这个完整要求可以写成一个分段数学函数。在 `lo <= hi` 时，它就是 `min(max(x, lo), hi)`。原例子的 `if` 表达式是同一个分段定义的另一种写法：

```rust
spec fn clamp_spec(x: int, lo: int, hi: int) -> int {
    if x < lo { lo } else if x > hi { hi } else { x }
}
```

把它理解成数学映射 `ℤ³ → ℤ`：给定三个整数，表达式确定一个整数值。这里的 `if` 选择表达式的值；规格不会因此在运行时更新变量、产生 I/O 或执行一次实际的限幅操作。Verus 将 `spec` 限制为纯函数式数学代码，`int` 也属于规格使用的无界数学整数。[规格函数说明](https://verus-lang.github.io/verus/guide/spec_functions.html)

这个定义对 `lo > hi` 也有一个由分支决定的值，但我们没有把那个值当作合法区间的限幅语义。业务前提写在使用它的实现契约和定理中。`spec fn` 本身不采用 `requires` / `ensures`；其可选 `recommends` 也不能替代必须证明的调用前提。[spec 与 proof 的差别](https://verus-lang.github.io/verus/guide/spec_vs_proof.html)

## 换成谓词写法，逻辑结构就显露出来了

也可以完全不定义“输出值是多少”的函数，而定义“这一组输入和输出是否合法”的关系：

```rust
spec fn is_clamped(x: int, lo: int, hi: int, r: int) -> bool {
    lo <= hi
        && (x < lo ==> r == lo)
        && (lo <= x && x <= hi ==> r == x)
        && (x > hi ==> r == hi)
}
```

`&&` 是逻辑合取，`==>` 是蕴含。每一行都在说一个条件成立时，输出必须满足什么。三个输入范围在合法区间上覆盖所有情况，所以这个谓词唯一确定了结果。

两种写法的对应关系是：

```text
在 lo <= hi 的前提下，对任意 x、r：

is_clamped(x, lo, hi, r)  ⇔  r = clamp_spec(x, lo, hi)
```

这条等价性已经在补充程序的 `lemma_forms_agree` 中验证。等式右边通过一个函数值约束结果，左边通过一组逻辑条件约束结果；本例中它们表达同一要求。实现的后置条件可以采用任一种，也可以如补充程序一样同时写出两者。

关系式写法还可以允许多个结果。例如，如果需求只是“返回区间内任意值”，`lo <= r && r <= hi` 就足够。限幅需求更精确，因此需要上述三个条件。规格应当有多强，取决于要承诺什么行为。

## Verus 的量词在哪里

Verus 直接支持 `forall` 和 `exists`。下面分别表达结果存在，以及结果唯一；它们都出现在已验证例子的 `lemma_exists_unique` 中，并以 `lo <= hi` 为前提：

```rust
exists|r: int| is_clamped(x, lo, hi, r)

forall|a: int, b: int|
    is_clamped(x, lo, hi, a) && is_clamped(x, lo, hi, b) ==> a == b
```

量词没有要求运行程序枚举无穷多个整数。它们属于交给证明工具处理的数学公式；复杂量词公式可能需要提供合适的证明步骤或实例化提示。[量词说明](https://verus-lang.github.io/verus/guide/quants.html)

原来的引理虽然没显式写 `forall`，其参数也不是某一组测试数据：

```rust
proof fn lemma_clamp_bounds(x: int, lo: int, hi: int)
    requires lo <= hi,
    ensures lo <= clamp_spec(x, lo, hi) <= hi,
{ }
```

它需要对任意满足前提的参数成立。对应的数学命题是：对所有整数 `x, lo, hi`，如果 `lo <= hi`，那么限幅结果位于区间内。补充程序的 `lemma_all_bounds` 又把这条性质写成了显式的 `forall`，并通过验证。

## 为什么空的证明体能够通过

这个引理只需要分三种情况讨论：

| 分支事实 | 根据定义得到 | 还需证明的界限 |
| --- | --- | --- |
| `x < lo` | 结果为 `lo` | 已知 `lo <= hi` |
| `x >= lo` 且 `x > hi` | 结果为 `hi` | 已知 `lo <= hi` |
| `x >= lo` 且 `x <= hi` | 结果为 `x` | 分支事实已给出两侧界限 |

这些布尔条件与整数比较足够简单，自动求解器能够处理，因此不需要手写证明步骤。这里的空函数体仍然负有建立后置条件的义务，不是把结论作为未经证明的公理。

Verus 的设计目标之一是生成适合 SMT 求解器处理的验证条件。对于本例，可以用下面的条件项理解 `if` 的逻辑含义：

```text
clamp_spec(x, lo, hi) = ite(x < lo, lo, ite(x > hi, hi, x))
```

`ite` 意为“条件为真选前一个值，否则选后一个值”。这只是本例的语义示意，不是截取的 Verus 内部输出。验证界限性质时，可以理解为检查“已知前提成立，但结论为假”的逻辑条件能否同时成立；无需抽取有限输入来代表所有情况。[验证条件与 SMT 的设计目标](https://verus-lang.github.io/verus/guide/overview.html)

## 规格与实现不需要长得一样

第一个教学例子的规格和实现都很短，采用了相同的分支结构。那有助于展示三种模式，但容易给人“把代码抄一次就叫规格”的印象。补充程序保留原规格，改用两次依次修正来实现：

```rust
let mut r = x;
if r < lo {
    r = lo;
}
if r > hi {
    r = hi;
}
r
```

这个函数的契约同时要求 `is_clamped(...)` 成立，以及结果等于 `clamp_spec(...)`。Verus 已证明这两个要求；检查依据是实现的语义和逻辑关系，源码无需逐字相同。

规格可以比实现更直接地表达需求：递归定义可以对应循环，数学序列可以对应 `Vec`，输入输出关系可以对应复杂分支。选用数学函数还是谓词，应服务于需求表达和后续证明，而不必刻意追求某种符号外观。

不过，把同一处业务误解同时写进规格与实现，验证器也无法凭空恢复真正的需求。我们特意加入了 `only_bounds`：它始终返回下界，契约只要求结果落在区间内。它通过了验证，但对输入 `7`、区间 `[3, 10]` 返回 `3`，与完整限幅的结果 `7` 不同。这是规格强度的区别，不是求解器失误。

## 对应到 TLA+ 会怎样

TLA+ 也可以先定义一个返回数值的操作符。下面是对本例的独立改写：

```tla
Clamp(x, lo, hi) ==
    IF x < lo THEN lo
    ELSE IF x > hi THEN hi
    ELSE x
```

如果要表达一次状态转换，可以再把值表达式放进动作关系中。假设状态变量是 `x, lo, hi, r`：

```tla
ClampStep ==
    /\ lo <= hi
    /\ r' = Clamp(x, lo, hi)
    /\ UNCHANGED <<x, lo, hi>>
```

前一个操作符定义值，后一个动作约束当前状态与下一状态之间的关系。`r' = ...` 是关于下一状态的等式。TLA+ 的 `IF/THEN/ELSE` 同样是条件表达式，动作则是关于一对状态的布尔表达式。[Lamport，第 16.1.4 与 16.2.3 节](https://lamport.azurewebsites.net/tla/book-21-07-04.pdf)

这些 TLA+ 片段用于对照记法，没有组成并运行一个新的 TLC 模型。要讨论系统的所有行为，还需加入初始化、下一步关系及时序性质。我们当前讨论的是一次限幅操作，所以 Verus 的函数契约与 TLA+ 的局部动作关系比较接近；把单个 `spec fn` 与完整时序规格比较，会把不同层面的东西放在一起。

## 设计取舍与本次检查范围

Verus 一方面复用 Rust 的表达式、数据类型和类型检查，让规格容易引用代码中的结构；另一方面，规格仍按纯数学语言组织，保留函数、逻辑连接词和量词，并尽量靠近 SMT 易于处理的形式。这种设计同时考虑了 Rust 开发者的使用方式与自动证明的效率。[官方概述](https://verus-lang.github.io/verus/guide/overview.html)

本次检查了函数与谓词的等价性、结果存在且唯一、显式全称界限、不同结构的实现，以及弱契约的例子。程序没有加入 `assume` 或跳过证明的标记。宏外 `main` 只是普通 Rust 的运行检查入口；本实验没有证明验证器本身、Verus 到 SMT 的翻译或新的系统时序性质。
