from PyQt6 import QtWidgets
import pyqtgraph as pg

class Plot(pg.PlotWidget):

    def __init__(self):
        super().__init__()
        self.setMenuEnabled(False)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        someAction = menu.addAction('New_Item')

        res = menu.exec(event.globalPos())
        if res == someAction:
            print('Hello')


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    plot = Plot()
    plot.show()
    app.exec()