import math

import numpy as np
import hot_wire_uploadSave

from shapely.geometry import LineString
from shapely import affinity
from scipy import interpolate
from PyQt5 import QtWidgets, uic ,QtCore
import pyqtgraph as pg

def setupCutView(self): # create the general setup depending on the view
    self.plotCutView.clear()
    self.plotCutView.enableAutoRange()
    self.plotCutView.addLegend()
    self.plotCutView.showGrid(x=True, y=True)
    self.plotCutView.setAspectLocked()    
    if self.cbCutType.currentIndex() == 0: #cut the current project
        self.gbCutSpar.hide()
        if self.rbTopView.isChecked(): # top view
            self.linePlotCutViewTable = self.plotCutView.plot([], [], name = 'Table', pen="g", fillLevel=-0.3 ,brush=(0,255,0,50))
            self.linePlotCutViewBloc = self.plotCutView.plot([], [], name = 'Bloc', pen="k" ,fillLevel=-0.3 ,brush=(0,0,0,50))
            penDashLine = pg.mkPen(color='k', width=1, style=QtCore.Qt.DashLine)
            self.linePlotCutViewLeading = self.plotCutView.plot([], [], name = 'Leading', pen=penDashLine) # leading edge
            penDashDotLine = pg.mkPen(color='k', width=1, style=QtCore.Qt.DashDotLine)
            self.linePlotCutViewTrailing = self.plotCutView.plot([], [], name = 'Trailing', pen=penDashDotLine) #trailing edge
            penDotLine = pg.mkPen(color='k', width=2, style=QtCore.Qt.DotLine)
            self.linePlotCutViewLeft = self.plotCutView.plot([], [], name = 'Left axis', pen=penDotLine) # left axis
            self.linePlotCutViewRight = self.plotCutView.plot([], [], name = 'Right axis', pen=penDotLine) # right axis
        elif self.rbFrontView.isChecked(): #front view
            self.linePlotCutViewTable = self.plotCutView.plot([], [], name = 'Table', pen="g", fillLevel=-0.3 ,brush=(0,255,0,50))
            self.linePlotCutViewBloc = self.plotCutView.plot([], [], name = 'Bloc', pen="k" ,fillLevel=-0.3 ,brush=(0,0,0,50))
            #penDashLine = pg.mkPen(color='k', width=1, style=QtCore.Qt.DashLine)
            #self.linePlotCutViewLeading = self.plotCutView.plot([], [], name = 'Leading', pen=penDashLine) # leading edge
            #penDashDotLine = pg.mkPen(color='k', width=1, style=QtCore.Qt.DashDotLine)
            #self.linePlotCutViewTrailing = self.plotCutView.plot([], [], name = 'Trailing', pen=penDashDotLine) #trailing edge
            penDotLine = pg.mkPen(color='k', width=2, style=QtCore.Qt.DotLine)
            self.linePlotCutViewLeft = self.plotCutView.plot([], [], name = 'Left axis', pen=penDotLine) # left axis
            self.linePlotCutViewRight = self.plotCutView.plot([], [], name = 'Right axis', pen=penDotLine) # right axis
        else:  #side  view (root, tip or both)
            self.linePlotCutViewTable = self.plotCutView.plot([], [], name = 'Table', pen="g", fillLevel=-0.3 ,brush=(0,255,0,50))
            penDotLine = pg.mkPen(color='k', width=2, style=QtCore.Qt.DotLine)
            self.linePlotCutViewLeft = self.plotCutView.plot([], [], name = 'Vertical axis', pen=penDotLine) # vertical axis
            if self.rbRootView.isChecked() or self.rbRootTipView.isChecked(): # Root or both
                self.linePlotCutViewBlocRoot = self.plotCutView.plot([], [], name = 'Root bloc', pen="r" ,fillLevel=-0.3 ,brush=(0,0,0,50))
                penDashLine = pg.mkPen(color='r', width=1)
                self.linePlotCutViewRoot = self.plotCutView.plot([], [], name = 'Root profile', pen=penDashLine) # profile
                penDashDotLine = pg.mkPen(color='r', width=1, style=QtCore.Qt.DashDotLine)
                self.linePlotCutViewWireRoot = self.plotCutView.plot([], [], name = 'Root wire', pen=penDashDotLine) #wire
            if self.rbTipView.isChecked() or self.rbRootTipView.isChecked(): #tip or both
                self.linePlotCutViewBlocTip = self.plotCutView.plot([], [], name = 'Tip bloc', pen="b" ,fillLevel=-0.3 ,brush=(0,0,0,50))
                penDashLine = pg.mkPen(color='b', width=1)
                self.linePlotCutViewTip = self.plotCutView.plot([], [], name = 'Tip profile', pen=penDashLine) # profile
                penDashDotLine = pg.mkPen(color='b', width=1, style=QtCore.Qt.DashDotLine)
                self.linePlotCutViewWireTip = self.plotCutView.plot([], [], name = 'Tip wire', pen=penDashDotLine) #wire
    else: # cut a spar/slot
        self.gbCutSpar.show()
        self.linePlotCutViewSparRoot =  self.plotCutView.plot([], [], name = 'Spar root', pen="r")
        self.linePlotCutViewSparTip =  self.plotCutView.plot([], [], name = 'Spar Tip', pen="b")
        penDotLine = pg.mkPen(color='r', width=2, style=QtCore.Qt.DotLine)
        self.linePlotCutViewSparWireRoot = self.plotCutView.plot([], [], name = 'Wire root', pen=penDotLine)
        penDotLine = pg.mkPen(color='b', width=2, style=QtCore.Qt.DotLine)
        self.linePlotCutViewSparWireTip = self.plotCutView.plot([], [], name = 'Wire tip', pen=penDotLine)
        penLine = pg.mkPen(color='k', width=2, style=QtCore.Qt.SolidLine)
        self.linePlotCutViewSparFoam = self.plotCutView.plot([], [], name = 'Foam level', pen=penLine)

