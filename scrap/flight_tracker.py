import sys
import os

from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QMainWindow

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# McMurdo Station coordinates
MC_MURDO_LAT = -77.8455
MC_MURDO_LON = 166.6698

class CartopyCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.proj = ccrs.SouthPolarStereo()
        fig = plt.figure(figsize=(5, 5))
        ax = fig.add_subplot(1, 1, 1, projection=self.proj)
        ax.set_title("Cartopy Map")

        # Add features
        ax.add_feature(cfeature.LAND.with_scale('50m'))
        ax.add_feature(cfeature.OCEAN.with_scale('50m'))
        ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
        ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':')

        # Set extent for Antarctica
        ax.set_extent([-180, 180, -90, -60], crs=ccrs.PlateCarree())

        # Add gridlines
        gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}

        # Add marker for McMurdo Station
        ax.plot(MC_MURDO_LON, MC_MURDO_LAT, marker='o', color='red',
                markersize=8, transform=ccrs.PlateCarree())

        super().__init__(fig)

class FlightTrackerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flight Tracker Widget")
        self.resize(1000, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Create and add only the Cartopy widget
        self.cartopy_widget = CartopyCanvas(self)
        layout.addWidget(self.cartopy_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlightTrackerWindow()
    window.show()
    sys.exit(app.exec())