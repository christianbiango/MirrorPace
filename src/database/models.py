from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
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
