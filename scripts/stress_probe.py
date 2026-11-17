"""Measure analytics and backup against an isolated 10,000-session archive."""
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from src.core.analytics import AnalyticsService
    from src.database.backup import BackupService
    from src.database.db import Database
    from src.database.models import SessionRecord, StatsRepository
    with tempfile.TemporaryDirectory() as folder:
        db = Database.reset(Path(folder) / "stress.db")
        repo = StatsRepository(db)
        record = SessionRecord("custom", "stress", "asdf " * 20, 100, 95, 5,
                               38, 40, 95, 40, duration_seconds=30)
        start = time.perf_counter()
        with db.transaction():
            for _ in range(10000):
                repo.save_session(record)
        inserted = time.perf_counter()
        report = AnalyticsService(db).report()
        reported = time.perf_counter()
        backup = Path(folder) / "backup.json"
        BackupService(db).export_file(backup)
        exported = time.perf_counter()
        assert report["count"] == 10000
        assert report["accuracy"] == 95
        assert report["average_wpm"] == 38
        result = {"sessions": 10000, "insert_seconds": inserted - start,
                  "report_seconds": reported - inserted, "export_seconds": exported - reported,
                  "backup_bytes": backup.stat().st_size}
        db.close()
    path = ROOT / ".dev-data" / "reports" / "stress.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
