"""Run the session-1 quality gate from any working directory."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    reports = ROOT / ".dev-data" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    commands = [
        [sys.executable, "-m", "ruff", "check", "tests/regressions",
         "tests/test_ui_smoke.py", "tests/conftest.py", "scripts", "src/core/session.py", "src/database/backup.py", "src/core/keyboard_layout.py", "src/core/lessons.py", "src/core/typing_engine.py", "src/core/analytics.py", "src/ui/pages/statistics.py"],
        [sys.executable, "-m", "compileall", "-q", "src", "main.py", "scripts"],
        [sys.executable, "-m", "pytest", "-ra", f"--junitxml={reports / 'tests.xml'}"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
