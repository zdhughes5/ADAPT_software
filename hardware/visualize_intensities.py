import sys
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.dockarea
import numpy as np

N_ELEMENTS = 10

class CustomScatterPlotItem(pg.ScatterPlotItem):
    sigRightClicked = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def hoverEvent(self, ev):
        if ev.isEnter():
            ev.acceptClicks(QtCore.Qt.MouseButton.RightButton)
        super().hoverEvent(ev)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            pts = self.pointsAt(ev.pos())
            if len(pts) > 0:
                self.sigRightClicked.emit(pts[0])
                ev.accept()
        else:
            super().mouseClickEvent(ev)


def create_text_symbol(label, font_size=10):
    """Creates a QPainterPath from a text label to use as a scatter plot symbol."""
    path = QtGui.QPainterPath()
    font = QtGui.QFont()
    font.setPointSize(font_size)
    path.addText(0, 0, font, label)
    # Center the text and normalize its size
    br = path.boundingRect()
    scale = 1.0 / br.width()
    transform = QtGui.QTransform()
    transform.scale(scale, scale)
    transform.translate(-br.center().x(), -br.center().y())
    return transform.map(path)


def generate_grid_positions(num_items, items_per_row, spacing):
    """Generates centered grid positions."""
    positions = []
    if num_items == 0:
        return positions
    
    num_rows = (num_items - 1) // items_per_row + 1
    grid_width = (min(num_items, items_per_row) - 1) * spacing
    grid_height = (num_rows - 1) * spacing
    
    start_x = -grid_width / 2.0
    start_y = -grid_height / 2.0

    for i in range(num_items):
        row = i // items_per_row
        col = i % items_per_row
        x = start_x + col * spacing
        y = start_y + row * spacing
        positions.append((x, y))
    return positions

def generate_layout_config(
    num_motherboards, num_daughter_boards_per_mb, num_pixels_per_db,
    mb_per_row, db_per_row, px_per_row,
    mb_size, db_size, px_size,
    mb_spacing, db_spacing, px_spacing,
    mb_label_offset, db_label_offset,
    mb_label_font_size, db_label_font_size,
    mb_label_scale, db_label_scale
):
    """Programmatically generates the layout configuration."""
    layout_config = []
    
    mb_positions = generate_grid_positions(num_motherboards, mb_per_row, mb_spacing)

    for mb_i in range(num_motherboards):
        mb_pos = mb_positions[mb_i]
        mb_label_pos = (mb_pos[0], mb_pos[1] + mb_label_offset)
        
        db_positions = generate_grid_positions(num_daughter_boards_per_mb, db_per_row, db_spacing)
        
        daughter_boards = []
        for db_i in range(num_daughter_boards_per_mb):
            db_pos_rel = db_positions[db_i]
            db_pos_abs = (mb_pos[0] + db_pos_rel[0], mb_pos[1] + db_pos_rel[1])
            db_label_pos = (db_pos_abs[0], db_pos_abs[1] + db_label_offset)

            px_positions = generate_grid_positions(num_pixels_per_db, px_per_row, px_spacing)
            
            pixels = []
            for px_i in range(num_pixels_per_db):
                px_pos_rel = px_positions[px_i]
                px_pos_abs = (db_pos_abs[0] + px_pos_rel[0], db_pos_abs[1] + px_pos_rel[1])
                pixels.append({'pos': px_pos_abs, 'size': px_size})

            daughter_boards.append({
                'pos': db_pos_abs,
                'size': db_size,
                'pixels': pixels,
                'label': f"DB {db_i + 1}",
                'label_pos': db_label_pos,
                'label_font_size': db_label_font_size,
                'label_scale': db_label_scale
            })

        layout_config.append({
            'pos': mb_pos,
            'size': mb_size,
            'daughter_boards': daughter_boards,
            'label': f"MB {mb_i + 1}",
            'label_pos': mb_label_pos,
            'label_font_size': mb_label_font_size,
            'label_scale': mb_label_scale
        })
        
    return layout_config


class WaveformViewWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Waveforms")
        self.setGeometry(200, 200, 500, 400)
        self.area = pg.dockarea.DockArea()
        self.setCentralWidget(self.area)
        self.docks = {}  # store docks by index
        self.plot_items = {}  # store plot items by index

    def clear_docks(self):
        # Close and remove all docks and plot items
        for dock in list(self.docks.values()):
            dock.close()
        self.docks.clear()
        self.plot_items.clear()

    def update_waveform(self, index, waveform):
        dock_name = f"Waveform for spot {index}"

        if index not in self.docks:
            dock = pg.dockarea.Dock(dock_name, size=(400, 300), closable=True)
            plot_widget = pg.PlotWidget()
            dock.addWidget(plot_widget)
            self.area.addDock(dock)
            self.docks[index] = dock
            # Create plot item only once
            plot_item = plot_widget.plot(waveform, pen='y')
            self.plot_items[index] = plot_item

            def dock_closed():
                if index in self.docks:
                    del self.docks[index]
                if index in self.plot_items:
                    del self.plot_items[index]

            dock.sigClosed.connect(dock_closed)
        else:
            dock = self.docks[index]
            plot_widget = dock.widgets[0]
            plot_item = self.plot_items.get(index)
            if plot_item is not None:
                plot_item.setData(waveform)
            else:
                plot_item = plot_widget.plot(waveform, pen='y')
                self.plot_items[index] = plot_item

    def update_open_waveforms(self, all_waveforms):
        open_indices = list(self.docks.keys())
        for index in open_indices:
            if index < len(all_waveforms):
                new_waveform = all_waveforms[index]
                self.update_waveform(index, new_waveform)
            else:
                if index in self.docks:
                    self.docks[index].close()