def drawCutView(self):
    if self.cutViewToclear: 
        setupCutView(self)  # clear all  and recreate a setup if there is a change
    if self.cbCutType.currentIndex() == 0: # draw a project view
        self.gbViewType.show()
        if self.rbTopView.isChecked():
            drawTopView(self)
        elif  self.rbFrontView.isChecked():
            drawFrontView(self)
        else:
            drawSideView(self) # draw side view with Root, tip or both 
    else:
        self.gbViewType.hide()
        drawSparView(self)
    self.cutViewToclear = False    
    
def drawTopView(self):
    self.plotCutView.removeItem(self.marginTrailingRootText)
    self.plotCutView.removeItem(self.marginTrailingTipText)
    self.plotCutView.removeItem(self.marginLeadingRootText)
    self.plotCutView.removeItem(self.marginLeadingTipText)    
    self.plotCutView.removeItem(self.blocToTableLeftText)
    self.plotCutView.removeItem(self.blocToTableRightText)
    self.plotCutView.removeItem(self.blocLXText)        
    #draw bloc
    cMaxY = self.cMaxY.value()
    cMaxX = self.tableYY.value() - self.tableYG.value() - self.tableYD.value()
    bGX = self.blocToTableLeft.value()
    bDX = self.blocToTableLeft.value() + self.blocLX.value()
    if self.rbRightWing.isChecked(): # "Right":        
        bGTY = self.blocToTableTrailingRoot.value()
        bGLY = self.blocToTableLeadingRoot
        bDTY = self.blocToTableTrailingTip
        bDLY = self.blocToTableLeadingTip
    else:
        bGTY = self.blocToTableTrailingTip
        bGLY = self.blocToTableLeadingTip
        bDTY = self.blocToTableTrailingRoot.value()
        bDLY = self.blocToTableLeadingRoot
    self.linePlotCutViewBloc.setData( [bGX , bGX , bDX, bDX , bGX ] , [bGTY , bGLY, bDLY , bDTY , bGTY] )
    # draw trailing edge
    fTGX = self.blocToTableLeft.value()
    fTDX = fTGX + self.blocLX.value()
    fTGXp = -self.tableYG.value()
    fTDXp = self.tableYY.value()  - self.tableYG.value() #- self.tableYD.value()
    if self.rbRightWing.isChecked(): # "Right":        
        fTGY = self.blocToTableTrailingRoot.value() + self.mTrailingRoot.value()
        fTDY = self.blocToTableTrailingTip + self.mTrailingTip.value() 
    else:
        fTGY = self.blocToTableTrailingTip + self.mTrailingTip.value()
        fTDY = self.blocToTableTrailingRoot.value() + self.mTrailingRoot.value() 
    fTGYp , fTDYp = hot_wire_uploadSave.projection( fTGX , fTDX , fTGY , fTDY , fTGXp , fTDXp  )        
    self.linePlotCutViewTrailing.setData( [fTGXp , fTDXp ] , [fTGYp , fTDYp] )
    #draw leading edge
    fLGX = fTGX
    fLDX = fTDX
    fLGXp = -self.tableYG.value()
    fLDXp = fTDXp
    if self.rbRightWing.isChecked(): # "Right":        
        fLGY = fTGY + self.cRoot.value()
        fLDY = fTDY + self.cTip.value()
    else:    
        fLGY = fTGY + self.cTip.value()
        fLDY = fTDY + self.cRoot.value()
    fLGYp , fLDYp = hot_wire_uploadSave.projection( fLGX , fLDX , fLGY , fLDY , fLGXp , fLDXp  )
    self.linePlotCutViewLeading.setData( [fLGXp , fLDXp ] , [fLGYp , fLDYp]  )
    #draw left and right axis
    self.linePlotCutViewLeft.setData( [-self.tableYG.value() , -self.tableYG.value() ] , [0 , self.cMaxY.value()]  )
    self.linePlotCutViewRight.setData( [self.tableYY.value()-self.tableYG.value() , self.tableYY.value()-self.tableYG.value()] ,
         [0 , self.cMaxY.value()]  )
    # draw table
    self.linePlotCutViewTable.setData([0, 0 , cMaxX, cMaxX, 0  ],[0 , cMaxY, cMaxY, 0 , 0 ]) 
    #add cotation
    if self.rbRightWing.isChecked(): # "Right":        
        colorLeft = "r"
        colorRight = "b"
    else:    
        colorLeft = "b"
        colorRight = "r"
     
    self.marginTrailingRootText = pg.TextItem(text=str(bDTY), color=colorRight, anchor=(1, 0))  # text for margin 
    self.marginTrailingRootText.setPos( bDX, bDTY )
    self.plotCutView.addItem(self.marginTrailingRootText)

    self.marginTrailingTipText = pg.TextItem(text=str(bGTY), color=colorLeft, anchor=(0, 0))  
    self.marginTrailingTipText.setPos( bGX, bGTY )              # draw the margin in the plot
    self.plotCutView.addItem(self.marginTrailingTipText)

    self.marginLeadingRootText = pg.TextItem(text=str(bDLY), color=colorRight, anchor=(1, 1))  
    self.marginLeadingRootText.setPos( bDX, bDLY )
    self.plotCutView.addItem(self.marginLeadingRootText)
    
    self.marginLeadingTipText = pg.TextItem(text= str(bGLY), color=colorLeft, anchor=(0, 1))  
    self.marginLeadingTipText.setPos( bGX, bGLY )              
    self.plotCutView.addItem(self.marginLeadingTipText)
    # add text for left and right margins
    self.blocToTableLeftText = pg.TextItem(text= str(bGX), color="k", anchor=(1, 0.5))
    self.blocToTableLeftText.setPos(bGX , (bGTY + bGLY)/2 )
    self.plotCutView.addItem(self.blocToTableLeftText)
    self.blocToTableRightText = pg.TextItem(text= str(self.blocToTableRight.value()), color="k", anchor=(0, 0.5))
    self.blocToTableRightText.setPos(bDX , (bDTY + bDLY)/2 )
    self.plotCutView.addItem(self.blocToTableRightText)
    self.blocLXText = pg.TextItem(text= str(self.blocLX.value()), color="k", anchor=(0.5, 0.5))
    self.blocLXText.setPos( (bGX + bDX) / 2, (bGTY + bGLY + bDTY + bDLY)/4 )
    self.plotCutView.addItem(self.blocLXText)

