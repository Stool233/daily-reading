# Verus 三种模式实验

先读[中文讲解](../../verus-study.md)，再按顺序打开：

| 文件 | 内容 |
| --- | --- |
| [clamp.rs](clamp.rs) | 数学规格、自动证明引理、可执行限幅及调用方契约 |
| [count_nonzero.rs](count_nonzero.rs) | `Seq` 规格、递归归纳证明、`Vec` 循环与不变量 |
| [quota.rs](quota.rs) | 抽象状态转换、可变引用、配额不变量与防溢出 |
| [run_checks.py](run_checks.py) | 三组正确程序和五组错误变体的验证脚本 |
| [results.json](results.json) | 实测诊断、运行输出、工具版本与源码哈希 |

所有 Rust 示例均为本次独立编写。`verus!` 里的函数接受验证，宏外的 `main` 是未验证的普通 Rust 运行检查入口。调用方样例使用满足前置条件的输入；这些入口不是公共 API 输入校验方案。

## 工具版本

本次使用官方 [Verus 0.2026.09.20.aef82ed 发布包](https://github.com/verus-lang/verus/releases/tag/release/0.2026.09.20.aef82ed)，目标平台为 macOS ARM64，配套 Rust 为 `1.98.1-aarch64-apple-darwin`。

下载的 ARM64 macOS 压缩包 SHA-256 已与 GitHub 发布资产的 digest 核对：

```text
3f89fd250d1e9792ed6d0c7c3ad72c03c02fdbca3f0638987af6e153d69377bc
```

安装方法见[官方说明](https://github.com/verus-lang/verus/blob/release/0.2026.09.20.aef82ed/INSTALL.md)。不同平台选择对应发布包；Rust 版本以发布包要求为准。仓库不包含工具二进制。

## 复现

在本目录执行：

```sh
python3 run_checks.py --verus /absolute/path/to/verus
```

脚本需要 Python 3 和已经安装的 Verus / Rust 工具链。若 `rustup` 不在 PATH 中，会尝试使用当前用户的 `~/.cargo/bin`；不会安装依赖或修改默认工具链。每项实验使用独立临时目录，最多同时运行三项；验证限时 60 秒，运行限时 10 秒。

单独验证、编译一个文件：

```sh
/absolute/path/to/verus clamp.rs --compile -o /tmp/verus-clamp
/tmp/verus-clamp
```

本次机器上可用的验证器是 `/Users/apple/.cache/daily-reading/verus/0.2026.09.20.aef82ed/verus-arm64-macos/verus`。准备实验时新增了指定版本的 Rust 工具链，原来的默认工具链保持不变。

## 如何读结果

三份正确程序应验证成功、编译成功，并通过运行检查。验证器的正常输出分别为 `3 verified, 0 errors`、`4 verified, 0 errors` 和 `4 verified, 0 errors`。

五份错误变体分别改错限幅分支、传反边界参数、颠倒非零判断、在配额检查前先加法，以及尝试从执行模式调用规格函数。脚本要求它们以非零状态退出，并包含对应错误诊断；错误变体不会执行。

只有八项实验都符合预期时，脚本才更新 `results.json`。这个文件中的失败诊断是设计好的教学结果，不是归档工作未完成；它们也不是 TLC 那样的状态轨迹反例。源码哈希包含正确程序，以及每份临时错误程序的准确内容。

没有使用未经证明的假设或跳过函数体检查来使核心例子通过。验证结论仍然以规格、调用前提及工具和标准库的可信部分为基础；详细讨论见[中文讲解](../../verus-study.md)。