class IntensityScatterPlotWidget(QtWidgets.QWidget):
    waveform_selected = QtCore.pyqtSignal(int, np.ndarray)
    all_waveforms_selected = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.getPlotItem().hideAxis('left')
        self.plot_widget.getPlotItem().hideAxis('bottom')
        self.plot_widget.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False)

        self.scatter = CustomScatterPlotItem(
            size=50, symbol="s", borderWidth=2, pen=pg.mkPen(None), hoverable=True, hoverPen=pg.mkPen('r', width=2)
        )
        self.scatter.sigRightClicked.connect(self.on_spot_right_clicked)
        self.plot_widget.addItem(self.scatter)
        self.plot_widget.setAspectLocked(True)
        
        self.waveforms = []
        
        # Generate layout configuration
        self.layout_config = generate_layout_config(
            num_motherboards=12, num_daughter_boards_per_mb=6, num_pixels_per_db=32,
            mb_per_row=4, db_per_row=3, px_per_row=8,
            mb_size=300.0, db_size=90.0, px_size=9,
            mb_spacing=5.0, db_spacing=1.5, px_spacing=0.18,
            mb_label_offset=1.9, db_label_offset=0.55,
            mb_label_font_size=10, db_label_font_size=8,
            mb_label_scale=60, db_label_scale=25
        )

        # Create points and a map to identify them
        spots = []
        self.point_map = []
        pixel_waveform_idx = 0

        # The order of adding points matters for z-index: MBs -> DBs -> Pixels
        # Motherboards
        for mb_idx, mb_config in enumerate(self.layout_config):
            spots.append({
                'pos': mb_config['pos'], 'size': mb_config['size'],
                'brush': pg.mkBrush(50, 50, 50, 150), 'pen': pg.mkPen(None)
            })
            self.point_map.append({'type': 'mb', 'mb_idx': mb_idx})

        # Daughterboards
        for mb_idx, mb_config in enumerate(self.layout_config):
            for db_idx, db_config in enumerate(mb_config['daughter_boards']):
                spots.append({
                    'pos': db_config['pos'], 'size': db_config['size'],
                    'brush': pg.mkBrush(100, 100, 100, 150), 'pen': pg.mkPen(None)
                })
                self.point_map.append({'type': 'db', 'mb_idx': mb_idx, 'db_idx': db_idx})

        # Pixels
        for mb_idx, mb_config in enumerate(self.layout_config):
            for db_idx, db_config in enumerate(mb_config['daughter_boards']):
                for px_idx, px_config in enumerate(db_config['pixels']):
                    spots.append({
                        'pos': px_config['pos'],
                        'size': px_config['size'],
                        'symbol': 's' # Ensure pixels are squares
                    })
                    self.point_map.append({
                        'type': 'px', 'waveform_idx': pixel_waveform_idx
                    })
                    pixel_waveform_idx += 1
        
        # Labels
        for mb_config in self.layout_config:
            spots.append({
                'pos': mb_config['label_pos'],
                'size': mb_config['label_scale'],
                'symbol': create_text_symbol(mb_config['label'], mb_config['label_font_size']),
                'pen': pg.mkPen('w')
            })
            self.point_map.append({'type': 'label'})
            for db_config in mb_config['daughter_boards']:
                spots.append({
                    'pos': db_config['label_pos'],
                    'size': db_config['label_scale'],
                    'symbol': create_text_symbol(db_config['label'], db_config['label_font_size']),
                    'pen': pg.mkPen('w')
                })
                self.point_map.append({'type': 'label'})

        self.num_pixels = pixel_waveform_idx
        self.scatter.addPoints(spots)

        # Set plot range dynamically based on layout
        all_x = [s['pos'][0] for s in spots]
        all_y = [s['pos'][1] for s in spots]
        x_range = [min(all_x) - 1, max(all_x) + 1]
        y_range = [min(all_y) - 1, max(all_y) + 1]
        self.plot_widget.setRange(xRange=x_range, yRange=y_range)

        # Create colormap and brush lookup table
        self.nPts = 256
        colormap = pg.colormap.get("viridis")
        colors = colormap.getLookupTable(0, 1, nPts=self.nPts)
        self.brushes_table = [QtGui.QBrush(QtGui.QColor(*color)) for color in colors]

    def on_spot_right_clicked(self, spot):
        menu = QtWidgets.QMenu()
        view_waveform_action = menu.addAction("View Waveform...")

        selected_action = menu.exec(QtGui.QCursor.pos())

        if selected_action == view_waveform_action:
            spot_index = spot.index()
            point_info = self.point_map[spot_index]

            if point_info['type'] == 'px':
                waveform_idx = point_info['waveform_idx']
                if self.waveforms and 0 <= waveform_idx < len(self.waveforms):
                    waveform = self.waveforms[waveform_idx]
                    self.waveform_selected.emit(waveform_idx, waveform)
            elif point_info['type'] == 'db' or point_info['type'] == 'mb':
                # Collect all waveforms associated with the clicked board
                waveforms_to_show = []
                start_idx, end_idx = self.get_waveform_indices_for_board(point_info)
                if self.waveforms:
                    waveforms_to_show = self.waveforms[start_idx:end_idx]
                
                self.all_waveforms_selected.emit(waveforms_to_show)

    def get_waveform_indices_for_board(self, point_info):
        """Get start and end waveform indices for a given motherboard or daughterboard."""
        start_idx = -1
        count = 0
        
        current_pixel_idx = 0
        for mb_idx, mb_config in enumerate(self.layout_config):
            if point_info['type'] == 'mb' and point_info['mb_idx'] != mb_idx:
                current_pixel_idx += sum(len(db['pixels']) for db in mb_config['daughter_boards'])
                continue

            for db_idx, db_config in enumerate(mb_config['daughter_boards']):
                num_pixels_in_db = len(db_config['pixels'])
                if point_info['type'] == 'db':
                    if point_info['mb_idx'] == mb_idx and point_info['db_idx'] == db_idx:
                        start_idx = current_pixel_idx
                        count = num_pixels_in_db
                        break 
                else: # Motherboard
                    if start_idx == -1:
                        start_idx = current_pixel_idx
                    count += num_pixels_in_db
                
                current_pixel_idx += num_pixels_in_db
            
            if start_idx != -1 and point_info['type'] == 'mb':
                break # Found all pixels for this MB

        return start_idx, start_idx + count

    def generate_waveforms(self):
        """Generates random N_ELEMENTS-element arrays for each pixel."""
        return [np.random.rand(N_ELEMENTS) for _ in range(self.num_pixels)]

    def update_plot(self):
        """Generates new data and updates the plot."""
        self.waveforms = self.generate_waveforms()
        intensities = [np.sum(wf) for wf in self.waveforms]

        # Normalize intensities to be between 0 and 1 for the colormap
        min_intensity = 0
        max_intensity = N_ELEMENTS * 1
        
        # Create array of brushes from lookup table for pixels
        brush_indices = [
            int(((i - min_intensity) / (max_intensity - min_intensity)) * (self.nPts - 1))
            for i in intensities
        ]
        pixel_brushes = [self.brushes_table[i] for i in brush_indices]

        # Construct the full list of brushes in the correct order
        all_brushes = []
        # Motherboard brushes
        all_brushes.extend([pg.mkBrush(50, 50, 50, 150)] * len([p for p in self.point_map if p['type'] == 'mb']))
        # Daughterboard brushes
        all_brushes.extend([pg.mkBrush(100, 100, 100, 150)] * len([p for p in self.point_map if p['type'] == 'db']))
        # Pixel brushes
        all_brushes.extend(pixel_brushes)
        # Label brushes
        num_labels = len([p for p in self.point_map if p['type'] == 'label'])
        all_brushes.extend([pg.mkBrush('w')] * num_labels)

        self.scatter.setBrush(all_brushes)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Waveform Intensity Visualization")
        self.setGeometry(100, 100, 1540, 1100)

        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        self.scatter_widget = IntensityScatterPlotWidget()
        layout.addWidget(self.scatter_widget)

        self.next_button = QtWidgets.QPushButton("Next Data")
        layout.addWidget(self.next_button)

        self.next_button.clicked.connect(self.update_all_plots)
        self.scatter_widget.waveform_selected.connect(self.show_waveform)
        self.scatter_widget.all_waveforms_selected.connect(self.show_all_waveforms)

        self.waveform_window = None

        self.scatter_widget.update_plot()

        # Add a timer to update data automatically every 1 second
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_all_plots)
        self.timer.start(10)  # 1000 ms = 1 second

    def update_all_plots(self):
        self.scatter_widget.update_plot()
        if self.waveform_window:
            self.waveform_window.update_open_waveforms(self.scatter_widget.waveforms)

    def show_all_waveforms(self, waveforms):
        if self.waveform_window is None:
            self.waveform_window = WaveformViewWindow()
            self.waveform_window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
            self.waveform_window.destroyed.connect(self.on_waveform_window_destroyed)
        else:
            self.waveform_window.clear_docks()  # Clear old docks before adding new ones
        for i, wf in enumerate(waveforms):
            self.waveform_window.update_waveform(i, wf)
        self.waveform_window.show()
        self.waveform_window.activateWindow()

    def show_waveform(self, index, waveform):
        if self.waveform_window is None:
            self.waveform_window = WaveformViewWindow()
            self.waveform_window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
            self.waveform_window.destroyed.connect(self.on_waveform_window_destroyed)

        self.waveform_window.update_waveform(index, waveform)
        self.waveform_window.show()
        self.waveform_window.activateWindow()

    def on_waveform_window_destroyed(self):
        self.waveform_window = None


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
