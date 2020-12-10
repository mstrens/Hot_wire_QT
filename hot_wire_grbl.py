from gerbil import Gerbil
import time
import re
import queue



class Grbl:
    def __init__(self,window, queue):
        #self.nb = nb
        self.app = window
        self.queue = queue
        self.grbl = Gerbil(self.my_callback)    
        #Next, we tell Gerbil to use its default log handler, which, instead of printing to stdout directly, will also call above my_callback function with eventstring on_log. You could use this, for example, to output the logging strings in a GUI window:
        self.grbl.setup_logging()
        self.alreadyConnectedState = False

    def connectToGrbl(self):
        #We now can connect to the grbl firmware, the actual CNC machine:
        self.grbl.cnect(self.app.tComPort.currentText() , self.app.tBaudrate.currentText())
        #We will poll every half tsecond for the state of the CNC machine (working position, etc.):
        time.sleep(1)
        self.grbl.poll_start()

    
    def disconnectToGrbl(self):
        self.grbl.disconnect()
        self.app.grblStatus.setText("Not connected")
        self.updateBtnState()
        #self.app.isConnected.setChecked(False)
        
    def resetGrbl(self):
        print("we will do a reset of grbl")
        self.grbl.abort()

    def unlockGrbl(self):
        self.grbl.killalarm()

    def homeGrbl(self):
        self.grbl.homing()

    def setPosGrbl(self):
        self.grbl.send_immediately("G28.1")

    def goToPosGrbl(self):
        self.grbl.send_immediately("G28")

    def stream(self, lines):
        self.grbl.stream(lines)
    
    def my_callback(self , eventstring, *data):
        args = []
        for d in data:
            args.append(str(d))
        print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))
        # Now, do something interesting with these callbacks
        if eventstring == "on_stateupdate":
            #print("args=", args)
            #print("status=", args[0])
            self.app.grblStatus.setText(args[0])
            self.updateBtnState()
            mpos = args[1].replace("(" ,"").replace(")","").split(",")
            self.app.grblXG.setText(mpos[0])
            self.app.grblYG.setText(mpos[1])
            self.app.grblXD.setText(mpos[2])
            self.app.grblYD.setText(mpos[3])
            self.app.grblF.setText(mpos[4])
            self.app.grblS.setText(mpos[5])
        elif eventstring == "on_msg":
            self.queue.put("\n".join(args))
            
        elif eventstring == "on_log":
            if "Error" in ", ".join(args):
                #print("grbl will disconnect because it get an error")
                self.app.grblStatus.setText("Connection lost")
                self.grbl.disconnect()
                #self.app.isConnected.setChecked(False)
                self.updateBtnState()     
        elif eventstring == "on_iface_error":
            #print("on_iface_error")
            self.queue.put("interface error\n")
            self.disconnectToGrbl()
            #self.app.isConnected.setChecked(False)
            self.updateBtnState()


    def updateBtnState(self):
        grblStatus= self.app.grblStatus.text()
        if grblStatus == "Not connected" or grblStatus == "Connection lost":
            state = False
            oppositeState = True
            self.app.pbMoveGuillotineForward.setEnabled(False)
            self.app.pbMoveGuillotineBack.setEnabled(False)
            self.app.pbMoveCancel.setEnabled(False)
            self.alreadyConnectedState = False
        elif grblStatus == "Run" or grblStatus == "run":
            self.app.pbCut.setEnabled(False)
            self.app.pbCutCancel.setEnabled(True)
            state = True
            oppositeState = False
        
        elif grblStatus == "Idle" or grblStatus == "idle":
            self.app.pbCut.setEnabled(True)
            self.app.pbCutCancel.setEnabled(False)
            state = True
            oppositeState = False         
        else:
            state = True
            oppositeState = False   
            if self.alreadyConnectedState == False:
                print("Cut enabled")
                self.app.pbMoveGuillotineForward.setEnabled(True)
                self.app.pbCut.setEnabled(state)
                self.app.pbCutCancel.setEnabled(oppositeState)
                self.alreadyConnectedState = True
            else:
                self.app.pbCut.setEnabled(False)
                self.app.pbCutCancel.setEnabled(True)
                    
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

        #self.app.pbSaveGcode.setEnabled(state)

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
        self.app.pbMoveGuillotineForward.setEnabled(False)
        self.app.pbMoveGuillotineBack.setEnabled(True)
        self.app.pbMoveCancel.setEnabled(True)
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
        self.app.pbMoveGuillotineForward.setEnabled(True)
        self.app.pbMoveGuillotineBack.setEnabled(False)
        self.app.pbMoveCancel.setEnabled(False)
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

    def startHeating(self):
        command = ["S" + str( int(self.app.gHeating.value()) )  , "M3"] 
        self.app.tGrbl.stream("\n".join(command))

    def stopHeating(self):
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
