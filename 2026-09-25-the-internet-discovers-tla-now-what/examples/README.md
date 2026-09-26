# TLA+ 阅读实验

这是为阅读文章独立编写的工作任务模型，不是原文的选主模型。状态只有 `ready`、`running`、`done`，另用 `started` 记录是否启动过。

## 文件

- [WorkerProgress.tla](WorkerProgress.tla)：模型与性质。
- [run_checks.py](run_checks.py)：并行运行七组配置，并核对是否得到预期的通过或反例。
- [results.json](results.json)：实测结果、反例摘录、工具版本和输入文件哈希。
- [publisher-checks.json](publisher-checks.json)：另行执行的原文选主模型检查记录。
- [中文导读](../translation.zh.md)：结果对照表。
- [讨论笔记](../notes.md)：反例和归纳说明。

## 运行

需要 Python 3、可运行当前 TLC 的 Java，以及已有的 `tla2tools.jar`。在本目录执行，并替换 jar 路径：

```sh
python3 run_checks.py --tlc-jar /absolute/path/to/tla2tools.jar
```

若 `java` 不在可用路径中，可用 `--java /absolute/path/to/java` 指定。脚本不会安装依赖；它为每次检查创建独立临时目录，并在七组结果符合预期后更新 `results.json`。TLC 每组运行限时 30 秒。

本次使用 TLC `2026.03.19.000345 (rev: 30a4862)`、OpenJDK `26.0.1`，单 worker。未关闭死锁检查；模型显式允许 `Wait` 自循环。

## 如何判断实验成功

| 配置 | 预期结果 |
| --- | --- |
| [SafetyOnly.cfg](SafetyOnly.cfg) | 通过 |
| [NoFairness.cfg](NoFairness.cfg) | 活性反例 |
| [WeakFairness.cfg](WeakFairness.cfg) | 通过 |
| [BlockedSafety.cfg](BlockedSafety.cfg) | 通过 |
| [BlockedProgress.cfg](BlockedProgress.cfg) | 活性反例 |
| [NotInductive.cfg](NotInductive.cfg) | 不变量反例 |
| [Strengthened.cfg](Strengthened.cfg) | 通过 |

运行脚本成功，表示这些预期结果全部出现，不表示七个模型配置的所有性质都通过。`NotInductive` 和 `Strengthened` 使用了不同于正常任务的初始条件；它们讨论的是不变量保持性。

这些是固定有限模型的检查。未在本实验中验证真实任务队列、Rust 实现或文章提到的证明生成系统。

## 原文选主模型的补充核对

从[作者交互页](https://reasonable.io/figures/tla-playground)取得其公开的 `Election` 规格后，在临时目录原样运行。两组都使用 `N = 3`、`Typo = FALSE`、`Staggered = FALSE`、`SPECIFICATION Spec`，检查 `TypeOK` 与 `AtMostOneLeader`；区别在于 `DoubleVote` 分别为 `FALSE` 和 `TRUE`。

这两组单独设置 `CHECK_DEADLOCK FALSE`，因为选主后的终止状态本身不违反所检查的安全不变量。正常配置完成检查，有 38 个不同状态；重复投票配置产生 7 状态、6 动作的反例。后者发现反例就停止，不能据已发现状态数推断完整规模。

结果和提取后规格的哈希保存在 [publisher-checks.json](publisher-checks.json)。作者的规格仅用于临时检查，未随归档复制；`run_checks.py` 只负责本地自编模型的七组检查，不会下载或重跑作者模型。
