from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkTarget:
    """Target metric threshold for a clinical benchmark suite."""

    metric: str
    threshold: float
    higher_is_better: bool = True


CHEXPERT_BENCHMARK_TARGETS = {
    "macro_auc": BenchmarkTarget(metric="macro_auc", threshold=0.75),
    "macro_sensitivity": BenchmarkTarget(metric="macro_sensitivity", threshold=0.70),
    "macro_specificity": BenchmarkTarget(metric="macro_specificity", threshold=0.70),
}


def compare_to_chexpert_benchmarks(
    metrics: dict,
    targets: dict[str, BenchmarkTarget] | None = None,
) -> dict:
    """Compare model evaluation metrics to the project CheXpert targets.

    The repo cannot ship CheXpert labels/images, so final evaluation is split
    into two steps: compute metrics from mounted CheXpert data, then run this
    comparison to produce pass/fail benchmark status.
    """

    active_targets = targets or CHEXPERT_BENCHMARK_TARGETS
    results = {}
    all_passed = True

    for name, target in active_targets.items():
        value = float(metrics.get(name, 0.0))
        passed = value >= target.threshold if target.higher_is_better else value <= target.threshold
        all_passed = all_passed and passed
        results[name] = {
            "value": value,
            "threshold": target.threshold,
            "passed": passed,
        }

    return {
        "suite": "CheXpert clinical benchmark",
        "passed": all_passed,
        "targets": results,
    }


def summarize_chexpert_benchmark(comparison: dict) -> str:
    status = "PASS" if comparison["passed"] else "NEEDS IMPROVEMENT"
    lines = [f"{comparison['suite']}: {status}"]
    for metric, result in comparison["targets"].items():
        lines.append(
            f"- {metric}: {result['value']:.3f} "
            f"(target {result['threshold']:.3f})"
        )
    return "\n".join(lines)
