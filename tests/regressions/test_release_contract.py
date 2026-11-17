"""Release metadata and persistence integration."""
import subprocess
import sys
from pathlib import Path

import tomllib

from src.config import APP_VERSION
from src.core.analytics import AnalyticsService
from src.database.backup import BackupService
from src.database.models import SessionRecord, StatsRepository

ROOT = Path(__file__).resolve().parents[2]


def test_release_version_consistent():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["version"] == APP_VERSION
    assert "main" in metadata["tool"]["setuptools"]["py-modules"]
    result = subprocess.run([sys.executable, str(ROOT / "main.py"), "--version"],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0
    assert APP_VERSION in result.stdout


def test_smoke_requires_isolated_directory():
    result = subprocess.run([sys.executable, str(ROOT / "main.py"), "--smoke-test"],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "requires --data-dir" in result.stderr


def test_save_backup_reset_restore_report(db, tmp_path):
    repo = StatsRepository(db)
    repo.save_session(SessionRecord("custom", "beta", "aş", 2, 1, 1, 12, 24, 50, 12,
                                    key_counts={"a": {"correct": 1, "incorrect": 0},
                                                "ş": {"correct": 0, "incorrect": 1}},
                                    duration_seconds=1))
    before = AnalyticsService(db).report()
    service = BackupService(db)
    path = tmp_path / "backup.json"
    service.export_file(path)
    service.reset()
    assert AnalyticsService(db).report()["count"] == 0
    service.import_file(path)
    service.import_file(path)
    after = AnalyticsService(db).report()
    for field in ("count", "accuracy", "average_wpm", "key_stats", "minutes"):
        assert after[field] == before[field]


def test_source_smoke_with_isolated_database(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "main.py"), "--smoke-test",
                             "--data-dir", str(tmp_path)], capture_output=True, timeout=25)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "typing_tutor.db").exists()
