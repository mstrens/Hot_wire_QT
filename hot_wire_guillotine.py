
class Guillotine:
    def __init__(self, app , queueCmd):
        self.app = app
        self.queueCmd = queueCmd
 
    def calculateMove(self , factor):
        axis = self.app.gCodeLetters.text()
        if self.app.rbGuillotineVertical.isChecked() : # "Vertical":
            move = axis[1] + str(factor * self.app.gVDist.value()) + axis[3] + str(factor * self.app.gVDist.value()) 
        elif  self.app.rbGuillotineHorizontal.isChecked() : # "Horizontal":
            move = axis[0] + str(factor * self.app.gHDist.value()) + axis[2] + str(factor * self.app.gHDist.value()) 
        else:
            move = axis[1] + str(factor * self.app.gVDist.value()) + axis[0] + str(factor * self.app.gHDist.value()) + (
                axis[3] + str(factor * self.app.gVDist.value()) + axis[2] + str(factor * self.app.gHDist.value()) )
        return move
    
    def goForward(self):
        command = ["G21" , "G91", "G94"]  # mm incremental normal feed rate
        if self.app.rbGuillotineForward.isChecked()  or self.app.rbGuillotineBoth.isChecked(): # "Forward" or "Both":
            command.append("M3")
            command.append("S" + str( int(self.app.gHeating.value()) ) )
            command.append( "G04P" + str(self.app.tPreHeat.value() ) ) 
            command.append("F" +str(60 * self.app.gCuttingSpeed.value() ))
            command.append( "G01")
        else:
            command.append( "G00")     
        command.append( self.calculateMove(1))
        if self.app.rbGuillotineForward.isChecked()  or self.app.rbGuillotineBoth.isChecked(): # "Forward" or "Both":
            command.append( "G04P" + str(self.app.tPostHeat.value() ) ) 
            command.append("M5")
        print("\n".join(command))
        self.app.tGrbl.stream("\n".join(command))
        
    def goBackward(self):
        command = ["G21" , "G91", "G94"]  # mm incremental normal feed rate
        if self.app.rbGuillotineBackward.isChecked()  or self.app.rbGuillotineBoth.isChecked(): # "Backward" or "Both":
            command.append("M3")
            command.append("S" + str( int(self.app.gHeating.value()) ) )
            command.append( "G04P" + str(self.app.tPreHeat.value() ) ) 
            command.append("F"+str(60 * self.app.gCuttingSpeed.value() ))
            command.append( "G01")
        else:
            command.append( "G00")     
        command.append( self.calculateMove(-1))
        if self.app.rbGuillotineForward.isChecked()  or self.app.rbGuillotineBoth.isChecked(): # "Forward" or "Both":
            command.append( "G04P" + str(self.app.tPostHeat.value() ) ) 
            command.append("M5")
        print("\n".join(command))
        self.app.tGrbl.stream("\n".join(command))

    def startHeat(self):
        command = ["S" + str( int(self.app.gHeating.value()) )  , "M3"] 
        self.app.tGrbl.stream("\n".join(command))

    def stopHeat(self):
        command = ["S0" ,"M5"] 
        self.app.tGrbl.stream("\n".join(command))
        
    def moveUp(self):
        self.move("Up")

    def moveDown(self):
        self.move("Down")

    def moveForward(self):
        self.move("Forward")

    def moveBack(self):
        self.move("Back")

    def move(self, dir):
        command = ["G21" , "G91" , "G94"]  # mm incremental normal feed rate
        axis = self.app.gCodeLetters.text()
        axisIdx = 0
        dirPos = 1
        if dir == "Up":
            axisIdx = 1
        elif dir == "Down":
            axisIdx = 1
            dirPos = -1
        elif dir == "Back":
            dirPos = -1
        if self.app.rbMoveLeftAxis.isChecked():  #"Left"
            command.append("G00 "+ axis[axisIdx]+ str(dirPos * self.app.gMoveDist.get() ) )
        elif self.app.rbMoveRightAxis.isChecked(): # "Right":
            command.append("G00 "+ axis[axisIdx+2]+ str(dirPos * self.app.gMoveDist.get() ) )
        else: # both axis
            command.append("G00 "+ axis[axisIdx]+ str(dirPos * self.app.gMoveDist.value() ) +
                axis[axisIdx+2]+ str(dirPos * self.app.gMoveDist.value() ) )
        print("\n".join(command))
        self.app.tGrbl.stream("\n".join(command))
        

    def connect(self):
        self.queueCmd.put("Connect") 
    
    
    def disconnect(self):
        self.queueCmd.put("Disconnect")
        
"""    
    def updateBtnState(self):
        grblStatus= self.app.grblStatus.text()
        if grblStatus == "Not connected" or grblStatus == "Connection lost":
            state = False
            oppositeState = True
        else:
            state = True
            oppositeState = False
        self.app.pbMoveGuillotineForward.setEnabled(state)
        self.app.pbMoveGuillotineForward.setEnabled(state)
        self.app.pbMoveCancel.setEnabled(state)
        self.app.pbConnect.setEnabled(oppositeState)
        self.app.pbDisconnect.setEnabled(state)
        self.app.pbReset.setEnabled(state)
        self.app.pbUnlock.setEnabled(state)
        self.app.pbHome.setEnabled(state)
        self.app.pbSetPosition.setEnabled(state)
        self.app.pbGoToPosition.setEnabled(state)
        self.app.pbStartHeating.setEnabled(state)
        self.app.pbStopHeating.setEnabled(state)
        self.app.pbMoveUp.setEnabled(state)
        self.app.pbMoveBack.setEnabled(state)
        self.app.pbMoveForward.setEnabled(state)
        self.app.pbMoveDown.setEnabled(state)

        self.app.pbCut.setEnabled(state)
        self.app.pbCutCancel.setEnabled(state)
        self.app.pbSaveGcode.setEnabled(state)
"""        
"""
def my_callback(eventstring, *data):
    args = []
    for d in data:
        args.append(str(d))
    print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))
    # Now, do something interesting with these callbacks

"""
"""
Add a connect button:
    Greate Gerbil instance
    Configure Com and baudrate
Add a disconnect button:
    Disconnect

Add a button reset GRBL
Add a button unlock GRBL
Display a value Disconnected or GRBL status

When Arming:
    generate the string for moving up
    set a heating flag on ON/OFF depending on GUI
    Check that connected and GRBL status
    Send GRBL command : mm, relatif
    If heating: 
        Calculate heating (for the speed)
        Send heating and pause
        Send G01 command with feedrate
        pause
    else
        send G00 command        
When Cutting
    idem with negative value
    set heating flag on OFF

"""