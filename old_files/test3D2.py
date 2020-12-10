# importing various libraries 
import sys 
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar 
import matplotlib.pyplot as plt 
import random 
   
# main window 
# which inherits QDialog 
class Window(QDialog): 
       
    # constructor 
    def __init__(self, parent=None): 
        super(Window, self).__init__(parent) 
   
        # a figure instance to plot on 
        self.figure = plt.figure() 
   
        # this is the Canvas Widget that  
        # displays the 'figure'it takes the 
        # 'figure' instance as a parameter to __init__ 
        self.canvas = FigureCanvas(self.figure) 
   
        # this is the Navigation widget 
        # it takes the Canvas widget and a parent 
        self.toolbar = NavigationToolbar(self.canvas, self) 
   
        # Just some button connected to 'plot' method 
        self.button = QPushButton('Plot') 
           
        # adding action to the button 
        self.button.clicked.connect(self.plot) 
   
        # creating a Vertical Box layout 
        layout = QVBoxLayout() 
           
        # adding tool bar to the layout 
        layout.addWidget(self.toolbar) 
           
        # adding canvas to the layout 
        layout.addWidget(self.canvas) 
           
        # adding push button to the layout 
        layout.addWidget(self.button) 
           
        # setting layout to the main window 
        self.setLayout(layout) 
   
    # action called by thte push button 
    def plot(self): 
           
        # random data 
        data = [random.random() for i in range(10)] 
   
        # clearing old figure 
        self.figure.clear() 
   
        # create an axis 
        ax = self.figure.add_subplot(111) 
   
        # plot data 
        ax.plot(data, '*-') 
   
        # refresh canvas 
        self.canvas.draw() 
   
# driver code 
if __name__ == '__main__': 
       
    # creating apyqt5 application 
    app = QApplication(sys.argv) 
   
    # creating a window object 
    main = Window() 
       
    # showing the window 
    main.show() 
   
    # loop 
    sys.exit(app.exec_())