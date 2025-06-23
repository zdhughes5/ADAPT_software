# Language: Python
import sys
import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# Add a single scale parameter, and redefine PIXEL_SIZE and GAP accordingly:
OVERALL_SCALE = 0.5
PIXEL_SIZE = int(100 * OVERALL_SCALE)
GAP = int(10 * OVERALL_SCALE)

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
        self.setWindowTitle("Experimental System Layout")
        self.resize(800, 800)  # Adjusted window size for complex layout
        
        # Create central widget with vertical layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create GraphicsView for the experimental layout
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setFixedHeight(700)
        layout.addWidget(self.view)
        
        # Create PlotWidget for time series display
        self.plot_widget = pg.PlotWidget(title="Time Series")
        self.plot_widget.setLabel("bottom", "Time (µs)")
        self.plot_widget.setLabel("left", "Voltage")
        layout.addWidget(self.plot_widget, 1)
        
        # Add "Next" button
        self.next_button = QtWidgets.QPushButton("Next")
        self.next_button.clicked.connect(self.generate_test_data_and_build_layout)
        layout.addWidget(self.next_button)
        
        self.setCentralWidget(central_widget)
        
        # Initialize variables to track selected pixel
        self.selected_pixel_idx = None
        self.sensor_data = []
        
        # Add a separate scale for the CsI x layer
        self.CSI_PIXEL_SCALE = 0.8  # Adjust this scale to make CsI x layer smaller
        self.CSI_PIXEL_SIZE = int(PIXEL_SIZE * self.CSI_PIXEL_SCALE)
        
        # Generate initial test data and build the layout
        self.generate_test_data_and_build_layout()
    
    def generate_test_data_and_build_layout(self):
        # Clear the scene before generating new data
        self.scene.clear()
        
        # Generate test data for all sensors
        self.sensor_data = []
        intensities = []
        for i in range(60):  # Simulate 60 sensors for the layout
            t = np.linspace(0, 2, 100)  # time in microseconds
            phase = np.random.uniform(0, np.pi)
            data = np.sin(2 * np.pi * t / 2 + phase) + np.random.normal(0, 0.2, t.shape)
            self.sensor_data.append((t, data))
            intensities.append(np.sum(data))
        
        min_intensity = min(intensities)
        max_intensity = max(intensities)
        
        # Build the layout layer by layer
        self.build_hodo_x_layer(min_intensity, max_intensity, intensities)
        self.build_hodo_y_layer()
        self.build_wls_y_layer()
        self.build_csi_layer()
        self.build_wls_x_layer(min_intensity, max_intensity, intensities)
        self.build_tail_counters()
    
    def build_hodo_x_layer(self, min_intensity, max_intensity, intensities):
        # Two rows of 14 round pixels, bottom row offset by radius
        radius = PIXEL_SIZE // 2
        for row in range(2):
            for col in range(14):
                x = col * (PIXEL_SIZE + GAP)
                y = row * (radius + GAP)
                if row == 1:
                    x += radius  # Offset bottom row horizontally
                    y += radius  # Offset bottom row vertically
                idx = row * 14 + col
                rect = QtCore.QRectF(0, 0, PIXEL_SIZE, PIXEL_SIZE)
                pixel = PixelCircle(rect, self.sensor_data[idx], intensities[idx], min_intensity, max_intensity, self.plot_time_series, idx)
                pixel.setPos(x, y)
                self.scene.addItem(pixel)
    
    def build_hodo_y_layer(self):
        # Two long rectangles representing the edge-on view of fibers
        width = 14 * (PIXEL_SIZE + GAP)
        height = PIXEL_SIZE // 4
        for row in range(2):
            y = 2 * (PIXEL_SIZE + GAP) + row * (height + GAP)
            rect = QtCore.QRectF(0, 0, width, height)
            pixel = QtWidgets.QGraphicsRectItem(rect)
            pixel.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 255)))  # Blue color
            pixel.setPos(0, y)
            self.scene.addItem(pixel)
    
    def build_wls_y_layer(self):
        # One long rectangle for WLS y layer
        width = 14 * (PIXEL_SIZE + GAP)
        height = PIXEL_SIZE // 2
        y = 2 * (PIXEL_SIZE + GAP) + 2 * (PIXEL_SIZE // 4 + GAP)
        rect = QtCore.QRectF(0, 0, width, height)
        pixel = QtWidgets.QGraphicsRectItem(rect)
        pixel.setBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0)))  # Green color
        pixel.setPos(0, y)
        self.scene.addItem(pixel)
    
    def build_csi_layer(self):
        # Large rectangle for CsI layer
        width = 14 * (PIXEL_SIZE + GAP)
        height = PIXEL_SIZE
        y = 2 * (PIXEL_SIZE + GAP) + 2 * (PIXEL_SIZE // 4 + GAP) + (PIXEL_SIZE // 2 + GAP)
        rect = QtCore.QRectF(0, 0, width, height)
        pixel = QtWidgets.QGraphicsRectItem(rect)
        pixel.setBrush(QtGui.QBrush(QtGui.QColor(255, 165, 0)))  # Orange color
        pixel.setPos(0, y)
        self.scene.addItem(pixel)
    
    def build_wls_x_layer(self, min_intensity, max_intensity, intensities):
        # 20 square pixels for WLS x layer with adjusted size
        for col in range(20):
            x = col * (self.CSI_PIXEL_SIZE + GAP)
            y = 2 * (PIXEL_SIZE + GAP) + 2 * (PIXEL_SIZE // 4 + GAP) + (PIXEL_SIZE // 2 + GAP) + (PIXEL_SIZE + GAP)
            idx = 28 + col  # Offset index for WLS x layer
            rect = QtCore.QRectF(0, 0, self.CSI_PIXEL_SIZE, self.CSI_PIXEL_SIZE)
            pixel = PixelRect(rect, self.sensor_data[idx], intensities[idx], min_intensity, max_intensity, self.plot_time_series, idx)
            pixel.setPos(x, y)
            self.scene.addItem(pixel)
    
    def build_tail_counters(self):
        # Three sets of 2 stacked rectangles
        width = 14 * (PIXEL_SIZE + GAP) // 3
        height = PIXEL_SIZE // 2
        for col in range(3):
            for row in range(2):
                x = col * (width + GAP)
                y = 2 * (PIXEL_SIZE + GAP) + 2 * (PIXEL_SIZE // 4 + GAP) + (PIXEL_SIZE // 2 + GAP) + (PIXEL_SIZE + GAP) + (PIXEL_SIZE + GAP) + row * (height + GAP)
                rect = QtCore.QRectF(0, 0, width, height)
                pixel = QtWidgets.QGraphicsRectItem(rect)
                pixel.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 0)))  # Yellow color
                pixel.setPos(x, y)
                self.scene.addItem(pixel)
    
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