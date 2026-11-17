"""Build the local executable, smoke-test it and write its SHA-256."""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from src.config import APP_VERSION
    subprocess.run([sys.executable, str(ROOT / "scripts/check.py")], cwd=ROOT, check=True)
    output = ROOT / "dist" / APP_VERSION
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm",
                    "--distpath", str(output), "--workpath", str(ROOT / "build" / APP_VERSION),
                    "TusKlavye.spec"], cwd=ROOT, check=True)
    executable = output / ("TusKlavye.exe" if sys.platform == "win32" else "TusKlavye")
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run([str(executable), "--smoke-test", "--data-dir", folder],
                       cwd=folder, check=True, timeout=90)
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {executable.name}\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
