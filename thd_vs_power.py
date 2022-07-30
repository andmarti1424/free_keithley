# some config
SIM = 1
DEBUG = 0
DISPLAY = 1 # display on or off

DEFAULT_QTY_HARM = 4 # default number of harmonics to use for THD measurement of each freq.
DEFAULT_VIN_MIN = 0.1
DEFAULT_VIN_MAX = 1.5
DEFAULT_POINTS = 40
DEFAULT_LOAD_IMPEDANCE = 8
DEFAULT_MAXY = 5 # default max value for Y axis in %
DEFAULT_FREQ = 1000

#TODO:
#add validations of user input
#add protection (max THD value)

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from math import log10
import serial
import time
from tkinter import *
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class mclass:

    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window
        self.plots = 0 # number of plots done. can be up to 4
        self.abort = 0

        # setup UI
        self.str_title = StringVar()

        # TYPE OF MEASUREMENT radio button
        self.lbl_harm_qty = Label(window, text = "Measure:", font='Helvetica 18')
        self.lbl_harm_qty.place(x = 40, y = 123)
        self.str_measurement_type = StringVar()
        self.rad_var = IntVar()
        self.rad_values = ["THD", "THD+N"]
        self.rad_thd = Radiobutton(window, variable=self.rad_var, text=self.rad_values[0], value=0, font='Helvetica 18', command=self.change_measurement_type)
        self.rad_thd.invoke()
        self.rad_thd.select()
        self.rad_thd.place(x = 244, y = 103)
        self.rad_thdn = Radiobutton(window, variable=self.rad_var, text=self.rad_values[1], value=1, font='Helvetica 18', command=self.change_measurement_type)
        self.rad_thdn.place(x = 244, y = 140)

        # title
        self.str_title.set("Keithley 2015 - %s vs Power" % self.rad_values[0])
        self.lbl_title = Label(window, textvariable=self.str_title, fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.lbl_title.pack(ipady=15, expand=False, side=TOP)

        # load impedance
        self.lbl_load_impedance = Label(window, text="load impedance", font='Helvetica 18')
        self.lbl_load_impedance.place(x = 40, y = 203)
        self.lbl_load_impedance = Label(window, text="ohms", font='Helvetica 18')
        self.lbl_load_impedance.place(x = 395, y = 203)
        self.str_load_impedance = StringVar()
        self.str_load_impedance.set(DEFAULT_LOAD_IMPEDANCE)
        self.etr_load_impedance = Entry(window, textvariable=self.str_load_impedance, font='Helvetica 18', width=6)
        self.etr_load_impedance.place(x = 300, y = 200)
        self.etr_load_impedance.focus_set()
        self.etr_load_impedance.icursor(1)

        # min input signal voltage
        self.lbl_vin_min = Label(window, text="min input signal", font='Helvetica 18')
        self.lbl_vin_min.place(x = 40, y = 263)
        self.lbl_vin_min = Label(window, text="Vrms", font='Helvetica 18')
        self.lbl_vin_min.place(x = 395, y = 263)
        self.str_vin_min = StringVar()
        self.str_vin_min.set(DEFAULT_VIN_MIN)
        self.etr_vin_min = Entry(window, textvariable=self.str_vin_min, font='Helvetica 18', width=6)
        self.etr_vin_min.place(x = 300, y = 260)
        self.etr_vin_min.icursor(1)

        # min input signal voltage
        self.lbl_vin_max = Label(window, text="max input signal", font='Helvetica 18')
        self.lbl_vin_max.place(x = 40, y = 323)
        self.lbl_vin_max = Label(window, text="Vrms", font='Helvetica 18')
        self.lbl_vin_max.place(x = 395, y = 323)
        self.str_vin_max = StringVar()
        self.str_vin_max.set(DEFAULT_VIN_MAX)
        self.etr_vin_max = Entry(window, textvariable=self.str_vin_max, font='Helvetica 18', width=6)
        self.etr_vin_max.place(x = 300, y = 320)
        self.etr_vin_max.icursor(1)

        # points in input range
        self.lbl_points = Label(window, text="points in input range", font='Helvetica 18')
        self.lbl_points.place(x = 40, y = 383)
        self.str_points = StringVar()
        self.str_points.set(DEFAULT_POINTS)
        self.etr_points = Entry(window, textvariable=self.str_points, font='Helvetica 18', width=6)
        self.etr_points.place(x = 300, y = 380)
        self.etr_points.icursor(1)

        # frequency
        self.lbl_freq = Label(window, text="input signal freq.", font='Helvetica 18')
        self.lbl_freq.place(x = 40, y = 443)
        self.lbl_freq = Label(window, text="Hz", font='Helvetica 18')
        self.lbl_freq.place(x = 395, y = 443)
        self.str_freq = StringVar()
        self.str_freq.set(DEFAULT_FREQ)
        self.etr_freq = Entry(window, textvariable=self.str_freq, font='Helvetica 18', width=6)
        self.etr_freq.place(x = 300, y = 440)
        self.etr_freq.icursor(1)

        # number of harmonics
        self.lbl_harm_qty = Label(window, text="number of harmonics", font='Helvetica 18')
        self.lbl_harm_qty.place(x = 40, y = 503)
        self.str_harm_qty = StringVar()
        self.str_harm_qty.set(DEFAULT_QTY_HARM)
        self.etr_harm_qty = Entry(window, textvariable=self.str_harm_qty, font='Helvetica 18', width=6)
        self.etr_harm_qty.place(x = 300, y = 500)
        self.etr_harm_qty.icursor(1)

        # y max
        self.lbl_maxy = Label(window, text="max value in Y axis", font='Helvetica 18')
        self.lbl_maxy.place(x = 40, y = 563)
        self.lbl_maxy = Label(window, text="%", font='Helvetica 18')
        self.lbl_maxy.place(x = 395, y = 563)
        self.str_maxy = StringVar()
        self.str_maxy.set(DEFAULT_MAXY)
        self.etr_maxy = Entry(window, textvariable=self.str_maxy, font='Helvetica 18', width=6)
        self.etr_maxy.place(x = 300, y = 560)
        self.etr_maxy.icursor(1)

        # details - input sweep
        self.str_details = StringVar()
        self.lbl_details = Label(window, textvariable=self.str_details, font='Helvetica 18 bold')
        self.lbl_details.place(x = 40, y = 880)

        # coordinates
        self.str_coordinates = StringVar()
        self.lbl_coordinates = Label(window, textvariable=self.str_coordinates, font='Helvetica 18 bold')
        self.lbl_coordinates.place(x = 410, y = 1000)

        # buttons
        self.but_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18')
        self.but_quit.place(x=40, y=680)
        self.but_start = Button(window, text="RUN", command=self.change_state, font='Helvetica 18')
        self.but_start.place(x=165, y=680)
        self.but_clear = Button(window, text="CLEAR", command=self.clear, font='Helvetica 18')
        self.but_clear.place(x=280, y=680)
        #end of ui

        if SIM:
            np.random.seed(42) # for data sim
        else:
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
            if not DISPLAY: self.send_cmd('DISP:ENAB OFF')
            self.send_cmd('*RST')
            self.send_cmd(':INITiate:CONTinuous OFF;:ABORt')
            self.send_cmd('*OPC?')
            resp = self.send_cmd('*IDN?')
            if DEBUG:
                print('version: {}'.format(repr(resp)))
        except:
            if (not self.ser.isOpen()):
                print("ERROR opening serial")
                return -1

    def write(self, s, term = '\r'):
        if DEBUG: print('TX >> ', s)
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
                if DEBUG: print("RX << ", repr(s))
                return s.strip()
            else:
                buf.append(c)

    def send_cmd(self, cmd):
        self.write(cmd)
        time.sleep(0.05)

        if '?' in cmd:
            response = self.read()

            if ',' in response:
                response = response.split(',')

            return response
        else:
            return None

    #enable en setup internal SIG GEN
    def enable_siggen(self):
        if DEBUG: print("Setting up internal SIGGEN")
        if SIM: return
        #self.send_cmd(':SENS:DIST:FREQ:AUTO OFF')
        self.send_cmd(':OUTP:IMP HIZ') # set high impedance source
        self.send_cmd(':OUTP:FREQ ' + self.str_freq.get()) # set frequency in Hz
        self.send_cmd(':OUTP:CHAN2 ISINE') # select inverted sine

    def set_siggen_amp(self, amp):
        if DEBUG: print("Setting SIGGEN amplitude to %s" % amp)
        if not SIM:
            self.send_cmd(':OUTP:AMPL ' + str(amp)) #;set amplitude in Vrms
            self.send_cmd(':OUTP ON') #;turn on source

    def setup_thd_measurement(self):
        if DEBUG: print("setup THD measurement")
        if SIM: return
        self.send_cmd(':SENS:FUNC \'DIST\'')
        self.send_cmd(':SENS:DIST:TYPE ' + self.rad_values[int(self.rad_var.get())].replace("+", ""))
        self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(int(self.str_harm_qty.get())))
        self.send_cmd(':UNIT:DIST PERC')
        self.send_cmd(':SENS:DIST:SFIL NONE')
        self.send_cmd(':SENS:DIST:RANG:AUTO ON')
        self.send_cmd(':SENS:DIST:FREQ:AUTO ON')

    def measure_thd(self):
        if DEBUG: print("measure THD")
        # return dist in percent
        res = self.send_cmd(':READ?')
        res = float(format(float(res), '.3f'))
        if DEBUG: print("% dist: " + str(res))
        #self.dist_perc = format(float(self.send_cmd(':SENS:DIST:THD?')), '.6f')
        #if DEBUG: print("measured " + self.rad_values[int(self.rad_var.get())] + ": " + self.dist_perc + " %")
        #return self.dist_perc
        return res

    def quit(self):
        if (not SIM and self.ser.isOpen()):
            self.ser.close()
        Tk().quit()

    def change_measurement_type(self):
        self.str_measurement_type.set(self.rad_values[int(self.rad_var.get())])
        #self.str_title.set("Keithley 2015 - %s vs Power" % self.str_measurement_type.get())

    def clear(self):
        self.measurement = pd.DataFrame(columns = ['id', 'vin', 'vout', 'thd', 'impedance'])
        self.plots = 0 # number of plots done. can be up to 4
        self.plot()

    def change_state(self):
        if (self.but_start['text'] == "ABORT"): self.abort = 1

        if (self.but_start['text'] == "RUN"):
            self.etr_load_impedance.config(state = 'disabled')
            self.etr_vin_min.config(state = 'disabled')
            self.etr_vin_max.config(state = 'disabled')
            self.etr_points.config(state = 'disabled')
            self.etr_harm_qty.config(state = 'disabled')
            self.etr_maxy.config(state = 'disabled')
            self.etr_freq.config(state = 'disabled')
            self.rad_thd.config(state = 'disabled')
            self.rad_thdn.config(state = 'disabled')
            self.but_start['text'] = "ABORT"

            # create data structure
            if not self.plots: self.measurement = pd.DataFrame(columns = ['id', 'vin', 'vout', 'thd', 'impedance'])

            vin_min = float(self.str_vin_min.get())
            vin_max = float(self.str_vin_max.get())
            step =  round((vin_max - vin_min) / (float(self.etr_points.get())-1), 4)
            #print(vin_min)
            #print(vin_max)
            #print(step, "\n----\n")

            #for each input signal we add it to dest data structure
            for n in np.arange(vin_min, vin_max + step, step):
                #print(">> ", round(n, 4))
                self.measurement = pd.concat([self.measurement, pd.DataFrame({'vin' : [round(n, 4)]})], ignore_index=True)

            #fill load impedance in case we change impedance between plots
            self.measurement['impedance'].fillna(int(self.str_load_impedance.get()), inplace=True)

            #fill empty values of id with self.plots
            self.measurement['id'].fillna(self.plots, inplace=True)

            # enable siggen
            self.enable_siggen()

            # setup equipment for measurement THD
            self.setup_thd_measurement()

            if not self.plots: self.plot()

            #if DEBUG: print(self.measurement)
            #time.sleep(20)

            # for each input signal, measure THD, save it in data structure and plot
            sm = self.measurement.loc[(self.measurement['id'] == self.plots)]
            for vin, row in sm.iterrows():
                if self.abort:
                    self.str_details.set("ABORTED")
                    self.but_start['text'] = "RUN"
                    self.abort = 0
                    self.etr_load_impedance.config(state = 'normal')
                    self.etr_vin_min.config(state = 'normal')
                    self.etr_vin_max.config(state = 'normal')
                    self.etr_points.config(state = 'normal')
                    self.etr_harm_qty.config(state = 'normal')
                    self.etr_maxy.config(state = 'normal')
                    self.rad_thd.config(state = 'normal')
                    self.rad_thdn.config(state = 'normal')
                    self.etr_freq.config(state = 'normal')
                    return

                self.str_details.set("Measuring THD at " + format(sm['vin'][vin], ".4f") + " Vrms input")
                if DEBUG: print("Measuring THD at " , format(sm['vin'][vin], ".4f") , " Vrms input")

                if SIM:
                    value = 0.4
                    if sm['thd'].notnull()[vin] and i > 0: value = sm['thd'][vin]
                    value = value + np.random.uniform(-0.2, 0.8)
                    if value < 0: value = 0.4
                    vout = (sm['vin'][vin] * 2.5) ** 2
                else:
                    self.set_siggen_amp(sm['vin'][vin])

                    #get thd in %
                    value = self.measure_thd()

                    #get vout in Vrms
                    vout = self.send_cmd(':SENS:DIST:RMS?')
                    vout = float(format(float(vout), '.6f'))

                # save measured data
                cond = (self.measurement['id'] == self.plots) & (self.measurement['vin'] == sm['vin'][vin])
                self.measurement.loc[cond, 'vout'] = vout
                self.measurement.loc[cond, 'thd'] = value

                #replot
                self.replot()

            if DEBUG: print(self.measurement)
            #time.sleep(20)

            self.plots += 1
            self.but_start['text'] = "RUN"
            self.str_details.set("DONE")
            self.rad_thd.config(state = 'normal')
            self.rad_thdn.config(state = 'normal')
            self.etr_load_impedance.config(state = 'normal')
            self.etr_vin_min.config(state = 'normal')
            self.etr_vin_max.config(state = 'normal')
            self.etr_points.config(state = 'normal')
            self.etr_harm_qty.config(state = 'normal')
            self.etr_maxy.config(state = 'normal')
            self.etr_freq.config(state = 'normal')

            if DEBUG: print("DONE")

    def replot(self):
        self.fig.tight_layout()
