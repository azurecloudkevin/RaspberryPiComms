# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103,R0205

import RPi.GPIO as GPIO


gpiofootprint = 32
class raspberrypi:
    def __init__(self, inputs, outputs):
        self.alarmstatus = False
        GPIO.setmode(GPIO.BCM)
        self.gpioin = list(inputs) 
        self.gpioout = list(outputs) 

        #Input GPIO ports set to 0
        for input in inputs:
            self.setinput(input)
            print("Setting input on channel ", input)

            # we update the iomask to set inputs to 0;

        #Output GPIO ports set to 1
        for output in outputs:
            self.setoutput(output)
            print("Setting output on channel ", output)

    # the input and output ports are right-justified / port zero is the 32nd bit
    # this aligns the bit array for the "notify" functions
    def setinput(self, port):
        GPIO.setup(port, GPIO.IN)
        
    
    def setoutput(self, port):
        GPIO.setup(port, GPIO.OUT)
        
    def setcallback(self, port, func):
        GPIO.add_event_detect(port, GPIO.RISING, callback=func, bouncetime=500)

    def getalarmstatus(self):
        return self.alarmstatus
    
    def setalarmstatus(self, newstatus):
        print("setting alarm status")
        self.alarmstatus = newstatus

    def buttonpress(self):
            print("button pressed\n")
    
    def alarmstate(self, newstate):
        print("setting alarm state")
        if(newstate == True):
            GPIO.output(self.gpioout[0], GPIO.HIGH)
        else:
            GPIO.output(self.gpioout[0], GPIO.LOW)
    
    def awaitedge(self, port):
        GPIO.wait_for_edge(port, GPIO.RISING)    