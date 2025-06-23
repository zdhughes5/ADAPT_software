import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer
import random
from ADAPT_MainWindow import Ui_MainWindow
from custom_widgets import SignalRotatingArrowWidget, ScrollingRatePlotWidget
from helper_classes import FifoWatcher
import os
import math
import numpy as np
from astropy.coordinates import Angle
import astropy.units as u
from time import time
import pyqtgraph as pg
from ADAPT_MW import MainWindow as ArrayViewerWindow  # <-- Add this import

# Load FIFO watcher configuration
with open(os.path.join(os.path.dirname(__file__), 'fifo_config.json'), 'r') as f:
    fifo_config = json.load(f)

def precompute_circle_track(center_lat=-80, center_lon=166.6698, radius=10, num_steps=100):
    """
    Precompute a circle track around the south pole.
    
    Args:
        center_lat: Center latitude of the circle
        center_lon: Center longitude of the circle  
        radius: Radius in degrees
        num_steps: Number of steps in the circle
        
    Returns:
        List of (lon, lat) tuples
    """
    track_points = []
    for i in range(num_steps):
        angle = 2 * math.pi * i / num_steps
        lat = radius * math.cos(angle)
        lon = radius * math.sin(angle)
        # Ensure longitude wraps correctly
        if lon > 180:
            lon -= 360
        elif lon < -180:
            lon += 360
        track_points.append((lon, lat))
    print(f"Precomputed: {track_points}")

    return track_points

