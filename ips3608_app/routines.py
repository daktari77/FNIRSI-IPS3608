from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .models import RoutineDefinition, RoutineRuntimeInfo, RoutineState, RoutineStep


class RoutineRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    _MAX_BACKUPS = 10

    def _backup_path(self, suffix: str = "") -> Path:
        backup_dir = self.file_path.parent / "backup" / "v1"
        backup_dir.mkdir(parents=True, exist_ok=True)
        tag = f"_{suffix}" if suffix else ""
        return backup_dir / f"{self.file_path.stem}{tag}_{time.strftime('%Y%m%d_%H%M%S')}.json"

    def _rotate_backups(self) -> None:
        """Delete oldest backup files, retaining at most _MAX_BACKUPS."""
        backup_dir = self.file_path.parent / "backup" / "v1"
        if not backup_dir.exists():
            return
        stem = self.file_path.stem
        files = sorted(
            (f for f in backup_dir.iterdir() if f.name.startswith(stem) and f.suffix == ".json"),
            key=lambda f: f.stat().st_mtime,
        )
        for old in files[: -self._MAX_BACKUPS]:
            try:
                old.unlink()
            except Exception:
                pass

    def _write_json_atomic(self, payload: object) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.file_path)

    @staticmethod
    def _load_step(s: dict) -> RoutineStep:
        if "voltage_start_v" in s:
            # v2 ramp format → migrate: use end values as constant setpoint
            return RoutineStep(
                voltage_v=float(s.get("voltage_end_v", s.get("voltage_start_v", 0.0))),
                current_a=float(s.get("current_end_a", s.get("current_start_a", 0.0))),
                duration_s=float(s.get("duration_s", 10.0)),
            )
        return RoutineStep(
            voltage_v=float(s.get("voltage_v", 0.0)),
            current_a=float(s.get("current_a", 0.0)),
            duration_s=float(s.get("duration_s", 10.0)),
            output_on=bool(s.get("output_on", True)),
            otp_limit_c=float(s.get("otp_limit_c", 0.0)),
            settle_ms=float(s.get("settle_ms", 200.0)),
            name=str(s.get("name", "")),
        )

    def load_all(self) -> list[RoutineDefinition]:
        if not self.file_path.exists():
            return []
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[RoutineRepository] Failed to load {self.file_path}: {exc}", file=sys.stderr)
            return []

        # Migrazione: lista grezza → dict versionato
        if isinstance(raw, list):
            self._backup_path("legacy").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            raw = {"version": 2, "routines": raw}
            self._write_json_atomic(raw)

        if not isinstance(raw, dict):
            return []

        routines_raw = raw.get("routines", [])
        out: list[RoutineDefinition] = []
        migrated = False

        for item in routines_raw:
            steps = []
            for s in item.get("steps", []):
                step = self._load_step(s)
                if "voltage_start_v" in s:
                    migrated = True
                steps.append(step)

            out.append(RoutineDefinition(
                name=item["name"],
                steps=steps,
                loops=int(item.get("loops", 1)),
                stop_output_on_finish=bool(item.get("stop_output_on_finish", True)),
                execution_limit_s=float(item.get("execution_limit_s", 0.0)),
            ))

        if migrated:
            self._backup_path("v2_ramp").write_text(
                self.file_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            self._write_json_atomic({"version": 3, "routines": [asdict(r) for r in out]})

        return out

    def save_all(self, routines: list[RoutineDefinition]) -> None:
        if self.file_path.exists():
            self._backup_path().write_text(self.file_path.read_text(encoding="utf-8"), encoding="utf-8")
        self._write_json_atomic({"version": 3, "routines": [asdict(r) for r in routines]})
        self._rotate_backups()


class ActiveRoutineRunner:
    """State machine that drives a RoutineDefinition in real time."""

    def __init__(self, routine: RoutineDefinition):
        self.routine = routine
        self.state: str = RoutineState.IDLE
        self._start_mono: float = 0.0
        self._pause_mono: float = 0.0
        self._paused_total_s: float = 0.0
        self._stop_reason: str = ""

    # ------------------------------------------------------------------ lifecycle

    def start(self) -> None:
        self._start_mono = time.monotonic()
        self._paused_total_s = 0.0
        self.state = RoutineState.RUNNING

    def pause(self) -> None:
        if self.state == RoutineState.RUNNING:
            self._pause_mono = time.monotonic()
            self.state = RoutineState.PAUSED

    def resume(self) -> None:
        if self.state == RoutineState.PAUSED:
            self._paused_total_s += time.monotonic() - self._pause_mono
            self.state = RoutineState.RUNNING

    def abort(self, reason: str = "user") -> None:
        self._stop_reason = reason
        self.state = RoutineState.ABORTED

    # ------------------------------------------------------------------ time

    def elapsed_s(self) -> float:
        if self.state == RoutineState.PAUSED:
            return self._pause_mono - self._start_mono - self._paused_total_s
        return time.monotonic() - self._start_mono - self._paused_total_s

    # ------------------------------------------------------------------ tick

    def tick(self) -> Optional[tuple[float, float, bool]]:
        """Return (voltage_v, current_a, output_on) for the current position.

        Returns None when paused, completed, or aborted.
        Transitions state to COMPLETED automatically when the last loop ends.
        """
        if self.state != RoutineState.RUNNING:
            return None

        step_total = self.routine.total_step_duration_s
        if step_total <= 0.0:
            self.state = RoutineState.COMPLETED
            return None

        elapsed = self.elapsed_s()
        loops = self.routine.loops

        if loops > 0 and elapsed >= step_total * loops:
            self.state = RoutineState.COMPLETED
            return None

        loop_elapsed = elapsed % step_total

        acc = 0.0
        for step in self.routine.steps:
            dur = max(0.0, step.duration_s)
            if loop_elapsed < acc + dur:
                return step.voltage_v, step.current_a, step.output_on
            acc += dur

        # Edge case: floating point overshoot on the last step
        if loops > 0:
            self.state = RoutineState.COMPLETED
        return None

    # ------------------------------------------------------------------ info

    def runtime_info(self) -> RoutineRuntimeInfo:
        elapsed = self.elapsed_s()
        step_total = self.routine.total_step_duration_s
        loops = self.routine.loops
        steps = self.routine.steps

        if step_total <= 0.0 or not steps:
            return RoutineRuntimeInfo(
                state=self.state, loop=0, total_loops=loops,
                step=0, step_name="", total_steps=len(steps),
                elapsed_step_s=0.0, elapsed_total_s=elapsed, remaining_step_s=0.0,
            )

        current_loop = int(elapsed / step_total) if step_total > 0 else 0
        if loops > 0:
            current_loop = min(current_loop, loops - 1)
        loop_elapsed = elapsed % step_total

        step_start = 0.0
        current_step_idx = len(steps) - 1
        current_step = steps[-1]
        for i, step in enumerate(steps):
            end = step_start + max(0.0, step.duration_s)
            if loop_elapsed < end:
                current_step_idx = i
                current_step = step
                break
            step_start = end

        elapsed_step = max(0.0, loop_elapsed - step_start)
        remaining_step = max(0.0, current_step.duration_s - elapsed_step)

        return RoutineRuntimeInfo(
            state=self.state,
            loop=current_loop,
            total_loops=loops,
            step=current_step_idx,
            step_name=current_step.name,
            total_steps=len(steps),
            elapsed_step_s=elapsed_step,
            elapsed_total_s=elapsed,
            remaining_step_s=remaining_step,
        )
