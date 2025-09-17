# Habit Tracker (Python, SQLite, SQLAlchemy)

> This project was developed as part of the IU module  
> *Object-Oriented and Functional Programming with Python (DLBDSOOFPP01)* – Phase 2.

A small, robust habit tracker with clear domain logic, daily/weekly period handling, streak analytics, and a simple CLI.  
Data is persisted in SQLite via SQLAlchemy 2.0.

## Table of Contents
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [Example Output](#example-output)
- [Tests](#tests)
- [Roadmap](#roadmap)


---

## Features
- Create and list habits (filter by periodicity)
- Check-offs with normalized period bounds (day / ISO week)
- View which habits are **due** today/this week
- Longest streak analytics (per habit or best overall)
- Export habits and checks to **JSON** and **CSV**

---

## Setup
Clone or download this repository, then install dependencies:

```bash
python -m pip install -r requirements.txt

# Add and list
python -m habits.cli add "Drink water" --periodicity daily
python -m habits.cli list

# List only weekly habits
python -m habits.cli list-by --periodicity weekly

# Check now (marks as done for the current period)
python -m habits.cli check "Drink water"

# Show which habits are due
python -m habits.cli due

# Streaks
python -m habits.cli streak "Drink water"
python -m habits.cli streak-all

# Export data
python -m habits.cli export-habits --format json --path export/habits.json
python -m habits.cli export-checks --format csv  --path export/checks.csv
python -m habits.cli export-checks --format json --path export/checks_drink.json --name "Drink water"

Usage

All commands are run from the project root:

# Add and list
python -m habits.cli add "Drink water" --periodicity daily
python -m habits.cli list

# List only weekly habits
python -m habits.cli list-by --periodicity weekly

# Check now (marks as done for the current period)
python -m habits.cli check "Drink water"

# Show which habits are due
python -m habits.cli due

# Streaks
python -m habits.cli streak "Drink water"
python -m habits.cli streak-all

# Export data
python -m habits.cli export-habits --format json --path export/habits.json
python -m habits.cli export-checks --format csv  --path export/checks.csv
python -m habits.cli export-checks --format json --path export/checks_drink.json --name "Drink water"


All data is stored in habits.db (SQLite file in the project root).

Design Decisions

UTC-only timestamps → avoids timezone/DST issues

Period start as key (00:00 or Monday 00:00) → ensures idempotent checks (UNIQUE(habit_id, period_start))

Pure functions for analytics (longest streak) → easy to test

Separation of concerns:

db.py → engine & session

models.py → ORM tables

repo.py → repository with business logic

cli.py → command line interface

Tests

Run the unit tests with:

pytest -q


Sample tests are included in tests/test_core.py and cover:

Period normalization (start_of_day, start_of_iso_week)

Period bounds (daily, weekly)

Longest streak calculation

Roadmap

Delete or rename habits (with cascade in checks)

Summary analytics (show streak for every habit)

Optional GUI (Streamlit dashboard)


