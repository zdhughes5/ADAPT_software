import sys
import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
import json

# Load sensor geometry config.
with open("sensor_config.json", "r") as f:
    sensor_config = json.load(f)

if sensor_config['hodo_front']['num_rows'] != 2:
    sys.exit("Error: hodo_front num_rows must be 2 for this code to work.")

# Global parameters
OVERALL_SCALE = 0.250
PIXEL_SIZE = int(100 * OVERALL_SCALE)
GAP = int(10 * OVERALL_SCALE)
OVERALL_WIDTH = 15 * PIXEL_SIZE + 13 * GAP  # New global variable for overall width


# Add the external function to generate test data.
def generate_test_data():
    sensor_data = []
    intensities = []
    for i in range(416):
        t = np.linspace(0, 2, 100)
        phase = np.random.uniform(0, np.pi)
        data = np.sin(2 * np.pi * t / 2 + phase) + np.random.normal(0, 0.2, t.shape)
        #data = np.array([i % 14] * 100)
        sensor_data.append((t, data))
        intensities.append(np.sum(data))
    
    #data_indices = mixedDataIndicies()
    #print(type(data_indices))
    #print(len(data_indices))
    #print(len(sensor_data))
    #print(len(intensities))
    #print(type(sensor_data))
    #print(type(intensities))
    
    # Reorder the lists using list comprehension
    #reordered_sensor_data = [sensor_data[i] for i in data_indices]
    #reordered_intensities = [intensities[i] for i in data_indices]
    
    #return reordered_sensor_data, reordered_intensities
    return sensor_data, intensities


def generate_creation_order(num_pixels_per_row, offset=0, top_first=False):
    """
    Returns pixel indices in top-row-first-then-bottom order,
    assuming 'pixel number' order is bottom0, top0, bottom1, top1, etc.
    """
    row1 = list(range(offset, offset + num_pixels_per_row))
    row2 = list(range(offset + num_pixels_per_row, offset + 2 * num_pixels_per_row))
    if top_first:
        return [val for pair in zip(row1, row2) for val in pair]
    else:
        return [val for pair in zip(row2, row1) for val in pair]
    
def generate_odd_even_list(length, offset=0, even_first=False):
    """
    Generates a list of numbers with odd values first and then even values,
    or the reverse if even_first is True.

    Args:
        length (int): The total number of values to generate.
        offset (int): The starting value for the sequence.
        even_first (bool): If True, places even values first, then odd values.

    Returns:
        list: A reordered list of numbers.
    """
    # Generate the sequence of numbers
    numbers = list(range(offset, offset + length))
    
    # Separate odd and even values
    odd_values = [n for n in numbers if n % 2 != 0]
    even_values = [n for n in numbers if n % 2 == 0]
    
    # Determine the order
    if even_first:
        return even_values + odd_values
    else:
        return odd_values + even_values

