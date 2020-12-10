"""
Gerbil - Copyright (c) 2015 Michael Franzl
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import serial
import time
import threading
import logging


class Interface:
    """Implements opening, closing, writing and threaded reading from the serial port. Read data are put into a Thread Queue.
    """
    
    def __init__(self, name, path, baud="115200"):
        """Straightforward initialization tasks.
        
        @param name
        An informal name of the instance. Useful if you are running
        several instances to control several serial ports at once.
        It is only used for logging output and UI messages.
        
        @param path
        The serial port device node living under /dev.
        e.g. /dev/ttyACM0 or /dev/ttyUSB0
        
        @param baud
        The baud rate. Default is 115200 for Grbl > v0.9i.
        """
        
        self.name = name
        self.path = path
        self.baud = baud
        self.queue = None
        self.logger = logging.getLogger("gerbil.interface")
        
        self._buf_receive = ""
        self._do_receive = False
        
        
    def start(self, queue):
        """
        Open the device node and start a Thread for reading.
        
        @param queue
        An instance of Python3's `Queue()` class.
        Used to send one line received on the UART
        """
        self.queue = queue
        self.logger.info("{}: connecting to {} with baudrate {}".format(self.name, self.path, self.baud) )
        try:
            self.serialport = serial.Serial(self.path, self.baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, writeTimeout=0)
            self.serialport.flushInput()
            self.serialport.flushOutput()
            self._do_receive = True
            self.serial_thread = threading.Thread(target=self._receiving)
            self.serial_thread.setDaemon(True) #added by mstrens in order to kill automatically the thread when program close
            self.serial_thread.start()
            return True
        except:
            self.logger.info("Error 1 Serial {} not open".format(self.path))  #added by mstrens
            return False

    def stop(self):
        """
        Close the device node and shut down the reading Thread.
        """
        #print("doreceive=",self._do_receive)
        if self._do_receive:
            self._do_receive = False
            #print("serial interface begin to stop")
            #self.logger.info("%s: stop()", self.name)
            #if self.serial_thread.is_alive():
            #print("serial thread receiving is alive; wait for join")
            self.serial_thread.join()
            #print("serial thread receiving join has been done")
        #self.logger.info("%s: JOINED thread", self.name)
        #self.logger.info("%s: Closing port", self.name)
        """
        self.serialport.flushInput()  
        self.serialport.flushOutput() 
        """
        try:                              #added by mstrens
            self.serialport.flushInput()  #added by mstrens
            self.serialport.flushOutput() #added by mstrens
        except:                           #added by mstrens
            pass                          #added by mstrens
        
        try:
            #print("try to close serial")
            self.serialport.close()
            #print("serial has been closed")
        except:
            pass
        #print("end of interface close()")

    def write(self, data):
        """
        Write `data` to the device node. If data is empty, no write is performed. The number of written characters is returned.
        """
        if len(data) > 0:
            try:
                num_written = self.serialport.write(bytes(data,"ascii"))
                #print("in write=" , data , num_written)
                return num_written
            except:
                self.logger.info("Error 2 Not possible to write to UART") #added by mstrens
                return 0
        #else:
        #    self.logger.debug("%s: nothing to write", self.name)
        return 0

    def _receiving(self):

        while self._do_receive == True:
            """data = self.serialport.read(1)
            waiting = self.serialport.inWaiting()
            data += self.serialport.read(waiting)
            self._handle_data(data)
            
            """
            try:
                data = self.serialport.read(1)
                waiting = self.serialport.inWaiting()
                data += self.serialport.read(waiting)
                self._handle_data(data)
            except:
                self._do_receive = False #allows the Thread to close
                self.logger.info("Error 3 Unable to read UART") #added by mstrens
                #self.logger.info("Unable to read com port; serialport is closed, thread is closed")
                #self.serialport.close()
                #print("serialport is closed")            
        
    def _handle_data(self, data):
        try:
            asci = data.decode("ascii")
        except UnicodeDecodeError:
            self.logger.info("{}: Received a non-ascii byte. Probably junk. Dropping it.".format( self.name) )
            asci = ""
        for i in range(0, len(asci)):
            char = asci[i]
            self._buf_receive += char
            # not all received lines are complete (end with \n)
            if char == "\n":
                self.queue.put(self._buf_receive.strip())
                #print(self._buf_receive)  # to test by mstrens
                self._buf_receive = ""
