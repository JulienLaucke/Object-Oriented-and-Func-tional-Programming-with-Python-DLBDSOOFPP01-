from __future__ import annotations
from datetime import datetime
from typing import Literal

from sqlalchemy import (
    String, CheckConstraint, UniqueConstraint, ForeignKey, DateTime, Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

Periodicity = Literal["daily", "weekly"]

class HabitORM(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    periodicity: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("periodicity IN ('daily','weekly')", name="ck_periodicity"),
    )

    checks: Mapped[list["CheckORM"]] = relationship(
        back_populates="habit",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class CheckORM(Base):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False
    )
    ts: Mapped[datetime] = mapped_column(DateTime, nullable=False)              
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)   
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)      

    __table_args__ = (
        UniqueConstraint("habit_id", "period_start", name="uq_check_unique_period"),
    )

    habit: Mapped[HabitORM] = relationship(back_populates="checks")
