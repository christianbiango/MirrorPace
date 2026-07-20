from pathlib import Path

from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.ingestion.parser import parse

engine = build_engine()
session = build_session(engine)
repo = ActivityRepository(session)

files = [
    Path("data/raw/strava/fit/20398531112.fit"),
    Path("data/raw/strava/gpx/18286260719.gpx"),
]

for f in files:
    if repo.exists(f):
        print(f"Skipped (already imported): {f.name}")
    else:
        activity = parse(f)
        repo.save(activity)
        print(f"Imported: {f.name}")
