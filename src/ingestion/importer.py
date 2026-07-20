from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from src.database.repository import ActivityRepository
from src.domain.activity import Activity
from src.ingestion.csv_enricher import ActivityEnrichment, apply_enrichment
from src.ingestion.parser import parse, is_activity_file


@dataclass
class ImportResult:
    imported: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    errors: dict[Path, str] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.imported) + len(self.skipped) + len(self.errors)

    def summary(self) -> str:
        return (
            f"Summary: {len(self.imported)} imported, "
            f"{len(self.skipped)} skipped, "
            f"{len(self.errors)} error(s)"
        )


def import_directory(
    directory: Path,
    repo: ActivityRepository,
    enrichments: dict[str, ActivityEnrichment] | None = None,
    on_event: Callable[[str, Path, str], None] | None = None,
) -> ImportResult:
    result = ImportResult()
    files = sorted(
        f for f in directory.rglob("*") if f.is_file() and is_activity_file(f)
    )

    for file in files:
        if repo.exists(file):
            result.skipped.append(file)
            if on_event:
                on_event("skipped", file, "already in DB")
            continue

        try:
            activity = parse(file)
            if enrichments and file.name in enrichments:
                apply_enrichment(activity, enrichments[file.name])
            repo.save(activity)
            result.imported.append(file)
            if on_event:
                on_event("imported", file, _activity_label(activity))
        except Exception as e:
            result.errors[file] = str(e)
            if on_event:
                on_event("error", file, str(e))

    return result


def _activity_label(activity: Activity) -> str:
    parts = []
    if activity.sport_type:
        parts.append(activity.sport_type)
    if activity.metrics and activity.metrics.distance_m:
        parts.append(f"{activity.metrics.distance_m / 1000:.1f}km")
    if activity.date:
        parts.append(activity.date.strftime("%Y-%m-%d"))
    return "  ".join(parts) if parts else "no metadata"
