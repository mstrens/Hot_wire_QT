import math
import time

import numpy as np

from shapely.geometry import LineString
from shapely import affinity
from scipy import interpolate

from PyQt5 import QtWidgets, uic ,QtCore

def setProfilesInBloc(self):
    # Create pRoot and pTip taking care of block parameters
    # First calculate redundant data that are not related to the profiles
    self.fTrailing.setValue( -(self.cRoot.value() - self.cTip.value() - self.fLeading.value()  ) )
    if self.rbTableToBlockLeft.isChecked(): # bloc on the left 
        self.blocToTableRight.setValue( self.tableYY.value() - self.tableYG.value() -
            self.tableYD.value() - self.blocToTableLeft.value() -  self.blocLX.value())
    else:
        self.blocToTableLeft.setValue( self.tableYY.value() - self.tableYG.value() -
            self.tableYD.value() - self.blocToTableRight.value() - self.blocLX.value())
    self.blocToTableTrailingTip = self.blocToTableTrailingRoot.value() - self.fTrailing.value()
    self.blocToTableLeadingRoot = self.blocToTableTrailingRoot.value() +  self.cRoot.value() + self.mTrailingRoot.value() + self.mLeading.value() 

    self.blocToTableLeadingTip= self.blocToTableTrailingTip +  self.cTip.value() + self.mTrailingTip.value() + self.mLeading.value() 
    self.mSpeedHalf.setValue(self.mSpeedHigh.value() / 2) #half speed = high speed /2

    #reset p array before calculation
    self.pRootX = np.array([])
    self.pTipX = np.array([])
    self.pRootY = np.array([])
    self.pTipY =  np.array([])
    self.pRootS = []
    self.pTipS = []   

    #create pRoot and pTip based on tRoot and tTip and based on bloc and margin
    #calculate Root and Tip offset to apply
    #print("tRootX", self.tRootX)
    if (len(self.tRootX) > 0) and (len(self.tTipX) >0 ): # and (len(self.tRootX) == len(self.tTipX)):

        #calculate relative height of max, min leading
        hMaxRootNorm, hMinRootNorm , hLeadingRootNorm = calculateRelativeHeigths(self, self.tRootX , self.tRootY )        
        hMaxTipNorm, hMinTipNorm , hLeadingTipNorm = calculateRelativeHeigths(self, self.tTipX , self.tTipY )        
        #print("hMaxRootNorm", hMaxRootNorm)

        #Apply vertical aligment
        if self.cbAlignProfiles.currentIndex() == 0: #"Trailing":
            self.hTrailingRoot = self.hProfil.value()
            self.hTrailingTip = self.hProfil.value()
        elif self.cbAlignProfiles.currentIndex() == 1: # "Leading":
            self.hTrailingRoot = self.hProfil.value() - hLeadingRootNorm 
            self.hTrailingTip = self.hProfil.value() - hLeadingTipNorm
        elif self.cbAlignProfiles.currentIndex() == 2: #"Extrados":
            self.hTrailingRoot = self.hProfil.value() - hMaxRootNorm
            self.hTrailingTip = self.hProfil.value() - hMaxTipNorm
        elif self.cbAlignProfiles.currentIndex() == 3: #"Intrados":
            self.hTrailingRoot = self.hProfil.value() - hMinRootNorm
            self.hTrailingTip = self.hProfil.value() - hMinTipNorm
        self.hTrailingTip = self.hTrailingTip + self.diedral.value() #add diedral to tip
        self.hLeadingRoot = self.hTrailingRoot + hLeadingRootNorm
        self.hLeadingTip = self.hTrailingTip + hLeadingTipNorm
        self.hMaxRoot = self.blocHZ.value() - self.hTrailingRoot - hMaxRootNorm
        self.hMaxTip = self.blocHZ.value() - self.hTrailingTip - hMaxTipNorm
        self.hMinRoot = self.hTrailingRoot + hMinRootNorm
        self.hMinTip = self.hTrailingTip + hMinTipNorm       
        
        #apply offsets
        """
        self.pRootX = self.tRootX + self.blocToTableTrailingRoot.value() + self.mTrailingRoot.value()
        self.pTipX = self.tTipX + self.blocToTableTrailingTip + self.mTrailingTip.value()
        self.pRootY = self.tRootY + self.hOffset.value() + self.hTrailingRoot.value()
        self.pTipY =  self.tTipY + self.hOffset.value() + self.hTrailingRoot.value()
        """
        self.pRootX = self.tRootX + self.mTrailingRoot.value()
        self.pTipX = self.tTipX + self.mTrailingTip.value()
        self.pRootY = self.tRootY + self.hTrailingRoot
        self.pTipY =  self.tTipY  + self.hTrailingTip
        self.pRootS = list(self.tRootS) #create list of synchro points
        self.pTipS = list(self.tTipS) #create list of synchro points   

def calculateRelativeHeigths (self , pX , pY ):
    maxX = np.max(pX)
    idxMax = np.where(pX == maxX) #return an array with indexes
    minY = np.min(pY)
    maxY = np.max(pY)
    maxh = maxY - pY[0]
    minh = minY - pY[0]
    if len(idxMax) > 0 and len(idxMax[0]) > 0:
        r = idxMax[0][0]
        leadingh = pY[r] - pY[0]
    else:
        leadingh = 0     
    return maxh ,minh, leadingh


