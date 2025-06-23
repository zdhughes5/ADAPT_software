# Language: Python
import sys
import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# Dimensions for each square in the grid:
PIXEL_SIZE = 100
GAP = 10

class PixelRect(QtWidgets.QGraphicsRectItem):
    def __init__(self, rect, time_series, intensity, min_intensity, max_intensity, click_callback, idx):
        super().__init__(rect)
        self.time_series = time_series
        self.click_callback = click_callback
        self.idx = idx
        # Normalize intensity value for color mapping (blue low, red high)
        norm = (intensity - min_intensity) / (max_intensity - min_intensity + 1e-6)
        r = int(255 * norm)
        b = int(255 * (1 - norm))
        color = QtGui.QColor(r, 0, b)
        self.setBrush(QtGui.QBrush(color))
        # Enable mouse events
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        # When clicked, trigger the callback with this pixel's time series
        self.click_callback(self.time_series, self.idx)
        super().mousePressEvent(event)

class PixelCircle(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, rect, time_series, intensity, min_intensity, max_intensity, click_callback, idx):
        super().__init__(rect)
        self.time_series = time_series
        self.click_callback = click_callback
        self.idx = idx
        # Normalize intensity value for color mapping (blue low, red high)
        norm = (intensity - min_intensity) / (max_intensity - min_intensity + 1e-6)
        r = int(255 * norm)
        b = int(255 * (1 - norm))
        color = QtGui.QColor(r, 0, b)
        self.setBrush(QtGui.QBrush(color))
        # Enable mouse events
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        # When clicked, trigger the callback with this pixel's time series
        self.click_callback(self.time_series, self.idx)
        super().mousePressEvent(event)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PMT Square Display")
        self.resize(500, 500)
        
        # Create central widget with vertical layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create GraphicsView for 3x2 pixel grid
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setFixedHeight(PIXEL_SIZE*2 + GAP*3)
        layout.addWidget(self.view)
        
        # Create PlotWidget for time series display
        self.plot_widget = pg.PlotWidget(title="Time Series")
        self.plot_widget.setLabel("bottom", "Time (µs)")
        self.plot_widget.setLabel("left", "Voltage")
        layout.addWidget(self.plot_widget, 1)
        
        # Add "Next" button
        self.next_button = QtWidgets.QPushButton("Next")
        self.next_button.clicked.connect(self.generate_test_data_and_build_grid)
        layout.addWidget(self.next_button)
        
        self.setCentralWidget(central_widget)
        
        # Initialize variables to track selected pixel
        self.selected_pixel_idx = None
        self.sensor_data = []
        
        # Generate initial test data and build the pixel grid.
        self.generate_test_data_and_build_grid()
    
    def generate_test_data_and_build_grid(self):
        # Clear the scene before generating new data
        self.scene.clear()
        
        # For testing, simulate 6 sensors: each sensor has a time series over 2µs.
        # Sample 100 points over 2µs.
        t = np.linspace(0, 2, 100)  # time in microseconds
        self.sensor_data = []
        intensities = []
        for i in range(6):  # Adjusted for 6 sensors
            # Create a sine wave with noise and phase offset.
            phase = np.random.uniform(0, np.pi)
            data = np.sin(2 * np.pi * t/2 + phase) + np.random.normal(0, 0.2, t.shape)
            self.sensor_data.append((t, data))
            intensities.append(np.sum(data))
        
        min_intensity = min(intensities)
        max_intensity = max(intensities)
        
        # Create a 3x2 grid with circles in the top row and squares in the bottom row.
        positions = [
            (0, 0), (PIXEL_SIZE + GAP, 0), (2 * (PIXEL_SIZE + GAP), 0),
            (0, PIXEL_SIZE + GAP), (PIXEL_SIZE + GAP, PIXEL_SIZE + GAP), (2 * (PIXEL_SIZE + GAP), PIXEL_SIZE + GAP)
        ]
        for idx, (x, y) in enumerate(positions):
            t_series, data = self.sensor_data[idx]
            intensity = intensities[idx]
            if y == 0:  # Top row: circles
                rect = QtCore.QRectF(0, 0, PIXEL_SIZE, PIXEL_SIZE)
                pixel = PixelCircle(rect, (t_series, data), intensity, min_intensity, max_intensity, self.plot_time_series, idx)
            else:  # Bottom row: squares
                rect = QtCore.QRectF(0, 0, PIXEL_SIZE, PIXEL_SIZE)
                pixel = PixelRect(rect, (t_series, data), intensity, min_intensity, max_intensity, self.plot_time_series, idx)
            pixel.setPos(x, y)
            self.scene.addItem(pixel)
        
        # Adjust scene size:
        total_width = 3 * PIXEL_SIZE + 4 * GAP  # Adjusted for 3 columns
        total_height = 2 * PIXEL_SIZE + 3 * GAP  # Adjusted for 2 rows
        self.scene.setSceneRect(0, 0, total_width, total_height)
        
        # If a pixel was previously selected, reselect it and update the plot
        if self.selected_pixel_idx is not None:
            self.plot_time_series(self.sensor_data[self.selected_pixel_idx], self.selected_pixel_idx)
    
    def plot_time_series(self, time_series, idx):
        # Update the selected pixel index
        self.selected_pixel_idx = idx
        
        # Clear previous plot and show the clicked pixel's time series.
        self.plot_widget.clear()
        t, data = time_series
        self.plot_widget.plot(t, data, pen=pg.mkPen('w', width=2))
        self.plot_widget.setTitle(f"Time Series for Selected Pixel {idx + 1}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
    
if __name__ == '__main__':
    main()