"""KB v1.3.1 C-12 — normative tests for `compute_fatigue_trend`."""

from src.knowledge_engine.domain.formulas.fatigue_trend import compute_fatigue_trend


def test_empty_history():
    assert compute_fatigue_trend([]) == "unknown"


def test_none_history():
    assert compute_fatigue_trend(None) == "unknown"


def test_single_entry():
    assert compute_fatigue_trend([3]) == "unknown"


def test_two_entries_improving():
    # index 0 = newest (2), index -1 = oldest (4) → fatigue dropped
    assert compute_fatigue_trend([2, 4]) == "improving"


def test_two_entries_worsening():
    assert compute_fatigue_trend([4, 2]) == "worsening"


def test_two_entries_stable():
    assert compute_fatigue_trend([3, 3]) == "stable"


def test_four_entries_stable():
    assert compute_fatigue_trend([3, 3, 3, 3]) == "stable"


def test_four_entries_improving_middle_noise():
    # [0]=2 < [-1]=4  → improving despite noise
    assert compute_fatigue_trend([2, 5, 3, 4]) == "improving"


def test_four_entries_worsening_middle_noise():
    assert compute_fatigue_trend([4, 2, 3, 1]) == "worsening"