def calculateWireProfil(self):
    #it starts from pRoot and pTip (= profile taking care of bloc size and position in bloc but with position of bloc)
    #add enty and exit points in bloc
    #applies offset for radiance
    #simplifies the profiles if possible = simRoot and Tip
    #add the bloc offset compare to the table.
    #calculate the projection GX GY DX and DY

    
    #reset array being used
    # profiles to be followed by the wire (simplified and synchronised)
    self.oSimRX = [] 
    self.oSimRY = []
    self.oSimTX = [] 
    self.oSimTY = []
    #print("tRootX in wire" , self.tRootX)
    #Vérifier la présence et l'égalité du nombre de points dans les 2 profils
    #to do control number of synchro points
    if (len(self.tRootX) > 0) and (len(self.tTipX) >0 ): # and (len(self.tRootX) == len(self.tTipX)):
        # create eRoot and eTip and add entry and exit points in the bloc (before applying heating offset)      
        #print("pRootX pTipX", self.pRootX , self.pTipX)
        #print("pRootY pTipY", self.pRootY , self.pTipY)
        #print("pRootS pTipS", self.pRootS , self.pTipS)
        eRootX = self.pRootX.tolist()
        eRootY = self.pRootY.tolist()
        eRootS = list(self.pRootS)
        eTipX =  self.pTipX.tolist()
        eTipY =  self.pTipY.tolist()
        eTipS = list(self.pTipS)
        deltaInRoot = math.tan(self.angleInRoot.value()/180*math.pi ) * self.mTrailingRoot.value()
        deltaOutRoot = math.tan(self.angleOutRoot.value()/180*math.pi ) * self.mTrailingRoot.value()
        deltaInTip = math.tan(self.angleInTip.value()/180*math.pi ) * self.mTrailingTip.value()
        deltaOutTip = math.tan(self.angleOutTip.value()/180*math.pi ) * self.mTrailingTip.value()
        
        eRootX.insert(0,0.0)
        eRootY.insert(0, self.pRootY[0]  - deltaInRoot )
        eTipX.insert(0,0.0)
        eTipY.insert(0, self.pTipY[0] - deltaInTip )
        eRootX.append(0.0)
        eRootY.append(self.pRootY[-1] - deltaOutRoot )
        eTipX.append(0.0)
        eTipY.append(self.pTipY[-1] - deltaOutTip)
        eRootS.insert(0,4) # add a Synchro (with radiance) point
        eTipS.insert(0,4) # add a Synchro (with radiance) point
        eRootS[-1] = 4 # mark the last point as Synchro (with radiance) point
        eTipS[-1] = 4 # mark the last point as Synchro (with radiance) point
        eRootS.append(4) #add a last point as Synchro
        eTipS.append(4) #add a last point as Synchro
        
        # insert X profile of leading edge when activated
        if self.gbXLeadingActive.isChecked(): 
            eRootX, eRootY, eRootS, eTipX, eTipY, eTipS = insertXLeadingEdge(self, eRootX, eRootY, eRootS, eTipX, eTipY, eTipS)

        #print("Root=", list(zip(eRootX, eRootY, eRootS)))
        #build 2 listes with length of segments 
        rootL = lengthSegment(eRootX , eRootY)
        tipL = lengthSegment(eTipX , eTipY)

        #build list of index of pt of synchro and length of sections between synchro
        eRootI , eRootL = lengthSection( eRootS , rootL)
        eTipI , eTipL = lengthSection( eTipS , tipL)
        #print("Root: Synchro code & Index, length segments & sections", eRootS ,  eRootI, rootL  , eRootL)        
        #print("Tip: Synchro code & Index, length segments & sections", eTipS , eTipI , tipL ,   eTipL)        
        #compare les longueurs pour trouver le coté le plus long
        compLength = compareLength( eRootL, eTipL)
        #print("compare length", compLength)
        #Calcule la radiance de chaque côté ; met 0 si 
        rRoot , rTip = calculate2Radiance( self, compLength, self.vCut.value())
        #print("radiance root", rRoot )
        #print("radiance tip",  rTip)
        #create eRootR and eTipR with the radiance to fit the same nbr of item as exxxS
        eRootR =  createRadiance(eRootS , rRoot)
        #print('full radiance root', eRootR)
        eTipR =  createRadiance(eTipS , rTip)
        #print('full radiance tip', eTipR)
        # calculate offset on each side; create one new point at each synchronisation to take care of different radiance offsets
        self.offsetRootX , self.offsetRootY ,self.offsetRootS = calculateOffset(eRootX, eRootY, eRootR ,eRootS)
        
        #print("offset root", list(zip( self.offsetRootX , self.offsetRootY ,self.offsetRootS)))
        self.offsetTipX , self.offsetTipY , self.offsetTipS = calculateOffset(eTipX, eTipY, eTipR, eTipS)
        #print("offset tip", list(zip( self.offsetTipX , self.offsetTipY ,self.offsetTipS)))
        
        #print("len R T",len(self.offsetRootX) , len(self.offsetTipX) )
        # adjust points in order to have the same number of points on each section
        self.syncRX , self.syncRY , self.syncTX, self.syncTY = synchrAllSections( self, 
            self.offsetRootX , self.offsetRootY ,self.offsetRootS , self.offsetTipX , self.offsetTipY , self.offsetTipS)
        """
        print("eRoot X Y", eRootX, eRootY)
        print("eTip X Y", eTipX, eTipY)
        print("offset RX RY", self.offsetRootX , self.offsetRootY)
        print("offset TX TY", self.offsetTipX , self.offsetTipY)
        print("distance offset Rx Ry", self.printDistance(self.offsetRootX , self.offsetRootY))
        print("distance offset Tx Ty",  self.printDistance(self.offsetTipX , self.offsetTipY))
        """
        #Remove points if they are to close from each other (on both sides)
        #print("Offset ", self.offsetRootX , self.offsetRootY , self.offsetTipX , self.offsetTipY)
        self.oSimRX , self.oSimRY, self.oSimTX , self.oSimTY = simplifyProfiles(
            self.syncRX , self.syncRY , self.syncTX, self.syncTY )

        #add block offsets (horizontal and vertical) to take care of block position on the table
        self.wireRX = np.array(self.oSimRX) + self.blocToTableTrailingRoot.value()
        self.wireTX = np.array(self.oSimTX) + self.blocToTableTrailingRoot.value() - self.fTrailing.value()
        self.wireRY = np.array(self.oSimRY) + self.hOffset.value()
        self.wireTY = np.array(self.oSimTY) + self.hOffset.value()
        #Calculate projections on cnc axis, messages, speed and feedRate (inverted)
        if self.rbRightWing.isChecked(): # 'Right': #for right wing, the root is on the left side
            self.GX , self.DX , self.GY, self.DY, self.warningMsg , self.speed , self.feedRate = projectionAll( self, 
                #self.oSimRX , self.oSimTX , self.oSimRY, self.oSimTY,
                self.wireRX , self.wireTX , self.wireRY, self.wireTY, 
                self.blocToTableLeft.value() + self.tableYG.value() , 
                self.blocLX.value() ,
                self.tableYY.value() -self.blocToTableLeft.value() - self.tableYG.value() - self.blocLX.value() )
        else: #Left wing = root is on rigth side
            self.GX , self.DX , self.GY, self.DY, self.warningMsg, self.speed, self.feedRate = projectionAll( self, 
                #self.oSimTX, self.oSimRX , self.oSimTY ,self.oSimRY,
                self.wireTX, self.wireRX , self.wireTY ,self.wireRY,  
                self.blocToTableLeft.value() + self.tableYG.value() , 
                self.blocLX.value() ,
                self.tableYY.value() -self.blocToTableLeft.value() - self.tableYG.value() - self.blocLX.value() )
        #print("Speed mm/sec", self.speed)        
        self.cutMsg.setText(self.warningMsg) 
        #print("Projection ", self.GX , self.DX , self.GY, self.DY)
        #print("Projection ", self.GX , self.DX )
        #genère le Gcode
        # set G54 à la valeur actuelle, set absolu et mm, set feed rate, met en chauffe, attend 5 sec 
        # monte à la hauteur du ppremier point puis avance au premier point
        # passe tous les points
        # revient à la verticale de l'origine puis à l'origine
        # attend 5 sec puis éteint la chauffe puis éteint les moteurs
        self.gcode = generateGcode(self , self.GX , self.DX , self.GY, self.DY, self.speed, self.feedRate, False) #false says that it is not a spar cut

