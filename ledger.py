import os
import psycopg
from datetime import datetime
from dotenv import load_dotenv
from types import TracebackType
load_dotenv()


class RunRecorder:
    # Context manager: records one script into ledger.script_runs
    def __init__(self, script: str) -> None:
        self.script = script
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None

    def __enter__(self) -> "RunRecorder":
        self.started_at = datetime.now()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        self.finished_at = datetime.now()
        ok = exc_type is None
        error = str(exc) if exc is not None else None
        try:
            conn = psycopg.connect(
                host="localhost", port=5432, dbname="ledger",
                user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"))
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO script_runs (script, started_at, finished_at, ok, error)
                VALUES (%s, %s, %s, %s, %s)""",
                (self.script, self.started_at, self.finished_at, ok, error))
            conn.commit()
            cursor.close()
            conn.close()
        except psycopg.Error as e:
            print(f"ledger: could not record run of {self.script}: {e}")
