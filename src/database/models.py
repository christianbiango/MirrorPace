from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ActivityRecord(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("source_file", name="uq_source_file"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identity
    source_file: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sport_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # ActivityMetrics (flattened — 1:1 with Activity)
    distance_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elevation_gain_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # PhysiologyMetrics (flattened — 1:1 with Activity)
    avg_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class RunnerSnapshotRecord(Base):
    __tablename__ = "runner_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Career
    total_activities: Mapped[int] = mapped_column(Integer, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    active_since: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Current state
    fitness_trend: Mapped[str] = mapped_column(String, nullable=False)
    current_avg_weekly_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_avg_pace_s_per_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_sessions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Training profile
    avg_pace_s_per_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Intensity distribution
    intensity_easy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intensity_moderate_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intensity_hard_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intensity_unknown_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Personal bests
    longest_run_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fastest_pace_s_per_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    best_week_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