def insertXLeadingEdge( self, RX, RY, RS, TX, TY, TS):
    # insert X leading edge
    # find the leading edge and check it is a synchro point
    # calculate coordinates for 4 points
    # insert the 4 points at of leading edge
    if self.cbXLeadingCut.currentIndex() == 1: # "Tip = Root" 
        self.xLeadingAngle1Tip.setValue(self.xLeadingAngle1Root.value())  
        self.xLeadingAngle2Tip.setValue(self.xLeadingAngle2Root.value()) 
        self.xLeadingHeight1Tip.setValue(self.xLeadingHeight1Root.value() )
        self.xLeadingHeight2Tip.setValue(self.xLeadingHeight2Root.value()  )
        self.xLeadingLengthTip.setValue(self.xLeadingLengthRoot.value() )
        self.xLeadingAngle1Tip.setEnabled(False)
        self.xLeadingAngle2Tip.setEnabled(False) 
        self.xLeadingHeight1Tip.setEnabled(False)
        self.xLeadingHeight2Tip.setEnabled(False)
        self.xLeadingLengthTip.setEnabled(False)
        
    elif self.cbXLeadingCut.currentIndex() == 0: # "Porportional tip dimensions"
        self.xLeadingAngle1Tip.setValue(self.xLeadingAngle1Root.value())  
        self.xLeadingAngle2Tip.setValue(self.xLeadingAngle2Root.value()) 
        self.xLeadingHeight1Tip.setValue(self.xLeadingHeight1Root.value() * self.cTip.value() / self.cRoot.value()  )
        self.xLeadingHeight2Tip.setValue(self.xLeadingHeight2Root.value() * self.cTip.value() / self.cRoot.value()  )
        self.xLeadingLengthTip.setValue(self.xLeadingLengthRoot.value() * self.cTip.value() / self.cRoot.value()  )   
        self.xLeadingAngle1Tip.setEnabled(False)
        self.xLeadingAngle2Tip.setEnabled(False) 
        self.xLeadingHeight1Tip.setEnabled(False)
        self.xLeadingHeight2Tip.setEnabled(False)
        self.xLeadingLengthTip.setEnabled(False)
    else:  # customs dimensions
        self.xLeadingAngle1Tip.setEnabled(True)
        self.xLeadingAngle2Tip.setEnabled(True) 
        self.xLeadingHeight1Tip.setEnabled(True)
        self.xLeadingHeight2Tip.setEnabled(True)
        self.xLeadingLengthTip.setEnabled(True)
    length1Root = self.xLeadingHeight1Root.value() / math.tan(self.xLeadingAngle1Root.value() * math.pi / 180)
    length2Root = self.xLeadingHeight2Root.value() / math.tan(self.xLeadingAngle2Root.value() * math.pi / 180)
    length1Tip = self.xLeadingHeight1Tip.value() / math.tan(self.xLeadingAngle1Tip.value() * math.pi / 180)
    length2Tip = self.xLeadingHeight2Tip.value() / math.tan(self.xLeadingAngle2Tip.value() * math.pi / 180)
    lengthRootMax = self.xLeadingLengthRoot.value() 
    if lengthRootMax < (length1Root + 5):
        lengthRootMax = length1Root + 5
    if  lengthRootMax < (length2Root + 5):
        lengthRootMax = length2Root + 5
    self.xLeadingLengthRoot.setValue(lengthRootMax)
    lengthTipMax = self.xLeadingLengthTip.value() 
    if lengthTipMax < (length1Tip + 5):
        lengthTipMax = length1Tip + 5
    if  lengthTipMax < (length2Tip + 5):
        lengthTipMax = length2Tip + 5
    self.xLeadingLengthTip.setValue(lengthTipMax)
    #lengthRootMax = max( [length1Root ,length2Root , self.xLeadingLengthRoot.value() ])
    #lengthTipMax = max( [length1Tip ,length2Tip , self.xLeadingLengthTip.value() ])
    vRMax = -10000.0
    iRMax = 0
    for i , x in enumerate(RX): #find the leading edge at root
        if x > vRMax:
            iRMax = i
            vRMax = x
    
    vTMax = -10000.0
    iTMax = 0
    for i , x in enumerate(TX): #find the leading edge at tip
        if x > vTMax:
            iTMax = i
            vTMax = x
    RX[iRMax:iRMax] = [ RX[iRMax] , RX[iRMax] + length1Root, RX[iRMax] + lengthRootMax , RX[iRMax] + lengthRootMax , RX[iRMax] + length2Root]
    RY[iRMax:iRMax] = [ RY[iRMax], RY[iRMax] - self.xLeadingHeight1Root.value(), RY[iRMax] - self.xLeadingHeight1Root.value() ,
        RY[iRMax] + self.xLeadingHeight2Root.value() , RY[iRMax] + self.xLeadingHeight2Root.value() ]
    RS[iRMax:iRMax] = [4,4,4,4,4]
    TX[iTMax:iTMax] = [ TX[iTMax], TX[iTMax] + length1Tip, TX[iTMax] + lengthTipMax , TX[iTMax] + lengthTipMax , TX[iTMax] + length2Tip]
    TY[iTMax:iTMax] = [ TY[iTMax], TY[iTMax] - self.xLeadingHeight1Tip.value(), TY[iTMax] - self.xLeadingHeight1Tip.value() ,
        TY[iTMax] + self.xLeadingHeight2Tip.value() , TY[iTMax] + self.xLeadingHeight2Tip.value() ]
    TS[iTMax:iTMax] = [4,4,4,4,4]
    
    return RX, RY, RS, TX, TY, TS

def lengthSegment(X , Y):
    l=[]
    i = 1
    imax = len(X)
    if imax > 1:
        x = X[0]
        y = Y[0]
        while i < imax:
            xn , yn = X[i] , Y[i]
            l.append(math.sqrt( ((xn-x) * (xn-x)) + ((yn-y) * (yn-y)) ) )
            x , y = xn ,yn
            i += 1
    return l

def lengthSection( s , l):
    #create a list with index of synchro point and with the length of section
    # s = list of synchro code and l = length of segments to cumulate
    # NB:  a section is all points between synchro
    #print("len s et l", len(s) , len(l))
    #print("s et l=", s , l)
    ls=[]
    idxSynchro=[]
    i=0
    iMax = len(s)
    if iMax > 1:
        while i < (iMax-1):
            idxSynchro.append(i)
            ls.append(l[i])
            i += 1
            while s[i] == 0:
                ls[-1] += l[i]
                i += 1
        idxSynchro.append(i)
    return idxSynchro , ls #return list of index and list of length    

def compareLength( r , t): #return empty list if legnth of 2 input list are not the same
    # return the ratio between the shortest and the longest
    # value is > 0 when root is greater or equal than tip; negative if the opposite 
    c=[]
    i=0
    rmax = len(r)
    tmax = len(t)
    if rmax > 0 and rmax == tmax:
        while i < rmax:
            ri = r[i]
            ti = t[i]
            if (ri + ti ) == 0:
                c.append( 1 )
            elif ri >= ti:
                c.append( ti / ri )
            else:
                c.append( -ri / ti )
            i += 1    
    return c            

def createRadiance( s , r):
    # create a radiance list with the same nbr of items as s and using the radiance in r
    imax = len(s)
    i=0
    rIdx = 0
    rTemp = 0
    result = []
    while i < (imax-1):
        if s[i] > 0:
            if s[i] > 4:  # this assume that the radiance must be forced to 0 
                rTemp= 0    
            else:
                rTemp= r[rIdx]
            rIdx += 1
        result.append(rTemp)
        i += 1
    return result

def printDistance(x,y):
    imax = len(x)
    i=0
    result = []
    while i < imax-1:
        d1 = x[i+1]-x[i]
        d2 = y[i+1]-y[i]
        result.append(math.sqrt(d1*d1 +d2*d2))
        i += 1
    return result

