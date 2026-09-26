"""Reproduce the reading experiments; expected counterexamples count as success."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


CASES = [
    ("SafetyOnly", "pass"),
    ("NoFairness", "temporal_violation"),
    ("WeakFairness", "pass"),
    ("BlockedSafety", "pass"),
    ("BlockedProgress", "temporal_violation"),
    ("NotInductive", "invariant_violation"),
    ("Strengthened", "pass"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", default="java")
    parser.add_argument("--tlc-jar", type=Path, required=True)
    args = parser.parse_args()
    jar = args.tlc_jar.resolve(strict=True)
    base = Path(__file__).resolve().parent

    def run(case):
        name, expected = case
        with tempfile.TemporaryDirectory(prefix="reading-tlc-") as tmp:
            command = [
                args.java, "-Xmx128m", "-XX:+UseParallelGC", "-cp", str(jar),
                "tlc2.TLC", "-workers", "1", "-seed", "1", "-fp", "0",
                "-noGenerateSpecTE", "-metadir", tmp,
                "-config", name + ".cfg", "WorkerProgress.tla",
            ]
            proc = subprocess.run(
                command, cwd=base, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=30,
            )
        output = proc.stdout.replace(str(base) + "/", "")
        if proc.returncode == 0 and "No error has been found." in output:
            observed = "pass"
        elif proc.returncode != 0 and "Temporal properties were violated." in output:
            observed = "temporal_violation"
        elif proc.returncode != 0 and re.search(r"Invariant \w+ is violated", output):
            observed = "invariant_violation"
        else:
            observed = "unexpected_error"
        if observed != expected:
            raise RuntimeError(name + " did not produce the expected result:\n" + output)
        counts = re.findall(
            r"([\d,]+) states generated, ([\d,]+) distinct states found", output
        )
        if not counts:
            raise RuntimeError("Missing state counts for " + name)
        excerpt = [
            line for line in output.splitlines()
            if not line.startswith("Progress(") and re.search(
                r"TLC2 Version|Error:|State \d+|phase =|started =|Stuttering|"
                r"states generated|No error", line
            )
        ]
        return {
            "config": name + ".cfg", "expected": expected, "observed": observed,
            "exit_code": proc.returncode,
            "generated_states": int(counts[-1][0].replace(",", "")),
            "distinct_states": int(counts[-1][1].replace(",", "")),
            "output_excerpt": excerpt,
        }

    with ThreadPoolExecutor(max_workers=3) as pool:
        runs = list(pool.map(run, CASES))
    version = subprocess.run(
        [args.java, "-version"], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True,
    ).stdout.splitlines()[0]
    inputs = [base / "WorkerProgress.tla", *(base / (n + ".cfg") for n, _ in CASES)]
    report = {
        "checked": date.today().isoformat(),
        "model": "WorkerProgress.tla",
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        "tool_jar_sha256": hashlib.sha256(jar.read_bytes()).hexdigest(),
        "tlc_build": next(line for line in runs[0]["output_excerpt"] if line.startswith("TLC2")),
        "java_version": version,
        "runs": runs,
    }
    (base / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for run in runs:
        print(f"{run['config']}: {run['observed']}; {run['distinct_states']} distinct states")


if __name__ == "__main__":
    main()