def generateDataMap():
    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    data_map = {}
    for layer in range(num_icc_layers):

        data_map[layer] = {}

        base = layer * num_pixels_per_layer
        hodo_offset1 = base
        hodo_offset2 = hodo_offset1 + num_hodo_pixels_per_layer
        wls_offset1 = hodo_offset2 + num_hodo_pixels_per_layer
        csi_offset = wls_offset1 + num_wls_pixels_per_layer
        wls_offset2 = csi_offset + num_csi_pixels
        tail_offset = wls_offset2 + num_wls_pixels_per_layer
        ending_offset = tail_offset + num_tail_pixels

        for rotated in range(2): #0 = not rotated, 1 = rotated
            data_map[layer][rotated] = {}
            if rotated == 0:
                #data_map[layer][rotated]['hodo_front'] = generate_creation_order(14, offset=hodo_offset1, top_first=True)
                data_map[layer][rotated]['hodo_front'] = generate_odd_even_list(28, offset=hodo_offset1)
                #data_map[layer][rotated]['hodo_front'] = list(range(hodo_offset1, hodo_offset2))
                data_map[layer][rotated]['hodo_side'] = generate_odd_even_list(28, offset=hodo_offset2)[-2:] # TODO: check if flipped and correct
                data_map[layer][rotated]['wls_side'] = list(range(wls_offset1, csi_offset))[-1]
                data_map[layer][rotated]['csi'] = [list(range(csi_offset, wls_offset2))[0]] # list of two and select first for non-rotated orientation
                data_map[layer][rotated]['wls_front'] = [list(range(wls_offset2, tail_offset))]
                data_map[layer][rotated]['tail'] = list(range(tail_offset, ending_offset))
            else:
                data_map[layer][rotated]['hodo_side'] = generate_creation_order(14, offset=hodo_offset1, top_first=True)[:2] # TODO: check if flipped and correct
                data_map[layer][rotated]['hodo_front'] = generate_creation_order(14, offset=hodo_offset2, top_first=False)
                data_map[layer][rotated]['wls_front'] = list(range(wls_offset1, csi_offset))
                data_map[layer][rotated]['csi'] = [list(range(csi_offset, wls_offset2))[1]] # list of two and select second for rotated orientation
                data_map[layer][rotated]['wls_side'] = [list(range(wls_offset2, tail_offset))[0]]
                data_map[layer][rotated]['tail'] = list(range(tail_offset, ending_offset))

    return data_map

def mixedDataIndicies():

    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    index_map = []
    for layer in range(num_icc_layers):
        
        base = layer * num_pixels_per_layer
        hodo_offset1 = base
        hodo_offset2 = hodo_offset1 + num_hodo_pixels_per_layer
        wls_offset1 = hodo_offset2 + num_hodo_pixels_per_layer
        csi_offset = wls_offset1 + num_wls_pixels_per_layer
        wls_offset2 = csi_offset + num_csi_pixels
        tail_offset = wls_offset2 + num_wls_pixels_per_layer
        ending_offset = tail_offset + num_tail_pixels
                
        index_map += generate_creation_order(14, offset=hodo_offset1, top_first=True)
        index_map += generate_creation_order(14, offset=hodo_offset2, top_first=True)
        index_map += list(range(wls_offset1, csi_offset))
        index_map += list(range(csi_offset, wls_offset2)) # list of two and select first for non-rotated orientation
        index_map += list(range(wls_offset2, tail_offset))
        index_map += list(range(tail_offset, ending_offset))

    #print(len(index_map))
    return index_map


