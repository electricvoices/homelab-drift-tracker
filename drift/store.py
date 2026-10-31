import os
import psycopg
from datetime import datetime
from dotenv import load_dotenv

from drift.models import ContainerSnapshot, DriftKind

load_dotenv()

class SnapshotStore:
    def __enter__(self) -> "SnapshotStore":
        try:
            self.conn = psycopg.connect(
                host="localhost", port=5432, dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"))
        except psycopg.OperationalError as e:
            print(f"Unable to connect to PSQL: {e}")
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

    def save(self, snapshots: list[ContainerSnapshot]) -> int:
        cursor = self.conn.cursor()
        inserted = 0
        for ss in snapshots:
            cursor.execute(
                """INSERT INTO container_snapshot (
                    name, image, image_id, restart_count, started_at, mem_bytes, taken_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name, taken_at) DO NOTHING""",
                    (ss.name, ss.image, ss.image_id, ss.restart_count, ss.started_at, ss.mem_bytes, ss.taken_at))
            inserted += cursor.rowcount
        return inserted

    def latest_taken_at(self) -> datetime | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(taken_at) FROM container_snapshot")
        row = cursor.fetchone()
        if not row:
            return None
        return row[0]

    def changes(self) -> list[tuple[str, datetime, DriftKind]]:
        results = []
        cursor = self.conn.cursor()
        cursor.execute(
        """WITH history AS (
            SELECT cs.name, cs.taken_at, cs.image_id, cs.started_at,
            LAG(image_id, 1) OVER (PARTITION BY cs.name ORDER BY cs.taken_at) AS prev_image_id,
            LAG(started_at, 1) OVER (PARTITION BY cs.name ORDER BY cs.taken_at) AS prev_started_at
        FROM container_snapshot cs)
        SELECT h.name, h.taken_at,
            CASE
                WHEN h.image_id <> h.prev_image_id THEN 'IMAGE_UPDATED'
                WHEN h.started_at <> h.prev_started_at THEN 'RESTARTED'
            END AS drift
        FROM history h
        WHERE h.image_id <> h.prev_image_id
            OR h.started_at <> h.prev_started_at
        ORDER BY h.taken_at, h.name""")
        rows = cursor.fetchall()
        for ss in rows:
            name = ss[0]
            taken_at = ss[1]
            drift = DriftKind[ss[2]]
            results.append((name, taken_at, drift))
        return results


if __name__ == "__main__":
    with SnapshotStore() as store:
        print(store.changes())
