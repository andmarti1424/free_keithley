# TODO:
#add entry box to set WINDOW TIME
#add combo to set measuring speed: NPLC
#add option to setup max value in y axis
#save plot?

#SOURCE:
#https://download.tek.com/manual/2015-900-01(F-Aug2003)(User).pdf

# settings
SIM = 1 # do not interact with equipment, just sim data
DEBUG = 0 # print debug data on terminal
DISPLAY = 0 # display on or off
WINDOW_TIME = 3000 # in ms
REFRESH_TIME = 0.05 # in seconds. Used only on simulation

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
from tkinter import messagebox, LEFT, RIGHT
import serial
from matplotlib.ticker import AutoMinorLocator
#, FormatStrFormatter

class mclass:
    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window
        self.continuePlotting = False
        self.plot_packed = False
        self.fig = Figure(figsize=(13,9))
        self.ax = self.fig.add_subplot(111)
        np.random.seed(42)

        self.title = Label(window, text='Keithley 2015 - Vdc Logger', fg='#1C5AAC', font=('Courier New', 24, 'bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)

        #details
        self.value = Label(window, text='', fg="red", font=('Courier New', 16, 'bold'))
        self.value.place(x=150, y=200)
        self.readings = Label(window, text='', fg='#1C5AAC', font=('Courier New', 16, 'bold'))
        self.readings.place(x=150, y=240)
        self.max_value = Label(window, text='', fg='#1C5AAC', font=('Courier New', 16, 'bold'))
        self.max_value.place(x=150, y=280)
        self.min_value = Label(window, text='', fg='#1C5AAC', font=('Courier New', 16, 'bold'))
        self.min_value.place(x=150, y=320)
        self.avg_value = Label(window, text='', fg='#1C5AAC', font=('Courier New', 16, 'bold'))
        self.avg_value.place(x=150, y=360)
        self.std_value = Label(window, text='', fg='#1C5AAC', font=('Courier New', 16, 'bold'))
        self.std_value.place(x=150, y=400)

        #bottom right checks frame
        fm = Frame(window)

        #moving window checkbox
        self.lbl_moving = Label(fm, text="Moving window", font=('Courier New', 12), fg='#1C5AAC', wraplength=150, justify='right', background=self.window['bg'])
        self.chk_moving_var = IntVar()
        self.chk_moving = Checkbutton(fm, command='', variable=self.chk_moving_var, onvalue=1, offvalue=0, width=3, anchor='w')
        self.chk_moving.select()
        self.lbl_moving.pack(side=LEFT)
        self.chk_moving.pack(side=LEFT)

        # VFD display
        self.lbl_display = Label(fm, text="VFD display", font=('Courier New', 12), wraplength=150, justify='right', background=self.window['bg'])
        self.chk_display_var = IntVar()
        self.chk_display = Checkbutton(fm, variable=self.chk_display_var, onvalue = 1, offvalue = 0, height=1, font=('Courier New', 12), command=self.chk_display_click, background=self.window['bg'], width=3, anchor="w")
        if DISPLAY: self.chk_display.select()
        self.chk_display.pack(side=RIGHT)
        self.lbl_display.pack(side=RIGHT)
        # debug check
        self.lbl_debug = Label(fm, text="debug", font=('Courier New', 12), wraplength=150, justify='right', background=self.window['bg'])
        self.chk_debug_var = IntVar()
        self.chk_debug = Checkbutton(fm, variable=self.chk_debug_var, onvalue = 1, offvalue = 0, height=1, font=('Courier New', 12), command=self.chk_debug_click, background=self.window['bg'], width=3, anchor='w')
        if DEBUG: self.chk_debug.select()
        self.chk_debug.pack(side=RIGHT)
        self.lbl_debug.pack(side=RIGHT)
        fm.pack(side=BOTTOM, anchor="se", padx=10, pady=20)

        #BUTTONS
        self.button_quit = Button(window, text="QUIT", command=self.quit, font=('Courier New', 18))
        self.button_quit.place(x=40, y=680)
        self.button_start = Button(window, text="START", command=self.change_state, font=('Courier New', 18))
        self.button_start.place(x=160, y=680)
        self.button_clear = Button(window, text="CLEAR", command=self.clear_chart, font=('Courier New', 18), state='normal')
        self.button_clear.place(x=293, y=680)
        self.but_export = Button(window, text="EXPORT", command=self.export, font=('Courier New', 18))
        self.but_export.place(x=420, y=680)
        #end of ui

        self.df = pd.DataFrame({'ms': [], 'value': []})

        if not SIM:
            self.start_serial()

    def chk_display_click(self):
        if SIM: return
        if int(self.chk_display_var.get()):
            self.send_cmd('DISP:ENAB ON')
        else:
            self.send_cmd('DISP:ENAB OFF')

    def chk_debug_click(self):
        global DEBUG
        DEBUG = not DEBUG

    def start_serial(self):
        try:
            self.ser.port='/dev/ttyUSB0'
            self.ser.baudrate=19200
            self.ser.timeout=0
            self.ser.parity=serial.PARITY_NONE
            self.ser.stopbits=serial.STOPBITS_ONE
            self.ser.bytesize=serial.EIGHTBITS
            self.ser.xonxoff=False
            self.ser.open()
            if not DISPLAY: self.send_cmd('DISP:ENAB OFF')
            else: self.send_cmd('DISP:ENAB ON')
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
        self.plot_start_time = round(time.time() * 1000)
        self.clear_chart = 1
        self.ax.clear() # clear previous plot !!!!
        self.df = pd.DataFrame({'ms': [], 'value': []})
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        self.update_measurements()

    def change_state(self):
        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
            #self.button_clear.config(state = 'disabled')
            self.but_export.config(state = 'normal')
            #self.value.config(text="")
            #self.max_value.config(text="")
            #self.min_value.config(text="")
            #self.avg_value.config(text="")
            #self.std_value.config(text="")
            #self.readings.config(text="")
        else:
            self.continuePlotting = True
            self.button_start['text'] = "STOP "
            #self.button_clear.config(state = 'normal')
            self.but_export.config(state = 'disabled')
            self.plot()

    def quit(self):
        if (self.ser.isOpen()):
            self.ser.close()
        self.continuePlotting = False
        Tk().quit()

    def export(self):
        if not len(self.df):
            messagebox.showerror("Export error", "No data to export")
        else:
            print("len: ", self.df.size)
            self.df.to_csv('logger.csv', index=False)
            messagebox.showinfo("Export", "Export completed - %s" % 'logger.csv')

    def update_measurements(self):
        self.readings.config(text="readings: %d" % self.df.shape[0])
        if not self.df.size:
            self.value.config(text="")
            self.max_value.config(text="max: 0 Vrms")
            self.min_value.config(text="min: 0 Vrms")
            self.avg_value.config(text="avg: 0 Vrms")
            self.std_value.config(text="std: 0 Vrms")
        else:
            self.max_value.config(text="max: %s Vrms" % format(self.df['value'].max(), '.6f').rjust(11))
            self.min_value.config(text="min: %s Vrms" % format(self.df['value'].min(), '.6f').rjust(11))
            self.avg_value.config(text="avg: %s Vrms" % format(self.df['value'].mean(), '.6f').rjust(11))
            self.std_value.config(text="std: %s Vrms" % format(self.df['value'].std(), '.6f').rjust(11))

    def plot(self):
        self.fig, self.ax = plt.subplots(figsize=(13, 9))
        self.fig.set_facecolor(self.window['bg'])
        plt.rcParams['toolbar'] = 'None'

        self.plot_start_time = round(time.time() * 1000)
        self.df = pd.DataFrame({'ms': [], 'value': []})

        self.ax.clear() # clear previous plot !!!!
        self.ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')

        self.ax.set_facecolor('xkcd:black')
        self.ax.set_xlabel('Time, ms', fontsize=10, loc='center')
        self.ax.set_ylabel('Voltage, Vrms', fontsize=10, loc='center')
        self.ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)

        self.ax.plot(self.df.ms, self.df.value)
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        if not self.plot_packed:
            canvas.get_tk_widget().place(relx=.65, rely=.48, anchor="c")
        self.plot_packed = 1

        canvas.draw()
        canvas.flush_events()

        while(self.continuePlotting):
            if SIM:
            ## data sim
                value = np.random.random()
                if (round(time.time() * 1000) - self.plot_start_time > 15000):
                    value *= -10
                if (round(time.time() * 1000) - self.plot_start_time > 10000):
                    value *= 10
            ##end of data sim
            else:
                value = self.measure()

            if self.clear_chart:
                self.ax.clear() # clear previous plot !!!!
                self.df = pd.DataFrame({'ms': [], 'value': []})
                self.clear_chart = 0

            mytime = round(time.time() * 1000) - self.plot_start_time
            self.value.config(text=format(value, '.6f') + " Vrms")
            if DEBUG: print("value measured: " + str(value))


            # move window
            if self.chk_moving_var.get() == 1 and mytime > WINDOW_TIME:
                self.ax.clear()
                self.df = self.df.tail(-1)

            dfn = pd.DataFrame({'ms': [mytime], 'value': [value]})
            self.df = pd.concat([self.df, dfn])

            self.update_measurements()

            self.ax.set_xlabel('time, ms', fontsize=20, loc='right')
            self.ax.set_ylabel('level, Vrms', fontsize=20, loc='center')
            self.ax.set_facecolor('xkcd:black')
            ax = self.fig.get_axes()[0]
            #ax.grid(visible=True, which='major', axis='both', color='slategray', linestyle='--', linewidth=0.5)
            ax.grid(visible=True, which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
            ax.tick_params(labeltop=False, labelright=True)
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            #self.ax.clear()
            self.ax.plot(self.df.ms, self.df.value, color="xkcd:orange")
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            if SIM: time.sleep(REFRESH_TIME)
            self.plot_packed = 0

window = Tk()
start = mclass(window)
window.mainloop()
