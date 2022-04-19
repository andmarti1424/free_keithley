import matplotlib.dates
import matplotlib.pyplot as plt
from datetime import datetime

import time
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')
from tkinter import *
import serial

# settings
REFRESH_TIME = 0.10 # in seconds

class mclass:
    def start_serial(self):
        self.ser = serial.Serial()
        try:
            self.ser.port='COM2'
            self.ser.baudrate=9600
            self.ser.timeout=1
            self.ser.parity=serial.PARITY_ODD
            self.ser.stopbits=serial.STOPBITS_TWO
            self.ser.bytesize=serial.SEVENBITS
            self.ser.open()
        except:
            if (not self.ser.isOpen()):
                return -1

    def write(s, term = '\r'):
        print('TX >> ', s)
        self.ser.write(str.encode(s))
        if term:
            self.ser.write(b'\r')
        self.ser.flush()

    def read(self):
        buf = []

        while True:
            c = self.ser.read(1)
            if c == b'\r':
                s = b''.join(buf).decode('ascii')
                print("RX << ", repr(s))
                return s.strip()
            else:
                buf.append(c)

    def send_cmd(cmd):
        write(cmd)

        if '?' in cmd:
            response = read()

            if ',' in response:
                response = response.split(',')

            return response
        else:
            return None

    def measure(self):
        """
        *RST
        :INITiate:CONTinuous OFF;:ABORt
        :SENS:FUNC ‘VOLT:DC’
        :SENS:VOLT:DC:RANG 10               #Use fixed range for fastest readings
        #:SENS:VOLT:AC:RANG:AUTO ON
        #:SENS:VOLT:DC:NPLC 0.01             #Use lowest NPLC setting for fastest readings
        #:SENS:VOLT:DC:NPLC 1                #Use med NPLC setting for fastest readings
        :SENS:VOLT:DC:NPLC 10               #Use highest NPLC setting for slowest readings
        #:SENS:VOLT:DC:DIG 3
        :DISP:ENAB OFF                      #Turn off display to increase speed
        :SYST:AZER:STAT OFF                 #Turn off autozero to increase speed, but may cause drift over time
        :SENS:VOLT:DC:AVER:STAT OFF         #Turn off averaging filter for speed

        #:SENS:VOLT:AC:AVER:TCON MOV
        #:SENS:VOLT:AC:AVER:TCON REP
        #:SENS:VOLT:AC:AVER:COUN 20
        #:SENS:VOLT:AC:AVER:STAT ON

        :TRIG:COUN 1
        :READ?
        ###############
        #TRIGger:SOURce BUS
        #:INITiate
        #*TRG
        """
        self.send_cmd('*RST')
        self.send_cmd(':INITiate:CONTinuous OFF;:ABORt')
        self.send_cmd('*OPC?')
        resp = self.send_cmd('*IDN?')
        print('version: {}'.format(repr(resp)))

        self.send_cmd(':SENS:FUNC \'VOLT:DC\'')
        self.send_cmd(':SENS:VOLT:DC:RANG 10')             #Use fixed range for fastest readings
        self.send_cmd(':SENS:VOLT:AC:RANG:AUTO ON')
        self.send_cmd(':SENS:VOLT:DC:NPLC 10')             #Use highest NPLC setting for slowest readings
        self.send_cmd(':SYST:AZER:STAT OFF')               #Turn off autozero to increase speed, but may cause drift over time
        self.send_cmd(':SENS:VOLT:DC:AVER:STAT OFF')       #Turn off averaging filter for speed
        self.send_cmd(':TRIG:COUN 1')
        res = self.send_cmd(':READ?')
        print(res)
        return res

    def __init__(self,  window):
        self.window = window
        self.continuePlotting = False
        self.plot_packed = False
        self.fig = Figure(figsize=(9,9))
        self.ax = self.fig.add_subplot(111)
        self.fig.canvas = FigureCanvasTkAgg(self.fig, master=window)
        np.random.seed(42)

        self.title = Label(window, text='Keithley 2015 - Logger', fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)
        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18 bold')
        self.button_start.place(x=350, y=85)
        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18 bold')
        self.button_quit.place(x=210, y=85)

    def change_state(self):
        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
        else:
            self.continuePlotting = True
            self.button_start['text'] = "STOP"
            self.plot()

    def quit(self):
        self.continuePlotting = False
        Tk().quit()

    def plot(self):
        plot_start_time = round(time.time() * 1000)

        df = pd.DataFrame({'ms': [], 'value': []})

        self.ax.clear() # clear previous plot !!!!
        self.ax.tick_params(labeltop=False, labelright=True)
        self.ax.plot(df.ms, df.value)
        if not self.plot_packed:
            self.fig.canvas.get_tk_widget().pack(side=BOTTOM, expand=0)
        self.plot_packed = 1
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        while(self.continuePlotting):
            #value = self.measure()
            # data sim
            value = np.random.random()
            if (round(time.time() * 1000) - plot_start_time > 15000):
                value *= -10
            if (round(time.time() * 1000) - plot_start_time > 10000):
                value *= 10
            mytime = round(time.time() * 1000) - plot_start_time
            #end of data sim

            dfn = pd.DataFrame({'ms': [mytime], 'value': [value]})
            df = pd.concat([df, dfn])
            self.ax.set_xlabel('time, ms', fontsize=20, loc='right')
            self.ax.set_ylabel('level, Vrms', fontsize=20, loc='center')
            self.ax.set_facecolor('xkcd:black')
            ax = self.fig.get_axes()[0]
            ax.grid(visible=True, which='major', axis='both', color='slategray', linestyle='--', linewidth=0.5)
            ax.tick_params(labeltop=False, labelright=True)
            ax.plot(df.ms, df.value, color="xkcd:orange")
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            time.sleep(REFRESH_TIME)

window = Tk()
start = mclass(window)
window.mainloop()
