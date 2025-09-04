import sys
import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
import json
import os
from helper_classes import FifoWatcher

# Load sensor geometry config.
with open("sensor_config.json", "r") as f:
    sensor_config = json.load(f)

# Load FIFO watcher configuration
with open(os.path.join(os.path.dirname(__file__), 'fifo_config.json'), 'r') as f:
    fifo_config = json.load(f)

if sensor_config['hodo_front']['num_rows'] != 2:
    sys.exit("Error: hodo_front num_rows must be 2 for this code to work.")

# Global parameters
#OVERALL_SCALE = 0.150
#PIXEL_SIZE = int(100 * OVERALL_SCALE)
#GAP = int(11 * OVERALL_SCALE)
#OVERALL_WIDTH = 55 * PIXEL_SIZE + 13 * GAP  # New global variable for overall width

OVERALL_SCALE = 1.0
OVERALL_WIDTH = int(OVERALL_SCALE * 1050)
num_wls_pixels = sensor_config['wls_front']['num_cols']
frac = 0.05
PIXEL_SIZE = int(OVERALL_WIDTH/(num_wls_pixels*frac+num_wls_pixels-frac))
PIXEL_SIZE = round(OVERALL_WIDTH/((frac+1)*(num_wls_pixels-1)))
#PIXEL_SIZE = 33
GAP = int(PIXEL_SIZE * frac)
if GAP == 1:
    OVERALL_WIDTH = int(OVERALL_SCALE * PIXEL_SIZE*num_wls_pixels + GAP*(num_wls_pixels-1))
    PIXEL_SIZE = int(OVERALL_WIDTH/(num_wls_pixels*frac+num_wls_pixels-frac))
    PIXEL_SIZE = round(OVERALL_WIDTH/((frac+1)*(num_wls_pixels-1)))


def get_overall_width():
    """Calculate overall width based on the largest layer"""
    max_cols = max(sensor_config["hodo_front"]["num_cols"], sensor_config["wls_front"]["num_cols"])
    return max_cols * PIXEL_SIZE + (max_cols - 1) * GAP


# Add the external function to generate test data.
def calculate_total_data_points():
    """Calculate total data points needed based on sensor configuration"""
    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    print('Total number of pixels per layer:', num_pixels_per_layer)
    print('Total number of layers:', num_icc_layers)
    print('Total number of pixels:', num_icc_layers * num_pixels_per_layer)
    return num_icc_layers * num_pixels_per_layer

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
                #data_map[layer][rotated]['hodo_front'] = generate_creation_order(sensor_config["hodo_front"]["num_cols"], offset=hodo_offset1, top_first=True)
                data_map[layer][rotated]['hodo_front'] = generate_odd_even_list(num_hodo_pixels_per_layer, offset=hodo_offset1)
                #data_map[layer][rotated]['hodo_front'] = list(range(hodo_offset1, hodo_offset2))
                data_map[layer][rotated]['hodo_side'] = generate_odd_even_list(num_hodo_pixels_per_layer, offset=hodo_offset2)[-2:] # TODO: check if flipped and correct
                data_map[layer][rotated]['wls_side'] = list(range(wls_offset1, csi_offset))[-1]
                data_map[layer][rotated]['csi'] = [list(range(csi_offset, wls_offset2))[0]] # list of two and select first for non-rotated orientation
                data_map[layer][rotated]['wls_front'] = [list(range(wls_offset2, tail_offset))]
                data_map[layer][rotated]['tail'] = list(range(tail_offset, ending_offset))
            else:
                #data_map[layer][rotated]['hodo_side'] = generate_creation_order(sensor_config["hodo_front"]["num_cols"], offset=hodo_offset1, top_first=True)[:2] # TODO: check if flipped and correct
                #data_map[layer][rotated]['hodo_front'] = generate_creation_order(sensor_config["hodo_front"]["num_cols"], offset=hodo_offset2, top_first=False)
                data_map[layer][rotated]['hodo_side'] = generate_odd_even_list(num_hodo_pixels_per_layer, offset=hodo_offset1)[-2:]
                data_map[layer][rotated]['hodo_front'] = generate_odd_even_list(num_hodo_pixels_per_layer, offset=hodo_offset2)
                data_map[layer][rotated]['wls_front'] = list(range(wls_offset1, csi_offset))
                data_map[layer][rotated]['csi'] = [list(range(csi_offset, wls_offset2))[1]] # list of two and select second for rotated orientation
                data_map[layer][rotated]['wls_side'] = [list(range(wls_offset2, tail_offset))[0]]
                data_map[layer][rotated]['tail'] = list(range(tail_offset, ending_offset))

    return data_map

