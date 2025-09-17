from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Iterable

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal, create_schema
from .models import HabitORM, CheckORM, Periodicity

# ---------- Time & period helpers ----------
def utcnow() -> datetime:
    return datetime.utcnow()

def start_of_day(ts: datetime) -> datetime:
    """Normalize to 00:00 of the same day (UTC)."""
    return datetime(ts.year, ts.month, ts.day)

def start_of_iso_week(ts: datetime) -> datetime:
    """Normalize to Monday 00:00 of the ISO week (UTC)."""
    day_start = start_of_day(ts)
    weekday = day_start.isoweekday()  # Monday=1..Sunday=7
    return day_start - timedelta(days=weekday - 1)

def period_bounds(ts: datetime, periodicity: Periodicity) -> Tuple[datetime, datetime]:
    """Return [period_start, period_end) for the given timestamp and periodicity."""
    if periodicity == "daily":
        start = start_of_day(ts)
        return start, start + timedelta(days=1)
    elif periodicity == "weekly":
        start = start_of_iso_week(ts)
        return start, start + timedelta(weeks=1)
    else:
        raise ValueError("periodicity must be 'daily' or 'weekly'")

def step_for(periodicity: Periodicity) -> timedelta:
    return timedelta(days=1) if periodicity == "daily" else timedelta(weeks=1)

def longest_streak_for_habit(period_starts: Iterable[datetime], step: timedelta) -> int:
    """Count the longest run of consecutive period_start values spaced exactly by `step`."""
    longest = 0
    current = 0
    prev: Optional[datetime] = None
    for p in sorted(period_starts):
        if prev is None:
            current = 1
        else:
            if p - prev == step:
                current += 1
            else:
                current = 1
        if current > longest:
            longest = current
        prev = p
    return longest

# ---------- Export helpers ----------
import json, csv
from pathlib import Path

def _dt(o):
    """Datetime -> ISO string without microseconds."""
    if isinstance(o, datetime):
        return o.replace(microsecond=0).isoformat()
    return o

def _ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

