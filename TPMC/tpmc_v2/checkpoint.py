from __future__ import annotations

from pathlib import Path
import json
import time
from typing import Any

from tpmc_v2.case_schema import TPMCCase


class CheckpointStore:
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _case_file(self, case_id: str) -> Path:
        return self.root_dir / f"{case_id}.json"

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

    def load(self, case_id: str) -> dict[str, Any] | None:
        path = self._case_file(case_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def status(self, case_id: str) -> str | None:
        data = self.load(case_id)
        if data is None:
            return None
        return data.get("status")

    def is_done(self, case_id: str) -> bool:
        return self.status(case_id) == "done"

    def mark_running(self, case: TPMCCase) -> None:
        payload = {
            "case_id": case.case_id,
            "case_name": case.name,
            "status": "running",
            "updated_at": time.time(),
            "case": case.to_payload(),
        }
        self._atomic_write_json(self._case_file(case.case_id), payload)

    def mark_done(
        self,
        case: TPMCCase,
        result_json_path: str | None = None,
        result_csv_path: str | None = None,
    ) -> None:
        payload = {
            "case_id": case.case_id,
            "case_name": case.name,
            "status": "done",
            "updated_at": time.time(),
            "result_json_path": result_json_path,
            "result_csv_path": result_csv_path,
            "case": case.to_payload(),
        }
        self._atomic_write_json(self._case_file(case.case_id), payload)

    def mark_failed(self, case: TPMCCase, error_message: str) -> None:
        payload = {
            "case_id": case.case_id,
            "case_name": case.name,
            "status": "failed",
            "updated_at": time.time(),
            "error": error_message,
            "case": case.to_payload(),
        }
        self._atomic_write_json(self._case_file(case.case_id), payload)