def create_reverse_data_map(data_map):
    """
    Creates a reverse mapping from absolute pixel index to (layer, rotated, component, relative_index).
    """
    reverse_map = {}
    for layer, rotated_data in data_map.items():
        for rotated, component_data in rotated_data.items():
            for component, pixel_indices in component_data.items():
                # Handle cases where pixel_indices is a list of lists (like wls_front in non-rotated)
                flat_indices = []
                if any(isinstance(i, list) for i in pixel_indices):
                    for sublist in pixel_indices:
                        flat_indices.extend(sublist)
                else:
                    flat_indices = pixel_indices

                if isinstance(flat_indices, list):
                    for i, abs_idx in enumerate(flat_indices):
                        reverse_map[abs_idx] = (layer, rotated, component, i)
                else: # for single values
                    reverse_map[flat_indices] = (layer, rotated, component, 0)
    return reverse_map

def translate_colleague_schema(colleague_data, total_pixels, data_map):
    """
    Translates data from the colleague's schema to the application's flat intensity list.

    This function assumes the colleague's 'axis' field ('x' or 'y') corresponds
    to the non-rotated and rotated views, respectively. It also assumes the 'ids'
    are enumerated across the primary components of that view (hodoscope, then WLS fibers).

    Args:
        colleague_data (dict): The data from the colleague, following their proposed schema.
        total_pixels (int): The total number of pixels in the detector.
        data_map (dict): The data map generated by generateDataMap.

    Returns:
        list: A flat list of intensities ready for setDetectorData.
    """
    intensities = [0] * total_pixels

    for layer_data in colleague_data.get("layers", []):
        layer_idx = layer_data.get("layer")
        axis = layer_data.get("axis")
        ids = layer_data.get("ids", [])
        values = layer_data.get("values", [])

        if layer_idx is None or axis is None or layer_idx not in data_map:
            continue

        # Map 'x'/'y' axis to rotated (0/1)
        rotated = 0 if axis == 'x' else 1

        if rotated not in data_map[layer_idx]:
            continue

        view_data = data_map[layer_idx][rotated]
        
        # The colleague's IDs are relative to the main components in that view.
        # For 'x' (rotated=0), this is hodo_front and wls_front.
        # For 'y' (rotated=1), this is also hodo_front and wls_front keys,
        # which map to the side hodoscope and side WLS fibers.
        hodo_pixels = view_data.get('hodo_front', [])
        wls_pixels = view_data.get('wls_front', [])

        # wls_front for rotated=0 is a list within a list
        if rotated == 0 and wls_pixels and isinstance(wls_pixels[0], list):
            wls_pixels = wls_pixels[0]

        for rel_id, value in zip(ids, values):
            if rel_id < len(hodo_pixels):
                # ID is in the hodoscope range
                abs_idx = hodo_pixels[rel_id]
                intensities[abs_idx] = value
            else:
                # ID is in the WLS fiber range, adjust index
                wls_rel_id = rel_id - len(hodo_pixels)
                if wls_rel_id < len(wls_pixels):
                    abs_idx = wls_pixels[wls_rel_id]
                    intensities[abs_idx] = value

    return intensities

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
                
        index_map += generate_creation_order(sensor_config["hodo_front"]["num_cols"], offset=hodo_offset1, top_first=True)
        index_map += generate_creation_order(sensor_config["hodo_front"]["num_cols"], offset=hodo_offset2, top_first=True)
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
        total_points = calculate_total_data_points()
        t = np.linspace(0, 2, 100) # dummy time axis
        dummy_waveform = np.zeros(100)
        sensor_data = [(t, dummy_waveform)] * total_points
        intensities = [0] * total_points
        self.setDetectorData(sensor_data, intensities)

    # Remove or leave generate_test_data_and_build_layout unused.
    # New external data setter is used to update the detector model.
    def setDetectorData(self, sensor_data, intensities):
        self.sensor_data = sensor_data
        min_intensity = min(intensities) if intensities else 0
        max_intensity = max(intensities) if intensities else 0
        # If pixel items already exist, just update them to preserve highlights
        if self.pixel_items:
            self.update_pixels(intensities, min_intensity, max_intensity)
        else:
            self._build_layout(intensities, min_intensity, max_intensity)
    
    def update_pixels(self, intensities, min_intensity, max_intensity):
        for idx, pixel in self.pixel_items.items():
            if idx < len(intensities) and idx < len(self.sensor_data):
                intensity = intensities[idx]
                pixel.time_series = self.sensor_data[idx]
                norm = (intensity - min_intensity) / (max_intensity - min_intensity + 1e-6)
                r = int(255 * norm)
                b = int(255 * (1 - norm))
                color = QtGui.QColor(r, 0, b)
                pixel.setBrush(QtGui.QBrush(color))

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
    
    # def build_hodo_front_layer(self, y_offset, intensities, min_intensity, max_intensity):
    #     overall_width = OVERALL_WIDTH
    #     num_cols = sensor_config["hodo_front"]["num_cols"]  # was sensor_config["front"]
    #     num_rows = sensor_config["hodo_front"]["num_rows"]    # was sensor_config["front"]
    #     adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
    #     radius = adaptive_size // 2
    #     # Use mapping from generateDataMap.
    #     mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['hodo_front']
    #     #print(f"Mapping for layer {self.layer} (rotate={self.rotate}): {mapping}")
    #     #print(f"Number of elements in mapping: {len(mapping)}")
    #     for row in range(num_rows):
    #         for col in range(num_cols):
    #             x = col * (adaptive_size + self.internal_gap) + (radius if row == 0 else 0)
    #             y = y_offset if row == 0 else y_offset + 2 * radius
    #             # get mapped index from the ordered list.
    #             #print(row * num_cols + col)
    #             mapped_idx = mapping[row * num_cols + col]
    #             #print(f"Mapped index: {mapped_idx}")
    #             #mapped_idx = row * num_cols + col
    #             rect = QtCore.QRectF(0, 0, adaptive_size, adaptive_size)
    #             pixel = PixelCircle(rect, self.sensor_data[mapped_idx], intensities[mapped_idx],
    #                                 min_intensity, max_intensity, self.on_pixel_clicked, mapped_idx)
    #             pixel.setPos(x, y)
    #             self.scene.addItem(pixel)
    #             self.pixel_items[mapped_idx] = pixel
    #     return y_offset + 2 * radius + adaptive_size
    
    def build_hodo_front_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        num_cols = sensor_config["hodo_front"]["num_cols"]  # was sensor_config["front"]
        num_rows = sensor_config["hodo_front"]["num_rows"]    # was sensor_config["front"]
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        #radius = adaptive_size // 2
        print((GAP + OVERALL_WIDTH - GAP*num_cols)/(2*num_cols + 1))
        radius = (GAP + OVERALL_WIDTH - GAP*num_cols)/(2*num_cols + 1)
        print(f"Calculated radius: {radius}")
        print(f"GAP: {GAP}")
        # Use mapping from generateDataMap.
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['hodo_front']
        #print(f"Mapping for layer {self.layer} (rotate={self.rotate}): {mapping}")
        #print(f"Number of elements in mapping: {len(mapping)}")
        for row in range(num_rows):
            for col in range(num_cols):
                x = col * (2*radius + self.internal_gap) + (radius if row == 0 else 0)
                y = y_offset if row == 0 else y_offset + 2 * radius
                # get mapped index from the ordered list.
                #print(row * num_cols + col)
                mapped_idx = mapping[row * num_cols + col]
                #print(f"Mapped index: {mapped_idx}")
                #mapped_idx = row * num_cols + col
                rect = QtCore.QRectF(0, 0, 2*radius, 2*radius)
                pixel = PixelCircle(rect, self.sensor_data[mapped_idx], intensities[mapped_idx],
                                    min_intensity, max_intensity, self.on_pixel_clicked, mapped_idx)
                pixel.setPos(x, y)
                self.scene.addItem(pixel)
                self.pixel_items[mapped_idx] = pixel
        return y_offset + 2 * round(radius) + adaptive_size

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
        #print(overall_width)
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

    #def build_wls_front_layer(self, y_offset, intensities, min_intensity, max_intensity):
    #    overall_width = OVERALL_WIDTH
    #    num_cols = sensor_config["wls_front"]["num_cols"]
    #    adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
    #    mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['wls_front']
    #    # mapping may be nested – use inner list if needed.
    #    mapping_list = mapping[0] if isinstance(mapping[0], list) else mapping
    #    for col in range(num_cols):
    #        x = col * (adaptive_size + self.internal_gap)
    #        mapped_idx = mapping_list[col]
    #        rect = QtCore.QRectF(0, 0, adaptive_size, adaptive_size)
    #        pixel = PixelRect(rect, self.sensor_data[mapped_idx], intensities[mapped_idx],
    #                          min_intensity, max_intensity, self.on_pixel_clicked, mapped_idx)
    #        pixel.setPos(x, y_offset)
    #        self.scene.addItem(pixel)
    #        self.pixel_items[mapped_idx] = pixel
    #    return y_offset + adaptive_size
    
    def build_wls_front_layer(self, y_offset, intensities, min_intensity, max_intensity):
        overall_width = OVERALL_WIDTH
        num_cols = sensor_config["wls_front"]["num_cols"]
        mapping = generateDataMap()[self.layer][0 if not self.rotate else 1]['wls_front']
        adaptive_size = int((overall_width - (num_cols - 1) * self.internal_gap) / num_cols)
        #print('BEEP')
        #print(adaptive_size)
        #print(PIXEL_SIZE)
        # mapping may be nested – use inner list if needed.
        mapping_list = mapping[0] if isinstance(mapping[0], list) else mapping
        for col in range(num_cols):
            x = col * (PIXEL_SIZE + self.internal_gap)
            #print(x)
            mapped_idx = mapping_list[col]
            rect = QtCore.QRectF(0, 0, PIXEL_SIZE, PIXEL_SIZE)
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

    def clear_highlight(self, idx):
        self.regular_view.clear_highlight(idx)
        self.rotated_view.clear_highlight(idx)

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

    def clear_highlight(self, idx):
        for layer in self.layers:
            layer.clear_highlight(idx)

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
        self.docks_in_order = []

        # Connect unified signal from DetectorMultiLayerWidget.
        self.detector_model.timeSeriesClicked.connect(self.on_pixel_selected)
        # Initialize display from one of the child widgets.
        self.detector_model.layers[0].regular_view.initializeDisplay()

        # Path to the array FIFO for lat/lon errors
        array_fifo_path = fifo_config['array']['path']
        self.array_fifo_watcher = FifoWatcher(array_fifo_path, poll_interval=fifo_config['array']['poll_interval'])
        self.array_fifo_watcher.data_received.connect(self.handle_array_fifo_data)
        self.array_fifo_watcher.start()

    def handle_array_fifo_data(self, data):
        try:
            # The data from the fifo is a string, so we need to parse it.
            # It will be a comma-separated list of numbers.
            str_values = data.strip().split(',')
            float_values = np.array([float(v) for v in str_values])
            t = np.linspace(0, 2, len(float_values)) # Create time axis
            total_points = calculate_total_data_points()
            sensor_data = []
            intensities = []
            rng = np.random.default_rng()
            
            for i in range(total_points):
                factor = rng.uniform(0.5, 2.0)
                this_sensor_data = float_values * factor
                sensor_data.append((t, this_sensor_data)) # Append tuple with time axis
                intensities.append(np.mean(this_sensor_data))

            self.detector_model.setDetectorData(sensor_data, intensities)
            self.updateDockPlots()

        except Exception as e:
            print(f"Error handling array data: {e}")
            pass

    def on_pixel_selected(self, time_series, idx):
        self.last_time_series = (time_series, idx)

    def add_time_series_dock(self):
        if self.last_time_series is None:
            print("No pixel selected.")
            return

        time_series, idx = self.last_time_series
        color = self.color_cycle[self.next_color_index]
        self.next_color_index = (self.next_color_index + 1) % len(self.color_cycle)

        dock_title = f"Pixel {idx}"
        new_dock = TimeSeriesDock(dock_title, pixel_index=idx, autoOrientation=False, closable=True)
        new_dock.color = color
        new_dock.highlight_clear_callback = self.detector_model.clear_highlight
        new_dock.remove_from_grid_callback = self.remove_dock_from_grid

        plot_widget = TimeSeriesPlotWidget()
        plot_widget.display_time_series(time_series, idx, color)
        new_dock.addWidget(plot_widget)

        if self.use_simple_layout:
            self.addDockVertically(new_dock)
        else:
            self.addDockToGrid(new_dock)

        self.detector_model.highlight_pixel(idx, color)
        self.ts_window.show()

    # New method for simple vertical layout
    def addDockVertically(self, dock):
        if self.last_dock is None:
            self.ts_dock_area.addDock(dock)
        else:
            self.ts_dock_area.addDock(dock, 'bottom', self.last_dock)
        self.last_dock = dock
        self.docks_in_order.append(dock)

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
            # Add to an existing column, below the previous dock in that column
            self.ts_dock_area.addDock(dock, 'bottom', self.ts_dock_grid[col][-1])
            self.ts_dock_grid[col].append(dock)
        
        self.ts_dock_count += 1

    # Modify the remove method to handle both layout modes
    def remove_dock_from_grid(self, dock):
        if self.use_simple_layout:
            if dock in self.docks_in_order:
                self.docks_in_order.remove(dock)
            if self.docks_in_order:
                self.last_dock = self.docks_in_order[-1]
            else:
                self.last_dock = None
        else:
            for col in self.ts_dock_grid:
                if dock in col:
                    col.remove(dock)
                    # If a column becomes empty, we could try to clean it up,
                    # but for now, we'll leave it.
                    break
            self.ts_dock_count -= 1

    def updateDockPlots(self):
        new_sensor_data = self.detector_model.layers[0].regular_view.sensor_data
        docks = self.ts_dock_area.findChildren(Dock)
        for dock in docks:
            if hasattr(dock, "pixel_index") and hasattr(dock, "color"):
                idx = dock.pixel_index
                color = dock.color
                if idx < len(new_sensor_data):
                    widgets = dock.widgets  # use the widgets list property
                    if widgets:
                        widgets[0].display_time_series(new_sensor_data[idx], idx, color)
                    self.detector_model.highlight_pixel(idx, color) # Re-apply highlight

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