def drawFrontView(self):
    # draw table
    cMaxX = self.tableYY.value() - self.tableYG.value() - self.tableYD.value()
    self.linePlotCutViewTable.setData([0,cMaxX ],[0 , 0 ]) 
    #draw bloc
    bGX = self.blocToTableLeft.value()
    bDX = self.blocToTableLeft.value() + self.blocLX.value()
    bHLow = self.hOffset.value()
    bHHigh = bHLow + self.blocHZ.value()
    self.linePlotCutViewBloc.setData( [bGX , bGX , bDX, bDX , bGX ] , [bHLow, bHHigh, bHHigh, bHLow, bHLow] )
    # leading /trailing edge : to do  replace by several lines with cutting
    #self.linePlotCutViewLeading = self.plotCutView.plot([], [], name = 'Leading', pen=penDashLine) # leading edge
    #self.linePlotCutViewTrailing = self.plotCutView.plot([], [], name = 'Trailing', pen=penDashDotLine) #trailing edge
    axeGX = - self.tableYG.value()
    axeDX = axeGX + self.tableYY.value()
    axeHeight = self.cMaxZ.value()
    self.linePlotCutViewLeft.setData([axeGX , axeGX] , [0, axeHeight]) # left vertical axis
    self.linePlotCutViewRight.setData([axeDX , axeDX] , [0, axeHeight]) # right vertical axis