# New class for time series plotting
class TimeSeriesPlotWidget(pg.PlotWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLabel("bottom", "Time (µs)")
        self.setLabel("left", "Voltage")
    
    def display_time_series(self, time_series, idx, color=None):  # new color parameter
        self.clear()
        t, data = time_series
        pen_color = color if color is not None else 'w'
        self.plot(t, data, pen=pg.mkPen(pen_color, width=2))
        self.setTitle(f"Time Series for Selected Pixel {idx + 1}")

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
        self.click_callback(self.time_series, self.idx)
        super().mousePressEvent(event)

class PixelCircle(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, rect, time_series, intensity, min_intensity, max_intensity, click_callback, idx):
        super().__init__(rect)
        self.time_series = time_series
        self.click_callback = click_callback
        self.idx = idx
        norm = (intensity - min_intensity) / (max_intensity - min_intensity + 1e-6)
        r = int(255 * norm)
        b = int(255 * (1 - norm))
        color = QtGui.QColor(r, 0, b)
        self.setBrush(QtGui.QBrush(color))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.click_callback(self.time_series, self.idx)
        super().mousePressEvent(event)

# New widget encapsulating the geometry and its functionality.
class ICCLayerView(QtWidgets.QWidget):
    # New signal to communicate a pixel click with its time series data
    timeSeriesClicked = QtCore.pyqtSignal(object, int)
    
    def __init__(self, parent=None, internal_gap=GAP, rotate=False, layer=0):  # Added layer parameter
        super().__init__(parent)
        self.internal_gap = internal_gap
        self.rotate = rotate   # Store rotate flag
        self.layer = layer  # store layer number for mapping
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create GraphicsView and scene for the detector model only.
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        # Remove fixed height to allow dynamic sizing:
        # self.view.setFixedHeight(700)
        layout.addWidget(self.view)
        
        self.selected_pixel_idx = None
        self.sensor_data = []
        self.pixel_items = {}  # NEW: map pixel index to its QGraphicsItem
        # Initialize display with all intensities 0.
        self.initializeDisplay()  # new function call in __init__
    
    # New method to initialize the display with zero intensities.
    def initializeDisplay(self):
        sensor_data, intensities = generate_test_data()
        zero_intensities = [0] * len(intensities)  # set all intensity values to 0
        self.setDetectorData(sensor_data, zero_intensities)
    
    # Remove or leave generate_test_data_and_build_layout unused.
    # New external data setter is used to update the detector model.
    def setDetectorData(self, sensor_data, intensities):
        self.sensor_data = sensor_data
        min_intensity = min(intensities)
        max_intensity = max(intensities)
        self._build_layout(intensities, min_intensity, max_intensity)
    
    def _build_layout(self, intensities, min_intensity, max_intensity):
        self.scene.clear()
        if self.rotate:
            # When rotated, use side first then hodo front view logic
            y_bottom = self.build_hodo_side_layer(0, intensities, min_intensity, max_intensity)  # side layer
            y_bottom = self.build_hodo_front_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
            y_bottom = self.build_wls_front_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
            y_bottom = self.build_csi_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
            y_bottom = self.build_wls_side_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
        else:
            # Regular: hodo front then side, then side_wls then csi then hodo front wls
            y_bottom = self.build_hodo_front_layer(0, intensities, min_intensity, max_intensity)
            y_bottom = self.build_hodo_side_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
            y_bottom = self.build_wls_side_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
            y_bottom = self.build_csi_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
            y_bottom = self.build_wls_front_layer(y_bottom + GAP, intensities, min_intensity, max_intensity)
        final_height = self.build_tail_counters(intensities, y_bottom + GAP, min_intensity, max_intensity)
        self.view.setMinimumHeight(final_height)
        return final_height
    
    def build_hodo_front_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        num_cols = sensor_config["hodo_front"]["num_cols"]  # was sensor_config["front"]
        num_rows = sensor_config["hodo_front"]["num_rows"]    # was sensor_config["front"]
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        radius = adaptive_size // 2
        # Use mapping from generateDataMap.
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['hodo_front']
        print(f"Mapping for layer {self.layer} (rotate={self.rotate}): {mapping}")
        #print(f"Number of elements in mapping: {len(mapping)}")
        for row in range(num_rows):
            for col in range(num_cols):
                x = col * (adaptive_size + self.internal_gap) + (radius if row == 0 else 0)
                y = y_offset if row == 0 else y_offset + 2 * radius
                # get mapped index from the ordered list.
                print(row * num_cols + col)
                mapped_idx = mapping[row * num_cols + col]
                print(f"Mapped index: {mapped_idx}")
                #mapped_idx = row * num_cols + col
                rect = QtCore.QRectF(0, 0, adaptive_size, adaptive_size)
                pixel = PixelCircle(rect, self.sensor_data[mapped_idx], intensities[mapped_idx],
                                    min_intensity, max_intensity, self.on_pixel_clicked, mapped_idx)
                pixel.setPos(x, y)
                self.scene.addItem(pixel)
                self.pixel_items[mapped_idx] = pixel
        return y_offset + 2 * radius + adaptive_size

    def build_hodo_side_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        # Use same number of columns as hodo_front for width consistency.
        num_cols = sensor_config["hodo_front"]["num_cols"]
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        bottom_height = adaptive_size
        top_height = int(0.634 * bottom_height)
        new_gap = int(GAP / 5)
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['hodo_side']
        # Assume mapping order: [top, bottom] for nonrotated and vice versa for rotated.
        sensor_idx_top = mapping[0]
        intensity = intensities[sensor_idx_top]
        rect = QtCore.QRectF(0, 0, overall_width, top_height)
        pixel = PixelRect(rect, self.sensor_data[sensor_idx_top], intensity,
                          min_intensity, max_intensity, self.on_pixel_clicked, sensor_idx_top)
        pixel.setPos(0, y_offset)
        self.scene.addItem(pixel)
        self.pixel_items[sensor_idx_top] = pixel
        # Bottom row uses top index + 1
        sensor_idx_bottom = mapping[1]
        intensity = intensities[sensor_idx_bottom]
        rect = QtCore.QRectF(0, 0, overall_width, bottom_height)
        pixel = PixelRect(rect, self.sensor_data[sensor_idx_bottom], intensity,
                          min_intensity, max_intensity, self.on_pixel_clicked, sensor_idx_bottom)
        pixel.setPos(0, y_offset + top_height + new_gap)
        self.scene.addItem(pixel)
        self.pixel_items[sensor_idx_bottom] = pixel
        return y_offset + top_height + new_gap + bottom_height

    def build_wls_side_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        # Use same number of columns as wls_front for width consistency.
        num_cols = sensor_config["wls_front"]["num_cols"]
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        height = adaptive_size
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['wls_side']
        # Ensure mapping is a list.
        if not isinstance(mapping, list):
            mapping = [mapping]
        sensor_idx = mapping[0]
        intensity = intensities[sensor_idx]
        rect = QtCore.QRectF(0, 0, overall_width, height)
        pixel = PixelRect(rect, self.sensor_data[sensor_idx], intensity,
                          min_intensity, max_intensity, self.on_pixel_clicked, sensor_idx)
        pixel.setPos(0, y_offset)
        self.scene.addItem(pixel)
        self.pixel_items[sensor_idx] = pixel
        return y_offset + height

    def build_csi_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        num_cols = sensor_config["csi"]["num_cols"]
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        height = adaptive_size
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['csi']
        sensor_idx = mapping[0]
        intensity = intensities[sensor_idx]
        border_rect = QtCore.QRectF(0, 0, overall_width, height)
        border_item = QtWidgets.QGraphicsRectItem(border_rect)
        border_item.setBrush(QtGui.QColor("yellow"))
        border_item.setPos(0, y_offset)
        self.scene.addItem(border_item)
        constant_inset = 10
        inner_width = overall_width - 2 * constant_inset
        inner_height = height - 2 * constant_inset
        inner_rect = QtCore.QRectF(0, 0, inner_width, inner_height)
        pixel = PixelRect(inner_rect, self.sensor_data[sensor_idx], intensity,
                          min_intensity, max_intensity, self.on_pixel_clicked, sensor_idx)
        pixel.setPos(constant_inset, y_offset + constant_inset)
        self.scene.addItem(pixel)
        self.pixel_items[sensor_idx] = pixel
        return y_offset + height

    def build_wls_front_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        num_cols = sensor_config["wls_front"]["num_cols"]
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['wls_front']
        # mapping may be nested – use inner list if needed.
        mapping_list = mapping[0] if isinstance(mapping[0], list) else mapping
        for col in range(num_cols):
            x = col * (adaptive_size + self.internal_gap)
            mapped_idx = mapping_list[col]
            rect = QtCore.QRectF(0, 0, adaptive_size, adaptive_size)
            pixel = PixelRect(rect, self.sensor_data[mapped_idx], intensities[mapped_idx],
                              min_intensity, max_intensity, self.on_pixel_clicked, mapped_idx)
            pixel.setPos(x, y_offset)
            self.scene.addItem(pixel)
            self.pixel_items[mapped_idx] = pixel
        return y_offset + adaptive_size

    def build_tail_counters(self, intensities, y_offset, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        num_cols = sensor_config["tail_counters"]["num_cols"]
        num_rows = sensor_config["tail_counters"]["num_rows"]
        tail_width = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        height = PIXEL_SIZE // num_rows
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['tail']
        count = 0
        for col in range(num_cols):
            for row in range(num_rows):
                x = col * (tail_width + self.internal_gap)
                y = y_offset + row * (height + self.internal_gap)
                sensor_idx = mapping[count]
                intensity = intensities[sensor_idx]
                rect = QtCore.QRectF(0, 0, tail_width, height)
                pixel = PixelRect(rect, self.sensor_data[sensor_idx], intensity,
                                  min_intensity, max_intensity, self.on_pixel_clicked, sensor_idx)
                pixel.setPos(x, y)
                self.scene.addItem(pixel)
                self.pixel_items[sensor_idx] = pixel
                count += 1
        return y_offset + num_rows * height + self.internal_gap

    # New methods to highlight and clear a pixel border.
    def highlight_pixel(self, idx, color):
        if idx in self.pixel_items:
            self.pixel_items[idx].setPen(QtGui.QPen(QtGui.QColor(color), 3))
    def clear_highlight(self, idx):
        if idx in self.pixel_items:
            # Remove border (set no pen)
            self.pixel_items[idx].setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))

    # New callback method that emits a signal instead of plotting directly.
    def on_pixel_clicked(self, time_series, idx):
        self.selected_pixel_idx = idx
        self.timeSeriesClicked.emit(time_series, idx)