def projectionAll(self, x1 , x2 , y1 , y2, lg, l, ld):
    # lg = outside length on the left side (from bloc to left axis) 
    # l = legnth between the 2 sides of bloc 
    # ld = outside length on the right side (from bloc to right axis)
    # x1 y1 = profil on the left side
    # x2 y2 = profil on the rigth side
    # return projection, warning msg and speed
    xg = []
    xd = []
    yg = []
    yd = []
    speed = [] # in mm/sec
    feedRate=[] # inverted feed rate for G93: e.g. 2 means that the movement has to be executed in 1/2 min 
    xgmin = x1[0]
    xgmax = x1[0]
    xdmin = x2[0]
    xdmax = x2[0]
    ygmin = y1[0]
    ygmax = y1[0]
    ydmin = y2[0]
    ydmax = y2[0]
    vxGMax = 0
    vyGMax = 0
    vxDMax = 0
    vyDMax = 0
    msg = ""
    i = 0
    imax = len(x1)
    if imax > 0:
        while i < imax:
            xg.append( ( (x1[i]-x2[i]) / l * lg ) + x1[i] )
            xd.append( ( (x2[i]-x1[i]) / l * (l+ld) ) + x1[i] )
            yg.append( ( (y1[i]-y2[i]) / l * lg ) + y1[i] )
            yd.append( ( (y2[i]-y1[i]) / l * (l+ld) ) + y1[i] )          
            if xg[i] < xgmin: xgmin = xg[i]
            if xg[i] > xgmax: xgmax = xg[i]
            if xd[i] < xdmin: xdmin = xd[i]
            if xd[i] > xdmax: xdmax = xd[i]
            if yg[i] < ygmin: ygmin = yg[i]
            if yg[i] > ygmax: ygmax = yg[i]
            if yd[i] < ydmin: ydmin = yd[i]
            if yd[i] > ydmax: ydmax = yd[i]
            if i > 0: #calculate speed on Y axis
                #calculate legnth of segment
                dx1 = x1[i-1] - x1[i]
                dy1 = y1[i-1] - y1[i]
                dx2 = x2[i-1] - x2[i]
                dy2 = y2[i-1] - y2[i]
                dxG = abs( xg[i-1] - xg[i] )
                dyG = abs( yg[i-1] - yg[i] )
                dxD = abs( xd[i-1] - xd[i] )
                dyD = abs( yd[i-1] - yd[i] )
                d1 = dx1 *dx1 + dy1 * dy1
                d2 = dx2 *dx2 + dy2 * dy2
                dG = dxG *dxG + dyG * dyG
                dD = dxD *dxD + dyD * dyD
                #select the longest side
                if d1 >= d2:
                    d1 = math.sqrt(d1)
                    dG = math.sqrt(dG)
                    d2 = math.sqrt(d2)
                    dD = math.sqrt(dD)
                    v1 = self.vCut.value()
                    speed.append( v1 * dG / d1)
                    feedRate.append( v1 / d1 * 60 )
                    vGD = v1 * dG / d1
                    vxG = v1 * dxG / d1
                    vyG = v1 * dyG / d1
                    vxD = v1 * dxD / d1
                    vyD = v1 * dyD / d1
                else:     
                    d1 = math.sqrt(d1)
                    dG = math.sqrt(dG)
                    d2 = math.sqrt(d2)
                    dD = math.sqrt(dD)
                    v2 = self.vCut.value()
                    speed.append( v2 * dD / d2)
                    feedRate.append( v2 / d2 * 60 )
                    vGD = v2 * dD / d2
                    vxG = v2 * dxG / d2
                    vyG = v2 * dyG / d2
                    vxD = v2 * dxD / d2
                    vyD = v2 * dyD / d2
                #print(" point {} dG={:.3f} d1={:.3f} dD={:.3f} d2={:.3f}  vGD={:.3f} vxG={:.3f}  vyG={:.3f} , vxD={:.3f} , vyD={:.3f} "\
                #    .format(i , dG , d1, dD , d2, vGD, vxG , vyG , vxD , vyD))
                if vxG > vxGMax: vxGMax = vxG
                if vyG > vyGMax: vyGMax = vyG
                if vxD > vxDMax: vxDMax = vxD
                if vyD > vyDMax: vyDMax = vyD 
            i += 1
        if xgmin < 0:
            msg = msg + "Left X axis precedes origin {:.1f}\n".format(xgmin)
        if xgmax > self.cMaxY.value():
            msg = msg + "Left X axis exceeds limit {:.1f}\n".format(xgmax)
        if xdmin < 0:
            msg = msg + "Right X axis precedes origin {:.1f}\n".format(xdmin)
        if xdmax > self.cMaxY.value():
            msg = msg + "Right X axis exceeds limit {:.1f}\n".format(xdmax)
        if ygmin < 0:
            msg = msg + "Left Y axis precedes origin {:.1f}\n".format(ygmin)
        if ygmax > self.cMaxZ.value():
            msg = msg + "Left Y axis exceeds limit {:.1f}\n".format(ygmax)
        if ydmin < 0:
            msg = msg + "Right Y axis precedes origin {:.1f}\n".format(ydmin)
        if ydmax > self.cMaxZ.value():
            msg = msg + "Right Y axis exceeds limit {:.1f}\n".format(ydmax)
        if vxGMax > self.vMaxY.value(): 
            msg = msg + "Left X axis speed to high {:.3f}\n".format(vxGMax)
        if vyGMax > self.vMaxZ.value():
            msg = msg + "Left Y axis speed to high {:.3f}\n".format(vyGMax)
        if vxDMax > self.vMaxY.value():
            msg = msg + "Right X axis speed to high {:.3f}\n".format(vxDMax)
        if vyDMax > self.vMaxZ.value():
            msg = msg + "Right Y axis speed to high {:.3f}\n".format(vyDMax)
    return xg ,xd ,yg , yd , msg , speed , feedRate
        
def simplifyProfiles( rX , rY , tX , tY ):
    imax = len(rX)
    oRX=[]
    oRY=[]
    oTX=[]
    oTY=[]
    i = 0
    if imax > 0:
        rXp = rX[i]
        rYp = rY[i]
        tXp = tX[i]
        tYp = tY[i]
        oRX.append(rXp)
        oRY.append(rYp)
        oTX.append(tXp)
        oTY.append(tYp)
        i = 1
        while i < imax:
            dRX = rX[i] - rXp
            dRX *= dRX
            dRY = rY[i] - rYp
            dRY *= dRY
            dTX = tX[i] - tXp
            dTX *= dTX
            dTY = tY[i] - tYp
            dTY *= dTY
            if dRX > 0.01 or dRY > 0.01 or dTX > 0.01 or dTY > 0.01:
                rXp = rX[i]
                rYp = rY[i]
                tXp = tX[i]
                tYp = tY[i]
                oRX.append(rXp)
                oRY.append(rYp)
                oTX.append(tXp)
                oTY.append(tYp)
            i += 1
    return oRX, oRY, oTX, oTY
            

def calculateOffset( x, y , r, s ):
    #create an offset for curve x y at a distance r (which varies) taking care of synchronisations
    # for each synchronisation point, create 2 offset points instead of 1 
    #x ,y, r (radiance) , s (synchro) have the same length
    # return new x y s 
    # pour 3 points successifs p1-p2-p3 avec r1-r2, calcule les pt d'intersection des 2 offsets
    #print("calculateOffset for x, y, r,s", x ,y , r ,s)
    ox=[]
    oy=[]
    os=[]
    imax = len(r)
    i = 0
    if imax >= 1:
        #met le premier point            
        oxi , oxj, oyi, oyj = offset1Segment(x[0], x[1] , y[0], y[1] , r[0])
        ox.append(oxi)
        oy.append(oyi)
        os.append(s[0])
        while i < (imax-1):
            if s[i+1] == 0: #if it not a syncho, then offset is the same on both segements and we just take the intersection of the 2 offsets
                oxi, oyi = offset2Segment(x[i] , x[i+1] ,x[i+2], y[i] ,y[i+1] ,y[i+2] ,r[i] )
                ox.append(oxi)
                oy.append(oyi)
                os.append(s[i+1])
            else:
                # for a synchro point, whe calculate 2 intersects (one for first offset and one for second offset)
                # and we add each of them (so we add a point)
                #print("offset2Segments" , x[i] , x[i+1] ,x[i+2], y[i] ,y[i+1] ,y[i+2] ,r[i])
                """
                
                oxi, oyi = offset2Segment(x[i] , x[i+1] ,x[i+2], y[i] ,y[i+1] ,y[i+2] ,r[i] )
                ox.append(oxi)
                oy.append(oyi)
                os.append(s[i+1])
                oxi, oyi = offset2Segment(x[i] , x[i+1] ,x[i+2], y[i] ,y[i+1] ,y[i+2] ,r[i+1] )
                ox.append(oxi)
                oy.append(oyi)
                os.append(s[i+1])
                """
                newX1, newY1 , newX2, newY2 = offsetASynchroPoint(x[i] , x[i+1] ,x[i+2], y[i] ,y[i+1] ,y[i+2] ,r[i] , r[i+1])
                ox.append(newX1)
                oy.append(newY1)
                os.append(s[i+1])
                ox.append(newX2)
                oy.append(newY2)
                os.append(s[i+1])    
            i += 1
        oxi , oxj, oyi, oyj = offset1Segment(x[i], x[i+1] , y[i], y[i+1] , r[i])
        ox.append(oxj)
        oy.append(oyj)
        os.append(s[-1])        
    return ox ,oy, os    

