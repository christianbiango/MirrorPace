"""Knowledge Engine — Coach Marathon IA V1.

Implements KB_CANONICAL v1.2 + v1.3 (Red Team patch) + v1.3.1 (clarifications)
+ v1.3.2 (experience_level_source exposed in DecisionEnvelope)
+ v1.3.3 (PlanHint.reason exposed)
+ v1.3.4 (taper_duration_weeks 3 -> 2)
+ v1.3.5 (RULE-027 — specific/taper structuring in a short race window).
Source of truth: docs/knowledge_engine/KB_IMPLEMENTATION_CONTRACT_V1.md.
"""

ENGINE_VERSION = "1.3.5"
SCHEMA_VERSION = "1.3.5"