# NEW: New widget that shows both regular and rotated (rotated 90°) detector views.
class DetectorDualViewWidget(QtWidgets.QWidget):
    timeSeriesClicked = QtCore.pyqtSignal(object, int)   # unified signal
    
    def __init__(self, parent=None, internal_gap=GAP, layer=0):  # added layer
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        # Regular (non-rotated) view:
        self.regular_view = ICCLayerView(internal_gap=internal_gap, rotate=False, layer=layer)
        # Rotated view represents detector rotated 90°
        self.rotated_view = ICCLayerView(internal_gap=internal_gap, rotate=True, layer=layer)
        layout.addWidget(self.regular_view)
        layout.addWidget(self.rotated_view)
        # Connect both child signals to our unified signal
        self.regular_view.timeSeriesClicked.connect(self.timeSeriesClicked.emit)
        self.rotated_view.timeSeriesClicked.connect(self.timeSeriesClicked.emit)
    
    def setDetectorData(self, sensor_data, intensities):
        self.regular_view.setDetectorData(sensor_data, intensities)
        self.rotated_view.setDetectorData(sensor_data, intensities)
        
    def highlight_pixel(self, idx, color):
        self.regular_view.highlight_pixel(idx, color)
        self.rotated_view.highlight_pixel(idx, color)

