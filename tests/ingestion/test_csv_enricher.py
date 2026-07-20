import io
from pathlib import Path

import pytest

from src.domain.activity import Activity, ActivityMetrics
from src.ingestion.csv_enricher import ActivityEnrichment, apply_enrichment, load_enrichments

CSV_PATH = Path("data/raw/strava/export_151936996/activities.csv")

_MINIMAL_CSV = """\
ID de l'activité,Date de l'activité,Nom de l'activité,Type d'activité,Description de l'activité,Temps écoulé,Distance,Fréquence cardiaque max.,Effort relatif,Déplacement-transport,Note privée sur les activités,Matériel utilisé pour l'activité,Nom du fichier,Poids de l'athlète,Poids du vélo,Temps écoulé,Durée de déplacement,Distance,Vitesse max.,Vitesse moyenne,Dénivelé positif
1,date,nom,Course à pied,desc,3600,10,,,false,,,activities/run.fit.gz,,,,,,,,45.5
2,date,nom,Vélo,desc,7200,30,,,false,,,activities/ride.gpx.gz,,,,,,,,120.0
3,date,nom,Inconnu,desc,1800,5,,,false,,,activities/unknown.fit.gz,,,,,,,,
"""


@pytest.fixture
def minimal_csv(tmp_path) -> Path:
    path = tmp_path / "activities.csv"
    path.write_text(_MINIMAL_CSV)
    return path


class TestLoadEnrichments:
    def test_returns_dict_keyed_by_filename(self, minimal_csv):
        enrichments = load_enrichments(minimal_csv)
        assert "run.fit.gz" in enrichments
        assert "ride.gpx.gz" in enrichments

    def test_maps_french_sport_type(self, minimal_csv):
        enrichments = load_enrichments(minimal_csv)
        assert enrichments["run.fit.gz"].sport_type == "running"
        assert enrichments["ride.gpx.gz"].sport_type == "cycling"

    def test_unknown_sport_type_is_none(self, minimal_csv):
        enrichments = load_enrichments(minimal_csv)
        assert enrichments["unknown.fit.gz"].sport_type is None

    def test_elevation_gain_parsed(self, minimal_csv):
        enrichments = load_enrichments(minimal_csv)
        assert enrichments["run.fit.gz"].elevation_gain_m == 45.5

    def test_missing_elevation_is_none(self, minimal_csv):
        enrichments = load_enrichments(minimal_csv)
        assert enrichments["unknown.fit.gz"].elevation_gain_m is None

    def test_real_csv_loads_all_activities(self):
        if not CSV_PATH.exists():
            pytest.skip("Strava export not present locally")
        enrichments = load_enrichments(CSV_PATH)
        assert len(enrichments) == 39


class TestApplyEnrichment:
    def _make_activity(self, sport_type=None, elevation_gain_m=None) -> Activity:
        return Activity(
            source_file=Path("run.gpx.gz"),
            source_type="GPX",
            date=None,
            sport_type=sport_type,
            metrics=ActivityMetrics(
                distance_m=5000.0,
                duration_s=1800.0,
                elevation_gain_m=elevation_gain_m,
            ),
        )

    def test_fills_missing_sport_type(self):
        activity = self._make_activity(sport_type=None)
        apply_enrichment(activity, ActivityEnrichment(sport_type="running"))
        assert activity.sport_type == "running"

    def test_does_not_overwrite_existing_sport_type(self):
        activity = self._make_activity(sport_type="cycling")
        apply_enrichment(activity, ActivityEnrichment(sport_type="running"))
        assert activity.sport_type == "cycling"

    def test_fills_missing_elevation(self):
        activity = self._make_activity(elevation_gain_m=None)
        apply_enrichment(activity, ActivityEnrichment(elevation_gain_m=50.0))
        assert activity.metrics.elevation_gain_m == 50.0

    def test_does_not_overwrite_existing_elevation(self):
        activity = self._make_activity(elevation_gain_m=30.0)
        apply_enrichment(activity, ActivityEnrichment(elevation_gain_m=50.0))
        assert activity.metrics.elevation_gain_m == 30.0
