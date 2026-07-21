"""KB v1.3.1 C-13 — normative tests for `min_restrictive`."""

import pytest

from src.knowledge_engine.engine.severity import SEVERITY_ORDER, min_restrictive


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("increase", "maintain", "maintain"),
        ("slight_increase", "maintain", "maintain"),
        ("maintain", "maintain", "maintain"),
        ("decrease", "maintain", "decrease"),
        ("deload", "maintain", "deload"),
        ("deload", "decrease", "deload"),
        ("slight_increase", "increase", "slight_increase"),
        ("maintain", "increase", "maintain"),
    ],
)
def test_table(a, b, expected):
    assert min_restrictive(a, b) == expected


def test_commutativity():
    actions = ["deload", "decrease", "maintain", "slight_increase", "increase"]
    for a in actions:
        for b in actions:
            assert min_restrictive(a, b) == min_restrictive(b, a)


def test_gf06_never_loosens_a_restricted_decision():
    """Property : min_restrictive(x, "maintain") stays ≥ "maintain" in severity."""
    for action in ["deload", "decrease", "maintain"]:
        result = min_restrictive(action, "maintain")
        assert SEVERITY_ORDER[result] >= SEVERITY_ORDER["maintain"]
