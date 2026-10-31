import json
import os
import subprocess
import yaml

from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from typing import Iterator

from drift.models import ContainerSnapshot, DriftKind

load_dotenv()

COMPOSE_FILE = Path(f"{os.getenv('HOST_PATH', '')}/docker-compose.yml")

def parse_mem_limit(value: str) -> int:
    unit = value[-1]
    if unit not in ("m", "g"):
        raise ValueError(f"Bad mem_limit: {value}")
    number = int(value[:-1])
    if unit == "m":
        return number * (1024 ** 2)
    return number * (1024 ** 3)

def load_compose_limits(compose: Path) -> dict[str, int]:
    svc_limits = {}
    with open(compose) as f:
        data = yaml.safe_load(f)
        services = data["services"]
        for svc, new_dict in services.items():
            mem_limit = parse_mem_limit(new_dict["mem_limit"])
            svc_limits[svc] = mem_limit
    return svc_limits

def iter_snapshots() -> Iterator[ContainerSnapshot]:
    result = subprocess.run(
        args=["docker", "ps", "-q"], capture_output=True, text=True, timeout=30)
    ids = result.stdout.split()
    raw_data = subprocess.run(
        args=["docker", "inspect", *ids], capture_output=True, text=True, timeout=30).stdout
    taken_at = datetime.now()
    for i in json.loads(raw_data):
        yield ContainerSnapshot(
            name=i["Name"],
            image=i["Config"]["Image"],
            image_id=i["Image"],
            restart_count=i["RestartCount"],
            started_at=datetime.fromisoformat(i["State"]["StartedAt"]),
            mem_bytes=i["HostConfig"]["Memory"],
            taken_at=taken_at)

def compare_limits(expected: dict[str, int], snapshots: list[ContainerSnapshot])-> list[tuple[str, DriftKind]]:
    results = []
    actual = {s.name: s.mem_bytes for s in snapshots}
    for name, mem_bytes in expected.items():
        if name not in actual:
            results.append((name, DriftKind.MISSING))
        elif actual[name] != mem_bytes:
            results.append((name, DriftKind.MEM_MISMATCH))
    for name in actual:
        if name not in expected:
            results.append((name, DriftKind.UNEXPECTED))
    return results

if __name__ == "__main__":
    snaps = list(iter_snapshots())
    print(len(snaps))
    grafana = [s for s in snaps if s.name == "grafana"][0]
    print(grafana.name, grafana.image, grafana.mem_bytes, grafana.restart_count)
    expected = load_compose_limits(COMPOSE_FILE)
    print(compare_limits(expected, snaps))
