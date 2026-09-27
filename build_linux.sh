#!/usr/bin/env bash
#
# Build TuşKlavye as a Linux AppImage.
#
# Prerequisites (Ubuntu/Debian):
#   sudo apt update && sudo apt install -y python3 python3-pip python3-venv \
#       desktop-file-utils libfuse2 wget
#
# Usage:
#   ./build_linux.sh
#
# Output:
#   dist/TusKlavye-x86_64.AppImage
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== TuşKlavye Linux AppImage Build ==="

VENV_DIR=".venv-linux"
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/6] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

echo "[2/6] Installing dependencies..."
pip install --upgrade pip
pip install PySide6 PyInstaller

echo "[3/6] Building binary with PyInstaller..."
python -m PyInstaller TusKlavye.spec --clean --noconfirm

echo "[4/6] Preparing AppDir..."
APPDIR="build/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/tusklavye"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

if [ -d "dist/TusKlavye" ]; then
    cp -r dist/TusKlavye/* "$APPDIR/usr/lib/tusklavye/"
elif [ -f "dist/TusKlavye" ]; then
    cp dist/TusKlavye "$APPDIR/usr/lib/tusklavye/TusKlavye"
else
    echo "ERROR: dist/TusKlavye not found!"
    exit 1
fi

cat > "$APPDIR/usr/bin/tusklavye" << 'RUNNER'
#!/usr/bin/env bash
exec "$(dirname "$0")/../lib/tusklavye/TusKlavye" "$@"
RUNNER
chmod +x "$APPDIR/usr/bin/tusklavye"

cp assets/icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/tusklavye.png"

cat > "$APPDIR/usr/share/applications/tusklavye.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=TuşKlavye
Comment=10 Parmak Yazma Eğitmeni
Exec=tusklavye
Icon=tusklavye
Categories=Education;Utility;
Terminal=false
DESKTOP

cat > "$APPDIR/AppRun" << 'APPRUN'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "${HERE}/usr/bin/tusklavye" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

cp assets/icon.png "$APPDIR/.DirIcon"
cp "$APPDIR/usr/share/applications/tusklavye.desktop" "$APPDIR/tusklavye.desktop"

echo "[5/6] Downloading appimagetool..."
APPIMAGETOOL="build/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    wget -q -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

echo "[6/6] Building AppImage..."
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "dist/TusKlavye-x86_64.AppImage"

echo ""
echo "=== Build complete! ==="
echo "Output: dist/TusKlavye-x86_64.AppImage"
ls -lh dist/TusKlavye-x86_64.AppImage