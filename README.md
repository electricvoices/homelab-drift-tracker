# Homelab Drift Tracker

A Python application that monitors Docker container configuration and detects configuration drift by storing snapshots in PostgreSQL and comparing historical values.

[1. **Why I Built This**](#why-i-built-this) • [2. **Technologies**](#technologies) • [3. **Features**](#features) • [4. **Architecture**](#architecture) • [5. **Project Structure**](#project-structure) • [6. **Installation**](#installation) • [7. **Running Tests**](#running-tests) • [8. **Example Query**](#example-query) • [9. **What I Learned**](#what-i-learned) • [10. **Future Improvements**](#future-improvements)

## Why I Built This

My homelab relies on more than 20 Docker services. Updates, configuration changes, or accidental edits can introduce unexpected behavior over time.

The Drift Tracker was built to automatically detect these changes, store historical records, and alert me when configuration drift occurs.

## Technologies

- Python
- PostgreSQL
- FastAPI
- pytest
- Docker
- Bash
- Cron

## Features

- Daily Snapshot Collection
- Configuration Drift Detection
- Historical PostgreSQL Storage
- REST API for Querying Drift Events
- Automated Execution through Cron jobs
- Test coverage using pytest

## Architecture

```text
+-------------------+
| Docker Containers |
+-------------------+
        ↓
   +------------+
   | collect.py |
   +------------+
        ↓
   +------------+
   | PostgreSQL |
   +------------+
        ↓
   +-----------------------+
   | Drift Detection Logic |
   +-----------------------+
        ↓
   +---------+
   | FastAPI |
   +---------+
        ↓
   +--------+
   | Alerts |
   +--------+
```

## Project Structure

```text
homelab-drift-tracker/
├── drift/
│   ├── api.py
│   ├── cli.py
│   ├── collect.py
│   ├── models.py
│   └── store.py
├── tests/
├── scripts/
└── README.md
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
python -m pytest
```

### Current Test Status:

```text
13 passed
```

## Example Query

```sql
SELECT *
FROM container_snapshot
ORDER BY taken_at DESC;
```

## What I Learned

- FastAPI Development
- PostgreSQL Persistence
- Automated Testing with pytest
- Data Collection Pipelines
- Historical Drift Analysis
- Production-Focused Automation

## Future Improvements

- SQLAlchemy Migration
- GitHub Actions CI/CD
- Dashboard Integration
- Historical Reporting Views
