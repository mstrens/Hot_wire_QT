import sys
from os import path
from PyQt5 import QtWidgets, uic ,QtCore ,QtGui
from PyQt5.QtWidgets import QFileDialog , QDialog
#from PyQt5.QtCore import QObject #, pyqtSignal, pyqtSlot

import matplotlib
matplotlib.use('Qt5Agg')
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
   FigureCanvasQTAgg as FigureCanvas )

import numpy as np
from hot_wire_ui import Ui_MainWindow
from dialog3DView import Ui_dialog3DView #dialog to display a 3D view using matplotlib 3D
import pyqtgraph as pg

import serial.tools.list_ports
import time
import threading
import atexit
import queue


import hot_wire_uploadSave
import hot_wire_transform
import hot_wire_calculate
import hot_wire_draw
#import hot_wire_cut
from hot_wire_grbl import Grbl
#from hot_wire_guillotine import Guillotine
import re


# to do: radiance should be reduced if heating exceed max!!!!!!!!!!
# remove all print from debug
# detecter comme erreur le fait de dépasser la chauffe max permise.
# ne pas activer le bouton Cut s'il y a des messages d'erreurs
# pouvoir changer le sens de l'offset pour la radiance de manière à pouvoir faire des supports
# pouvoir faire de la mise en forme du bloc (?? utile si le bloc est en hauteur et si ce n'est gênant de passer 2 X au même endroit)
# pouvoir définir les points servant à calculer la corde (revoir aussi la normalisation)
# pouvoir choisir le point d'entrée dans le bloc (face latérale/face supérieure)
# vérifier l'ordre des tabulations (certains champs ont été ajoutés)
"""

oRoot and oTip = original profil (displayed on tab profil) (list or np.array? )
tRoot and tTip = transformed profil (taking into account coord and transformation but not position)
pRoot and pTip = positioned profil inside the bloc (taking into account coord, transformation AND position in the bloc) (np.array)
offsetRoot and offsetTip = offset for radiance on pRoot and pTip (but with duplicates)
oSimR and oSimT = simplified offsetRoot and offsetTip (taking care of position in the bloc but not position of bloc) (list)
GX, GY, DX and DY = projection on the axes (only traject inside the bloc)
synchronisation points codification (4 = synchro; 0 = no synchro, 10 = synchro and no radiance)
"""
    
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        #uic.loadUi("hot_wire_ui1.ui", self)
        pg.setConfigOption('background', 'w') #use a white background for plot; must be defined before creating widget
        pg.setConfigOption('antialias', True)
        pg.setConfigOption('leftButtonPan', False)
        # here some line to test the offset calculation on synchro points (8 cases)
        #print("cas 1:  0,1,0,  0,0,1,  0.8, 0.2= ", hot_wire_calculate.offsetASynchroPoint(0,1,0,  0,0,1, 0.8, 0.2))
        #print("cas 2:  0,1,2,  0,0,1,  0.8, 0.2= ", hot_wire_calculate.offsetASynchroPoint(0,1,2,  0,0,1, 0.8, 0.2))
        #print("cas 3:  0,1,2,  0,0,-1,  0.8, 0.2= ", hot_wire_calculate.offsetASynchroPoint(0,1,2,  0,0,-1, 0.8, 0.2))
        #print("cas 4:  0,1,0,  0,0,-1,  0.8, 0.2= ", hot_wire_calculate.offsetASynchroPoint(0,1,0,  0,0,-1, 0.8, 0.2))
        #print("cas 5:  0,1,0,  0,0,1,  0.2, 0.8= ", hot_wire_calculate.offsetASynchroPoint(0,1,0,  0,0,1, 0.2, 0.8))
        #print("cas 6:  0,1,2,  0,0,1,  0.2, 0.8= ", hot_wire_calculate.offsetASynchroPoint(0,1,2,  0,0,1, 0.2, 0.8))
        #print("cas 7:  0,1,2,  0,0,-1,  0.2, 0.8= ", hot_wire_calculate.offsetASynchroPoint(0,1,2,  0,0,-1, 0.2, 0.8))
        #print("cas 8:  0,1,0,  0,0,-1,  0.2, 0.8= ", hot_wire_calculate.offsetASynchroPoint(0,1,0,  0,0,-1, 0.2, 0.8))
        
        self.initData()
        self.setupUi(self)
        self.setWindowTitle("Hot wire cutter (version 0.1.g)")
        self.tBaudrate.setCurrentText("115200")
        self.tComPort.setCurrentText('COM5')
        self.cbXLeadingCut.setCurrentText('Porportional tip dimensions')
        self.cutMsg.setTextBackgroundColor(QtGui.QColor(255,0,0))
    
        self.queueTkSendMsg = queue.Queue()
        self._thread_cmd = threading.Thread(target=self.execCmd, args=(self.queueTkSendMsg, "rien"))  
        self._thread_cmd.setDaemon(True) #added by mstrens in order to kill automatically the thread when program close
        self._thread_cmd.start()

        self.queueTkGetMsg = queue.Queue()
        self.tGrbl = Grbl( self, self.queueTkGetMsg) #create an instance of Gerbil in order to communicate with GRBL
                                                       # queue is used to get message back from interface    
        
        #plot Profile
        self.plotORoot.addLegend()
        self.plotORoot.showGrid(x=True, y=True)
        self.plotORoot.setAspectLocked()
        self.linePlotORoot = self.plotORoot.plot(self.oRootX, self.oRootY, name = 'Root', pen="r", symbol='o', symbolBrush='r', symbolSize=5)
        self.linePlotORootSynchro = self.plotORoot.plotItem.plot([], [], name ='Synchro', pen = None, symbol='o' ,
              symbolPen=pg.mkPen(color=(0, 0, 0), width=0), symbolBrush=pg.mkBrush(255, 255, 255, 255), symbolSize=7)
        self.plotOTip.addLegend()
        self.plotOTip.showGrid(x=True, y=True)
        self.plotOTip.setAspectLocked()
        self.linePlotOTip = self.plotOTip.plot(self.oTipX, self.oTipY, name = 'Tip', pen="b", symbol='o', symbolBrush='b', symbolSize=5)
        self.linePlotOTipSynchro = self.plotOTip.plotItem.plot([], [], name ='Synchro', pen = None, symbol='o' ,
              symbolPen=pg.mkPen(color='k', width=0), symbolBrush=pg.mkBrush(255, 255, 255, 255), symbolSize=7)
        
        #plot T profile (so after transform)
        self.plotTRoot.addLegend()
        self.plotTRoot.showGrid(x=True, y=True)
        self.plotTRoot.setAspectLocked()
        self.linePlotTRoot = self.plotTRoot.plotItem.plot(self.tRootX, self.tRootY, name = 'Root', pen="r", symbol='o', symbolBrush='r', symbolSize=5)
        self.plotTTip.addLegend()
        self.plotTTip.showGrid(x=True, y=True)
        self.plotTTip.setAspectLocked()
        self.linePlotTTip = self.plotTTip.plotItem.plot(self.tTipX, self.tTipY, name = 'Tip', pen="b", symbol='o', symbolBrush='b', symbolSize=5)
        
        #plot cut view
        self.cutViewToclear = True #will force an initial setup
        # setup and drawing will be done using drawCutView() 
        #hot_wire_draw.setupCutView(self)
        
        #plot bloc side view Root
        self.plotBlocSideViewRoot.addLegend()
        self.plotBlocSideViewRoot.showGrid(x=True, y=True)
        self.plotBlocSideViewRoot.setAspectLocked()
        #self.linePlotBlocSideViewRootTable = self.plotBlocSideViewRoot.plot([], [], name = 'Table', pen="g")
        self.linePlotBlocSideViewRootBloc = self.plotBlocSideViewRoot.plot([], [], name = 'Bloc', pen="k" ,fillLevel=-0.3 ,brush=(0,0,0,50))
        self.linePlotBlocSideViewRootProfile = self.plotBlocSideViewRoot.plot([], [], name = 'Root', pen="r")
        penDashDotLineRed = pg.mkPen(color='r', width=1, style=QtCore.Qt.DashDotLine)
        self.linePlotBlocSideViewRootWire = self.plotBlocSideViewRoot.plot([], [], name = 'Wire', pen=penDashDotLineRed)
        
        self.hTrailingRootText = None # use to display text on side view
        self.hLeadingRootText = None
        self.hTrailingTipText = None
        self.hLeadingTipText = None
        self.hMaxRootText = None
        self.hMinRootText = None
        self.hMaxTipText = None
        self.hMinTipText = None
        self.arrowRoot = None #used to display an arrow
        self.arrowTip = None #used to display an arrow
        self.marginTrailingRootText = None # use to display text on top view
        self.marginTrailingTipText = None
        self.marginLeadingRootText = None
        self.marginLeadingTipText = None
        self.blocToTableLeftText = None
        self.blocToTableRightText = None
        self.blocLXText = None

        #plot bloc side view Tip
        self.plotBlocSideViewTip.addLegend()
        self.plotBlocSideViewTip.showGrid(x=True, y=True)
        self.plotBlocSideViewTip.setAspectLocked()
        #self.linePlotBlocSideViewTipTable = self.plotBlocSideViewTip.plot([], [], name = 'Table', pen="g")
        self.linePlotBlocSideViewTipBloc = self.plotBlocSideViewTip.plot([], [], name = 'Bloc', pen="k",fillLevel=-0.3 ,brush=(0,0,0,50))
        self.linePlotBlocSideViewTipProfile = self.plotBlocSideViewTip.plot([], [], name = 'Tip', pen="b")
        penDashDotLineBlue = pg.mkPen(color='b', width=1, style=QtCore.Qt.DashDotLine)
        self.linePlotBlocSideViewTipWire = self.plotBlocSideViewTip.plot([], [], name = 'Wire', pen=penDashDotLineBlue)
        """
        #plot for testing
        self.testPlot.addLegend()
        self.testPlot.showGrid(x=True, y=True)
        self.testPlot.setAspectLocked()
        self.lineTestPlot = self.testPlot.plot([], [], name = 'Spar', pen="k", symbol="o")
        self.lineTestPlotOffset = self.testPlot.plot([], [], name = 'Wire', pen="r", symbol="o")
        """
        if path.isfile("startup.ini"):
            try:
                hot_wire_uploadSave.getProjectFromFile(self, "startup.ini")
                #self.drawOProfiles()
            except:
                pass    
        self.calculateAndDrawAll()
        self.createAllQtSignals()                 #define all functions to call when an action occurs in the ui
                                                #this is done after calculation in order to avoid dubble calculation
        #self.myEmit.mySignal.emit() # emit the signal
        #self.myEmit.mySignal.emit() # emit the signal
        #self.myEmit.mySignal.emit() # emit the signal
        self.port_controller = threading.Thread(target=self.check_presence)
        self.port_controller.setDaemon(True)
        self.port_controller.start()
        self.running = True # continue to read the queue from grbl interface and reactivate it as long as running is True
        self.redraw = True # force a redraw in periodic call as long as X range of bloc top view is to big 
        #self.periodicCall() #listen to the queue getting data back from the grbl interface
        #self.myEmit.mySignal.emit() # emit the signal
        
        self.periodicCall() #listen to the queue getting data back from the grbl interface
        #self.tabs.setCurrentIndex(0)

    def initData(self):
            #saved in config
            #profil section
            self.oRootX = []
            self.oRootY = []
            self.oRootS = []
            self.oTipX =  []
            self.oTipY =  []
            self.oTipS =  []
            self.nameRoot = '' # we need to save here because there is no QT objet with the name 
            self.nameTip = ''
            # Transformed profil based on original (filled by validateTransform) ; is an numpy array and not a usual List
            #take care of Chord, but not of position of block and margins...
            self.tRootX = np.array([])                   
            self.tRootY = np.array([])
            self.tRootS = []
            self.tTipX = np.array([])                   
            self.tTipY = np.array([])
            self.tTipS = []
            # Position profil (in a numpy array) based on "t" profile and position in block and margins...
            self.pRootX = np.array([])                   
            self.pRootY = np.array([])
            self.pRootS = []
            self.pTipX = np.array([])                   
            self.pTipY = np.array([])
            self.pTipS = []
            # profiles to be followed by the wire (simplified and synchronised)
            self.oSimRX = [] 
            self.oSimRY = []
            self.oSimTX = [] 
            self.oSimTY = []
                   
            # initialise filenames
            self.projectUploadFileName = None
            self.projectSaveFileName = None
            self.tableUploadFileName = None
            self.tableSaveFileName = None
            self.materialUploadFileName = None
            self.materialSaveFileName = None
            self.lastGcodeFileName = None

    
    def clickOnORootPoint(self, plotdataitem, points_clicked):
        #print("Root point" ,points_clicked[0].pos())
        self.updateSynchroPoints(self.oRootX, self.oRootY, self.oRootS, points_clicked[0].pos() , 4 )
    def clickOnORootSynchroPoint(self, plotdataitem, points_clicked):
        #print("Root synchro point" ,points_clicked[0].pos())
        self.updateSynchroPoints(self.oRootX, self.oRootY, self.oRootS , points_clicked[0].pos() , 0 )
    def clickOnOTipPoint(self, plotdataitem, points_clicked):
        #print("Tip point" ,points_clicked[0].pos())
        self.updateSynchroPoints(self.oTipX, self.oTipY, self.oTipS, points_clicked[0].pos() , 4 )
    def clickOnOTipSynchroPoint(self, plotdataitem, points_clicked):
        #print("Tip synchro point" ,points_clicked[0].pos())
        self.updateSynchroPoints(self.oTipX, self.oTipY, self.oTipS, points_clicked[0].pos() , 0 )

    def updateSynchroPoints(self, X, Y , S, point, synchroValue):
        #point contains X and Y coordinates to be checked in X and Y list; S list is updated with synchroValue
        for i , xi in enumerate (X):
            if xi == point[0] and Y[i] == point[1]:
                S[i] = synchroValue    
        self.calculateAndDrawAll()

    def createAllQtSignals(self): 
        self.linePlotORoot.sigPointsClicked.connect(self.clickOnORootPoint)
        self.linePlotORootSynchro.sigPointsClicked.connect(self.clickOnORootSynchroPoint)   
        self.linePlotOTip.sigPointsClicked.connect(self.clickOnOTipPoint)   
        self.linePlotOTipSynchro.sigPointsClicked.connect(self.clickOnOTipSynchroPoint)   

        self.pbUploadProject.clicked.connect(self.uploadProject)
        self.pbSaveProject.clicked.connect(self.saveProject)
        self.pbSelectRootProfile.clicked.connect(self.uploadRoot)
        self.pbSelectTipProfile.clicked.connect(self.uploadTip)
        self.pbUploadMaterial.clicked.connect(self.uploadMaterial)
        self.pbSaveMaterial.clicked.connect(self.saveMaterial)
        self.pbUploadTable.clicked.connect(self.uploadTable)
        self.pbSaveTable.clicked.connect(self.saveTable)
        self.pbUploadComplexes.clicked.connect(self.uploadComplexes)
        self.cbComplexProfiles.toggled.connect(self.fnComplexProfiles)

        self.cRoot.editingFinished.connect(self.fnTransform)
        self.thicknessRoot.editingFinished.connect(self.fnTransform)
        self.incidenceRoot.editingFinished.connect(self.fnTransform)
        self.vInvertRoot.toggled.connect(self.fnTransform)
        self.cTip.editingFinished.connect(self.fnTransform)
        self.thicknessTip.editingFinished.connect(self.fnTransform)
        self.incidenceTip.editingFinished.connect(self.fnTransform)
        self.vInvertTip.toggled.connect(self.fnTransform)
        self.smooth.toggled.connect(self.fnTransform)
        self.nbrPoints.editingFinished.connect(self.fnTransform)
        self.repartition.editingFinished.connect(self.fnTransform)
        self.covering.editingFinished.connect(self.fnTransform)
        self.keepChord.toggled.connect(self.fnTransform)
        
        self.reducePoints.toggled.connect(self.fnTransform)
        self.cbShowPoints.toggled.connect(self.fnTransform)
        self.blocLX.editingFinished.connect(self.fnBloc)
        self.fLeading.editingFinished.connect(self.fnBloc)
        self.mLeading.editingFinished.connect(self.fnBloc)
        self.mTrailingRoot.editingFinished.connect(self.fnBloc)
        self.mTrailingTip.editingFinished.connect(self.fnBloc)
        self.rbLeftWing.toggled.connect(self.fnBloc)
        self.blocToTableLeft.editingFinished.connect(self.fnBloc)
        self.blocToTableRight.editingFinished.connect(self.fnBloc)
        self.blocToTableTrailingRoot.editingFinished.connect(self.fnBloc)
        self.blocHZ.editingFinished.connect(self.fnBloc)
        self.hOffset.editingFinished.connect(self.fnBloc)
        self.hProfil.editingFinished.connect(self.fnBloc)
        self.diedral.editingFinished.connect(self.fnBloc)
        self.cbAlignProfiles.currentIndexChanged.connect(self.fnBloc)
        #self.rbAlignTrailing.toggled.connect(lambda:self.fnBloc())
        #self.rbAlignLeading.toggled.connect(lambda:self.fnBloc())
        #self.rbAlignExtrados.toggled.connect(lambda:self.fnBloc())
        #self.rbAlignIntrados.toggled.connect(lambda:self.fnBloc())
        self.cbShowWire.toggled.connect(self.fnTransform)
        self.mSpeedHigh.editingFinished.connect(lambda:self.fnBloc())
        self.mSpeedLow.editingFinished.connect(lambda:self.fnBloc())
        self.mHeatSpHigh.editingFinished.connect(lambda:self.fnBloc())
        self.mHeatSpLow.editingFinished.connect(lambda:self.fnBloc())
        self.mRadSpHigh.editingFinished.connect(lambda:self.fnBloc())
        self.mRadSpHalf.editingFinished.connect(lambda:self.fnBloc())
        self.vCut.editingFinished.connect(lambda:self.fnBloc())
        self.angleInRoot.editingFinished.connect(self.fnBloc)
        self.angleInTip.editingFinished.connect(self.fnBloc)
        self.angleOutRoot.editingFinished.connect(self.fnBloc)
        self.angleOutTip.editingFinished.connect(self.fnBloc)
        self.gbXLeadingActive.toggled.connect(self.fnBloc)
        self.cbXLeadingCut.currentIndexChanged.connect(self.fnBloc)
        #self.rbXLeadingProportional.toggled.connect(self.fnBloc)
        #self.rbXLeadingSameAsRoot.toggled.connect(self.fnBloc)
        #self.rbXLeadingCustom.toggled.connect(self.fnBloc)
        self.xLeadingAngle1Root.editingFinished.connect(self.fnBloc)
        self.xLeadingAngle2Root.editingFinished.connect(self.fnBloc)
        self.xLeadingHeight1Root.editingFinished.connect(self.fnBloc)
        self.xLeadingHeight2Root.editingFinished.connect(self.fnBloc)
        self.xLeadingLengthRoot.editingFinished.connect(self.fnBloc)
        self.xLeadingAngle1Tip.editingFinished.connect(self.fnBloc)
        self.xLeadingAngle2Tip.editingFinished.connect(self.fnBloc)
        self.xLeadingHeight1Tip.editingFinished.connect(self.fnBloc)
        self.xLeadingHeight2Tip.editingFinished.connect(self.fnBloc)
        self.xLeadingLengthTip.editingFinished.connect(self.fnBloc)

        self.tableYY.editingFinished.connect(lambda:self.fnBloc())
        self.tableYG.editingFinished.connect(lambda:self.fnBloc())
        self.tableYD.editingFinished.connect(lambda:self.fnBloc())
        self.cMaxY.editingFinished.connect(lambda:self.fnBloc())
        self.vMaxY.editingFinished.connect(lambda:self.fnBloc())
        self.cMaxZ.editingFinished.connect(lambda:self.fnBloc())
        self.vMaxZ.editingFinished.connect(lambda:self.fnBloc())
        self.tHeatingMax.editingFinished.connect(lambda:self.fnBloc())
        self.tPreHeat.editingFinished.connect(lambda:self.fnBloc())
        self.tPostHeat.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeStart1.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeStart2.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeStart3.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeStart4.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeEnd1.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeEnd2.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeEnd3.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeEnd4.editingFinished.connect(lambda:self.fnBloc())
        self.gCodeLetters.editingFinished.connect(self.fnBloc)
        self.pbRefreshComList.clicked.connect(self.refreshComList)        
        self.pbConnect.clicked.connect(self.tGrbl.connectToGrbl)
        self.pbDisconnect.clicked.connect(self.tGrbl.disconnectToGrbl)
        #self.pbClearMsg.clicked.connect()
        self.pbMoveGuillotineForward.clicked.connect(self.tGrbl.goForward)
        #self.pbMoveGuillotineForward.clicked.connect(lambda:self.pbMoveGuillotineForward.setEnabled(False))
        #self.pbMoveGuillotineForward.clicked.connect(lambda:self.pbMoveGuillotineBack.setEnabled(True))
        #self.pbMoveGuillotineForward.clicked.connect(lambda:self.pbMoveCancel.setEnabled(True))
        self.pbMoveGuillotineBack.clicked.connect(self.tGrbl.goBackward)
        #self.pbMoveGuillotineBack.clicked.connect(lambda:self.pbMoveGuillotineBack.setEnabled(False))
        #self.pbMoveGuillotineBack.clicked.connect(lambda:self.pbMoveGuillotineForward.setEnabled(True))
        #self.pbMoveGuillotineBack.clicked.connect(lambda:self.pbMoveCancel.setEnabled(False))

        #self.pbMoveCancel.clicked.connect(self.tGrbl.)
        self.pbReset.clicked.connect(self.tGrbl.resetGrbl)
        self.pbUnlock.clicked.connect(self.tGrbl.unlockGrbl)
        self.pbHome.clicked.connect(self.tGrbl.homeGrbl)
        self.pbSetPosition.clicked.connect(self.tGrbl.setPosGrbl)
        self.pbGoToPosition.clicked.connect(self.tGrbl.goToPosGrbl)
        self.pbStartHeating.clicked.connect(self.tGrbl.startHeating)
        self.pbStopHeating.clicked.connect(self.tGrbl.stopHeating)
        self.pbMoveUp.clicked.connect(self.tGrbl.moveUp)
        self.pbMoveBack.clicked.connect(self.tGrbl.moveBack)
        self.pbMoveForward.clicked.connect(self.tGrbl.moveForward)
        self.pbMoveDown.clicked.connect(self.tGrbl.moveDown)

        self.pbCut.clicked.connect(self.cut)
        self.pbCutCancel.clicked.connect(self.tGrbl.resetGrbl)
        self.pbSaveGcode.clicked.connect(self.saveGcode)
        self.cbCutType.currentIndexChanged.connect(self.setupCutViewAndRedraw)
        self.rbTopView.toggled.connect(self.setupCutViewAndRedraw)
        self.rbFrontView.toggled.connect(self.setupCutViewAndRedraw)
        self.rbRootView.toggled.connect(self.setupCutViewAndRedraw)
        self.rbTipView.toggled.connect(self.setupCutViewAndRedraw)
        self.rbRootTipView.toggled.connect(self.setupCutViewAndRedraw)

        self.cbSparType.currentIndexChanged.connect(self.fnSpar)
        self.cbSparDirection.currentIndexChanged.connect(self.fnSpar)
        self.cbSparWidthTipType.currentIndexChanged.connect(self.fnSpar)
        self.cbSparDepthTipType.currentIndexChanged.connect(self.fnSpar)
        self.sparRetract.editingFinished.connect(self.fnSpar)
        self.sparDepthRoot.editingFinished.connect(self.fnSpar)
        self.sparWidthRoot.editingFinished.connect(self.fnSpar)
        self.sparDepthTip.editingFinished.connect(self.fnSpar)
        self.sparWidthTip.editingFinished.connect(self.fnSpar)

        self.pbDialog3DView.clicked.connect(self.fnOpenDialog3DView)

    def fnSpar(self):
        hot_wire_calculate.calculateSparSlot(self)
        hot_wire_draw.drawCutView(self)

    def setupCutViewAndRedraw(self):
        """
        if self.cbCutType.currentIndex() == 0: #cut a project
            self.gbCutSpar.hide()
        else:
            self.gbCutSpar.show()    
        """
        #hot_wire_draw.setupCutView(self)
        self.cutViewToclear = True #will force an initial setup to clear the current graph because CutType or type of view changed
        hot_wire_draw.drawCutView(self)


    def execCmd(self , queue , rien):
        """
        thread in order to execute task outside the main tkhtread (when they can take to much time e.g.)
        get Cmd via a queue queueTkSendMsg
        used e.g. when a button is clicked in Thinker
        not sure it is really requested for this application
        """
        while True:
            msg = queue.get()
            if msg == "Connect":
                self.tGrbl.connectToGrbl()
                self.tGrbl.updateBtnState()
            elif msg == "Disconnect":    
                self.tGrbl.disconnectToGrbl()
                self.tGrbl.updateBtnState()

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.queueTkGetMsg.qsize(  ):
            try:
                msg = self.queueTkGetMsg.get(0)
                # Check contents of message and add it to the textEdit box
                self.teMsgBox.append(msg)
            except queue.Empty:
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass
    
    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        execute it when tkinter is sleeping
        """
        self.processIncoming()
        # this section has been added to force redraw because at startup the range of chart with textItems are wrong
        if self.redraw:
            #print(str(self.plotCutView.viewRange()))
            aTopView = self.plotCutView.getAxis('bottom')
            aSideViewRoot = self.plotBlocSideViewRoot.getAxis('bottom')
            #print ("top view range=", aTopView.range[1] , " Side view range=", aSideViewRoot.range[1] )
            if aTopView.range[1] > (self.tableYY.value()*1.5):
                self.tabs.setCurrentIndex(5)
                hot_wire_draw.drawBlocSideView(self)
                hot_wire_draw.drawCutView(self)
            elif aSideViewRoot.range[1] > (self.cMaxY.value()*1.5):
                self.tabs.setCurrentIndex(2)
                hot_wire_draw.drawBlocSideView(self)
                hot_wire_draw.drawCutView(self)
            else:
                self.redraw = False
                self.tabs.setCurrentIndex(0)    
        
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            #import sys
            #sys.exit(1)
            pass
        QtCore.QTimer.singleShot(200, self.periodicCall) #function will be call 200 msec later
        
            
    #to do remove this function
    """def fnLeftWing(self):
        print(self.rbLeftWing.text() + " is " + str(self.rbLeftWing.isChecked()))
        if self.rbLeftWing.isChecked():
            self.leftRightWing = 'Left'
        else:
            self.leftRightWing = 'Right'
    """
    
    def uploadProject(self):
        if self.projectUploadFileName == None:
            self.projectUploadFileName = self.projectSaveFileName
        fname = QFileDialog.getOpenFileName(self, 'Choose a file to open a projet', self.projectUploadFileName ,"Ini files (*.ini);;All files (*.*)" , "Ini files (*.ini)" )
        if len(fname[0]) > 0:  # fname[0] = file name with full path
            hot_wire_uploadSave.getProjectFromFile(self, fname[0])
            self.projectUploadFileName = fname[0] #save the project name
            self.calculateAndDrawAll()
            #print("End of upload project : after first calculate")
            

    def uploadMaterial(self):
        if self.materialUploadFileName == None:
            self.materialUploadFileName = self.materialSaveFileName
        fname = QFileDialog.getOpenFileName(self, 'Choose a file to open a material', self.materialUploadFileName ,"Material files (*.mat);;All files (*.*)" , "Material files (*.mat)" )
        if len(fname[0]) > 0:  # fname[0] = file name with full path
            hot_wire_uploadSave.getMaterialFromFile(self, fname[0])
            self.materialUploadFileName = fname[0]
            self.self.fnTransform()

    def uploadTable(self):
        if self.tableUploadFileName == None:
            self.tableUploadFileName = self.tableSaveFileName
        fname = QFileDialog.getOpenFileName(self, 'Choose a file to open a table', self.tableUploadFileName ,"Table files (*.tab);;All files (*.*)" , "Table files (*.tab)" )
        if len(fname[0]) > 0:  # fname[0] = file name with full path
            hot_wire_uploadSave.getTableFromFile(self, fname[0])
            self.tableUploadFileName = fname[0]
            self.fnTransform()

    def saveProject(self):
        if self.projectSaveFileName == None:
            self.projectSaveFileName = self.projectUploadFileName    
        fname = QFileDialog.getSaveFileName(self, 'Save current project', self.projectSaveFileName , "Ini files (*.ini);;All files (*.*)" , "Ini files (*.ini)" )
        if len(fname[0])>0:
            hot_wire_uploadSave.saveProjectToFile(self, fname[0])
            self.projectSaveFileName = fname[0]

    def saveMaterial(self):
        if self.materialSaveFileName == None:
            self.materialSaveFileName = self.materialUploadFileName    
        fname = QFileDialog.getSaveFileName(self, 'Save material', self.materialSaveFileName, "Material files (*.mat);;All files (*.*)" , "Material files (*.mat)" )
        if len(fname[0])>0:
            hot_wire_uploadSave.saveMaterialToFile(self, fname[0])
            self.materialSaveName = fname[0]

    def saveTable(self):
        if self.tableSaveFileName == None:
            self.tableSaveFileName = self.tableUploadFileName    
        fname = QFileDialog.getSaveFileName(self, 'Save table', self.tableSaveFileName , "Table files (*.tab);;All files (*.*)" , "Table files (*.tab)" )
        if len(fname[0])>0:
            hot_wire_uploadSave.saveTableToFile(self, fname[0])
            self.tableSaveName = fname[0]

    def uploadRoot(self):
        self.oRootX , self.oRootY , self.nameRoot = self.uploadProfil("Select root profile")
        #self.app.nameRoot.set(nameRoot)
        self.oRootS = []
        if len(self.oTipX) == 0: # copy root to tip when tip is empty
            self.oTipX = self.oRootX.copy()  
            self.oTipY = self.oRootY.copy()
            self.oTipS = []
            self.nameTip = self.nameRoot
        self.calculateAndDrawAll()  

    def uploadTip(self):
        self.oTipX , self.oTipY , self.nameTip= self.uploadProfil("Select tip profile")   
        self.oTipS = []
        self.calculateAndDrawAll()
        
    def uploadProfil(self ,typeName):
        fname = QFileDialog.getOpenFileName(self, typeName , '' ,"Dat files (*.dat);;All files (*.*)" , "Dat files (*.dat)" )
        errors = []
        name = ""
        profilDatX = []
        profilDatY = []
        linenum = 0
        lineDatNum = 0
        pattern = re.compile(r"(\s*[+-]?([0-9]*[.])?[0-9]+)\s+([+-]?([0-9]*[.])?[0-9]+)")
        #pattern = re.compile(r"(\s*[0-9]+\.?[0-9]*)|([0-9]*\.[0-9]+)")
        if len(fname[0]) > 0 :
            with open (fname[0], 'rt') as myfile:
                for line in myfile:
                    linenum += 1
                    #print(line)
                    pSearch = pattern.search(line)           
                    if pSearch == None:  # If pattern search  does not find a match,   
                        errors.append(line.rstrip('\n'))
                    else:                            # If pattern search  does not find a match,
                        profilDatX.append(float(pSearch.group(1)))
                        profilDatY.append(float(pSearch.group(3)))
                        lineDatNum += 1
            if len(errors) > 0:
                name = errors[0]
            else:
                name = fname[0]   
            #for err i:
            # n errors:
            #    print("Line without coordinates ", str(err[0]), ": " + err[1])
            
        return profilDatX , profilDatY , name 

    def uploadComplexes(self):
        fname = QFileDialog.getOpenFileName(self, "Select a file generated by Complexes (from RP-FC)" ,
            '' ,"cpx files (*.cpx);;All files (*.*)" , "cpx files (*.cpx)" )
        state = None
        if len(fname[0]) > 0 :
            with open (fname[0], 'rt') as myfile:
                self.oRootX = []
                self.oRootY = []
                self.oRootS = []
                self.nameRoot = ""
                self.oTipX = []
                self.oTipY = []
                self.oTipS = []
                self.nameTip = ""
                nbrSynchroRoot = 0
                nbrSynchroTip = 0
                for line in myfile:
                    if line == "[Emplanture]\n":
                        state = "Emplanture"
                    elif line == "[Saumon]\n":
                        state = "Saumon"
                    elif '=' in line:
                        l1 = line.split('=') 
                        if l1[0].isdigit():
                            l2 = l1[1].split(":")
                            if state == "Emplanture":
                                self.oRootX.append(float(l2[0]) )
                                self.oRootY.append(float(l2[1]) )
                                self.oRootS.append( int(l2[2]) & 4 ) # check only bit 2 for synchronisation
                                if (self.oRootS[-1] == 4):
                                    nbrSynchroRoot +=1 #count the number of synschro     
                            elif state == "Saumon":
                                self.oTipX.append(float(l2[0]) )
                                self.oTipY.append(float(l2[1]) )
                                self.oTipS.append(int(l2[2])  & 4)
                                if (self.oTipS[-1] == 4 ) :
                                    nbrSynchrotip +=1 #count the number of synschro
                        elif l1[0] == "Ecartement":
                            self.blocLX.setValue(float(l1[1]))
                        elif l1[0] == "NomFichier":
                            if state == "Emplanture":
                                self.nameRoot = l1[1]
                            elif state == "Saumon":
                                self.nameTip = l1[1]                   
            #print ("synchro = " , nbrSynchroRoot , " " , nbrSynchroTip)    
            if nbrSynchroRoot == 0 or nbrSynchroRoot != nbrSynchroTip: # discard synchro if not equal
                self.oRootS = []
                self.oTipS = []
        self.calculateAndDrawAll()
        
    def drawOProfiles(self):
        self.linePlotORoot.setData(self.oRootX, self.oRootY) 
        self.plotORoot.setTitle(self.nameRoot)
        self.linePlotOTip.setData(self.oTipX, self.oTipY)
        self.plotOTip.setTitle(self.nameTip)
        
        npRootS = np.array(self.oRootS) == 4
        self.linePlotORootSynchro.setData(np.array(self.oRootX)[npRootS] , np.array(self.oRootY)[npRootS])
        npTipS = np.array(self.oTipS) == 4
        self.linePlotOTipSynchro.setData(np.array(self.oTipX)[npTipS] , np.array(self.oTipY)[npTipS])


    # to do : upload complex
    def drawTProfiles(self):
        if self.cbShowPoints.isChecked():
            self.linePlotTRoot.setSymbol('o')
            self.linePlotTTip.setSymbol('o')    
        else:
            self.linePlotTRoot.setSymbol(None)
            self.linePlotTTip.setSymbol(None)
        self.linePlotTRoot.setData(self.tRootX, self.tRootY) 
        self.linePlotTTip.setData(self.tTipX, self.tTipY)

    def calculateAndDrawAll(self):
        #print("calculate and draw all")
        # insert synchro points if they do not yet exist
        if len(self.oRootX) > 0:
            #print("oRootX", self.oRootX)
            if len(self.oRootS) == 0 :
                self.oRootS = self.addSynchroPoints(self.oRootX, self.oRootY)
            if len(self.oTipS) == 0 :
                self.oTipS = self.addSynchroPoints(self.oTipX, self.oTipY)
            #set always a synchro at first and last point
            if len(self.oRootX)> 0:
                self.oRootS[0] = 4
                self.oRootS[-1] = 4
            if len(self.oTipX)> 0:
                self.oTipS[0] = 4
                self.oTipS[-1] = 4
            self.oRootSynchroCount = self.oRootS.count(4) # count the number of synchro code  
            self.oTipSynchroCount = self.oTipS.count(4)
            #print("oRootSynchroCount",self.oRootSynchroCount)
            #print("oTipSynchroCount",self.oTipSynchroCount)
            if self.oRootSynchroCount != self.oTipSynchroCount:
                #self.synchroMsg.setStyleSheet("background-color: red;")#setTextBackgroundColor(QtGui.QColor(255,0,0))
                self.synchroMsg.setTextColor(QtGui.QColor(255,0,0))
                self.synchroMsg.setText("Number of synchronisation points must be equal on root and tip profiles")
                self.synchroMsg.append("At root: " + str(self.oRootSynchroCount) + " points")
                self.synchroMsg.append("At tip: " + str(self.oTipSynchroCount) + " points")
            else:
                #self.synchroMsg.setStyleSheet("background-color: white;")#setTextBackgroundColor(QtGui.QColor(255,2550,255))
                self.synchroMsg.setTextColor(QtGui.QColor(0,0,0))
                self.synchroMsg.setText("")
                self.synchroMsg.append("At root: " + str(self.oRootSynchroCount) + " synchro points")
                self.synchroMsg.append("At tip: " + str(self.oTipSynchroCount) + " synchro points")    
        self.drawOProfiles()
        self.fnTransform()

    def addSynchroPoints(self , x, y):
        #create a list with the synchronisation point (4 = synchro; 0 = no synchro, 10 = synchro and no radiance)
        #first and last points are synchronisation points
        # this function add a point with the greatest X (it is also a synchro when there are no predefined synchro point  
        s = []
        synchroCount = 0 #count the number of synchro code
        if len(x) > 0:
            s = [0] * len(x) # create a list with 0 every where
            if self.cbComplexProfiles.isChecked() == False: #for wing profiles, add a synscho at leading edge
                # find the point with max X
                maxX = np.min(x)
                # find the index of this point
                idxMax = np.where(x == maxX) #return an array with indexes
                if len(idxMax) > 0 and len(idxMax[0]) > 0:
                    r = idxMax[0][0]
                    s[r] = 4
                else:
                    r=0 # not sure if it can happens  
        return s      

    def fnComplexProfiles(self):
        if self.cbComplexProfiles.isChecked():
            self.covering.setEnabled(False)
            self.covering.setValue(0) #added in version g
            self.keepChord.setEnabled(False)
            self.linePlotORoot.blockSignals(False)
            self.linePlotORootSynchro.blockSignals(False)   
            self.linePlotOTip.blockSignals(False)   
            self.linePlotOTipSynchro.blockSignals(False)

        else:
            self.covering.setEnabled(True)
            self.keepChord.setEnabled(True)
            self.linePlotORoot.blockSignals(True)
            self.linePlotORootSynchro.blockSignals(True)   
            self.linePlotOTip.blockSignals(True)   
            self.linePlotOTipSynchro.blockSignals(True)   
            self.oRootS = []
            self.oTipS = []
        self.calculateAndDrawAll()        

    def fnTransform(self):
        #print("run fbTransform")
        self.nbrPoints.setEnabled(self.smooth.isChecked())
        self.repartition.setEnabled(self.smooth.isChecked())
        hot_wire_transform.applyTransform(self)
        self.drawTProfiles()
        self.fnBloc()
        

    def fnBloc(self):
        #print("run fnBoc")
        hot_wire_calculate.setProfilesInBloc(self) 
        hot_wire_calculate.calculateWireProfil(self)
        hot_wire_calculate.calculateSparSlot(self)
        hot_wire_draw.drawBlocSideView(self)
        hot_wire_draw.drawCutView(self)

    def fnOpenDialog3DView(self): # open a dialog box that will display a 3 D view
        # create the dialog and draw the 3d plot 
        dlg = Dialog3DView(self) # create the view
        dlg.fillAndDraw(self)
        dlg.exec()                 #display the dialog
    
    def check_presence(self): #check if selected COM is still connected
        while True:
            comlist = serial.tools.list_ports.comports()
            connectedCom = []
            for element in comlist:
                connectedCom.append(element.device)
            if self.tComPort.currentText() in connectedCom:
                self.connected.setText("ON")
            else:
                self.connected.setText("OFF")
            #print(connectedCom)
            time.sleep(1)
        
    def comGet(self):
        comlist = serial.tools.list_ports.comports()
        connectedCom = []
        for element in comlist:
            connectedCom.append(element.device)
        #print("Connected COM ports: " + str(connectedCom))
        return connectedCom
    
    def refreshComList(self):
        currentComPort= self.tComPort.currentText()
        newComList =  self.comGet()
        self.tComPort.clear() 
        self.tComPort.addItems(newComList)
        if currentComPort in newComList:
            self.tComPort.setCurrentText(currentComPort)
        self.tComPort.update()    

    def cut(self):
        if self.cbCutType.currentIndex() == 0: #cut the project
            self.tGrbl.stream(self.gcode)
        else:
            self.tGrbl.stream(self.sparGcode)

    def saveGcode(self):
        gcodeFileName = QFileDialog.getSaveFileName(self, 'Save Gcode',
            self.lastGcodeFileName , "Gcode files (*.gcode);;All files (*.*)" , "Gcode files (*.gcode)" )
        if len(gcodeFileName[0]) > 0:
            f = open(gcodeFileName[0] ,'w')
            f.write(self.gcode)
            f.close()
            self.lastGcodeFileName = gcodeFileName[0] 
 
class Dialog3DView(QDialog):
    """3D view dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_dialog3DView()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # setup the signal to react to the buttons
        self.ui.pbZoomPlus.clicked.connect(self.fnZoomPlus)
        self.ui.pbZoomMinus.clicked.connect(self.fnZoomMinus)
        self.ui.pbRUp.clicked.connect(self.fnRUp)
        self.ui.pbRDown.clicked.connect(self.fnRDown)
        self.ui.pbRLeft.clicked.connect(self.fnRLeft)
        self.ui.pbRRight.clicked.connect(self.fnRRight)
        self.ui.pbUp.clicked.connect(self.fnUp)
        self.ui.pbDown.clicked.connect(self.fnDown)
        self.ui.pbLeft.clicked.connect(self.fnLeft)
        self.ui.pbRight.clicked.connect(self.fnRight)
        self.ui.pbFront.clicked.connect(self.fnFront)
        self.ui.pbBack.clicked.connect(self.fnBack)
        self.ui.pbHome.clicked.connect(self.fnHome)
        self.ui.pbTopView.clicked.connect(self.fnTopView)
        self.ui.pbFrontView.clicked.connect(self.fnFrontView)
        self.ui.pbLeftView.clicked.connect(self.fnLeftView)
        self.ui.pbRightView.clicked.connect(self.fnRightView)

        # save initial value of elevation and azimuth
        self.elev= 10
        self.azim= 40

    def fillAndDraw(self, w): #w = the main window (used to get access to the main data)
        fig1 = Figure()          #prepare a figure with the data  
        self.axes3d = fig1.add_subplot(111, projection='3d', proj_type = 'ortho')   # add different plot to the figure

        #table
        tableX = w.tableYY.value() - w.tableYG.value() - w.tableYD.value()
        tableY = w.cMaxY.value()
        tableZ = w.cMaxZ.value()
        a = np.array([0,tableX])
        b = np.array([0,tableY])
        z= np.array([0.0, 0.0]) 
        a, b = np.meshgrid(a, b)
        z, zz = np.meshgrid(z, z)
        self.axes3d.plot_surface( b, a, z, alpha = 0.2) 
        #bloc
        bGX = w.blocToTableLeft.value()
        bDX = w.blocToTableLeft.value() + w.blocLX.value()
        if w.rbRightWing.isChecked(): # "Right":        
            bGTY = w.blocToTableTrailingRoot.value()
            bGLY = w.blocToTableLeadingRoot
            bDTY = w.blocToTableTrailingTip
            bDLY = w.blocToTableLeadingTip
        else:
            bGTY = w.blocToTableTrailingTip
            bGLY = w.blocToTableLeadingTip
            bDTY = w.blocToTableTrailingRoot.value()
            bDLY = w.blocToTableLeadingRoot
        """
        bTGY = w.blocToTableTrailingRoot.value()
        bTDY = bTGY + w.fTrailing.value()
        bLGY = bTGY + w.cRoot.value() + w.mTrailingRoot.value() +w.mLeading.value()
        bLDY = bTDY + w.cTip.value() + w.mTrailingTip.value() +w.mLeading.value()
        """
        bZLow = w.hOffset.value()
        bZHigh = bZLow + w.blocHZ.value()
        self.axes3d.plot(  [bGTY, bDTY, bDLY, bGLY, bGTY] , [bGX, bDX , bDX , bGX ,bGX ] ,  [bZLow,bZLow,bZLow,bZLow,bZLow], color='b')
        self.axes3d.plot( [bGTY, bDTY, bDLY, bGLY, bGTY] , [bGX, bDX , bDX , bGX ,bGX ] , [bZHigh,bZHigh,bZHigh,bZHigh,bZHigh,] , color='b')
        self.axes3d.plot( [bGTY, bGTY] ,[bGX, bGX] ,  [bZLow , bZHigh]  , color='b')
        self.axes3d.plot( [bDTY, bDTY] ,[bDX, bDX] ,  [bZLow , bZHigh]  , color='b')
        self.axes3d.plot( [bGLY, bGLY] ,[bGX, bGX] ,  [bZLow , bZHigh]  , color='b')
        self.axes3d.plot( [bDLY, bDLY] ,[bDX, bDX] , [bZLow , bZHigh]  , color='b')
        #profile
        self.axes3d.plot( w.pRootX + bGTY , w.pRootY + bZLow, zs=bGX , zdir="y")
        self.axes3d.plot( w.pTipX + bDTY , w.pTipY + bZLow, zs=bDX , zdir="y")
        #left CNC axis
        axeGX = -w.tableYG.value()
        axeDX = axeGX + w.tableYY.value()
        self.axes3d.plot( [0,tableY], [axeGX, axeGX], [0, 0], color="k", linestyle="dashed")
        self.axes3d.plot( [0,0], [axeGX, axeGX], [0, tableZ], color="k", linestyle="dashed")
        self.axes3d.plot( [0,0], [axeGX,axeDX], [0,0], color="k", linestyle="dotted")
        self.axes3d.plot( [0,tableY], [axeDX, axeDX], [0,0], color="k", linestyle="dashed")
        self.axes3d.plot( [0,0], [axeDX, axeDX], [0,tableZ], color="k", linestyle="dashed")

        self.axes3d.view_init(elev=self.elev, azim=self.azim)
        self.axes3d.autoscale(False)
        self.axes3d.set_xlabel('$X$') 
        self.axes3d.set_ylabel('$Y$')
        self.axes3d.set_zlabel('$Z$')
        self.axes3d.set_xlim(0, tableY)
        self.axes3d.set_ylim(0, tableX)
        self.axes3d.set_zlim(0, tableZ)
        self.axes3d.invert_xaxis()
        self.axes3d.set_xbound(0, tableY)
        self.axes3d.set_ybound(0, tableX)
        self.axes3d.set_zbound(0, tableZ)
        self.axes3d.set_axis_off()
        # save the bound in order to restore them for the of Home buttom    
        self.xbound0 = self.axes3d.get_xbound()[0]
        self.xbound1 = self.axes3d.get_xbound()[1]
        self.ybound0 = self.axes3d.get_ybound()[0]
        self.ybound1 = self.axes3d.get_ybound()[1]
        self.zbound0 = self.axes3d.get_zbound()[0]
        self.zbound1 = self.axes3d.get_zbound()[1]
        self.axes3d.set_box_aspect([tableY,tableX,tableZ]) 
        self.axes3d.set_proj_type('ortho') # OPTIONAL - default is perspective (shown in image above)
        
        self.canvas = FigureCanvas(fig1)
        self.ui.mplvl.addWidget(self.canvas)
        self.setLabels()

    def fnZoomPlus(self): 
        k= 0.5
        print("Zomm +")
        print("x bound before",self.axes3d.get_xbound()[0] , self.axes3d.get_xbound()[1])
        self.axes3d.set_xbound(self.axes3d.get_xbound()[0], self.axes3d.get_xbound()[1]*k)
        self.axes3d.set_ybound(self.axes3d.get_ybound()[0], self.axes3d.get_ybound()[1]*k)
        self.axes3d.set_zbound(self.axes3d.get_zbound()[0], self.axes3d.get_zbound()[1]*k)
        self.setLabels()
        print("x bound after",self.axes3d.get_xbound()[0] , self.axes3d.get_xbound()[1])
                   
    def fnZoomMinus(self): 
        print("Zomm -")           
        k= 0.5
        print("x bound before",self.axes3d.get_xbound()[0] , self.axes3d.get_xbound()[1])
        self.axes3d.set_xbound(self.axes3d.get_xbound()[0], self.axes3d.get_xbound()[1]/k)
        self.axes3d.set_ybound(self.axes3d.get_ybound()[0], self.axes3d.get_ybound()[1]/k)
        self.axes3d.set_zbound(self.axes3d.get_zbound()[0], self.axes3d.get_zbound()[1]/k)
        self.setLabels()
        print("x bound after",self.axes3d.get_xbound()[0] , self.axes3d.get_xbound()[1])

    def fnRUp(self):
        self.elev= max(0,self.elev - 10)
        self.axes3d.view_init(elev=self.elev, azim=self.azim)
        self.setLabels()

    def fnRDown(self):
        self.elev= min(self.elev + 10 , 90)
        self.axes3d.view_init(elev=self.elev, azim=self.azim)
        self.setLabels()

    def fnRLeft(self):
        self.azim= min(self.azim + 10 , 90)
        self.axes3d.view_init(elev=self.elev, azim=self.azim)
        self.setLabels()

    def fnRRight(self):
        self.azim= max(self.azim - 10 , -90)
        self.axes3d.view_init(elev=self.elev, azim=self.azim)
        self.setLabels()

    def fnUp(self):
        koef = 10
        bkoef = ((self.axes3d.get_zbound()[0] - self.axes3d.get_zbound()[1]) / koef )
        self.axes3d.set_zbound(self.axes3d.get_zbound()[0] + bkoef, self.axes3d.get_zbound()[1] + bkoef)
        self.setLabels()

    def fnDown(self):
        koef = -10
        bkoef = ((self.axes3d.get_zbound()[0] - self.axes3d.get_zbound()[1]) / koef )
        self.axes3d.set_zbound(self.axes3d.get_zbound()[0] + bkoef, self.axes3d.get_zbound()[1] + bkoef)
        self.setLabels()


    def fnLeft(self):
        koef = -10
        bkoef = ((self.axes3d.get_ybound()[0] - self.axes3d.get_ybound()[1]) / koef )
        self.axes3d.set_ybound(self.axes3d.get_ybound()[0] + bkoef, self.axes3d.get_ybound()[1] + bkoef)
        self.setLabels()


    def fnRight(self):
        koef = +10
        bkoef = ((self.axes3d.get_ybound()[0] - self.axes3d.get_ybound()[1]) / koef )
        self.axes3d.set_ybound(self.axes3d.get_ybound()[0] + bkoef, self.axes3d.get_ybound()[1] + bkoef)
        self.setLabels()

    def fnFront(self):
        koef = 10
        bkoef = ((self.axes3d.get_xbound()[0] - self.axes3d.get_xbound()[1]) / koef )
        self.axes3d.set_xbound(self.axes3d.get_xbound()[0] + bkoef, self.axes3d.get_xbound()[1] + bkoef)
        self.setLabels()

    def fnBack(self):
        koef = -10
        bkoef = (self.axes3d.get_xbound()[0] - self.axes3d.get_xbound()[1]) / koef
        self.axes3d.set_xbound(self.axes3d.get_xbound()[0] + bkoef, self.axes3d.get_xbound()[1] + bkoef)
        self.setLabels()

    def fnHome(self):
        self.elev= 10
        self.azim= 40
        self.axes3d.view_init(elev=self.elev, azim=self.azim) #restore elevation and azimuth
        self.axes3d.set_xbound(self.xbound0, self.xbound1) #restore the limits
        self.axes3d.set_ybound(self.ybound0, self.ybound1)
        self.axes3d.set_zbound(self.zbound0, self.zbound1)
        self.setLabels()
        
    def fnTopView(self):
        self.elev= 90
        self.azim= 0
        self.axes3d.view_init(elev=self.elev, azim=self.azim) #restore elevation and azimuth
        self.axes3d.set_xbound(self.xbound0, self.xbound1) #restore the limits
        self.axes3d.set_ybound(self.ybound0, self.ybound1)
        self.axes3d.set_zbound(self.zbound0, self.zbound1)
        self.setLabels()
        
    def fnFrontView(self):
        self.elev= 0
        self.azim= 0
        self.axes3d.view_init(elev=self.elev, azim=self.azim) #restore elevation and azimuth
        self.axes3d.set_xbound(self.xbound0, self.xbound1) #restore the limits
        self.axes3d.set_ybound(self.ybound0, self.ybound1)
        self.axes3d.set_zbound(self.zbound0, self.zbound1)
        self.setLabels()

    def fnRightView(self):
        self.elev= 0
        self.azim= 90
        self.axes3d.view_init(elev=self.elev, azim=self.azim) #restore elevation and azimuth
        self.axes3d.set_xbound(self.xbound0, self.xbound1) #restore the limits
        self.axes3d.set_ybound(self.ybound0, self.ybound1)
        self.axes3d.set_zbound(self.zbound0, self.zbound1)
        self.setLabels()

    def fnLeftView(self):
        self.elev= 0
        self.azim= -90
        self.axes3d.view_init(elev=self.elev, azim=self.azim) #restore elevation and azimuth
        self.axes3d.set_xbound(self.xbound0, self.xbound1) #restore the limits
        self.axes3d.set_ybound(self.ybound0, self.ybound1)
        self.axes3d.set_zbound(self.zbound0, self.zbound1)
        self.setLabels()

    def setLabels(self):
        self.ui.sbAzim.setValue(self.azim)
        self.ui.sbElev.setValue(self.elev)
        self.canvas.draw()

    

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()


