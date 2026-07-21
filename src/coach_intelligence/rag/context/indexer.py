from __future__ import annotations

from src.runner_model.snapshot import RunnerSnapshot

from ..store import InMemoryVectorStore


class MemoryIndexer:
    """Offline process: builds a runner memory store from a RunnerSnapshot."""

    def build_store(self, runner_id: str, snapshot: RunnerSnapshot) -> InMemoryVectorStore:
        store = InMemoryVectorStore()
        store.add(self._snapshot_to_documents(runner_id, snapshot))
        return store

    def _snapshot_to_documents(self, runner_id: str, snapshot: RunnerSnapshot) -> list[dict]:
        docs: list[dict] = []

        docs.append({
            "id": f"{runner_id}_career",
            "runner_id": runner_id,
            "type": "pattern",
            "reference_period": f"depuis {snapshot.active_since}" if snapshot.active_since else "historique complet",
            "text": (
                f"coureur depuis {snapshot.active_since} "
                f"{snapshot.total_distance_km:.0f} km total "
                f"{snapshot.total_activities} activites"
            ),
            "observation": f"{snapshot.total_distance_km:.0f} km au total, {snapshot.total_activities} activités",
            "relevance_note": "Contexte de carrière",
        })

        if snapshot.fitness_trend != "unknown":
            trend_type = {
                "improving": "positive_precedent",
                "stable": "pattern",
                "declining": "warning_precedent",
            }.get(snapshot.fitness_trend, "pattern")
            docs.append({
                "id": f"{runner_id}_fitness_trend",
                "runner_id": runner_id,
                "type": trend_type,
                "reference_period": "4 dernières semaines",
                "text": f"tendance fitness forme {snapshot.fitness_trend} charge volume progression",
                "observation": f"Tendance de forme : {snapshot.fitness_trend}",
                "relevance_note": "Évolution récente de la condition physique",
            })

        if snapshot.current_window:
            cw = snapshot.current_window
            docs.append({
                "id": f"{runner_id}_current_window",
                "runner_id": runner_id,
                "type": "pattern",
                "reference_period": "4 dernières semaines",
                "text": f"charge hebdomadaire volume {cw.avg_weekly_km:.0f} km semaine allure rythme",
                "observation": f"Charge récente : {cw.avg_weekly_km:.1f} km/sem, allure {cw.avg_pace_s_per_km:.0f} s/km",
                "relevance_note": "Volume et allure actuels",
            })

        if snapshot.longest_run_km:
            docs.append({
                "id": f"{runner_id}_longest_run",
                "runner_id": runner_id,
                "type": "positive_precedent",
                "reference_period": "meilleur historique",
                "text": "sortie longue record distance longue course",
                "observation": f"Plus longue sortie : {snapshot.longest_run_km:.1f} km",
                "relevance_note": "Capacité maximale documentée",
            })

        if snapshot.best_week_km:
            docs.append({
                "id": f"{runner_id}_best_week",
                "runner_id": runner_id,
                "type": "positive_precedent",
                "reference_period": "meilleur historique",
                "text": "meilleure semaine volume charge record hebdomadaire pic",
                "observation": f"Meilleure semaine : {snapshot.best_week_km:.1f} km",
                "relevance_note": "Pic de charge historique",
            })

        return docs
