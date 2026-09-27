"""Generate app icon files (.ico, .png) from the programmatic icon design."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QBrush, QLinearGradient, QFont, QIcon,
    QImage,
)
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

def render_icon(size: int) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    grad = QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0, QColor("#0078d4"))
    grad.setColorAt(1, QColor("#00549b"))
    p.setBrush(QBrush(grad))
    p.setPen(QColor("#00345e"))
    margin = size // 32
    p.drawRoundedRect(margin, margin, size - 2*margin, size - 2*margin, size//5, size//5)

    p.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", int(size * 0.4), QFont.Bold)
    p.setFont(font)
    p.drawText(px.rect().adjusted(0, -size//10, 0, 0), Qt.AlignCenter, "10")

    p.setPen(QColor("#ffffff"))
    p.setBrush(QColor("#ffffff"))
    key_w = size // 10
    key_h = size // 16
    gap = size // 32
    total_w = 5 * key_w + 4 * gap
    start_x = (size - total_w) // 2
    y = int(size * 0.69)
    for i in range(5):
        p.drawRoundedRect(start_x + i * (key_w + gap), y, key_w, key_h, 2, 2)

    p.end()
    return px


assets_dir = Path(__file__).resolve().parent / "assets"
assets_dir.mkdir(exist_ok=True)

pixmap_256 = render_icon(256)
pixmap_256.save(str(assets_dir / "icon.png"), "PNG")

pixmap_256.save(str(assets_dir / "icon.ico"), "ICO")

for size in [16, 32, 48, 64, 128]:
    render_icon(size).save(str(assets_dir / f"icon_{size}.png"), "PNG")

print(f"Created: {assets_dir / 'icon.png'}")
print(f"Created: {assets_dir / 'icon.ico'}")
print(f"PNG size: {(assets_dir / 'icon.png').stat().st_size} bytes")
print(f"ICO size: {(assets_dir / 'icon.ico').stat().st_size} bytes")