import argparse
import sys

from collections import Counter

from drift.collect import iter_snapshots, COMPOSE_FILE, compare_limits, load_compose_limits
from drift.store import SnapshotStore
from ledger import RunRecorder

def cmd_snapshot() -> None:
    """Collect all running containers, save them, print how many were saved."""
    snaps = list(iter_snapshots())
    with SnapshotStore() as store:
        count = store.save(snaps)
    print(f"Saved {count} containers")

def cmd_report() -> None:
    """Print compose-vs-running drift, changes between snapshots, and a summary."""
    snaps = list(iter_snapshots())
    problems = compare_limits(load_compose_limits(COMPOSE_FILE), snaps)
    with SnapshotStore() as store:
        changes = store.changes()
    print("Compose vs running:")
    if not problems:
        print("  no drift")
    for name, kind in problems:
        print(f"  {name}: {kind.value}")
    print("Changes between snapshots:")
    if not changes:
        print("  none")
    for name, taken_at, kind in changes:
        print(f"  {taken_at:%Y-%m-%d %H:%M} {name}: {kind.value}")
    counts = Counter(kind.value for _, kind in problems)
    counts += Counter(kind.value for _, _, kind in changes)
    if counts:
        print(f"Summary: {dict(counts)}")
    else:
        print("Summary: all clear")

def cmd_check() -> int:
    """Print anything new since the last snapshot. Return 3 if found, 0 if clean"""
    snaps = list(iter_snapshots())
    problems = compare_limits(load_compose_limits(COMPOSE_FILE), snaps)
    with SnapshotStore() as store:
        latest = store.latest_taken_at()
        changes = store.changes()
    new_changes = [
        (name, kind) for name, taken_at, kind in changes if taken_at == latest]
    found = problems + new_changes
    if not found:
        print("all clear")
        return 0
    for name, kind in found:
        print(f"{name}: {kind.value}")
    return 3


def main() -> None:
    """Read the command from the terminal and call the matching function."""
    parser = argparse.ArgumentParser(description="Tracks drift in the homelab Docker stack.")
    parser.add_argument(
        "command", type=str, choices=["snapshot", "report", "check"], help="what to do")
    args = parser.parse_args()

    if args.command == "snapshot":
        with RunRecorder("drift.snapshot"):
            cmd_snapshot()
    elif args.command == "report":
        cmd_report()
    elif args.command == "check":
        with RunRecorder("drift.check"):
            code = cmd_check()
        sys.exit(code)

if __name__ == "__main__":
    main()