def offsetASynchroPoint(x1 , x2 ,x3, y1 ,y2 ,y3 ,o1 , o2):
    # calculate the angle between the 2 segments
    #print("offset synchro for ",x1 , x2 ,x3, y1 ,y2 ,y3 , o1, o2)
    alpha = ( math.atan2(y1-y2 , x1-x2) - math.atan2(y3-y2 , x3-x2) ) * 180 / math.pi # angle between the 2 segments
    if alpha < 0:
        alpha = alpha + 360
    if o1 > o2: # first segment has a greter ofsset
        if alpha <= 180:
            #print("cas 1, 2")
            # p1 = intersec segment1+offset1 with segment2+offset1
            # p2 = projection of this point on segment2+offset2
            l1x1, l1x2 , l1y1 ,l1y2 =  offset1Segment(x1,x2,y1,y2,o1)
            #print("segment 1 offset 1= ", l1x1, l1x2 , l1y1 ,l1y2)
            l2x1, l2x2 , l2y1 ,l2y2 =  offset1Segment(x2,x3,y2,y3,o1)
            #print("segment 2 offset 1= ", l2x1, l2x2 , l2y1 ,l2y2)
            newX1, newY1 = intersec(l1x1, l1x2 , l1y1 ,l1y2 , l2x1, l2x2 , l2y1 ,l2y2)
            #print("intersec=p1=", newX1, newY1)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment 2 offset 2= ", l2x1, l2x2 , l2y1 ,l2y2)
            newX2, newY2 = projection( l2x1, l2x2 , l2y1 ,l2y2, newX1, newY1)
            #print("projection=p2=", newX2, newY2)        
        elif alpha <= 270:
            #print("cas 3")
            # p1 = intersec segment1+offset1 with segment2+offset1
            # p2 = projection of mid point of segment on segment2+offset2
            l1x1, l1x2 , l1y1 ,l1y2 =  offset1Segment(x1,x2,y1,y2,o1)
            #print("segment 1 offset 1= ", l1x1, l1x2 , l1y1 ,l1y2)
            l2x1, l2x2 , l2y1 ,l2y2 =  offset1Segment(x2,x3,y2,y3,o1)
            #print("segment 2 offset 1= ", l2x1, l2x2 , l2y1 ,l2y2)
            newX1, newY1 = intersec(l1x1, l1x2 , l1y1 ,l1y2 , l2x1, l2x2 , l2y1 ,l2y2)
            #print("intersec=p1=", newX1, newY1)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment 2 offset 2= ", l2x1, l2x2 , l2y1 ,l2y2)
            newX2, newY2 = projection( l2x1, l2x2 , l2y1 ,l2y2, x2, y2)
            #print("projection=p2=", newX2, newY2)        
        else: 
            #print("cas 4")
            # p1 = Projection of mid point on segment1+offset1 and calculate extend of offset2 on segment1+offset1
            # p2 = Projection of mid point on segment2+offset2 and calculate extend of offset1 on segment2+offset2
            l1x1, l1x2 , l1y1 ,l1y2 = offset1Segment(x1,x2,y1,y2,o1)  
            #print("segment 1 offset 1" , l1x1, l1x2 , l1y1 ,l1y2)
            x, y  =  projection( l1x1, l1x2 , l1y1 ,l1y2 , x2, y2)
            #print("projection", x, y)
            newX1, newY1 = extension(x,y, l1x1, l1x2 , l1y1 ,l1y2, o2)
            #print("extension= p1 =", newX1, newY1)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment 2 offset 2", l2x1, l2x2 , l2y1 ,l2y2 )
            x, y  =  projection( l2x1, l2x2 , l2y1 ,l2y2 , x2 , y2)
            #print("projection", x, y)
            newX2, newY2 = extension(x,y, l2x2, l2x1 , l2y2 ,l2y1 ,o1)
            #print("extension = p2 =", newX2, newY2)
    else:
        if alpha < 90:
            #print("cas 5")
            # 2X intersec segment1+offset1 with segment2+offset2
            l1x1, l1x2 , l1y1 ,l1y2 = offset1Segment(x1,x2,y1,y2,o1)
            #print("segment 1 offset 1" , l1x1, l1x2 , l1y1 ,l1y2)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment 2 offset 2", l2x1, l2x2 , l2y1 ,l2y2 )
            newX1, newY1 = intersec( l1x1, l1x2 , l1y1 ,l1y2 , l2x1, l2x2 , l2y1 ,l2y2 )
            #print("intersec= p1 = p2= ", newX1, newY1)
            newX2 = newX1
            newY2 = newY1
        elif alpha <= 180:
            #print("cas 6")
            # p2 = intersec segment1+offset2 with segment2+offset2 (calculation in reverse order)
            # p1 = projection on segment1+offset1
            l1x1, l1x2 , l1y1 ,l1y2 = offset1Segment(x1,x2,y1,y2,o2)
            #print("segment1 offset2=", l1x1, l1x2 , l1y1 ,l1y2)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment2 offset2=", l2x1, l2x2 , l2y1 ,l2y2 ) 
            newX2 , newY2 = intersec(l1x1, l1x2 , l1y1 ,l1y2 , l2x1, l2x2 , l2y1 ,l2y2)
            l1x1, l1x2 , l1y1 ,l1y2 = offset1Segment(x1,x2,y1,y2,o1)
            #print("segment1 offset1=", l1x1, l1x2 , l1y1 ,l1y2)
            newX1 , newY1 = projection( l1x1, l1x2 , l1y1 ,l1y2 , newX2 , newY2)
            #print("projection=p1 = ", newX1 , newY1)
            #print("intersec=p2 = ", newX2 , newY2)
        elif alpha < 270:
            #print("cas 7")
            # p1 = intersec segment1+offset1 with segment2+offset1
            # p2 = projection on segment2+offset2
            l1x1, l1x2 , l1y1 ,l1y2 = offset1Segment(x1,x2,y1,y2,o1)
            #print("segment1 offset1=", l1x1, l1x2 , l1y1 ,l1y2)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o1)
            #print("segment2 offset1=", l2x1, l2x2 , l2y1 ,l2y2 )
            newX1, newY1 = intersec(l1x1, l1x2 , l1y1 ,l1y2 , l2x1, l2x2 , l2y1 ,l2y2 )
            #print("intersec= p1 = ", newX1, newY1)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment2 offset2=", l2x1, l2x2 , l2y1 ,l2y2 )
            newX2, newY2 = projection( l2x1, l2x2 , l2y1 ,l2y2 , newX1 , newY1)
            #print("projection=p2 = ", newX2 , newY2)
        else:       
            # Projection of mid point of segment1 on segment1+offset1
            # p1 = extend from this point on a length = offset2 on segment1+offset1 
            # Projection of mid point of segment1 on segment2+offset2
            # p2 = extend from this point on a length = offset1 on segment2+offset2
            #print("cas8")
            l1x1, l1x2 , l1y1 ,l1y2 = offset1Segment(x1,x2,y1,y2,o1) 
            #print("segment1 offset1=", l1x1, l1x2 , l1y1 ,l1y2)
            x , y = projection( l1x1, l1x2 , l1y1 ,l1y2 , x2 , y2)
            #print("projection for p1=", x,y)
            newX1, newY1 = extension( x,y, l1x1, l1x2 , l1y1 ,l1y2 , o2)
            #print("extension=P1= ",newX1, newY1)
            l2x1, l2x2 , l2y1 ,l2y2 = offset1Segment(x2,x3,y2,y3,o2)
            #print("segment2 offset2=", l2x1, l2x2 , l2y1 ,l2y2 )
            x , y = projection( l2x1, l2x2 , l2y1 ,l2y2 , x2 , y2)
            #print("projection for p2=", x,y)
            newX2, newY2 = extension( x,y, l2x2, l2x1 , l2y2 ,l2y1 , o1)
            #print("extension=P2= ",newX2, newY2)
    return newX1, newY1 , newX2, newY2