def precompute_circle_track2(radius=23, num_steps=100):
    """
    Precompute a circle track around the south pole.
    
    Args:
        center_lat: Center latitude of the circle
        center_lon: Center longitude of the circle  
        radius: Radius in degrees
        num_steps: Number of steps in the circle
        
    Returns:
        List of (lon, lat) tuples
    """
    lons = np.linspace(0, 360, num_steps)
    lats = radius*np.ones(num_steps) - 90  # All points at the same latitude
    track_points = [(lon, lat) for lon, lat in zip(lons, lats)]
    print(f"Precomputed: {track_points}")

    return track_points


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Precompute the circle track
        self.circle_track = precompute_circle_track2(radius=20, num_steps=20)
        self.current_track_index = 0
        
        # Use config for FIFO watcher setup
        self.fifo1_path = fifo_config['float1']['path']
        self.fifo2_path = fifo_config['float2']['path']
        self.fifo1_watcher = FifoWatcher(self.fifo1_path, poll_interval=fifo_config['float1']['poll_interval'])
        self.fifo2_watcher = FifoWatcher(self.fifo2_path, poll_interval=fifo_config['float2']['poll_interval'])
        self.fifo1_watcher.data_received.connect(self.handle_pointing_data)
        self.fifo1_watcher.data_received.connect(self.handle_fifo1_data)
        self.fifo2_watcher.data_received.connect(self.handle_fifo2_data)
        self.fifo1_watcher.start()
        self.fifo2_watcher.start()
        self.last_float1 = None
        self.last_float2 = None

        # Path to the array FIFO for lat/lon errors
        array_fifo_path = fifo_config['array']['path']
        self.array_fifo_watcher = FifoWatcher(array_fifo_path, poll_interval=fifo_config['array']['poll_interval'])
        #self.array_fifo_watcher.data_received.connect(self.handle_array_fifo_data)
        self.array_fifo_watcher.start()

        # Add ScrollingRatePlotWidget
        self.rate_plot_widget = ScrollingRatePlotWidget(array_size=100)
        # You may want to add this widget to your UI layout, e.g.:
        # self.ui.verticalLayout.addWidget(self.rate_plot_widget)
        # For now, just keep it as an attribute

        # Path to the FIFO (int1.fifo)
        int1_fifo_path = fifo_config['int1']['path']
        self.int1_fifo_watcher = FifoWatcher(int1_fifo_path, poll_interval=fifo_config['int1']['poll_interval'])
        self.int1_fifo_watcher.data_received.connect(self.handle_rate_data)
        self.int1_fifo_watcher.start()

        self.array_size1 = 20000
        self.data1 = np.zeros(self.array_size1)
        now = time()
        now_sub_one = now - 1
        self.times1 = np.linspace(now_sub_one, now, self.array_size1)
        self.ui.default_plot_widget.setLabel('left', 'Rate')
        self.ui.default_plot_widget.setLabel('bottom', 'Time')
        self.ui.default_plot_widget.showGrid(x=True, y=True)
        self.ui.default_plot_widget.addLegend()
        self.ui.default_plot_widget.setAxisItems({'bottom': pg.DateAxisItem()})
        self.curve = self.ui.default_plot_widget.plot(self.times1, self.data1, pen='y', name='Raw Rate')
        self.int1_fifo_watcher.data_received.connect(self.handle_rate_data1)

        # Connect array_viewer_button to launch the array viewer window
        if hasattr(self.ui, 'array_viewer_button'):
            self.ui.array_viewer_button.clicked.connect(self.launch_array_viewer)
        self.array_viewer_window = None  # Keep a reference

        # Add watcher for string.fifo and log to log_text_box
        if 'string' in fifo_config:
            self.string_fifo_watcher = FifoWatcher(fifo_config['string']['path'], poll_interval=fifo_config['string']['poll_interval'])
            self.string_fifo_watcher.data_received.connect(self.handle_string_fifo_data)
            self.string_fifo_watcher.start()


    def handle_pointing_data(self, data):
        try:
            angle = float(data)
            self.ui.pointing_widget.set_angle(angle)
        except Exception:
            pass

    def handle_fifo1_data(self, data):
        try:
            self.last_float1 = float(data)
            self.update_sexagesimal_lines()
        except Exception:
            pass

    def handle_fifo2_data(self, data):
        try:
            self.last_float2 = float(data)
            self.update_sexagesimal_lines()
        except Exception:
            pass

    def update_sexagesimal_lines(self):
        if self.last_float1 is not None and self.last_float2 is not None:
            # float1 as latitude, float2 as longitude
            lat_angle = Angle(self.last_float1, unit=u.deg)
            lon_angle = Angle(self.last_float2, unit=u.deg)
            lat_sex = lat_angle.to_string(unit=u.degree, sep=':', precision=2, pad=True)
            lon_sex = lon_angle.to_string(unit=u.degree, sep=':', precision=2, pad=True)
            # Write to all 6 fields
            self.ui.sun_sensor_line_1.setText(lat_sex)
            self.ui.sun_sensor_line_2.setText(lon_sex)
            self.ui.dpgs_line_1.setText(lat_sex)
            self.ui.dgps_line_2.setText(lon_sex)
            self.ui.ins_line_1.setText(lat_sex)
            self.ui.ins_line_2.setText(lon_sex)

    def handle_fifo_data(self, data):
        try:
            angle = float(data)
            self.ui.pointing_widget.set_angle(angle)
        except Exception:
            pass
    
    def handle_array_fifo_data(self, data):
        try:
            # Parse the comma-separated array data
            values = [float(x.strip()) for x in data.split(',')]
            if len(values) >= 2:
                # Scale the random values to +/- 5 degrees
                lat_error = (values[0] / 1000) * 5  # Scale from +/-1000 to +/-5
                lon_error = (values[1] / 1000) * 5  # Scale from +/-1000 to +/-5
                
                # Get the current point in the circle
                base_lon, base_lat = self.circle_track[self.current_track_index]
                
                # Add jitter
                jittered_lon = base_lon + lon_error
                jittered_lat = base_lat + lat_error
                
                # Add the point to the map
                self.ui.tracker_widget.add_point(jittered_lon, jittered_lat)
                
                # Move to the next point in the circle
                self.current_track_index = (self.current_track_index + 1) % len(self.circle_track)
        except Exception as e:
            print(f"Error handling array FIFO data: {e}")
            pass
        
    def handle_rate_data(self, data):
        try:
            value = float(data)
            # Optionally, you could use the current timestamp for x, but the widget uses a fixed x axis
            current_time = time()
            self.rate_plot_widget.update_plot(current_time, value)
            print(f"Rate data received: {value}")
        except Exception as e:
            print(f"Error handling rate data: {e}")
            pass

    def handle_rate_data1(self, data):
        try:
            value = float(data)
            current_time = time()
            self.data1 = np.roll(self.data1, -1)
            self.times1 = np.roll(self.times1, -1)
            self.times1[-1] = current_time
            self.data1[-1] = data
            self.curve.setData(x=self.times1, y=self.data1)
            self.ui.default_plot_widget.setXRange(current_time-20, current_time)
            # Update legend to show latest value
            legend = self.ui.default_plot_widget.legend
            if legend is not None:
                # Remove all legend items and re-add with updated label
                legend.clear()
                self.curve.setName(f'Raw Rate: {value:.2f}')
                legend.addItem(self.curve, self.curve.name())
            print(f"Rate data received: {value}")
        except Exception as e:
            print(f"Error handling rate data: {e}")
            pass
        
    def handle_string_fifo_data(self, data):
        # Append the string data to the log_text_box
        current = self.ui.log_text_box.toPlainText()
        if current:
            self.ui.log_text_box.setPlainText(current + '\n' + data)
        else:
            self.ui.log_text_box.setPlainText(data)
        # Scroll to bottom
        self.ui.log_text_box.verticalScrollBar().setValue(self.ui.log_text_box.verticalScrollBar().maximum())

    def launch_array_viewer(self):
        if self.array_viewer_window is None or not self.array_viewer_window.isVisible():
            self.array_viewer_window = ArrayViewerWindow()
            self.array_viewer_window.show()
        else:
            self.array_viewer_window.raise_()
            self.array_viewer_window.activateWindow()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
