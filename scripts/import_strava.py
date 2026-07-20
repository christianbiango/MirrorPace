from pathlib import Path

from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.ingestion.importer import import_directory

STRAVA_DIR = Path("data/raw/strava/export_151936996/activities")


def on_event(status: str, file: Path, detail: str) -> None:
    icons = {"imported": "✓", "skipped": "–", "error": "✗"}
    icon = icons.get(status, "?")
    print(f"  {icon}  {status:<10} {file.name:<45} {detail}")


def main() -> None:
    if not STRAVA_DIR.exists():
        print(f"Directory not found: {STRAVA_DIR}")
        return

    engine = build_engine()
    session = build_session(engine)
    repo = ActivityRepository(session)

    print(f"Importing from {STRAVA_DIR} ...\n")
    result = import_directory(STRAVA_DIR, repo, on_event=on_event)

    print(f"\n{result.summary()}")

    if result.errors:
        print("\nErrors:")
        for file, msg in result.errors.items():
            print(f"  {file.name}: {msg}")


if __name__ == "__main__":
    main()