def projection( x1, x2, y1, y2 , x3, y3):
    # x1,y1 = first point of a line; x2,y2 = second point of the line
    # x3,y3 = point to be projected
    #return x4,y4 = projected point
    #print("projection of line =", x1, x2, y1, y2 ," by point", x3, y3)
    if  ((x2 -x1) * (x2 -x1) + (y2 - y1) * (y2 - y1)) == 0:
        print("div by 0 in projection of line x1 x2 y1 y2=", x1, x2, y1, y2 ," by point", x3, y3)
        return x3, y3
    x = ( (x2-x1) * (x3-x2) + (y2-y1) * (y3-y2)) / ( (x2 -x1) * (x2 -x1) + (y2 - y1)*(y2-y1))
    x4 = x2 + (x2-x1)*x
    y4 = y2 + (y2-y1)*x
    return x4,y4

def extension(pX,pY,x1,x2,y1,y2,o):
    # pX, pY = point on the line defiened by x1,x2,y1,y2 ; o = extension
    len = math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))
    if len == 0:
        return pX,pY
    x = x2 + o * (x2-x1) / len
    y = y2 + o * (y2-y1) / len      
    return x ,y

def calculate2Radiance( self,  compLength , speedMax):    
    #print("in calculate2Radaiance, speedMax =" , speedMax)
    oMin = radiance(self, speedMax)
    #print("oMin =", oMin )
    imax = len(compLength)
    rR = [] #radiance at root
    rT = [] #radiance at tip
    i=0
    if imax > 0:
        while i < imax:
            cLi = compLength[i]
            speedLow = speedMax * cLi
            #print("speedLow=", speedLow)
            #print("radiance speedLow" , self.radiance(speedLow) )
            if cLi >= 0: # root is longer
                rR.append(oMin)
                rT.append(radiance(self, speedLow))
            else:
                rT.append(oMin)
                rR.append(radiance(self, -speedLow))
            i += 1        
    return rR , rT

def radiance(self , speed):
    #print("mRadSpHalf=", self.mRadSpHalf.value() )
    #print("mRadSpHigh" , self.mRadSpHigh.value() )
    #print("mSpeedHalf" , self.mSpeedHalf.value() )
    #print("mSpeedHigh" , self.mSpeedHigh.value() )
    a = (self.mRadSpHalf.value() - self.mRadSpHigh.value()) / (self.mSpeedHalf.value() - self.mSpeedHigh.value())
    return 0.5 * ( ( a * ( speed - self.mSpeedHalf.value())) + self.mRadSpHalf.value() ) # use only 1/2 of radiance for the offset

def synchrAllSections(self, rX, rY, rS, tX, tY , tS):
    #synchronise 2 profiles in order to get the same number of points
    #it has to respect synchronisation points
    sectionsIdxR = sectionsIdx (rS)
    sectionsIdxT = sectionsIdx (tS)
    imax = len(sectionsIdxR)
    i=0
    syncRX=[]
    syncRY=[]
    syncTX=[]
    syncTY=[]
    
    if imax > 0:
        while i < imax:
            firstR = sectionsIdxR[i][0]
            lastR =  sectionsIdxR[i][1] + 1
            firstT = sectionsIdxT[i][0]
            lastT =  sectionsIdxT[i][1] + 1
            #print( "first fast", firstR, lastR , firstT, lastT)
            #print("rX" ,  rX[firstR:lastR] )
            sRX, sRY, sTX, sTY = synchroOneSection(  rX[firstR:lastR], rY[firstR:lastR], tX[firstT:lastT], tY[firstT:lastT])     
            syncRX = syncRX + sRX.tolist()
            syncRY = syncRY + sRY.tolist()
            syncTX = syncTX + sTX.tolist()
            syncTY = syncTY + sTY.tolist()
            i += 1
    return syncRX , syncRY , syncTX, syncTY

def sectionsIdx( s ):
    # return a list of turple with begin and end Idx of each section
    i=0
    imax = len(s)
    result = []
    if imax > 1:
        while i < (imax-1):
            j = i+1
            while s[j] == 0:
                j += 1
            result.append( (i , j))
            i = j+1         
    return result

def synchroOneSection( rX, rY, tX, tY):
    """pour chaque tronçon
    calcule la longueur cumulée R et T
    Ramène les longueurs cumulées dans un range 0 <> 1 pour R et T
    Crée une liste qui mélange les 2 (concatene, trie, élimine les doublons)
    Fait un interpolate de R et de T suivant cette liste
    Simplifie en enlevant les points trop rapprochés des 2 cotés
    """
    #print("synchro one section", rX , rY ,tX , tY)
    cumulLengthR = np.array(cumulLength(rX , rY))
    cumulLengthT = np.array(cumulLength(tX , tY))
    totLengthR = cumulLengthR[-1]
    totLengthT = cumulLengthT[-1]
    if totLengthR == 0:  # this happens when the 2 points are identical
        normLengthR = cumulLengthR   
    else:
        normLengthR = cumulLengthR / totLengthR
    if totLengthT== 0:
        normLengthT = cumulLengthT
    else:
        normLengthT = cumulLengthT / totLengthT
    mergedLength = np.concatenate([normLengthR , normLengthT]) # concatenate
    mergedLength = np.unique(mergedLength)
    if mergedLength[0] > 0: #Add a point at zero except if it already exists (when a totalLength = 0)
        mergedLength = np.insert(mergedLength , 0 , 0)
    if totLengthR == 0:
        rXnew = np.asarray([rX[0]] * len(mergedLength))
        rYnew = np.asarray([rY[0]] * len(mergedLength))
    else:    
        mytck,myu=interpolate.splprep([rX,rY], k=1, s=0)
        rXnew,rYnew= interpolate.splev(mergedLength, mytck)
    if totLengthT == 0:
        tXnew = np.asarray([tX[0]] * len(mergedLength))
        tYnew = np.asarray([tY[0]] * len(mergedLength))
    else:    
        mytck,myu=interpolate.splprep([tX,tY], k=1, s=0)
        tXnew,tYnew= interpolate.splev(mergedLength, mytck)
    return rXnew , rYnew , tXnew , tYnew

def cumulLength( x, y):
    imax = len(x)
    i=0
    cL=[]
    cumLength = 0
    if imax > 1:
        while i < (imax-1):
            dx = x[i+1] - x[i]
            dy = y[i+1] - y[i]
            cumLength += math.sqrt(dx*dx + dy*dy) #calculate cumulative length
            cL.append(cumLength)
            i += 1
    return cL

def offset2Segment(x1, x2, x3, y1, y2, y3, o):
    #- calcule 2 fois l'offset de 1 segment
    #- calcule le point d'intersection
    #- retourne le point d'intersection
    
    X1 , X2 , Y1 ,Y2 = offset1Segment(x1 ,x2 ,y1 ,y2, o)
    X3 , X4 , Y3 ,Y4 = offset1Segment(x2 ,x3 ,y2 ,y3, o )
    interX , interY = intersec(X1, X2, Y1, Y2, X3, X4, Y3, Y4) 
    #print("intersec x=", x1, X2, x3, " y=", y1 , y2, y3 , " o=", o, "=>", interX, interY)
    return interX , interY

