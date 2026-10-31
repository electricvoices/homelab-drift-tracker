import os
import psycopg
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from typing import Iterator

from drift.collect import COMPOSE_FILE, compare_limits, iter_snapshots, load_compose_limits
from drift.store import SnapshotStore

load_dotenv()


app = FastAPI()

def get_store() -> Iterator[SnapshotStore]:
    """Open a SnapshotStore for one request; 503 if psql is unreachable"""
    try:
        with SnapshotStore() as store:
            yield store
    except psycopg.OperationalError:
        raise HTTPException(status_code=503, detail="database unavailable")

@app.get("/changes")
def list_changes(store: SnapshotStore = Depends(get_store)) -> list[dict]:
    """Every change between snapshots, as JSON."""
    return [
        {"name": name, "taken_at": taken_at, "drift": kind.value}
        for name, taken_at, kind in store.changes()]

def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("DNS_API_KEY")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid or missing API key")

@app.post("/snapshot", dependencies=[Depends(require_api_key)])
def take_snapshot() -> dict:
    """Collect and save a snapshot. Return how many containers were saved."""
    snaps = list(iter_snapshots())
    with SnapshotStore() as store:
        saved = store.save(snaps)
    return {"saved": saved}

@app.get("/drift")
def current_drift() -> list[dict]:
    """Compose vs running: MISSING, MEM_MISMATCH, UNEXPECTED, as JSON."""
    snaps = list(iter_snapshots())
    problems = compare_limits(load_compose_limits(COMPOSE_FILE), snaps)
    results = []
    for entry in problems:
        name, drift_kind = entry
        results.append({"name": name, "drift": drift_kind.value})
    return results

