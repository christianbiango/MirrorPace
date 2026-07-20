from pathlib import Path

from src.domain.activity import Activity
from src.ingestion.fit_parser import parse_fit
from src.ingestion.gpx_parser import parse_gpx

_PARSERS = {
    ".fit": parse_fit,
    ".gpx": parse_gpx,
}


def parse(file_path: Path | str) -> Activity:
    file_path = Path(file_path)
    parser_fn = _PARSERS.get(file_path.suffix.lower())
    if parser_fn is None:
        raise ValueError(f"Unsupported format: {file_path.suffix!r}. Supported: {list(_PARSERS)}")
    return parser_fn(file_path)
