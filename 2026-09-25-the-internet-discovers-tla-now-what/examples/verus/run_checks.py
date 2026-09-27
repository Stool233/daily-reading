#!/usr/bin/env python3
"""Verify three examples, run their binaries, and check five deliberate mistakes."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Mutation must match exactly once: " + old)
    return source.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verus", default=shutil.which("verus"))
    parser.add_argument("--results", type=Path, default=ROOT / "results.json")
    args = parser.parse_args()
    if not args.verus:
        parser.error("Pass --verus /absolute/path/to/verus")
    verus = str(Path(args.verus).expanduser().resolve())
    env = dict(os.environ)
    rustup_dir = Path.home() / ".cargo" / "bin"
    if not shutil.which("rustup") and (rustup_dir / "rustup").is_file():
        env["PATH"] = str(rustup_dir) + os.pathsep + env.get("PATH", "")
    version = subprocess.check_output(
        [verus, "--version"], env=env, text=True, stderr=subprocess.STDOUT, timeout=30
    ).strip()
    sources = {name: (ROOT / (name + ".rs")).read_text()
               for name in ("clamp", "count_nonzero", "quota")}
    cases = [(name, source, "verified_and_ran", None)
             for name, source in sources.items()]
    cases.extend([
        ("clamp_wrong_branch", replace_once(
            sources["clamp"],
            "let r = if x < lo { lo } else if x > hi { hi } else { x };",
            "let r = if x < lo { lo } else if x > hi { lo } else { x };",
        ), "rejected", "postcondition not satisfied"),
        ("clamp_bad_caller", replace_once(
            sources["clamp"], "clamp_value(15, 3, 10)", "clamp_value(15, 10, 3)"
        ), "rejected", "precondition not satisfied"),
        ("count_wrong_predicate", replace_once(
            sources["count_nonzero"], "if values[i] != 0 {", "if values[i] == 0 {"
        ), "rejected", "invariant not satisfied"),
        ("quota_add_before_guard", replace_once(
            sources["quota"], "if amount <= self.limit - self.used {",
            "if self.used + amount <= self.limit {"
        ), "rejected", "possible arithmetic underflow/overflow"),
        ("ghost_value_in_exec", """use vstd::prelude::*;
verus! {
    spec fn ghost_identity(x: u32) -> u32 { x }
    fn bad(x: u32) -> u32 { ghost_identity(x) }
    fn main() {}
}
""", "rejected", "with mode spec"),
    ])

    def run(case):
        name, source, expected, diagnostic = case
        with tempfile.TemporaryDirectory(prefix="verus-reading-") as directory:
            folder = Path(directory)
            file = folder / (name + ".rs")
            file.write_text(source)
            binary = folder / name
            command = [verus, str(file)]
            if expected == "verified_and_ran":
                command += ["--compile", "-o", str(binary)]
            check = subprocess.run(
                command, cwd=folder, env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60
            )
            output = check.stdout.replace(directory, "<case-dir>")
            summary = re.search(r"verification results:: (\d+) verified, (\d+) errors", output)
            result = {
                "name": name, "source_sha256": sha256(source),
                "expected": expected, "verifier_exit": check.returncode,
                "diagnostic_expected": diagnostic, "verifier_output": output,
            }
            if summary:
                result["verification_summary"] = {
                    "verified": int(summary.group(1)), "errors": int(summary.group(2))
                }
            if expected == "verified_and_ran" and check.returncode == 0 and summary:
                execution = subprocess.run(
                    [str(binary)], cwd=folder, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=10
                )
                result["runtime_exit"] = execution.returncode
                result["runtime_output"] = execution.stdout
                ok = execution.returncode == 0 and int(summary.group(2)) == 0
            else:
                ok = expected == "rejected" and check.returncode != 0 and diagnostic in output
            result["matched_expectation"] = ok
            return result

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, cases))
    for result in results:
        print(result["name"] + ": " + str(result["matched_expectation"]))
        if not result["matched_expectation"]:
            print(result["verifier_output"])
    if not all(result["matched_expectation"] for result in results):
        raise SystemExit("At least one experiment differed from its expected outcome")
    report = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "verus_version": version,
        "sources_sha256": {name + ".rs": sha256(source) for name, source in sources.items()},
        "scope": "Verus checks the code inside verus!; ordinary Rust main harnesses are compiled and run, not verified. Mutants are temporary and never executed.",
        "cases": results,
    }
    args.results.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Recorded:", args.results)


if __name__ == "__main__":
    main()
