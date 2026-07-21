"""Load RunnerProfile from a YAML config file.

For a single-athlete project a flat YAML file is the right tradeoff:
human-readable, version-controllable, no DB migration needed.

Expected path: data/runner_profile.yaml
Schema mirrors RunnerProfile exactly; unknown keys are ignored.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.knowledge_engine.domain.schemas.runner_state import RunnerProfile

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "runner_profile.yaml"


class RunnerProfileStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path else _DEFAULT_PATH

    def load(self) -> tuple[str, RunnerProfile]:
        """Return (runner_id, RunnerProfile) from the YAML file."""
        with self._path.open(encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh) or {}

        runner_id: str = str(raw.get("runner_id", "default"))

        profile = RunnerProfile(
            age=int(raw["age"]),
            experience_level_declared=str(raw.get("experience_level_declared", "intermediate")),
            sessions_per_week_available=int(raw.get("sessions_per_week_available", 4)),
            sex=str(raw.get("sex", "unspecified")),
            pathologies_connues=list(raw.get("pathologies_connues") or []),
            recent_race_time_10k=_opt_int(raw.get("recent_race_time_10k")),
            recent_race_time_half=_opt_int(raw.get("recent_race_time_half")),
            recent_race_time_marathon=_opt_int(raw.get("recent_race_time_marathon")),
            VMA_kmh=_opt_float(raw.get("VMA_kmh")),
            race_target_time=_opt_int(raw.get("race_target_time")),
            race_target_date=raw.get("race_target_date"),
            years_running=_opt_float(raw.get("years_running")),
        )
        return runner_id, profile

    def exists(self) -> bool:
        return self._path.exists()


def _opt_int(v) -> int | None:
    return int(v) if v is not None else None


def _opt_float(v) -> float | None:
    return float(v) if v is not None else None
