from __future__ import annotations
from argparse import ArgumentParser
from datetime import datetime
from typing import Optional

from .repo import HabitRepo, utcnow

def parse_iso(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse 'YYYY-MM-DD[ T]HH:MM:SS' to datetime, or None if not provided."""
    if not ts_str:
        return None
    return datetime.fromisoformat(ts_str.replace(" ", "T"))

def to_iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat()

def main():
    parser = ArgumentParser(prog="habitr", description="Habit Tracker (SQLite + SQLAlchemy)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # add
    p_add = sub.add_parser("add", help="add a habit")
    p_add.add_argument("name", type=str)
    p_add.add_argument("--periodicity", choices=["daily", "weekly"], required=True)

    # list
    sub.add_parser("list", help="list all habits")

    # list-by
    p_listby = sub.add_parser("list-by", help="list habits by periodicity")
    p_listby.add_argument("--periodicity", choices=["daily", "weekly"], required=True)

    # check
    p_check = sub.add_parser("check", help="check off a habit for now or a given timestamp")
    p_check.add_argument("name", type=str)
    p_check.add_argument("--ts", type=str, help="ISO time, e.g. 2025-09-15T09:00:00")

    # due
    p_due = sub.add_parser("due", help="show due habits (optionally filtered)")
    p_due.add_argument("--periodicity", choices=["daily", "weekly"])

    # streak
    p_streak = sub.add_parser("streak", help="longest streak for a habit")
    p_streak.add_argument("name", type=str)

    # streak-all
    sub.add_parser("streak-all", help="best longest streak overall")

    # export
    p_exp_h = sub.add_parser("export-habits", help="export habits to JSON/CSV")
    p_exp_h.add_argument("--format", choices=["json", "csv"], required=True)
    p_exp_h.add_argument("--path", required=True)

    p_exp_c = sub.add_parser("export-checks", help="export checks to JSON/CSV")
    p_exp_c.add_argument("--format", choices=["json", "csv"], required=True)
    p_exp_c.add_argument("--path", required=True)
    p_exp_c.add_argument("--name", help="optional habit name filter")

    args = parser.parse_args()
    repo = HabitRepo()
    repo.init_schema()

    if args.cmd == "add":
        h = repo.add_habit(args.name, args.periodicity)
        print(f"Added: {h.name} ({h.periodicity}) @ {to_iso(h.created_at)}")

    elif args.cmd == "list":
        habits = repo.list_all()
        if not habits:
            print("No habits yet.")
        else:
            for h in habits:
                print(f"- {h.periodicity:6} | {h.name} | created {to_iso(h.created_at)}")

    elif args.cmd == "list-by":
        habits = repo.list_by(args.periodicity)
        if not habits:
            print(f"No {args.periodicity} habits.")
        else:
            for h in habits:
                print(f"- {h.periodicity:6} | {h.name}")

    elif args.cmd == "check":
        ts = parse_iso(args.ts) or utcnow()
        try:
            p_start, p_end = repo.check(args.name, ts=ts)
            print(f"Checked '{args.name}' for period [{to_iso(p_start)} .. {to_iso(p_end)})")
        except KeyError as e:
            print(e)

    elif args.cmd == "due":
        habits = repo.due(periodicity=args.periodicity)
        if not habits:
            print("Nothing due. Great job!")
        else:
            for h in habits:
                print(f"- {h.periodicity:6} | {h.name}")

    elif args.cmd == "streak":
        try:
            s = repo.longest_streak_for(args.name)
            print(f"Longest streak for '{args.name}': {s}")
        except KeyError as e:
            print(e)

    elif args.cmd == "streak-all":
        h, s = repo.longest_streak_all()
        if h:
            print(f"Best longest streak: {s} ({h.name})")
        else:
            print("No streaks yet.")

    elif args.cmd == "export-habits":
        out = repo.export_habits_json(args.path) if args.format == "json" else repo.export_habits_csv(args.path)
        print(f"Exported habits → {out}")

    elif args.cmd == "export-checks":
        out = repo.export_checks_json(args.path, name=args.name) if args.format == "json" else repo.export_checks_csv(args.path, name=args.name)
        print(f"Exported checks → {out}")

if __name__ == "__main__":
    main()