#        self.fig.tight_layout(rect=[0.08, 0.08, 0.95, 0.95])
        ax = self.fig.get_axes()[0]
#        #ax.clear()         # clear axes from previous plot !!!!
#        #plt.rcParams['toolbar'] = 'None'
#        ax.tick_params(labeltop=False, labelright=True, labelsize=14)
#        #ax.set(xscale="log")
#        #ax.set_facecolor('xkcd:black')
#        #ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
#        ax.set_ylabel('%s, %%' % self.str_measurement_type.get(), fontsize=20, loc='center')
#        #ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
#        #ax.minorticks_on()
#        #ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
#        #ax.set_xlim([20, 20000])
        ax.yaxis.set_ticks(np.arange(0, float(self.str_maxy.get()), 0.5), fontsize=20, visible=True) # la escala del eje Y cada 0.5 entre 0 y 5
#        #ax.yaxis.set_minor_locator(AutoMinorLocator())
#        #ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        ax.set_ylim([0, float(self.str_maxy.get())])
        for id in self.measurement['id'].unique():
            if id < self.plots: continue
            cond = (self.measurement['id'] == id)
            df = self.measurement.loc[cond]
            c = 'white'
            if id == 1: c = 'salmon'
            if id == 2: c = 'deepskyblue'
            if id == 3: c = 'limegreen'
            ax.plot(df['vout'] ** 2 / df['impedance'], df['thd'], color=c)
        plt.gcf().canvas.draw_idle()
        plt.gcf().canvas.start_event_loop(0.01)
        plt.gcf().canvas.mpl_connect('motion_notify_event', self.motion_hover)

    def plot(self):
        self.fig, ax = plt.subplots(figsize=(13, 9))
        self.fig.tight_layout()
        plt.rcParams['toolbar'] = 'None'
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.set(xscale="log")
        ax.set_facecolor('xkcd:black')
        ax.set_xlabel('Power, Wrms', fontsize=20, loc='center')
        ax.set_ylabel('%s, %%' % self.str_measurement_type.get(), fontsize=20, loc='center')
        ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        #ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        ax.set_xticks([0.01, 0.1, 1, 10, 100], ["0.01", "0.1", "1", "10", "100"])
        ax.set_xlim([0.1, 100])
        ax.yaxis.set_ticks(np.arange(0, float(self.str_maxy.get()), 0.5), fontsize=20) # la escala del eje Y cada 0.5 entre 0 y 5
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        #ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        ax.set_ylim([0, float(self.str_maxy.get())])
        ax.plot(self.measurement['vout'] ** 2 / self.measurement['impedance'], self.measurement['thd'], color='white')
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().place(relx=.65, rely=.48, anchor="c")
        canvas.draw()
        canvas.start_event_loop(0.05)
        canvas.mpl_connect('motion_notify_event', self.motion_hover)

    def motion_hover(self, event):
        if self.measurement.empty: return
        if self.but_start['text'] == "ABORT": return
        if event.inaxes is not None:
            df = self.measurement
            x = event.xdata
            y = format(event.ydata, '.2f')
            t = df.iloc[((df['vout']**2/df['impedance'])-x).abs().argsort()[:1]]
            vin = t['vin'].tolist()[0]
            vout = t['vout'].tolist()[0]
            p = vout ** 2 / 8

            self.str_coordinates.set("power %s Wrms" % format(p, '.2f'))
            for i, r in (df.loc[(df['vin'] == vin)]).iterrows():
                self.str_coordinates.set(self.str_coordinates.get() + " - %s %% THD" % format(r['thd'], '.2f'))

            self.str_coordinates.set(self.str_coordinates.get() + "\n (%s, %s)" % (format(event.xdata, '.2f'),y))

window = Tk()
start = mclass(window)
window.mainloop()
