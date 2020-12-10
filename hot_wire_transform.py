import math

import numpy as np

from shapely.geometry import LineString
from shapely import affinity
from scipy import interpolate

def applyTransform(w):
    #at the end, tRoot and tTip are generated, and draw but do not take care of bloc and margin
    w.tRootX = []
    w.tRootY = []
    w.tRootS = []
    w.tTipX = []
    w.tTipY = []
    w.tTipS = []
    
    if len(w.oRootX) > 0 and len(w.oTipX) > 0 and (w.oRootSynchroCount == w.oTipSynchroCount) :
        #convert List to numpy array
        w.tRootX = np.array(w.oRootX)
        w.tRootY = np.array(w.oRootY)
        w.tRootS = w.oRootS.copy()
        w.tTipX = np.array(w.oTipX)
        w.tTipY = np.array(w.oTipY)
        w.tTipS = w.oTipS.copy()
        #apply thickness
        if w.thicknessRoot.value() != 100.0:
            w.tRootY = w.tRootY * w.thicknessRoot.value() / 100
        if w.thicknessTip.value() != 100.0:
            w.tTipY = w.tTipY * w.thicknessTip.value() / 100
        #apply incidence
        if w.incidenceRoot.value() != 0:
            line = LineString( tuple(zip(w.tRootX, w.tRootY)) ) #create a linestring with a list of turple
            rotated = affinity.rotate(line, -1 * w.incidenceRoot.value() ) #rotate the linestring
            rotatedXY = rotated.xy #extract the coordinate
            w.tRootX = np.array(rotatedXY[0])
            w.tRootY = np.array(rotatedXY[1])
        if w.incidenceTip.value() != 0:
            line = LineString( tuple(zip(w.tTipX, w.tTipY)) ) #create a linestring with a list of turple
            rotated = affinity.rotate(line, -1 * w.incidenceTip.value() ) #rotate the linestring
            rotatedXY = rotated.xy #extract the coordinate
            w.tTipX = np.array(rotatedXY[0])
            w.tTipY = np.array(rotatedXY[1])
        # appy vertical invert
        if w.vInvertRoot.isChecked():
            w.tRootY = w.tRootY * -1.0
            w.tRootX = np.flip(w.tRootX)
            w.tRootY = np.flip(w.tRootY)
            w.tRootS = np.flip(w.tRootS)
        if w.vInvertTip.isChecked():
            w.tTipY = w.tTipY * -1.0
            w.tTipX = np.flip(w.tTipX)
            w.tTipY = np.flip(w.tTipY)
            w.tTipS = np.flip(w.tTipS)
        
        # Normalise the 2 profiles based on chords
        # Here we don't yet take care of position of bloc and of margin
        w.tRootX, w.tRootY = normaliseArrayProfil( w.tRootX , w.tRootY , w.cRoot.value() )
        w.tTipX, w.tTipY = normaliseArrayProfil( w.tTipX , w.tTipY , w.cTip.value() )   
        #print("root after normalise", self.app.tRootX, self.app.tRootY)        
        
        # apply smoothing (if asked) based on number of points and spreading repartition
        if w.smooth.isChecked():
            w.tRootX, w.tRootY , w.tRootS = changeNbrPoints(w.tRootX, w.tRootY, w.tRootS , w.nbrPoints.value(), w.repartition.value() )
            w.tTipX, w.tTipY , w.tTipS = changeNbrPoints(w.tTipX, w.tTipY , w.tTipS , w.nbrPoints.value(), w.repartition.value() )
        #w.lineTestPlot.setData(w.tRootX, w.tRootY)
        # take care of covering
        if w.covering.value() != 0:
            #save a copy of txxxx before covering because we use it after synchro when Extend Chord is ON
            w.nRootX = np.copy(w.tRootX)
            w.nRootY = np.copy(w.tRootY)
            w.nTipX = np.copy(w.tTipX)
            w.nTipY = np.copy(w.tTipY)
            w.tRootX , w.tRootY = applyOffset(w.nRootX, w.nRootY , w.covering.value())
            w.tTipX , w.tTipY = applyOffset(w.nTipX, w.nTipY , w.covering.value())
        """
        # insert synchro points if they do not yet exist
        if len(w.tRootS) == 0 or len(w.tTipS) == 0:
            w.tRootS = addSynchroPoints(w.tRootX, w.tRootY)
            w.tTipS = addSynchroPoints(w.tTipX, w.tTipY)
        """
        #self.printProfile("before simplify", self.app.tRootX , self.app.tRootY , self.app.tRootS)
        # reduce the number of points but keep the synchronisation; the parameter is the max error (in mm)
        if w.reducePoints.isChecked():
            #self.app.tRootX , self.app.tRootY , self.app.tTipX , self.app.tTipY = self.simplify(0.01) 
            w.tRootX , w.tRootY , w.tRootS = simplifyOneProfile(w.tRootX , w.tRootY , w.tRootS , 0.01 )
            w.tTipX , w.tTipY , w.tTipS = simplifyOneProfile(w.tTipX , w.tTipY , w.tTipS , 0.01 )
            #self.printProfile("after simplify", self.app.tRootX , self.app.tRootY , self.app.tRootS)        
        
        # insert mid first and last points of profile as defined before covering when extend to original coord is requested 
        if (w.keepChord.isChecked()) and (w.covering.value() != 0 ):
            #insert first and last points before applying offset (reuse nxxxx saved before covering)
            w.tRootX = np.insert(w.tRootX, 0, w.nRootX[0])
            w.tRootX = np.append(w.tRootX, w.nRootX[-1])
            w.tRootY = np.insert(w.tRootY, 0, w.nRootY[0])
            w.tRootY = np.append(w.tRootY, w.nRootY[-1])
            w.tTipX = np.insert(w.tTipX, 0, w.nTipX[0])
            w.tTipX = np.append(w.tTipX, w.nTipX[-1])
            w.tTipY = np.insert(w.tTipY, 0, w.nTipY[0])
            w.tTipY = np.append(w.tTipY, w.nTipY[-1])
            w.tRootS.insert(0,10) #insert a first point as synchro  and No radiance
            w.tRootS[-1] = 10 # convert last point as synchro  and No radiance
            w.tRootS.append( 4) #add a last point as synchro
            w.tTipS.insert(0,10) #insert a first point as synchro  and No radiance
            w.tTipS[-1] = 10 # convert last point as synchro  and No radiance
            w.tTipS.append( 4) #add a last point as synchro

    
