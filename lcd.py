#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep

class LCD:

    def __init__(self, pin_rs=7, pin_e=8, pins_db=[25, 24, 23, 18]):
        
        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_db = pins_db

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_e, GPIO.OUT)
        GPIO.setup(self.pin_rs, GPIO.OUT)
        for pin in self.pins_db:
            GPIO.setup(pin, GPIO.OUT)

        self.clear()

    def clear(self):
        """ Reset LCD """
        self.cmd(0x33) 
        self.cmd(0x32) 
        self.cmd(0x28) 
        self.cmd(0x0C) 
        self.cmd(0x06) 
        self.cmd(0x01)
        self.cmd(0x02)
        
    def cmd(self, bits, char_mode=False):
        sleep(0.001)
        bits=bin(bits)[2:].zfill(8)
        
        GPIO.output(self.pin_rs, char_mode)

        for pin in self.pins_db:
            GPIO.output(pin, False)

        for i in range(4):
            if bits[i] == "1":
                GPIO.output(self.pins_db[::-1][i], True)

        GPIO.output(self.pin_e, True)
        GPIO.output(self.pin_e, False)

        for pin in self.pins_db:
            GPIO.output(pin, False)

        for i in range(4,8):
            if bits[i] == "1":
                GPIO.output(self.pins_db[::-1][i-4], True)

        GPIO.output(self.pin_e, True)
        GPIO.output(self.pin_e, False)


    def display(self, text):
        self.clear()
        line_counter =0   
        for char in text:
            if char == '\n':
                if line_counter==0:
                    self.cmd(0xC0)
                elif line_counter==1:
                    self.cmd(0x90)
                elif line_counter==2:
                    self.cmd(0xD0)
                line_counter+=1
            else:
                self.cmd(ord(char),True)

if __name__ == '__main__':

    lcd = LCD()

    lcd.display(" People counter\n    made by\n Zajac&Wieczorek\n\n Initializing...")
    #lcd.cmd(0x08 | 0x02)