def offset1Segment(px1, px2 , py1, py2 ,o):
    #calcule les coordonnées des points avec un offset o
    X1 = px1
    X2 = px2
    Y1 = py1
    Y2 = py2
    DX = X2 - X1
    DY = Y2 - Y1
    L12 = math.sqrt(DX * DX + DY * DY)
    if L12 >0:
        r = o / L12
        dx = r * DY
        dy = r * DX
    else: #si le segment a une longueur nulle, 
        dx = 0
        dy = 0    
    #print("offset 1 segment" , X1, X2, Y1, Y2, o , X1-dx , X2-dx , Y1+dy , Y2+dy)
    return X1-dx , X2-dx , Y1+dy , Y2+dy 

def intersec(x1 , x2 , y1 ,y2 , x3, x4 , y3, y4):
    #première version avec numpy; ne va pas si un segment est 1 seul point
    #u = np.cross(np.array([x1 , y1, 1]), np.array([x2 , y2, 1]))
    #v = np.cross(np.array([x3 , y3, 1]), np.array([x4 , y4, 1]))
    #r = np.cross(u,v)
    ##print("intersec de ", x1 , x2 ,x3, x4 , y1 ,y2 ,y3, y4, "=" ,r)
    #if r[2] > 1e-10 or r[2] < -1e-10: #when different from 0, then the 2 segments are not // and there is an intersection 
    #    return  (r[0]/r[2]) , (r[1]/r[2]) 
    #return (x2+x3)/2 , (y2+y3)/2   #si // retourne le point milieu
    #print("dans intersec" , x1 , x2 ,x3, x4 , y1 ,y2 ,y3, y4)
    if x1 == x2 and y1 == y2: #si la première ligne est un point, retourne p3
        return x3, y3
    if x3 == x4 and y3 == y4: #si la première ligne est un point, retourne p2
        return x2, y2
    #here we have 2 segments of line
    d =  (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    if d > 1e-10 or d< -1e-10: # si les segments ne sont pas // ou confondus
        d12 = (x1*y2-y1*x2)
        d34 = (x3*y4-y3*x4)
        #return ( d12*(x4-x3)-d34*(x1-x2) ) / d , ( d12*(y3-y4)-d34*(y1-y2) ) / d   
        #return ( d12*(x3-x4)-d34*(x2-x1) ) / d , ( d34*(y1-y2) - d12*(y3-y4)) / d
        return ( d12*(x3-x4)-d34*(x1-x2) ) / d , ( d12*(y3-y4)-d34*(y1-y2) ) / d   
    else:
        return (x2+x3)/2 , (y2+y3)/2   #si // ou confondue, retourne le point milieu


def generateGcode(self, GX , DX , GY, DY, axisSpeed, feedRate, sparFlag):
    #gCodeStart ="G10 L20 P1 X0 Y0 Z0 A0 \n G90 G21 M3 \n G04 P5.0\n G01 X0 \n"
    #gCodeEnd = "G04 P5.0\n M5\n M2\n"
    heat = calculateHeating( self, self.vCut.value())
    formatAxis = "{:.3f} "
    #A="X{:.3f} Y{:.3f} Z{:.3f} A{:.3f}\n"
    L = self.gCodeLetters.text() + "XYZA"   # contains 4 letters
    G00 = "G00 "+L[0] + formatAxis + L[1] + formatAxis + L[2] + formatAxis + L[3] + formatAxis + "\n"
    G01 = "G01 "+L[0] + formatAxis + L[1] + formatAxis + L[2] + formatAxis + L[3] + formatAxis + "F{:d}\n" 
    xyza = L[0] + formatAxis + L[1] + formatAxis + L[2] + formatAxis + L[3] + formatAxis + "\n"
    st = self.gCodeStart1.text() + "\n" + self.gCodeStart2.text() + "\n" + self.gCodeStart3.text() + "\n" + self.gCodeStart4.text() + "\n"
    st = st + "G10 L20 P1"+ xyza.format(0,0,0,0) #set wcs to current position: G10 L20 P1 X0 Y0 Z0 A0
    st = st + "G54\n" # apply wcs1
    st = st + "S{:d}\n".format( int(heat)) # set the heating value based on speed
    if sparFlag: # for a spar we do not preheat and wait before the first move
        st = st + "G90 G21 G93 \n" # apply  Absolute and mm and inverted feedrate but not yet heating
        st2 = "M3\n" # apply heating
        st2 = st2 + "G04 P{:.1f}\n".format(self.tPreHeat.value()) # pause for the post delay 
        en = "" # do not pause after cutting
    else: 
        st = st + "G90 G21 G93 M3\n" # apply  Absolute and mm and inverted feedrate and heating
        st = st + "G04 P{:.1f}\n".format(self.tPreHeat.value()) # pause for the preheat delay
        st2 = ""
        en = "G04 P{:.1f}\n".format(self.tPostHeat.value()) # pause for the post delay
    en = en + "G94\nM5\nM2\n" # go back to normal feedrate , stop heating and stop motor
    en = en + self.gCodeEnd1.text() + "\n" + self.gCodeEnd2.text() + "\n" + self.gCodeEnd3.text() + "\n" + self.gCodeEnd4.text() + "\n"           
    li=[]
    imax = len(GX)
    if imax > 1:
        i = 1
        li.append(st) #append start
        li.append(G00.format(0.0, GY[0] , 0.0 , DY[0]), ) #move up
        li.append(G00.format(GX[0], GY[0] , DX[0] , DY[0]), ) #move up to entry of bloc
        li.append(st2) #append start part 2 for spar cut
        while i < imax:
            li.append(G01.format(GX[i], GY[i] , DX[i] , DY[i] , int(feedRate[i-1]  ) ) ) # we use inverted feedRate
            i += 1
        if  not sparFlag: #for a wing cut, go back to zero; for spar cut, stay at last position
            li.append(G00.format(0, GY[-1] , 0 , DY[-1]))
            li.append(G00.format(0.0, 0.0 , 0.0 , 0.0))
        li.append(en) #append End
    #print("".join(li)) #print the Gcode
    return "".join(li)  # return a string containing the /n

def calculateHeating(self, speed):
        x1 = self.mSpeedLow.value()
        x2 = self.mSpeedHigh.value()
        y1 = self.mHeatSpLow.value()
        y2 = self.mHeatSpHigh.value()
        heat = 0
        
        if (x2-x1) != 0:
            heat = y1 + (y2-y1)/(x2-x1)*(speed - x1) 
        #print(x1, x2, y1 ,y2 , heat)
        if heat < 1:
            heat =1
        if heat > self.tHeatingMax.value():
           heat = self.tHeatingMax.value()     
        return heat
# to do: radiance should be reduced if heating exceed max!!!!!!!!!!


def calculateSparSlot(self):
    xR=[]  #prepare a set of coordonate
    yR=[]
    sR=[]
    xT=[]
    yT=[]
    sT=[]
    if self.cbSparWidthTipType.currentIndex() == 0: # same as root
        self.sparWidthTip.setValue(self.sparWidthRoot.value() )
        self.sparWidthTip.setEnabled(False)
    elif self.cbSparWidthTipType.currentIndex() == 1: # proportional
        self.sparWidthTip.setValue(self.sparWidthRoot.value() * self.cTip.value() / self.cRoot.value() )
        self.sparWidthTip.setEnabled(False)
    else: # custom
        self.sparWidthTip.setEnabled(True)
    if self.cbSparDepthTipType.currentIndex() == 0: # same as root
        self.sparDepthTip.setValue(self.sparDepthRoot.value() )
        self.sparDepthTip.setEnabled(False)
    elif self.cbSparDepthTipType.currentIndex() == 1: # proportional
        self.sparDepthTip.setValue(self.sparDepthRoot.value() * self.cTip.value() / self.cRoot.value() )
        self.sparDepthTip.setEnabled(False)
    else: # custom
        self.sparDepthTip.setEnabled(True)
    retract = self.sparRetract.value()
    wR= self.sparWidthRoot.value()/2
    dR= self.sparDepthRoot.value()
    wT= self.sparWidthTip.value()/2
    dT= self.sparDepthTip.value()
    if self.cbSparType.currentIndex() == 0: #rectangular
        if self.cbSparDirection.currentIndex() == 0: #vertical
            xR = [0, -wR, -wR, wR , wR , 0]
            yR = [retract, retract, -dR , -dR , retract , retract ]
            sR = [ 4,4,4,4,4,4]
            xT = [0, -wT, -wT, wT , wT , 0]
            yT = [retract, retract, -dT , -dT , retract , retract ]
            sT = [ 4,4,4,4,4,4]
        else: #horizontal
            yR = [0, wR, wR, -wR , -wR , 0]
            xR = [retract, retract, -dR , -dR , retract , retract ]
            sR = [ 4,4,4,4,4,4]
            yT = [0, wT, wT, -wT , -wT , 0]
            xT = [retract, retract, -dT , -dT , retract , retract ]
            sT = [ 4,4,4,4,4,4]
    elif self.cbSparType.currentIndex() == 2: #Triangular
        if self.cbSparDirection.currentIndex() == 0: #vertical
            wR = wR / dR * (dR+retract)
            xR = [0, -wR, 0 , wR , 0]
            yR = [retract, retract, -dR , retract , retract ]
            sR = [ 4,4,4,4,4]
            wT = wT/ dT * (dT+retract)
            xT = [0, -wT, 0 , wT , 0]
            yT = [retract, retract, -dT , retract , retract ]
            sT = [ 4,4,4,4,4]
        else: #horizontal
            wR = wR / dR * (dR+retract)
            yR = [0, wR, 0 , -wR , 0]
            xR = [retract, retract, -dR , retract , retract ]
            sR = [ 4,4,4,4,4]
            wT = wT / dT * (dT+retract)
            yT = [0, wT, 0 , -wT , 0]
            xT = [retract, retract, -dT , retract , retract ]
            sT = [ 4,4,4,4,4]
    else: #Circular
        if self.cbSparDirection.currentIndex() == 0: #vertical
            xR = [0 , 0]
            yR = [retract, - dR + wR]
            sR = [10,4]
            xT = [0 , 0]
            yT = [retract, - dT + wT]
            sT = [10,4]
            for i in range(105, 360+105, 15):
                xR.append( math.cos(i*math.pi/180)* wR)
                yR.append( (math.sin(i*math.pi/180)* wR) - dR )
                sR.append(4)
                xT.append( math.cos(i*math.pi/180)* wT)
                yT.append( (math.sin(i*math.pi/180)* wT) - dT )
                sT.append(4)
        else: #horizontal
            yR = [0 , 0]
            xR = [retract, - dR + wR]
            sR = [10,4]
            yT = [0 , 0]
            xT = [retract, - dT + wT]
            sT = [10,4]
            for i in range(360 +90, 90-15, -15):
                yR.append( math.cos(i*math.pi/180)* wR)
                xR.append( (math.sin(i*math.pi/180)* wR) - dR )
                sR.append(4)
                yT.append( math.cos(i*math.pi/180)* wT)
                xT.append( (math.sin(i*math.pi/180)* wT) - dT )
                sT.append(4)
    #save in self in order to use them in draw function            
    self.sparXR = xR
    self.sparYR = yR
    self.sparSR = sR
    self.sparXT = xT
    self.sparYT = yT
    self.sparST = sT
    #print("spar to offset=",  xR, yR, sR , xT, yT, sT)        
    syncRX , syncRY , syncTX, syncTY = sparOffset(self, xR, yR, sR , xT, yT, sT)
    #print("spar offset result=", syncRX , syncRY , syncTX, syncTY)
    #Remove points if they are to close from each other (on both sides)
    oSimRX , oSimRY, oSimTX , oSimTY = simplifyProfiles(
        syncRX , syncRY , syncTX, syncTY )
    #print("Sim", oSimRX , oSimRY)    

    #do not add block offsets (horizontal and vertical) to take care of block position on the table
    self.sparWireRX = np.array(oSimRX)
    self.sparWireTX = np.array(oSimTX)
    self.sparWireRY = np.array(oSimRY)
    self.sparWireTY = np.array(oSimTY)
    #Calculate projections on cnc axis, messages, speed and feedRate (inverted)
    if self.rbRightWing.isChecked(): # 'Right': #for right wing, the root is on the left side
        GX , DX , GY, DY, warningMsg , speed , feedRate = projectionAll( self, 
            self.sparWireRX , self.sparWireTX , self.sparWireRY, self.sparWireTY, 
            self.blocToTableLeft.value() + self.tableYG.value() , 
            self.blocLX.value() ,
            self.tableYY.value() -self.blocToTableLeft.value() - self.tableYG.value() - self.blocLX.value() )
    else: #Left wing = root is on rigth side
        GX , DX , GY, DY, warningMsg, speed, feedRate = projectionAll( self, 
            self.sparWireTX, self.sparWireRX , self.sparWireTY , self.sparWireRY,  
            self.blocToTableLeft.value() + self.tableYG.value() , 
            self.blocLX.value() ,
            self.tableYY.value() -self.blocToTableLeft.value() - self.tableYG.value() - self.blocLX.value() )
    ##### self.cutMsg.setText(self.warningMsg) 
    self.sparGcode = generateGcode(self , GX , DX , GY, DY, speed, feedRate, True) # True says it is a spar cut

def sparOffset(self, eRootX, eRootY, eRootS , eTipX, eTipY, eTipS):
    
    if len(eRootX) > 0:
        #print("start sparOffset")
        #build 2 listes with length of segments 
        rootL = lengthSegment(eRootX , eRootY)
        tipL = lengthSegment(eTipX , eTipY)

        #build list of index of pt of synchro and length of sections between synchro
        eRootI , eRootL = lengthSection( eRootS , rootL)
        eTipI , eTipL = lengthSection( eTipS , tipL)
        #print("Root: Synchro code & Index, length segments & sections", eRootS ,  eRootI, rootL  , eRootL)        
        #print("Tip: Synchro code & Index, length segments & sections", eTipS , eTipI , tipL ,   eTipL)        
        #compare les longueurs pour trouver le coté le plus long
        compLength = compareLength( eRootL, eTipL)
        #print("compare length", compLength)
        #Calcule la radiance de chaque côté ; met 0 si 
        rRoot , rTip = calculate2Radiance( self, compLength, self.vCut.value())
        #print("radiance root", rRoot )
        #print("radiance tip",  rTip)
        #create eRootR and eTipR with the radiance to fit the same nbr of item as exxxS
        eRootR =  createRadiance(eRootS , rRoot)
        #print('full radiance root', eRootR)
        eTipR =  createRadiance(eTipS , rTip)
        #print('full radiance tip', eTipR)
        # calculate offset on each side; create one new point at each synchronisation to take care of different radiance offsets
        offsetRootX , offsetRootY , offsetRootS = calculateOffset(eRootX, eRootY, eRootR ,eRootS)
        #print("offset root", list(zip( offsetRootX , offsetRootY , offsetRootS)))
        offsetTipX , offsetTipY , offsetTipS = calculateOffset(eTipX, eTipY, eTipR, eTipS)
        #print("offset tip", list(zip( offsetTipX , offsetTipY , offsetTipS)))
        
        #print("len R T",len(offsetRootX) , len(offsetTipX) )
        # adjust points in order to have the same number of points on each section
        syncRX , syncRY , syncTX, syncTY = synchrAllSections( self, 
            offsetRootX , offsetRootY , offsetRootS , offsetTipX , offsetTipY , offsetTipS)
        return syncRX , syncRY , syncTX, syncTY

