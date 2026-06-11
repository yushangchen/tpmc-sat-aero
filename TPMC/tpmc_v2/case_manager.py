from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import csv
import json
import traceback

from tpmc_v2.case_schema import TPMCCase
from tpmc_v2.checkpoint import CheckpointStore
from tpmc_v2.solver_adapter import solve_case


def _worker(case_payload: dict) -> dict:
    case = TPMCCase(**case_payload)
    return solve_case(case)


class BatchCaseManager:
    def __init__(self, work_dir: str | Path = "runs_v2"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.result_json_dir = self.work_dir / "case_results"
        self.result_json_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoints = CheckpointStore(self.work_dir / "checkpoints")
        self.result_csv_path = self.work_dir / "batch_results.csv"

    def _result_json_path(self, case: TPMCCase) -> Path:
        return self.result_json_dir / f"{case.case_id}.json"

    def _save_result_json(self, case: TPMCCase, result: dict) -> Path:
        path = self._result_json_path(case)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return path

    def _append_result_csv(self, result: dict) -> None:
        file_exists = self.result_csv_path.exists()
        fieldnames = list(result.keys())

        with open(self.result_csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)

    def _run_one_case(self, case: TPMCCase) -> dict:
        self.checkpoints.mark_running(case)
        result = solve_case(case)
        result_json_path = self._save_result_json(case, result)
        self._append_result_csv(result)
        self.checkpoints.mark_done(
            case,
            result_json_path=str(result_json_path),
            result_csv_path=str(self.result_csv_path),
        )
        return result

    def run(
        self,
        cases: list[TPMCCase],
        max_workers: int = 1,
        resume: bool = True,
    ) -> list[dict]:
        pending_cases: list[TPMCCase] = []

        for case in cases:
            if resume and self.checkpoints.is_done(case.case_id):
                continue
            pending_cases.append(case)

        if not pending_cases:
            print("No pending cases. All requested cases are already completed.")
            return []

        results: list[dict] = []

        if max_workers <= 1:
            for case in pending_cases:
                try:
                    result = self._run_one_case(case)
                    results.append(result)
                    print(f"[DONE] {case.name}")
                except Exception as e:
                    self.checkpoints.mark_failed(case, f"{type(e).__name__}: {e}")
                    print(f"[FAIL] {case.name}: {e}")
            return results

        future_to_case = {}

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for case in pending_cases:
                self.checkpoints.mark_running(case)
                future = executor.submit(_worker, case.to_payload())
                future_to_case[future] = case

            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    result_json_path = self._save_result_json(case, result)
                    self._append_result_csv(result)
                    self.checkpoints.mark_done(
                        case,
                        result_json_path=str(result_json_path),
                        result_csv_path=str(self.result_csv_path),
                    )
                    results.append(result)
                    print(f"[DONE] {case.name}")
                except Exception as e:
                    err = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
                    self.checkpoints.mark_failed(case, err)
                    print(f"[FAIL] {case.name}: {e}")

        return results