# New subclass of Dock that clears pixel highlight on close.
class TimeSeriesDock(Dock):
    def __init__(self, title, pixel_index, *args, **kwargs):
        super().__init__(title, *args, **kwargs)
        self.pixel_index = pixel_index
        self.highlight_clear_callback = None
        self.remove_from_grid_callback = None  # New callback for grid cleanup
    
    def closeEvent(self, event):
        if self.highlight_clear_callback:
            self.highlight_clear_callback(self.pixel_index)
        if self.remove_from_grid_callback:
            self.remove_from_grid_callback(self)
        super().closeEvent(event)

# NEW: New widget that shows four stacked DetectorDualViewWidget layers.
class DetectorMultiLayerWidget(QtWidgets.QWidget):
    timeSeriesClicked = QtCore.pyqtSignal(object, int)
    
    def __init__(self, parent=None, internal_gap=GAP):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.layers = []
        for i in range(4):
            layer_widget = DetectorDualViewWidget(layer=i, internal_gap=internal_gap)
            layout.addWidget(layer_widget)
            layer_widget.timeSeriesClicked.connect(self.timeSeriesClicked.emit)
            self.layers.append(layer_widget)
    
    def setDetectorData(self, sensor_data, intensities):
        for layer in self.layers:
            layer.setDetectorData(sensor_data, intensities)
    
    def highlight_pixel(self, idx, color):
        for layer in self.layers:
            layer.highlight_pixel(idx, color)

