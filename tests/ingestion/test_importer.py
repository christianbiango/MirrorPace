import shutil
from pathlib import Path

import pytest

from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.ingestion.importer import ImportResult, import_directory

FIT_FILE = Path("data/raw/strava/export_151936996_strava/activities/20398531112.fit.gz")
GPX_FILE = Path("data/raw/strava/export_151936996_strava/activities/18286260719.gpx.gz")


@pytest.fixture
def repo():
    engine = build_engine("sqlite:///:memory:")
    session = build_session(engine)
    return ActivityRepository(session)


@pytest.fixture
def sample_dir(tmp_path) -> Path:
    """Isolated directory with exactly 2 known activity files."""
    shutil.copy(FIT_FILE, tmp_path / FIT_FILE.name)
    shutil.copy(GPX_FILE, tmp_path / GPX_FILE.name)
    return tmp_path


class TestImportDirectory:
    def test_imports_all_files(self, repo, sample_dir):
        result = import_directory(sample_dir, repo)
        assert len(result.imported) == 2
        assert len(result.errors) == 0

    def test_skips_already_imported(self, repo, sample_dir):
        import_directory(sample_dir, repo)
        result = import_directory(sample_dir, repo)
        assert len(result.skipped) == 2
        assert len(result.imported) == 0

    def test_activities_persisted_in_db(self, repo, sample_dir):
        import_directory(sample_dir, repo)
        assert len(repo.get_all()) == 2

    def test_empty_directory(self, repo, tmp_path):
        result = import_directory(tmp_path, repo)
        assert result.total == 0

    def test_on_event_callback_called(self, repo, sample_dir):
        events = []
        import_directory(sample_dir, repo, on_event=lambda s, f, d: events.append(s))
        assert events.count("imported") == 2

    def test_error_captured_without_crashing(self, repo, tmp_path):
        bad_file = tmp_path / "broken.fit"
        bad_file.write_bytes(b"not a fit file")
        result = import_directory(tmp_path, repo)
        assert len(result.errors) == 1
        assert bad_file in result.errors


class TestImportResult:
    def test_summary_format(self):
        result = ImportResult(
            imported=[Path("a.fit"), Path("b.fit")],
            skipped=[Path("c.fit")],
            errors={Path("d.fit"): "oops"},
        )
        assert result.summary() == "Summary: 2 imported, 1 skipped, 1 error(s)"

    def test_total(self):
        result = ImportResult(
            imported=[Path("a.fit")],
            skipped=[Path("b.fit")],
            errors={Path("c.fit"): "oops"},
        )
        assert result.total == 3