def normaliseArrayProfil ( aX , aY , chord):
    #normalise the profil with chord
    if len(aX) > 0:
        minX = np.min(aX)
        maxX = np.max(aX)
        ratio= chord / ( maxX - minX )  
        aXn = aX * ratio
        aXn = aXn - aXn[0]
        aXn = -1.0 * aXn # multiply by -1 to reverse the order
        aYn = aY * ratio
        aYn = aYn - aYn[0]
        return aXn , aYn

def changeNbrPoints(x , y, s, nbrPoints , repartition):
    xnew = []
    ynew = []
    snew = []
    #print("x", x)
    #print("y", y)
    #print("s", s)
    indexes = []
    if len(x) > 0:
        xnew = [x[0]]
        ynew = [y[0]]
        snew = [s[0]]
        # find index of synchro points
        for i , v in enumerate(s):
            if v == 4:
                indexes.append(i)
        #print("indexes= ", indexes)
        for i in range(len(indexes)-1):
            xInterpolated , yInterpolated, sInterpolated = interpolateAProfile( x[ indexes[i]: indexes[i+1] + 1 ] ,
             y[ indexes[i]: indexes[i+1] + 1 ] , s[ indexes[i]: indexes[i+1] + 1 ] , nbrPoints , repartition)        
            xnew = np.concatenate([xnew , xInterpolated[1:]])
            ynew = np.concatenate([ynew , yInterpolated[1:]])
            snew = np.concatenate([snew , sInterpolated[1:]])
        
    return xnew , ynew , snew            
    """
        # find the point with max X
        maxX = np.max(x)
        # find the index of this point
        idxMax = np.where(x == maxX) #return an array with indexes
        if len(idxMax) > 0 and len(idxMax[0]) > 0:
            r = idxMax[0][0]
        else:
            r=0 # not sure if it can happens    
        # split extrados / intrados in 2 lines
        #print("r=",r)
        #print("x,y", x, y)
        eX= x[0 : r+1]
        eY= y[0 : r+1]
        iX= x[r:]
        iY= y[r:]
        #print("extrados avant=", eX, eY)
        
        mytck,myu=interpolate.splprep([eX,eY], k=1, s=0)
        arrayRepartition = np.linspace(0,1,int(nbrPoints/2) ) ** repartition
        arrayRepartitionExt = (np.flip(arrayRepartition) * -1 ) + 1
        eXnew,eYnew= interpolate.splev(arrayRepartitionExt, mytck)
        #print("arrayRepartition ext",arrayRepartitionExt)
        #print("extrados après", eXnew, eYnew)    
        
        #print("intrados avant=", iX, iY)
        mytck,myu=interpolate.splprep([iX,iY], k=1, s=0)
        arrayRepartition = np.linspace(0,1,int(nbrPoints/2) ) ** repartition
        #print("arrayRepartition int",arrayRepartition)
        #arrayRepartition = np.flip(arrayRepartition)
        iXnew,iYnew= interpolate.splev(arrayRepartition, mytck)
        #print("intrados après",self.printDistance(iXnew, iYnew))    
        
        xnew = np.concatenate([eXnew, iXnew[1:]])
        ynew = np.concatenate([eYnew, iYnew[1:]])
        #print("xy new=" , xnew , ynew)
    return xnew, ynew
    """