def drawSideView(self):
    # table
    cMaxY = self.cMaxY.value()
    self.linePlotCutViewTable.setData([0, cMaxY], [0,0]) 
    #bloc
    cMaxX = self.tableYY.value() - self.tableYG.value() - self.tableYD.value()
    bHLow = self.hOffset.value()
    bHHigh = bHLow + self.blocHZ.value()
    #bGX = self.blocToTableLeft.value()
    #bDX = self.blocToTableLeft.value() + self.blocLX.value()
        
    bTR = self.blocToTableTrailingRoot.value()
    bLR = self.blocToTableLeadingRoot
    bTT = self.blocToTableTrailingTip
    bLT = self.blocToTableLeadingTip
    if self.rbRootView.isChecked() or self.rbRootTipView.isChecked():
        self.linePlotCutViewBlocRoot.setData([bTR,bTR , bLR, bLR, bTR ], [bHLow, bHHigh , bHHigh, bHLow,bHLow])    
        #Root
        self.linePlotCutViewRoot.setData(self.pRootX + bTR , self.pRootY + bHLow)
        #Root wire
        self.linePlotCutViewWireRoot.setData(np.array(self.oSimRX) + bTR, np.array(self.oSimRY) + bHLow)
    if self.rbTipView.isChecked() or self.rbRootTipView.isChecked():
        self.linePlotCutViewBlocTip.setData([bTT,bTT , bLT, bLT, bTT ], [bHLow, bHHigh , bHHigh, bHLow,bHLow])    
        #Root
        self.linePlotCutViewTip.setData(self.pTipX + bTT , self.pTipY + bHLow)
        #Root wire
        self.linePlotCutViewWireTip.setData(np.array(self.oSimTX) + bTT, np.array(self.oSimTY) + bHLow)
    
    # vertical axis
    self.linePlotCutViewLeft.setData([0, 0], [0, self.cMaxZ.value()])

def drawSparView(self):
    #print("update drawing of spar view")
    #print("sparXR", self.sparXR)
    #print("sparwireRX", self.sparWireRX)
    self.linePlotCutViewSparRoot.setData(self.sparXR,self.sparYR)
    self.linePlotCutViewSparTip.setData(self.sparXT,self.sparYT)
    self.linePlotCutViewSparWireRoot.setData(self.sparWireRX,self.sparWireRY)
    self.linePlotCutViewSparWireTip.setData(self.sparWireTX,self.sparWireTY)
    wide = max (self.sparWidthRoot.value(), self.sparRetract.value(),self.sparWidthTip.value())
    self.linePlotCutViewSparFoam.setData( [- wide , wide ] , [0,0] )

