"""Run with project-local development data, never the normal user database."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run():
    sys.path.insert(0, str(ROOT))
    data_dir = ROOT / ".dev-data"
    data_dir.mkdir(exist_ok=True)
    # Configure before importing modules that capture DB_PATH in default arguments.
    import src.config as config

    config.DATA_DIR = data_dir
    config.DB_PATH = data_dir / "typing_tutor.db"
    from main import main

    main()


if __name__ == "__main__":
    run()
