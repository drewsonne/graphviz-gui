import os
import sys
import tempfile

import click
import pydot
from PyQt5 import QtWidgets
from PyQt5.QtCore import QFile, QTimer, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox, QMainWindow

from graphviz_gui.svg import SvgView


class GraphvizCanvas(QMainWindow):
    def __init__(
        self,
        app: QtWidgets.QApplication,
        working_directory: str,
        initial_dot_file: str = None,
    ):
        super().__init__()
        self._view = None
        self._app = app

        self._do_timer = False

        self._output = tempfile.NamedTemporaryFile(suffix=".svg")
        self.output = QFile(self._output.name)

        self.init_ui()

        self._open_file = None
        if initial_dot_file is not None:
            self._open_file_name = os.path.join(working_directory, initial_dot_file)
            self._do_timer = True

    def init_ui(self):
        exit_action = QAction(QIcon("exit.png"), "&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit GraphViz Editor")
        exit_action.triggered.connect(self._app.quit)

        open_action = QAction(QIcon("SP_DialogOpenButton"), "&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open GraphViz dot file")
        open_action.triggered.connect(self.open_file)
        self._error_dialog = QtWidgets.QErrorMessage()

        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action)

        self.view = SvgView()
        self.view.outlineItem = False
        self.view.setRenderer(SvgView.OpenGL)
        self.setCentralWidget(self.view)

        self.setWindowTitle("Graphviz Editor")
        self.resize(250, 150)

        self.reload_timer = QTimer()
        self.reload_timer.setInterval(500)
        self.reload_timer.timeout.connect(self.run_timer)
        self.reload_timer.start()

    def run_timer(self):
        try:
            if self._do_timer:
                self.flush()
        except Exception as e:
            self._do_timer = False
            self._error_dialog.showMessage(str(e))

    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "Graphviz Files (*.dot);;All Files (*)",
            options=options,
        )
        if fileName:
            self._open_file_name = fileName
            self._open_file = QFile(self._open_file_name)
            if not self._open_file.exists():
                QMessageBox.critical(
                    self, "Open SVG File", "Could not open file '%s'." % self._open_file
                )
            else:
                self._do_timer = True
                self.flush()

    def flush(self):
        (graph,) = pydot.graph_from_dot_file(self._open_file_name)
        graph.write_svg(self._output.name)

        self.view.openFile(self.output)

        self.resize(self.view.sizeHint() + QSize(80, 80 + self.menuBar().height()))


@click.command()
@click.argument("dot_file", default=None)
def main(dot_file=None):
    app = QtWidgets.QApplication(sys.argv)

    canvas = GraphvizCanvas(app, os.getcwd(), dot_file)
    canvas.show()

    exit_code = app.exec_()  # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
