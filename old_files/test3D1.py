"""
==============================
3D ploting using PyQt5 for GUI
==============================
Brief:
------
    A **matplotlib** widget displays a 3D graph inside
    a **PyQt5** widget window.
Important
---------
    This project is published under **MIT License**
"""

import argparse
import sys

import numpy as np

from matplotlib import cm
from matplotlib.pyplot import figure
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication as Application, QWidget as Widget, QPushButton as Button
from PyQt5.QtWidgets import QLabel as Label, QGridLayout, QDesktopWidget

import print_string_colors as COLOUR


#
# Following functions are used to generate nice looking plots
#
def f(x, y):  # For Generating Z coordinates
    return np.sin(np.sqrt(x ** 2 + y ** 2))


def g(x, y):  # For Generating Z coordinates (alternative)
    return np.sin(x) + np.cos(y)


#
# Following class code partly taken from 'StackOverflow'
#
class ThreeDSurfaceGraphWindow(FigureCanvas):  # Class for 3D window
    def __init__(self):
        self.plot_colorbar = None
        self.plot_figure = figure(figsize=(7, 7))
        FigureCanvas.__init__(self, self.plot_figure)  # creating FigureCanvas
        self.axes = self.plot_figure.gca(projection='3d')  # generates 3D Axes object
        self.setWindowTitle("figure")  # sets Window title

    def draw_graph(self, x, y, z):  # Function for graph plotting
        self.axes.clear()
        if self.plot_colorbar is not None:  # avoids adding one more colorbar at each draw operation
            self.plot_colorbar.remove()
        # plots the 3D surface plot
        plot_stuff = self.axes.plot_surface(x, y, z,
                                            cmap=cm.coolwarm, linewidth=0, antialiased=False)
        self.axes.zaxis.set_major_locator(LinearLocator(10))
        self.axes.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
        # Add a color bar which maps values to colors.
        self.plot_colorbar = self.plot_figure.colorbar(plot_stuff, shrink=0.5, aspect=5)
        # draw plot
        self.draw()


class ProgramGUI(Widget):

    def __init__(self):
        super().__init__()
        # GUI window specific values
        self.title = '\'MatPlotLib\' test program'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        # Other object specific values
        self.label_str = "This program will test the \'MatPlotLib\' through a Qt widget display."
        self.plot_status = u'a'
        self.X_plot_val = None
        self.Y_plot_val = None
        self.Z_plot_val = None

        # Call argument parsing to enable/disable debug options
        dbg_parse = argparse.ArgumentParser()
        dbg_parse.add_argument(u'-d',
                               u'--debug',
                               action='store_true',
                               help=u'Enable DEBUG specific functions')
        self.argh = dbg_parse.parse_args()

        # Debug output
        if self.argh.debug is True:
            print(COLOUR.STRONG_BLUE +
                  "====================\n" +
                  "==== DEBUG MODE ====\n" +
                  "====================" +
                  COLOUR.NORMAL)

        # initialize UI
        self.init_ui()

    def init_ui(self):
        #
        # Setup Window Title and geometry
        #
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.center()
        #
        # Setup User message
        #
        self.label = Label(self.label_str)
        #
        # Setup "Program" button
        #
        self.test_graph_button = Button(u'Update graph', self)
        self.test_graph_button.setToolTip(u'Call update function to change graph')
        self.test_graph_button.clicked.connect(self.test_std_out)
        #
        # Setup "Plot" object
        #
        self.plot_container = ThreeDSurfaceGraphWindow()  # creating 3D Window
        #
        # Setup grid layout for global window
        #
        main_layout = QGridLayout()  # Layout for Main Tab Widget
        main_layout.setRowMinimumHeight(0, 5)  # setting layout parameters
        main_layout.setRowMinimumHeight(2, 10)
        main_layout.setRowMinimumHeight(4, 5)
        main_layout.addWidget(self.label, 1, 1, Qt.AlignHCenter)
        main_layout.addWidget(self.test_graph_button, 2, 1)
        main_layout.addWidget(self.plot_container, 3, 1)  # add 3D Window to Main layout
        self.setLayout(main_layout)  # sets Main layout
        #
        # calculate 3D sin function
        #
        self.test_std_out()
        #
        # Special setup when '--debug' is passed as an argument
        #
        if self.argh.debug is True:
            # tell user that all debug Widgets are setup
            print(COLOUR.YELLOW +
                  "Debug Wigets & objects setup done" +
                  COLOUR.NORMAL)

    def center(self):
        """centers the window on the screen"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    @pyqtSlot()
    def test_std_out(self):
        # Make plot data
        if self.plot_status == u'a':
            self.X_plot_val = np.arange(-10, 10, 0.25)  # X coordinates
            self.Y_plot_val = np.arange(-10, 10, 0.25)  # Y coordinates
            # Forming MeshGrid
            self.X_plot_val, self.Y_plot_val = np.meshgrid(self.X_plot_val, self.Y_plot_val)
            self.Z_plot_val = g(self.X_plot_val, self.Y_plot_val)
            self.plot_status = u'b'
        else:
            self.X_plot_val = np.arange(-5, 5, 0.25)  # X coordinates
            self.Y_plot_val = np.arange(-5, 5, 0.25)  # Y coordinates
            # Forming MeshGrid
            self.X_plot_val, self.Y_plot_val = np.meshgrid(self.X_plot_val, self.Y_plot_val)
            self.Z_plot_val = f(self.X_plot_val, self.Y_plot_val)
            self.plot_status = u'a'
        # call plot for tests
        self.plot_container.draw_graph(self.X_plot_val, self.Y_plot_val, self.Z_plot_val)


if __name__ == '__main__':
    app = Application(sys.argv)
    gui = ProgramGUI()

    qr = gui.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    gui.move(qr.topLeft())
    app.processEvents()

    gui.show()

    exit_val = app.exec_()

    # behaviour to trigger on exit
    sys.exit(exit_val)