def interpolateAProfile(x , y , s , nbrPoints , repartition):
    #print("x to interpolate" ,x)
    mytck,myu=interpolate.splprep([x,y], k=1, s=0)
    arrayRepartition = np.linspace(0,1,int(nbrPoints) ) ** repartition
    if x[-1] > x[0]:
        arrayRepartition = (np.flip(arrayRepartition) * -1 ) + 1
    xNew,yNew= interpolate.splev(arrayRepartition, mytck)
    sNew = np.zeros(len(xNew)) #fill synchro with 0
    sNew[-1] = 4 #mark last point as synchro point"
    #print("x interpolated", xNew)
    return xNew , yNew , sNew    

def applyOffset( xN, yN, d):
    line = LineString(  tuple(zip(xN , yN)) ) #create a linestring with a list of turple
    offLine= line.parallel_offset(d , side='right' , resolution=16, join_style=2, mitre_limit=5)
    if "Multi" in str(type(offLine)) :
        offLineXY = offLine[0].xy #extract the coordinate
    else:
        offLineXY = offLine.xy #extract the coordinate
    # there is a bug in the Offset function. With side = right, sequence is revered and have to be reversed afterward    
    return np.array(list(reversed(offLineXY[0])))  , np.array(list(reversed(offLineXY[1])))


def simplifyOneProfile( x , y , s, errorMax):
    # remove points when a direct connection does not lead to to big error nor on Root nor on Tip
    # Keep always first and last points and synchro points
    # Return the new Root and Tip in numpy arry and new s in list
    #print("length", len(x), len(y), len(s))
    i = 0
    errorMax2 = errorMax * errorMax #power of 2 because distance between points are calculated in power of 2
    iMax = len(x)
    rX=[]
    rY=[]
    rS=[]
    if iMax > 0:
        #always keep the first point
        rX.append(x[0])
        rY.append(y[0])
        rS.append(s[0])
        while i < iMax:
            nextPoint = lookNextPoint(x , y , i, errorMax2)
            nextSynchro = lookNextSynchro(s , i) #search next Synchro point
            if nextPoint < nextSynchro:
                i = nextPoint
            else:
                i = nextSynchro
            if i < iMax: #add the point if we did not reach the end
                rX.append(x[i])
                rY.append(y[i])
                rS.append(s[i])            
        #add the last point in all cases
        #rX.append(x[iMax-1]) 
        #rY.append(y[iMax-1])
        #rS.append(s[iMax-1])
        return np.array(rX) , np.array(rY) , rS         

def lookNextPoint( x, y , idx , errorMax):
    #look from idx up to max, for the next point to keep in order to keep the error less than a value
    # return the last point where the error is lower
    # if it is possible to go up to the end of the polyline, return the index of the last point
    iMax = len(x)
    i = idx + 2
    while i < iMax:
        j = idx + 1
        while j < i:
            h = distPoint2(x[idx], x[j], x[i], y[idx], y[j], y[i])
            if h > errorMax:
                #print("idex max" , j , i)
                return i-1
            #print("idx, j , i ,h" , idx , j , i , h)
            j += 1    
        i += 1
    #print("fin de iterHauteur")
    return iMax

def lookNextSynchro( s , idx ):
    #look from idx + 1 up to max, for the next synchro point
    # if it is possible to go up to the end of the polyline, return the index of the last point
    iMax = len(s)
    i = idx + 1
    while i < iMax:
        if s[i] > 0:
            return i    
        i += 1
    return iMax

def distPoint2(x1, x2 ,x3 ,y1, y2, y3):
    # calculate distance between point 2 and line 1-3
    # returned value is the power of 2 of the distance (avoid a square root)
    a = (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1)
    b = (x3-x2)*(x3-x2) + (y3-y2)*(y3-y2)
    c = (x3-x1)*(x3-x1) + (y3-y1)*(y3-y1)
    return a - (a*a + b*b + c*c + 2*(a*c - a*b - b*c))/4/c
