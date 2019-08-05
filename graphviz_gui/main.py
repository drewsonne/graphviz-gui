import sys
import tempfile
import threading
import time
from abc import ABC, abstractmethod

import click
import pydot
from PyQt5 import QtSvg
from PyQt5.QtCore import QFile, Qt, QSize, QTimer
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPixmap, QPen
from PyQt5.QtGui import QIcon
from PyQt5.QtOpenGL import QGL, QGLFormat, QGLWidget
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import (QFileDialog,
                             QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
                             QMainWindow, QMessageBox, QWidget)
from fbs_runtime.application_context.PyQt5 import ApplicationContext
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtCore import QSize


class Thread(ABC):
    def __init__(self):
        self._runtime_thread = None
        self._do_run = False
        self._sleep = 60
        self._is_running = False

    def start(self):
        self._do_run = True
        self._runtime_thread = threading.Thread(
            target=self._runtime,
            args=()
        )
        self._runtime_thread.daemon = True
        self._runtime_thread.start()

    def _runtime(self):
        self._is_running = True
        while (self._do_run):
            self.run()
            time.sleep(self._sleep)

        self._is_running = False

        self.clean_up()

    def end(self):
        self._do_run = False

    def clean_up(self): ...

    @abstractmethod
    def run(self): ...

    @property
    def is_running(self):
        return self._is_running


class GraphvizCanvas(QMainWindow):

    def __init__(self, app: QtWidgets.QApplication):
        super().__init__()
        self._view = None
        self._app = app

        self._do_timer = False

        self._output = tempfile.NamedTemporaryFile(suffix='.svg')
        self.output = QFile(self._output.name)

        self.init_ui()

        self._open_file = None

    def init_ui(self):
        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit GraphViz Editor')
        exit_action.triggered.connect(self._app.quit)

        open_action = QAction(QIcon('SP_DialogOpenButton'), '&Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open GraphViz dot file')
        open_action.triggered.connect(self.open_file)

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action)

        self.view = SvgView()
        self.view.outlineItem = False
        self.setCentralWidget(self.view)

        self.setWindowTitle('Graphviz Editor')
        self.resize(250, 150)

        self.reload_timer = QTimer()
        self.reload_timer.setInterval(500)
        self.reload_timer.timeout.connect(self.run_timer)
        self.reload_timer.start()

    def run_timer(self):
        if self._do_timer:
            self.flush()

    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            self._open_file_name = fileName
            self._open_file = QFile(self._open_file_name)
            if not self._open_file.exists():
                QMessageBox.critical(self, "Open SVG File",
                                     "Could not open file '%s'." % self._open_file)
            self._do_timer = True
            self.flush()

    def flush(self):
        (graph,) = pydot.graph_from_dot_file(self._open_file_name)
        graph.write_svg(self._output.name)

        self.view.openFile(self.output)

        self.resize(self.view.sizeHint() + QSize(80, 80 + self.menuBar().height()))


class SvgView(QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, parent=None):
        super(SvgView, self).__init__(parent)

        self.renderer = SvgView.Native
        self.svgItem = None
        self.backgroundItem = None
        self.outlineItem = None
        self.image = QImage()

        self.setScene(QGraphicsScene(self))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def drawBackground(self, p, rect):
        p.save()
        p.resetTransform()
        p.drawTiledPixmap(self.viewport().rect(),
                          self.backgroundBrush().texture())
        p.restore()

    def openFile(self, svg_file):
        if not svg_file.exists():
            return

        s = self.scene()

        if self.backgroundItem:
            drawBackground = self.backgroundItem.isVisible()
        else:
            drawBackground = False

        if self.outlineItem:
            drawOutline = self.outlineItem.isVisible()
        else:
            drawOutline = True

        s.clear()
        self.resetTransform()

        self.svgItem = QGraphicsSvgItem(svg_file.fileName())
        self.svgItem.setFlags(QGraphicsItem.ItemClipsToShape)
        self.svgItem.setCacheMode(QGraphicsItem.NoCache)
        self.svgItem.setZValue(0)

        s.addItem(self.svgItem)

    def setRenderer(self, renderer):
        self.renderer = renderer

        if self.renderer == SvgView.OpenGL:
            if QGLFormat.hasOpenGL():
                self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
        else:
            self.setViewport(QWidget())

    def setHighQualityAntialiasing(self, highQualityAntialiasing):
        if QGLFormat.hasOpenGL():
            self.setRenderHint(QPainter.HighQualityAntialiasing,
                               highQualityAntialiasing)

    def setViewBackground(self, enable):
        if self.backgroundItem:
            self.backgroundItem.setVisible(enable)

    def setViewOutline(self, enable):
        if self.outlineItem:
            self.outlineItem.setVisible(enable)

    def paintEvent(self, event):
        if self.renderer == SvgView.Image:
            if self.image.size() != self.viewport().size():
                self.image = QImage(self.viewport().size(),
                                    QImage.Format_ARGB32_Premultiplied)

            imagePainter = QPainter(self.image)
            QGraphicsView.render(self, imagePainter)
            imagePainter.end()

            p = QPainter(self.viewport())
            p.drawImage(0, 0, self.image)
        else:
            super(SvgView, self).paintEvent(event)

    def wheelEvent(self, event):
        factor = pow(1.2, event.delta() / 240.0)
        self.scale(factor, factor)
        event.accept()


# @click.command()
# @click.argument('dot_file', default=None)
def main(dot_file=None):
    app = QtWidgets.QApplication(sys.argv)

    canvas = GraphvizCanvas(app)
    canvas.show()

    exit_code = app.exec_()  # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
