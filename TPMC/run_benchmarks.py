from __future__ import annotations

from tpmc_v2.case_manager import BatchCaseManager
from tpmc_v2.benchmarks import build_cube_benchmark_suite


def main():
    suite = build_cube_benchmark_suite()
    cases = [b.case for b in suite]

    print("=== Benchmark Suite ===")
    for b in suite:
        print(f"{b.key}: {b.description}")

    manager = BatchCaseManager(work_dir="runs_benchmarks")

    results = manager.run(
        cases=cases,
        max_workers=4,
        resume=True,
    )

    print()
    print(f"Benchmark run finished. New completed cases: {len(results)}")


if __name__ == "__main__":
    main()