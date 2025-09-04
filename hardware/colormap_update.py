import time

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
from time import perf_counter


# This function generates the hexgonal array x's and y's in the required ordering.
# It is ugly, but works for now.
def drawHexGridLoop2(origin, depth, apothem, padding):
    def getCoords(xs, ys):
        xs = [item for sublist in xs for item in sublist]
        ys = [item for sublist in ys for item in sublist]
        coords = list(zip(xs, ys))
        return coords

    def flattenList(l):
        rv = [item for sublist in l for item in sublist]
        return rv

    ang60 = np.deg2rad(60)
    xs = [[origin[0]]]
    ys = [[origin[1]]]
    labels = [['1']]
    labelN = 2
    thisX = 0
    thisY = 0
    for d in range(1, depth):
        thisXArr = []
        thisYArr = []
        thisLabelArr = []
        loc = 1
        n = 0
        while n < d * 6:
            if n == 0:
                anchorN = 0
                thisX = round(xs[-1][0] + 2 * apothem, 8)
                thisY = round(ys[-1][0], 8)
                anchorX = xs[-1][anchorN]
                anchorY = ys[-1][anchorN]
                thisXArr.append(thisX)
                thisYArr.append(thisY)
                thisLabelArr.append(str(labelN))
                labelN += 1

            else:
                thisX = round(anchorX + 2 * apothem * np.cos(-1 * ang60 * loc), 8)
                thisY = round(anchorY + 2 * apothem * np.sin(-1 * ang60 * loc), 8)
                if (thisX, thisY) in getCoords(xs, ys):
                    anchorN += 1
                    anchorX = xs[-1][anchorN]
                    anchorY = ys[-1][anchorN]
                    loc -= 1
                    continue
                thisXArr.append(thisX)
                thisYArr.append(thisY)
                thisLabelArr.append(str(labelN))
                labelN += 1
                loc += 1
            n += 1
        xs.append(thisXArr)
        ys.append(thisYArr)
        labels.append(thisLabelArr)
    xs = flattenList(xs)
    ys = flattenList(ys)
    labels = flattenList(labels)
    return xs, ys, labels


# Function to create the scatter plot in each viewbox.
# Adapted from ScatterPlotItem.py
def createArray(w):
    s = pg.ScatterPlotItem(
        pxMode=False,  # Set pxMode=False to allow spots to transform with the view
        hoverable=True,
        hoverPen=pg.mkPen('g'),
        hoverSize=hexSize
    )
    spots = []
    xs, ys, labels = drawHexGridLoop2((0, 0), 14, 1e-6, 0)
    for i, thing in enumerate(xs):
        spots.append(
            {'pos': (xs[i], ys[i]), 'size': hexSize, 'pen': {'color': 'w', 'width': 2}, 'brush': pg.intColor(10, 10),
             'symbol': 'h'})
    s.addPoints(spots)
    w.addItem(s)

    return w, s, spots, xs, ys


hexSize = 2.2e-6
app = pg.mkQApp("Scatter Plot Item Example")
mw = QtWidgets.QMainWindow()
mw.resize(800, 800)
view = pg.GraphicsLayoutWidget()  ## GraphicsView with GraphicsLayout inserted by default
mw.setCentralWidget(view)
mw.show()
mw.setWindowTitle('pyqtgraph example: ScatterPlot')
view.ci.setBorder((50, 50, 100))

## create four areas to add plots
w1 = view.addViewBox()
w1.setAspectLocked()
w2 = view.addViewBox()
w2.setAspectLocked()
view.nextRow()
w3 = view.addViewBox()
w3.setAspectLocked()
w4 = view.addViewBox()
w4.setAspectLocked()

# Create the scatter plots.
w1, s1, spots1, xs, ys = createArray(w1)
w2, s2, spots1, xs, ys = createArray(w2)
w3, s3, spots1, xs, ys = createArray(w3)
w4, s4, spots1, xs, ys = createArray(w4)

# Create the color map.
# Adapted from https://github.com/pyqtgraph/pyqtgraph/issues/1712#issuecomment-819745370
nPts = 255
colormap = pg.colormap.get('cividis')
valueRange = np.linspace(0, 255, num=nPts)
colors = colormap.getLookupTable(0, 1, nPts=nPts)

# *** Create brushes lookup table
brushes_table = [QtGui.QBrush(QtGui.QColor(*color)) for color in colors]

fps = None
lastTime = perf_counter()


def update():
    global fps, lastTime
    z = np.random.randint(0, 255, size=547)
    # *** Create array of already created brushes from lookup table
    brushes = [brushes_table[i] for i in z]
    s1.setBrush(brushes)  # Now update is much faster!
    s2.setBrush(brushes)
    s3.setBrush(brushes)
    s4.setBrush(brushes)
    now = perf_counter()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0 / dt
    else:
        s = np.clip(dt * 3., 0, 1)
        fps = fps * (1 - s) + (1.0 / dt) * s
    mw.setWindowTitle('%0.2f fps' % fps)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    pg.exec()