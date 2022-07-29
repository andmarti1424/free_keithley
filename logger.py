# settings
SIM = 1 # do not interact with equipment, just sim data
DEBUG = 0 # print debug data on terminal
DISPLAY = 1 # display on or off
WINDOW_TIME = 10000 # in ms
REFRESH_TIME = 0.05 # in seconds. Used only on simulation

# TODO:
#add check to avoid moving window. will make measuring slower over time. Clear button should make it quicker again.
#clear button
#add combo to setup measuring speed: NPLC
#add option to setup max value in y axis
#export data measured
#save plot?

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
from matplotlib.ticker import AutoMinorLocator
#, FormatStrFormatter

class mclass:
    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window
        self.continuePlotting = False
        self.plot_packed = False
        self.fig = Figure(figsize=(9,9))
        self.ax = self.fig.add_subplot(111)
        self.fig.canvas = FigureCanvasTkAgg(self.fig, master=window)
        np.random.seed(42)

        self.title = Label(window, text='Keithley 2015 - Vdc Logger', fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)

        #details
        self.value = Label(window, text='', fg="red", font=('Helvetica 16 bold'))
        self.value.place(x=150, y=200)
        self.readings = Label(window, text='', fg='#1C5AAC', font=('Helvetica 16 bold'))
        self.readings.place(x=150, y=240)
        self.max_value = Label(window, text='', fg='#1C5AAC', font=('Helvetica 16 bold'))
        self.max_value.place(x=150, y=280)
        self.min_value = Label(window, text='', fg='#1C5AAC', font=('Helvetica 16 bold'))
        self.min_value.place(x=150, y=320)
        self.avg_value = Label(window, text='', fg='#1C5AAC', font=('Helvetica 16 bold'))
        self.avg_value.place(x=150, y=360)
        self.std_value = Label(window, text='', fg='#1C5AAC', font=('Helvetica 16 bold'))
        self.std_value.place(x=150, y=400)

        #BUTTONS
        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18 bold')
        self.button_quit.place(x=40, y=680)
        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18 bold')
        self.button_start.place(x=165, y=680)
        self.button_clear = Button(window, text="CLEAR", command=self.clear_chart, font='Helvetica 18 bold', state='disabled')
        self.button_clear.place(x=310, y=680)
        #end of ui

        if not SIM:
            self.start_serial()

    def start_serial(self):
        try:
            self.ser.port='/dev/ttyUSB0'
            self.ser.baudrate=9600
            self.ser.timeout=0
            self.ser.parity=serial.PARITY_NONE
            self.ser.stopbits=serial.STOPBITS_ONE
            self.ser.bytesize=serial.EIGHTBITS
            self.ser.xonxoff=False
            self.ser.open()
            self.send_cmd('*RST')
            self.send_cmd(':INITiate:CONTinuous OFF;:ABORt')
            self.send_cmd('*OPC?')
            resp = self.send_cmd('*IDN?')
            if DEBUG:
                print('version: {}'.format(repr(resp)))

            self.send_cmd(':SENS:FUNC \'VOLT:DC\'')
            self.send_cmd(':SENS:VOLT:DC:RANG 10')             #Use fixed range for fastest readings
            #self.send_cmd(':SENS:VOLT:AC:RANG:AUTO ON')
            if not DISPLAY: self.send_cmd('DISP:ENAB OFF')
            self.send_cmd(':SENS:VOLT:DC:NPLC 0.01')           #Use lowest NPLC setting for highest speed readings
            self.send_cmd(':SYST:AZER:STAT OFF')               #Turn off autozero to increase speed, but may cause drift over time
            self.send_cmd(':SENS:VOLT:DC:AVER:STAT OFF')       #Turn off averaging filter for speed
            self.send_cmd(':TRIG:COUN 1')
        except:
            if (not self.ser.isOpen()):
                print("ERROR opening serial")
                return -1

    def write(self, s, term = '\r'):
        if DEBUG:
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
                if DEBUG:
                    print("RX << ", repr(s))
                return s.strip()
            else:
                buf.append(c)

    def send_cmd(self, cmd):
        self.write(cmd)

        if '?' in cmd:
            response = self.read()

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
        res = float(self.send_cmd(':READ?'))
        if DEBUG:
            print(res)
        return res

    def clear_chart(self):
        self.clear_chart = 1

    def change_state(self):
        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
            self.button_clear.config(state = 'disabled')
            #self.value.config(text="")
            #self.max_value.config(text="")
            #self.min_value.config(text="")
            #self.avg_value.config(text="")
            #self.std_value.config(text="")
            #self.readings.config(text="")
        else:
            self.continuePlotting = True
            self.button_start['text'] = "STOP "
            self.button_clear.config(state = 'normal')
            self.plot()

    def quit(self):
        if (self.ser.isOpen()):
            self.ser.close()
        self.continuePlotting = False
        Tk().quit()

    def plot(self):
        plot_start_time = round(time.time() * 1000)

        df = pd.DataFrame({'ms': [], 'value': []})

        self.ax.clear() # clear previous plot !!!!
        self.ax.tick_params(labeltop=False, labelright=True)

        #format y axis
        #ax.yaxis.set_minor_locator(AutoMinorLocator())
        #ax.yaxis.set_minor_formatter(FormatStrFormatter("%.3f"))

        self.ax.plot(df.ms, df.value)
        if not self.plot_packed:
            self.fig.canvas.get_tk_widget().pack(side=TOP, expand=0)
        self.plot_packed = 1
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        while(self.continuePlotting):
            if SIM:
            ## data sim
                value = np.random.random()
                if (round(time.time() * 1000) - plot_start_time > 15000):
                    value *= -10
                if (round(time.time() * 1000) - plot_start_time > 10000):
                    value *= 10
            ##end of data sim
            else:
                value = self.measure()

            if self.clear_chart:
                self.ax.clear() # clear previous plot !!!!
                df = pd.DataFrame({'ms': [], 'value': []})
                self.clear_chart = 0

            mytime = round(time.time() * 1000) - plot_start_time
            self.value.config(text=format(value, '.6f') + " Vrms")
            if DEBUG: print("value measured: " + str(value))

            df_graph = df
            dfn = pd.DataFrame({'ms': [mytime], 'value': [value]})

            # move window
            if (mytime > WINDOW_TIME): df_graph = df_graph.iloc[1:]

            df = pd.concat([df, dfn])
            df_graph = pd.concat([df_graph, dfn])


            self.readings.config(text="readings: %d" % df.size)
            self.max_value.config(text="max: %s Vrms" % format(df['value'].max(), '.6f'))
            self.min_value.config(text="min: %s Vrms" % format(df['value'].min(), '.6f'))
            self.avg_value.config(text="avg: %s Vrms" % format(df['value'].mean(), '.6f'))
            self.std_value.config(text="std: %s Vrms" % format(df['value'].std(), '.6f'))

            self.ax.set_xlabel('time, ms', fontsize=20, loc='right')
            self.ax.set_ylabel('level, Vrms', fontsize=20, loc='center')
            self.ax.set_facecolor('xkcd:black')
            ax = self.fig.get_axes()[0]
            #ax.grid(visible=True, which='major', axis='both', color='slategray', linestyle='--', linewidth=0.5)
            ax.grid(visible=True, which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
            ax.tick_params(labeltop=False, labelright=True)
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            #self.ax.clear()
            self.ax.plot(df.ms, df.value, color="xkcd:orange")
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            if SIM: time.sleep(REFRESH_TIME)

window = Tk()
start = mclass(window)
window.mainloop()
