import folium
import io
import sys

from folium.plugins import Draw, MousePosition, HeatMap
from PyQt6 import QtWidgets, QtWebEngineWidgets
from PyQt6.QtCore import Qt

class FoliumMap(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.layout = QtWidgets.QVBoxLayout()
        m = folium.Map(
            title='coastlines',
            zoom_start=3)

        data = io.BytesIO()
        m.save(data, close_file=False)
        webView = QtWebEngineWidgets.QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        self.layout.addWidget(webView)
        self.setLayout(self.layout)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window title and size
        self.setWindowTitle("Folium Map Viewer")
        self.resize(1000, 800)
        
        # Create and set the folium map as central widget
        self.map_widget = FoliumMap()
        self.setCentralWidget(self.map_widget)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()