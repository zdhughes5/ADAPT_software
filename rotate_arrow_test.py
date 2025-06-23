import sys
import math
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QTransform, QPainter
from PyQt6.QtCore import QTimer, Qt

class RotatingArrowWidget(QWidget):
    def __init__(self, image_path="arrow.png", interval_ms=10, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_arrow)
        self.timer.start(interval_ms)
        self.setMinimumSize(32, 32)  # Set a reasonable minimum size

    def rotate_arrow(self):
        self.angle = (self.angle + 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # Calculate center and scale
        w, h = self.width(), self.height()
        pix_w, pix_h = self.pixmap.width(), self.pixmap.height()
        scale = min(w / pix_w, h / pix_h)
        # Transform: move to center, rotate, scale, move back
        painter.translate(w / 2, h / 2)
        painter.rotate(self.angle)
        painter.scale(scale, scale)
        painter.translate(-pix_w / 2, -pix_h / 2)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RotatingArrowWidget()
    window.setWindowTitle("Rotating Arrow Test")
    window.resize(100, 100)  # Example: small size
    window.show()
    sys.exit(app.exec())
