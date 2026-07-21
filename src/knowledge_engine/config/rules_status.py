"""Per-rule activation flags — KB v1.2 §4.1 (`rules_status.yaml`)."""

from __future__ import annotations

from types import MappingProxyType

_STATUS: dict[str, bool] = {
    # P0
    "RULE-001": True,
    "RULE-002": True,
    "RULE-003": True,
    # P1
    "RULE-004": True,
    "RULE-005": True,
    "RULE-006": True,
    "RULE-007": True,
    "RULE-026": True,
    # P2
    "RULE-008": True,
    "RULE-009": True,
    "RULE-010": True,
    # P3
    "RULE-011": True,
    "RULE-012": True,
    "RULE-013": False,  # disabled_v1 — needs performance_trend (CONF-008)
    "RULE-014": False,  # disabled_v1 — needs zone_distribution (CONF-010)
    # P4
    "RULE-015": True,
    "RULE-016": True,
    "RULE-017": False,  # disabled_v1 — depends on D-05 (mapping table)
    "RULE-018": True,
    "RULE-019": True,
    "RULE-020": True,
    "RULE-021": True,
    "RULE-022": True,
    "RULE-023": True,
    "RULE-024": False,  # V2 — ambient temperature
    "RULE-025": True,
}

RULES_STATUS = MappingProxyType(_STATUS)
