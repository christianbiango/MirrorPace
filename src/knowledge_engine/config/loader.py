"""Config container with deterministic hash — KB v1.2 §4.4 rule 5."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .rules_status import RULES_STATUS
from .thresholds import default_thresholds


@dataclass(frozen=True)
class EngineConfig:
    """Immutable configuration snapshot used by a single engine run.

    `config_hash` is a sha256 over the sorted JSON of thresholds+rules_status.
    It appears in every DecisionEnvelope (GF-05 traceability).
    """

    thresholds: dict[str, Any]
    rules_status: dict[str, bool]
    config_hash: str = field(init=False)

    def __post_init__(self) -> None:
        payload = json.dumps(
            {"thresholds": self.thresholds, "rules_status": self.rules_status},
            sort_keys=True,
            default=str,
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        object.__setattr__(self, "config_hash", digest)

    def get(self, key: str) -> Any:
        return self.thresholds[key]

    def is_rule_active(self, rule_id: str) -> bool:
        return self.rules_status.get(rule_id, False)


def load_default_config() -> EngineConfig:
    return EngineConfig(
        thresholds=default_thresholds(),
        rules_status=dict(RULES_STATUS),
    )