# MainWindow now simply wraps ICCLayerView for easy embedding.
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Experimental System Layout Testbed")
        self.last_time_series = None  # store last selected pixel's time series
        # NEW: color cycle and pointer for unique colors.
        self.color_cycle = ['purple', 'red', 'green', 'blue', 'orange', 'magenta']
        self.next_color_index = 0
        
        # Left panel: now uses DetectorMultiLayerWidget instead of single DetectorDualViewWidget.
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        self.detector_model = DetectorMultiLayerWidget(internal_gap=1)
        left_layout.addWidget(self.detector_model)
        
        buttons_layout = QtWidgets.QHBoxLayout()
        self.next_button = QtWidgets.QPushButton("Next")
        self.next_button.clicked.connect(self.updateDetectorData)
        buttons_layout.addWidget(self.next_button)
        self.add_ts_button = QtWidgets.QPushButton("Add time series")
        self.add_ts_button.clicked.connect(self.add_time_series_dock)
        buttons_layout.addWidget(self.add_ts_button)
        left_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(left_panel)
        self.setCentralWidget(central_widget)
        self.resize(1000, 1200)
        
        # Create a separate popout window for the dock area.
        self.ts_dock_area = DockArea()
        self.ts_window = QtWidgets.QMainWindow()
        self.ts_window.setWindowTitle("Time Series Docks")
        self.ts_window.setCentralWidget(self.ts_dock_area)
        self.ts_window.resize(600, 600)
        
        # Flag to control layout behavior (True = simple vertical layout, False = grid layout)
        self.use_simple_layout = True
        
        # Initialize structures for grid layout tracking (even if not immediately used)
        self.ts_dock_grid = []
        self.ts_dock_count = 0
        self.last_dock = None  # Track the last added dock for simple vertical layout
        
        # Connect unified signal from DetectorMultiLayerWidget.
        self.detector_model.timeSeriesClicked.connect(self.on_pixel_selected)
        # Initialize display from one of the child widgets.
        self.detector_model.layers[0].regular_view.initializeDisplay()
    
    def on_pixel_selected(self, time_series, idx):
        self.last_time_series = (time_series, idx)
    
    def add_time_series_dock(self):
        if not self.last_time_series:
            return
        time_series, idx = self.last_time_series
        color = self.color_cycle[self.next_color_index % len(self.color_cycle)]
        self.next_color_index += 1
        self.detector_model.highlight_pixel(idx, color)
        dock = TimeSeriesDock(f"Time Series for Pixel {idx + 1}", idx, closable=True)
        dock.color = color
        dock.highlight_clear_callback = lambda i: self.detector_model.clear_highlight(i)
        dock.remove_from_grid_callback = lambda d: self.remove_dock_from_grid(d)
        ts_widget = TimeSeriesPlotWidget()
        ts_widget.display_time_series(time_series, idx, color)
        dock.addWidget(ts_widget)
        
        # Use either simple layout or grid layout based on the flag
        if self.use_simple_layout:
            self.addDockVertically(dock)
        else:
            self.addDockToGrid(dock)
            
        if not self.ts_window.isVisible():
            self.ts_window.show()
    
    # New method for simple vertical layout
    def addDockVertically(self, dock):
        # Check if last_dock is still valid (in the dock area)
        if self.last_dock is not None:
            # Verify the dock is still in the area
            docks = self.ts_dock_area.findChildren(Dock)
            if self.last_dock not in docks:
                self.last_dock = None  # Reset if no longer valid
        
        if self.last_dock is None:
            # First dock or no valid previous dock - add directly to the dock area
            self.ts_dock_area.addDock(dock)
        else:
            # Add below the last dock
            self.ts_dock_area.addDock(dock, 'bottom', self.last_dock)
        
        # Update the last dock reference
        self.last_dock = dock
    
    # Keep the existing grid layout method (unchanged)
    def addDockToGrid(self, dock):
        # Initialize grid tracking if not already done.
        if not hasattr(self, "ts_dock_count"):
            self.ts_dock_count = 0
            self.ts_dock_grid = []  # List of columns, each column is a list of docks
        
        col = self.ts_dock_count // 8   # 8 docks per column
        row = self.ts_dock_count % 8
        
        if col == len(self.ts_dock_grid):
            # New column: align rows with the previous column
            if col == 0:
                # First dock in the grid
                self.ts_dock_area.addDock(dock)
            else:
                # Add the first dock in the new column to the right of the first dock in the previous column
                self.ts_dock_area.addDock(dock, 'right', self.ts_dock_grid[col - 1][0])
            self.ts_dock_grid.append([dock])
        else:
            # Existing column: align the dock with the corresponding row in the previous column
            if row < len(self.ts_dock_grid[col - 1]):
                # Align with the corresponding row in the previous column
                self.ts_dock_area.addDock(dock, 'right', self.ts_dock_grid[col - 1][row])
            else:
                # If the previous column doesn't have this row, align below the last dock in the current column
                self.ts_dock_area.addDock(dock, 'bottom', self.ts_dock_grid[col][-1])
            self.ts_dock_grid[col].append(dock)

        self.ts_dock_count += 1
    
    # Modify the remove method to handle both layout modes
    def remove_dock_from_grid(self, dock):
        if self.use_simple_layout:
            # For simple layout, if this was the last dock, update the reference
            if self.last_dock == dock:
                # Find a new last dock among the remaining docks
                docks = self.ts_dock_area.findChildren(Dock)
                remaining_docks = [d for d in docks if d != dock and isinstance(d, TimeSeriesDock)]
                
                if remaining_docks:
                    self.last_dock = remaining_docks[-1]
                else:
                    self.last_dock = None
        else:
            # Grid layout handling (existing code)
            if hasattr(self, "ts_dock_grid"):
                for col_idx, column in enumerate(self.ts_dock_grid):
                    if dock in column:
                        column.remove(dock)
                        if len(column) == 0:
                            self.ts_dock_grid.pop(col_idx)
                        break

    def updateDetectorData(self):
        sensor_data, intensities = generate_test_data()
        self.detector_model.setDetectorData(sensor_data, intensities)
        # Reapply highlights using each active dock's stored color.
        docks = self.ts_dock_area.findChildren(Dock)
        for dock in docks:
            if hasattr(dock, "pixel_index") and hasattr(dock, "color"):
                self.detector_model.highlight_pixel(dock.pixel_index, dock.color)
        self.updateDockPlots()  # update open docks with new sensor data
    
    def updateDockPlots(self):
        new_sensor_data = self.detector_model.layers[0].regular_view.sensor_data
        docks = self.ts_dock_area.findChildren(Dock)
        for dock in docks:
            if hasattr(dock, "pixel_index") and hasattr(dock, "color"):
                idx = dock.pixel_index
                if idx < len(new_sensor_data):
                    widgets = dock.widgets  # use the widgets list property
                    if widgets:
                        widgets[0].display_time_series(new_sensor_data[idx], idx, dock.color)

    # Add a closeEvent handler to close the dock window when main window closes
    def closeEvent(self, event):
        # Close the dock area window if it exists
        if hasattr(self, "ts_window") and self.ts_window is not None:
            self.ts_window.close()
        
        # Proceed with the normal close event
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
    
if __name__ == '__main__':
    main()