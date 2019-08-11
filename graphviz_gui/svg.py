from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtOpenGL import QGL, QGLFormat, QGLWidget
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QWidget


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
        p.drawTiledPixmap(self.viewport().rect(), self.backgroundBrush().texture())
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
            self.setRenderHint(
                QPainter.HighQualityAntialiasing, highQualityAntialiasing
            )

    def setViewBackground(self, enable):
        if self.backgroundItem:
            self.backgroundItem.setVisible(enable)

    def setViewOutline(self, enable):
        if self.outlineItem:
            self.outlineItem.setVisible(enable)

    def paintEvent(self, event):
        if self.renderer == SvgView.Image:
            if self.image.size() != self.viewport().size():
                self.image = QImage(
                    self.viewport().size(), QImage.Format_ARGB32_Premultiplied
                )

            imagePainter = QPainter(self.image)
            QGraphicsView.render(self, imagePainter)
            imagePainter.end()

            p = QPainter(self.viewport())
            p.drawImage(0, 0, self.image)
        else:
            super(SvgView, self).paintEvent(event)

    def wheelEvent(self, event):
        factor = pow(1.2, event.angleDelta() / 240.0)
        self.scale(factor, factor)
        event.accept()
