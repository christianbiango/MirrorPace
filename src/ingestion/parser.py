from pathlib import Path

from src.domain.activity import Activity
from src.ingestion.fit_parser import parse_fit
from src.ingestion.gpx_parser import parse_gpx

_PARSERS = {
    ".fit": parse_fit,
    ".gpx": parse_gpx,
}

SUPPORTED_EXTENSIONS = set(_PARSERS.keys())


def _resolve(file_path: Path):
    """Return the parser function for a file, handling .gz transparently."""
    suffix = file_path.suffix.lower()
    if suffix == ".gz":
        inner_suffix = Path(file_path.stem).suffix.lower()
        return _PARSERS.get(inner_suffix)
    return _PARSERS.get(suffix)


def is_activity_file(file_path: Path) -> bool:
    return _resolve(file_path) is not None


def parse(file_path: Path | str) -> Activity:
    file_path = Path(file_path)
    parser_fn = _resolve(file_path)
    if parser_fn is None:
        raise ValueError(f"Unsupported format: {file_path.name!r}. Supported: {list(_PARSERS)}")
    return parser_fn(file_path)
