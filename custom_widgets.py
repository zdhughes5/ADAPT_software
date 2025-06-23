import sys
import math
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMainWindow, QHBoxLayout
from PyQt6.QtGui import QPixmap, QTransform, QPainter
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pyqtgraph as pg
import numpy as np
import time

# McMurdo Station coordinates
MC_MURDO_LAT = -77.8455
MC_MURDO_LON = 166.6698

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

class SignalRotatingArrowWidget(QWidget):
    def __init__(self, image_path="arrow.png", parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        self.angle = 0
        self.setMinimumSize(32, 32)

    def set_angle(self, angle):
        self.angle = angle % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        pix_w, pix_h = self.pixmap.width(), self.pixmap.height()
        scale = min(w / pix_w, h / pix_h)
        painter.translate(w / 2, h / 2)
        painter.rotate(self.angle)
        painter.scale(scale, scale)
        painter.translate(-pix_w / 2, -pix_h / 2)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.end()

class CartopyCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.proj = ccrs.SouthPolarStereo()
        self.fig = plt.figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(1, 1, 1, projection=self.proj)
        self.ax.set_title("Cartopy Map")

        # Add features
        self.ax.add_feature(cfeature.LAND.with_scale('50m'))
        self.ax.add_feature(cfeature.OCEAN.with_scale('50m'))
        self.ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
        self.ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':')

        # Set extent for Antarctica
        self.ax.set_extent([-180, 180, -90, -60], crs=ccrs.PlateCarree())

        # Add gridlines
        gl = self.ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}

        # Add marker for McMurdo Station
        self.ax.plot(MC_MURDO_LON, MC_MURDO_LAT, marker='*', color='red',
                markersize=8, transform=ccrs.PlateCarree())

        self.track_lons = []
        self.track_lats = []
        self.track_line, = self.ax.plot([], [], color='blue', linewidth=2, marker='o', markersize=4, transform=ccrs.PlateCarree(), label='Balloon Track')

        super().__init__(self.fig)

    def add_point(self, lon, lat):
        """Add a new point to the balloon track and update the plot."""
        self.track_lons.append(lon)
        self.track_lats.append(lat)
        self.track_line.set_data(self.track_lons, self.track_lats)
        self.draw_idle()

    def clear_track(self):
        """Clear the balloon track from the plot."""
        self.track_lons = []
        self.track_lats = []
        self.track_line.set_data([], [])
        self.draw_idle()



class ScrollingRatePlotWidget(QWidget):
    def __init__(self, array_size=100, parent=None):
        super().__init__(parent)
        self.array_size = array_size
        self.data = np.zeros(self.array_size)
        now = time.time()
        now_sub_one = now - 1
        self.times = np.linspace(now_sub_one, now, self.array_size)
        self.plot_widget = pg.PlotWidget(axisItems = {'bottom': pg.DateAxisItem()})
        self.plot_widget.setLabel('left', 'Rate')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.showGrid(x=True, y=True)
        self.curve = self.plot_widget.plot(self.times, self.data, pen='y')
        layout = QVBoxLayout(self)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_plot(self, time, value):
        """Add a new value to the plot, scrolling the data."""
        self.data = np.roll(self.data, -1)
        self.times = np.roll(self.times, -1)
        self.times[-1] = time
        self.data[-1] = value
        print(self.times, self.data)
        self.curve.setData(x=self.times, y=self.data)
        print("self.curve is type:", type(self.curve))
        print(f"Updated plot with value: {value}")
