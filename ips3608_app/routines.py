from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .models import RoutineDefinition, RoutineStep


class RoutineRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def _backup_path(self, suffix: str = "") -> Path:
        backup_dir = self.file_path.parent / "backup" / "v1"
        backup_dir.mkdir(parents=True, exist_ok=True)
        tag = f"_{suffix}" if suffix else ""
        return backup_dir / f"{self.file_path.stem}{tag}_{time.strftime('%Y%m%d_%H%M%S')}.json"

    def _write_json_atomic(self, payload: object) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.file_path)

    def load_all(self) -> list[RoutineDefinition]:
        if not self.file_path.exists():
            return []
        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        # Migrazione automatica: se è una lista, convertila in oggetto versionato
        if isinstance(raw, list):
            # Backup vecchio formato
            self._backup_path("legacy").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            raw = {"version": 2, "routines": raw}
            # Aggiorna file
            self._write_json_atomic(raw)
        if not isinstance(raw, dict):
            return []
        routines = raw.get("routines", [])
        out: list[RoutineDefinition] = []
        for item in routines:
            steps = [RoutineStep(**step) for step in item.get("steps", [])]
            out.append(
                RoutineDefinition(
                    name=item["name"],
                    steps=steps,
                    stop_output_on_finish=bool(item.get("stop_output_on_finish", True)),
                    execution_limit_s=float(item.get("execution_limit_s", 0.0)),
                )
            )
        return out

    def save_all(self, routines: list[RoutineDefinition]) -> None:
        if self.file_path.exists():
            self._backup_path().write_text(self.file_path.read_text(encoding="utf-8"), encoding="utf-8")
        serializable = {
            "version": 2,
            "routines": [asdict(r) for r in routines]
        }
        self._write_json_atomic(serializable)


class ActiveRoutineRunner:
    def __init__(self, routine: RoutineDefinition):
        self.routine = routine
        self.started_mono = time.monotonic()
        self.completed = False

    def elapsed_s(self) -> float:
        return max(0.0, time.monotonic() - self.started_mono)

    def current_setpoints(self) -> Optional[tuple[float, float]]:
        if self.completed:
            return None

        elapsed = self.elapsed_s()
        limit = self.routine.execution_limit_s
        if limit > 0.0 and elapsed >= limit:
            self.completed = True
            return None

        acc = 0.0
        for step in self.routine.steps:
            dur = max(0.0, step.duration_s)
            end = acc + dur
            if elapsed <= end:
                if dur <= 0.0:
                    return step.voltage_end_v, step.current_end_a
                alpha = (elapsed - acc) / dur
                alpha = min(1.0, max(0.0, alpha))
                v = step.voltage_start_v + alpha * (step.voltage_end_v - step.voltage_start_v)
                i = step.current_start_a + alpha * (step.current_end_a - step.current_start_a)
                return v, i
            acc = end

        self.completed = True
        return None
