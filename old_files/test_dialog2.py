import sys
from os import path
from PyQt5 import QtWidgets, uic ,QtCore ,QtGui
from PyQt5.QtWidgets import QFileDialog , QDialog
from PyQt5.QtCore import QObject , pyqtSignal, pyqtSlot

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
import numpy as np

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(120, 120, 75, 23))
        self.pushButton.setObjectName("pushButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.pushButton.setText("PushButton")
        #self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    """def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))
    """
class Ui_dialog3DView(object):
    def setupUi(self, dialog3DView):
        dialog3DView.setObjectName("dialog3DView")
        dialog3DView.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(dialog3DView)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mplwindow = QtWidgets.QWidget(dialog3DView)
        self.mplwindow.setObjectName("mplwindow")
        self.mplvl = QtWidgets.QVBoxLayout(self.mplwindow)
        self.mplvl.setObjectName("mplvl")
        self.horizontalLayout.addWidget(self.mplwindow)
        
        self.retranslateUi(dialog3DView)
        QtCore.QMetaObject.connectSlotsByName(dialog3DView)

    def retranslateUi(self, dialog3DView):
        _translate = QtCore.QCoreApplication.translate
        dialog3DView.setWindowTitle(_translate("dialog3DView", "3d view"))



class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        #self.initData()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.fnOpenDialog3DView)

    def fnOpenDialog3DView(self):
        # create the dialog and start it 
        dlg = Dialog3DView(self) # create the view
        dlg.draw()
        '''
        fig1 = Figure()          #prepare a figure with the data  
        axes3d = fig1.add_subplot(111, projection='3d', proj_type = 'ortho')   # add different plot to the figure
        axes3d.plot( [0,1,2] , [0,1,0], zs=1 , zdir="x")
        axes3d.plot( [0,1,2], [0,1,2] , zs=2 , zdir="x")
        dlg.addmpl(fig1)               # add the figure to a Qwidget inside the dialog 
        axes3d.mouse_init(rotate_btn=1, zoom_btn=3)  # enables mouse interactions
        dlg.exec()                 #display the dialog
        '''    
class Dialog3DView(QDialog):
    """3D view dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_dialog3DView()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
    '''
    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.ui.mplvl.addWidget(self.canvas)
        #self.ui.mplwindow.addToolBar(NavigationToolbar(self.canvas, self))
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar(self.canvas, 
            self.ui.mplwindow, coordinates=True)
        self.ui.mplvl.addWidget(self.toolbar)
    '''
    def  draw( self):
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot( [0,1,2] , [0,1,0], zs=1 , zdir="x")
        plt.show()        

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
