from pathlib import Path
from src.ingestion.parser import parse

fit = parse(Path("data/raw/strava/fit/20398531112.fit"))
gpx = parse(Path("data/raw/strava/gpx/18286260719.gpx"))
print("FIT:", fit)
print("GPX:", gpx)