# ---------- Repository ----------
class HabitRepo:
    """High-level API wrapping SQLAlchemy session operations."""
    def __init__(self, session: Optional[Session] = None) -> None:
        self._external_session = session

    def _session(self) -> Session:
        return self._external_session or SessionLocal()

    # Schema
    def init_schema(self) -> None:
        create_schema()

    # Habits
    def add_habit(self, name: str, periodicity: Periodicity) -> HabitORM:
        name = name.strip()
        with self._session() as s:
            h = HabitORM(name=name, periodicity=periodicity, created_at=utcnow())
            s.add(h)
            try:
                s.commit()
            except IntegrityError as e:
                s.rollback()
                if "UNIQUE" in str(e.orig):
                    raise ValueError(f"Habit '{name}' already exists") from e
                raise
            s.refresh(h)
            return h

    def list_all(self) -> List[HabitORM]:
        with self._session() as s:
            res = s.execute(
                select(HabitORM).order_by(HabitORM.periodicity.asc(), HabitORM.name.asc())
            )
            return list(res.scalars())

    def list_by(self, periodicity: Periodicity) -> List[HabitORM]:
        with self._session() as s:
            res = s.execute(
                select(HabitORM)
                .where(HabitORM.periodicity == periodicity)
                .order_by(HabitORM.name.asc())
            )
            return list(res.scalars())

    def get_by_name(self, name: str) -> HabitORM:
        with self._session() as s:
            res = s.execute(select(HabitORM).where(HabitORM.name == name))
            h = res.scalar_one_or_none()
            if not h:
                raise KeyError(f"Habit '{name}' not found")
            return h

    # Check-offs
    def check(self, name: str, ts: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        if ts is None:
            ts = utcnow()
        with self._session() as s:
            h = s.execute(select(HabitORM).where(HabitORM.name == name)).scalar_one_or_none()
            if not h:
                raise KeyError(f"Habit '{name}' not found")
            p_start, p_end = period_bounds(ts, h.periodicity)

            c = CheckORM(habit_id=h.id, ts=ts, period_start=p_start, period_end=p_end)
            s.add(c)
            try:
                s.commit()
            except IntegrityError:
                s.rollback()
                # Already checked in that period → idempotent behavior
                pass
            return p_start, p_end

    def has_checked(self, name: str, ts: Optional[datetime] = None) -> bool:
        if ts is None:
            ts = utcnow()
        with self._session() as s:
            h = s.execute(select(HabitORM).where(HabitORM.name == name)).scalar_one_or_none()
            if not h:
                raise KeyError(f"Habit '{name}' not found")
            p_start, _ = period_bounds(ts, h.periodicity)
            exists = s.execute(
                select(func.count()).select_from(CheckORM)
                .where(CheckORM.habit_id == h.id, CheckORM.period_start == p_start)
            ).scalar_one()
            return exists > 0

    # Due
    def is_due(self, name: str, ref: Optional[datetime] = None) -> bool:
        return not self.has_checked(name, ts=ref)

    def due(self, periodicity: Optional[Periodicity] = None, ref: Optional[datetime] = None) -> List[HabitORM]:
        if ref is None:
            ref = utcnow()
        habits = self.list_all() if periodicity is None else self.list_by(periodicity)
        return [h for h in habits if not self.has_checked(h.name, ts=ref)]

    # Analytics
    def longest_streak_for(self, name: str) -> int:
        with self._session() as s:
            h = s.execute(select(HabitORM).where(HabitORM.name == name)).scalar_one_or_none()
            if not h:
                raise KeyError(f"Habit '{name}' not found")
            periods = s.execute(
                select(CheckORM.period_start)
                .where(CheckORM.habit_id == h.id)
                .order_by(CheckORM.period_start.asc())
            ).scalars().all()
            return longest_streak_for_habit(periods, step_for(h.periodicity))

    def longest_streak_all(self) -> Tuple[Optional[HabitORM], int]:
        best_habit = None
        best = 0
        for h in self.list_all():
            s = self.longest_streak_for(h.name)
            if s > best:
                best = s
                best_habit = h
        return best_habit, best

    # Listing checks (for export/UI)
    def list_checks(self, name: Optional[str] = None) -> List[CheckORM]:
        with self._session() as s:
            q = select(CheckORM).order_by(CheckORM.period_start.asc())
            if name:
                h = s.execute(select(HabitORM).where(HabitORM.name == name)).scalar_one_or_none()
                if not h:
                    raise KeyError(f"Habit '{name}' not found")
                q = q.where(CheckORM.habit_id == h.id)
            return list(s.execute(q).scalars())

    # Exports
    def export_habits_json(self, path: str | Path) -> Path:
        rows = []
        for h in self.list_all():
            rows.append({
                "id": h.id,
                "name": h.name,
                "periodicity": h.periodicity,
                "created_at": _dt(h.created_at),
            })
        out = _ensure_parent(path)
        out.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        return out

    def export_habits_csv(self, path: str | Path) -> Path:
        out = _ensure_parent(path)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "name", "periodicity", "created_at"])
            for h in self.list_all():
                w.writerow([h.id, h.name, h.periodicity, _dt(h.created_at)])
        return out

    def export_checks_json(self, path: str | Path, name: Optional[str] = None) -> Path:
        rows = []
        for c in self.list_checks(name=name):
            rows.append({
                "id": c.id,
                "habit_id": c.habit_id,
                "ts": _dt(c.ts),
                "period_start": _dt(c.period_start),
                "period_end": _dt(c.period_end),
            })
        out = _ensure_parent(path)
        out.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        return out

    def export_checks_csv(self, path: str | Path, name: Optional[str] = None) -> Path:
        out = _ensure_parent(path)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "habit_id", "ts", "period_start", "period_end"])
            for c in self.list_checks(name=name):
                w.writerow([c.id, c.habit_id, _dt(c.ts), _dt(c.period_start), _dt(c.period_end)])
        return out