def drawBlocSideView(self):
    # draw root & tip bloc
    # remove text items with height & margin
    self.plotBlocSideViewRoot.removeItem(self.hTrailingRootText)
    self.plotBlocSideViewRoot.removeItem(self.hLeadingRootText)
    self.plotBlocSideViewTip.removeItem(self.hTrailingTipText)
    self.plotBlocSideViewTip.removeItem(self.hLeadingTipText)
    self.plotBlocSideViewRoot.removeItem(self.hMaxRootText)
    self.plotBlocSideViewRoot.removeItem(self.hMinRootText)
    self.plotBlocSideViewTip.removeItem(self.hMaxTipText)
    self.plotBlocSideViewTip.removeItem(self.hMinTipText)
    self.plotBlocSideViewRoot.removeItem(self.arrowRoot)
    self.plotBlocSideViewTip.removeItem(self.arrowTip)
    

    #draw the bloc
    blocChordRoot = self.cRoot.value() + self.mLeading.value() + self.mTrailingRoot.value()
    blocChordTip = self.cTip.value() + self.mLeading.value() + self.mTrailingTip.value()
    blocRootX = [0, blocChordRoot , blocChordRoot , 0, 0 ]
    blocTipX = [0, blocChordTip, blocChordTip, 0, 0]
    #hOffset = self.hOffset.value()
    blocHZ =  self.blocHZ.value()
    blocRootY = [0, 0, blocHZ, blocHZ, 0]
    blocTipY = blocRootY
    self.linePlotBlocSideViewRootBloc.setData( blocRootX , blocRootY )
    self.linePlotBlocSideViewTipBloc.setData( blocTipX , blocTipY )
    
    #draw root & tip profiles 
    #then update profil
    self.linePlotBlocSideViewRootProfile.setData( self.pRootX.tolist() , self.pRootY.tolist() )
    self.linePlotBlocSideViewTipProfile.setData( self.pTipX.tolist() , self.pTipY.tolist() )
    
    if self.cbShowWire.isChecked():
        #print("redraw wire")
        self.linePlotBlocSideViewRootWire.setData( self.oSimRX , self.oSimRY )
        self.linePlotBlocSideViewTipWire.setData( self.oSimTX , self.oSimTY )
        if len(self.oSimRX) > 2:
            self.arrowRoot = pg.CurveArrow(self.linePlotBlocSideViewRootWire)
            self.arrowRoot.setStyle(headlen=40, pen={'color': 'r'}, brush=None )
            self.plotBlocSideViewRoot.addItem(self.arrowRoot)
            self.arrowTip = pg.CurveArrow(self.linePlotBlocSideViewTipWire)
            self.arrowTip.setStyle(headlen=40, pen={'color': 'b'}, brush=None )
            self.plotBlocSideViewTip.addItem(self.arrowTip)    
    else:
        self.linePlotBlocSideViewRootWire.setData( [] , [] )
        self.linePlotBlocSideViewTipWire.setData( [] , [] )
    #at the end add text with all heights and margins
    if (len(self.tRootX) > 0) and (len(self.tTipX) >0 ):
        self.hTrailingRootText = pg.TextItem(text="{:.1f}".format(self.hTrailingRoot), color="r" , anchor=(0, 0))  # text for margin trailing Root
        self.hTrailingRootText.setPos( self.mTrailingRoot.value() , self.hTrailingRoot )   
        self.plotBlocSideViewRoot.addItem(self.hTrailingRootText)
        self.hLeadingRootText = pg.TextItem(text="{:.1f}".format(self.hLeadingRoot), color="r" , anchor=(1, 0)) 
        self.hLeadingRootText.setPos( self.cRoot.value() + self.mTrailingRoot.value() , self.hLeadingRoot )   
        self.plotBlocSideViewRoot.addItem(self.hLeadingRootText)
        self.hTrailingTipText = pg.TextItem(text="{:.1f}".format(self.hTrailingTip), color="b" , anchor=(0, 0)) 
        self.hTrailingTipText.setPos( self.mTrailingTip.value() , self.hTrailingTip )   
        self.plotBlocSideViewTip.addItem(self.hTrailingTipText)
        self.hLeadingTipText = pg.TextItem(text="{:.1f}".format(self.hLeadingTip), color="b" , anchor=(1, 0))  
        self.hLeadingTipText.setPos( self.cTip.value() + self.mTrailingTip.value() , self.hLeadingTip )   
        self.plotBlocSideViewTip.addItem(self.hLeadingTipText)

        self.hMaxRootText = pg.TextItem(text="{:.1f}".format(self.hMaxRoot), color="r" , anchor=(0.5, 1))  
        self.hMaxRootText.setPos( self.mTrailingRoot.value() + self.cRoot.value()/2 , self.blocHZ.value() - self.hMaxRoot )   
        self.plotBlocSideViewRoot.addItem(self.hMaxRootText)
        self.hMinRootText = pg.TextItem(text="{:.1f}".format(self.hMinRoot), color="r" , anchor=(0.5, 0))  
        self.hMinRootText.setPos( self.mTrailingRoot.value() + self.cRoot.value()/2 , self.hMinRoot )   
        self.plotBlocSideViewRoot.addItem(self.hMinRootText)
        self.hMaxTipText = pg.TextItem(text="{:.1f}".format(self.hMaxTip), color="b" , anchor=(0.5 , 1))  
        self.hMaxTipText.setPos( self.mTrailingTip.value() + self.cTip.value()/2 , self.blocHZ.value() - self.hMaxTip )   
        self.plotBlocSideViewTip.addItem(self.hMaxTipText)
        self.hMinTipText = pg.TextItem(text="{:.1f}".format(self.hMinTip), color="b" , anchor=(0.5 , 0))  
        self.hMinTipText.setPos( self.mTrailingTip.value() + self.cTip.value()/2 , self.hMinTip )   
        self.plotBlocSideViewTip.addItem(self.hMinTipText)

