# some config
SIM = 1
DEBUG = 0
DISPLAY = 1 # display on or off
DEFAULT_POINTS_PER_DECADE = 3  #4 means for instance that between 20hz and 30hz you will have 2 other points: [22.89 Hz and 26.21 Hz]
DEFAULT_MAXY = 5 # default max value for Y axis in %
DEFAULT_QTY_HARM = 4 # default number of harmonics to use for THD measurement of each freq.
DEFAULT_INPUT_SIGNAL_AMPLITUDE = 2 # default amplitude for input signal in Vrms

#TODO:
#export data measured
#save plot?
#add validations of input values. see change_state function
#test case in which you change points per decade between two different plots

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
        self.str_title.set("Keithley 2015 - %s vs Freq. measurement" % self.rad_values[0])
        self.lbl_title = Label(window, textvariable=self.str_title, fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.lbl_title.pack(ipady=15, expand=False, side=TOP)

        # amplitude
        self.lbl_amplitude = Label(window, text="input signal amplitude", font='Helvetica 18')
        self.lbl_amplitude.place(x = 40, y = 203)
        self.str_amplitude = StringVar()
        self.str_amplitude.set(DEFAULT_INPUT_SIGNAL_AMPLITUDE)
        self.etr_amplitude = Entry(window, textvariable=self.str_amplitude, font='Helvetica 18', width=3)
        self.etr_amplitude.place(x = 280, y = 200)
        self.etr_amplitude.focus_set()
        self.etr_amplitude.icursor(1)
        self.lbl_amplitude_vrms = Label(window, text="Vrms", font='Helvetica 18')
        self.lbl_amplitude_vrms.place(x = 330, y = 203)

        # points per decade
        self.lbl_points_decade = Label(window, text="points per decade", font='Helvetica 18')
        self.lbl_points_decade.place(x = 40, y = 263)
        self.str_points_decade = StringVar()
        self.str_points_decade.set(DEFAULT_POINTS_PER_DECADE)
        self.etr_points_decade = Entry(window, textvariable=self.str_points_decade, font='Helvetica 18', width=3)
        self.etr_points_decade.place(x = 280, y = 260)
        #self.etr_points_decade.focus_set()
        self.etr_points_decade.icursor(1)


        # number of harmonics
        self.lbl_harm_qty = Label(window, text="number of harmonics", font='Helvetica 18')
        self.lbl_harm_qty.place(x = 40, y = 323)
        self.str_harm_qty = StringVar()
        self.str_harm_qty.set(DEFAULT_QTY_HARM)
        self.etr_harm_qty = Entry(window, textvariable=self.str_harm_qty, font='Helvetica 18', width=3)
        self.etr_harm_qty.place(x = 280, y = 320)
        #self.etr_harm_qty.focus_set()
        self.etr_harm_qty.icursor(1)

        # y max
        self.lbl_maxy = Label(window, text="max value in Y axis", font='Helvetica 18')
        self.lbl_maxy.place(x = 40, y = 383)
        self.lbl_maxy = Label(window, text="%", font='Helvetica 18')
        self.lbl_maxy.place(x = 330, y = 383)
        self.str_maxy = StringVar()
        self.str_maxy.set(DEFAULT_MAXY)
        self.etr_maxy = Entry(window, textvariable=self.str_maxy, font='Helvetica 18', width=3)
        self.etr_maxy.place(x = 280, y = 380)
        #self.etr_maxy.focus_set()
        self.etr_maxy.icursor(1)

        # details - Freq measured
        self.str_details = StringVar()
        self.lbl_details = Label(window, textvariable=self.str_details, font='Helvetica 18 bold')
        self.lbl_details.place(x = 40, y = 880)

        # coordinates
        self.str_coordinates = StringVar()
        self.lbl_coordinates = Label(window, textvariable=self.str_coordinates, font='Helvetica 18 bold')
        self.lbl_coordinates.place(x = 440, y = 1000)

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
        if not SIM:
            #self.send_cmd(':SENS:DIST:FREQ:AUTO OFF')
            self.send_cmd(':OUTP:IMP HIZ') #;set high impedance source
            self.send_cmd(':OUTP:AMPL ' + self.str_amplitude.get()) #;set amplitude in Vrms
            self.send_cmd(':OUTP:CHAN2 ISINE') #;select inverted sine

    def set_siggen_freq(self, freq):
        if DEBUG: print("Setting freq to %s" % freq)
        if not SIM:
            self.send_cmd(':OUTP:FREQ ' + str(freq)) #;set frequency in Hz
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
        self.dist_perc = format(float(self.send_cmd(':SENS:DIST:THD?')), '.6f')
        if DEBUG: print("measured " + self.rad_values[int(self.rad_var.get())] + ": " + self.dist_perc + " %")
        return res
        #return self.dist_perc

    def quit(self):
        if (not SIM and self.ser.isOpen()):
            self.ser.close()
        Tk().quit()

    def change_measurement_type(self):
        self.str_measurement_type.set(self.rad_values[int(self.rad_var.get())])
        #self.str_title.set("Keithley 2015 - %s vs Freq. measurement" % self.str_measurement_type.get())

    def clear(self):
        self.measurement = pd.DataFrame(columns = ['id', 'freq', 'thd'])
        self.plots = 0 # number of plots done. can be up to 4
        self.plot()

    def change_state(self):
        #TODO #int(self.etr_maxy.get()) must be numeric and less than 21
        #TODO #int(self.str_points_decade.get()) must be numeric and less that 30
        #TODO str_amplitude must be numeric and less than 10 Vrms
        #TODO str_harm_qty must be numeric and less than 64

        if (self.but_start['text'] == "ABORT"): self.abort = 1

        if (self.but_start['text'] == "RUN"):
            self.etr_points_decade.config(state = 'disabled')
            self.etr_maxy.config(state = 'disabled')
            self.but_start['text'] = "ABORT"
            self.rad_thd.config(state = 'disabled')
            self.rad_thdn.config(state = 'disabled')
            self.etr_harm_qty.config(state = 'disabled')
            self.etr_amplitude.config(state = 'disabled')

            #store each decade freq (range)
            self.decades_freq = pd.DataFrame(columns = ['freq'])
            if not self.plots: self.measurement = pd.DataFrame(columns = ['id', 'freq', 'thd'])
            for d in range(1, 5, 1):
                for x in range(2, 11, 1):
                    self.decades_freq = pd.concat([self.decades_freq, pd.DataFrame({'freq' : [x*10**d]})], ignore_index=True)
                    #print(x * (10 ** d))
                    if d == 4 and x == 2: break
            #print(self.decades_freq)

            # now identify each freq for the measurement, based on points per decade
            for i in self.decades_freq.index:
                if i == self.decades_freq.size-1: break
                # cada decade
                #print("-------------")
                start = self.decades_freq['freq'][i]
                end = self.decades_freq['freq'][i+1]
                #print(start, end)
                points = np.logspace(log10(start), log10(end), num=int(self.str_points_decade.get()), endpoint=True, base=10)
                points = [round(num, 2) for num in points]
                #print(points)
                #for each freq. we add it to dest data structure
                self.measurement = pd.concat([self.measurement, pd.DataFrame(points, columns =['freq'])], ignore_index=True).drop_duplicates()
                #print(self.measurement)

            #fill empty values of id with self.plots
            self.measurement['id'].fillna(self.plots, inplace=True)

            if not self.plots: self.plot()

            # enable siggen
            self.enable_siggen()

            # setup equipment for measurement THD
            self.setup_thd_measurement()

            # for each frequency, measure THD, save it in data structure and plot
            sm = self.measurement.loc[(self.measurement['id'] == self.plots)]
            for i, row in sm.iterrows():
                if self.abort:
                    self.str_details.set("ABORTED")
                    self.but_start['text'] = "RUN"
                    self.abort = 0
                    self.etr_points_decade.config(state = 'normal')
                    self.etr_maxy.config(state = 'normal')
                    self.rad_thd.config(state = 'normal')
                    self.rad_thdn.config(state = 'normal')
                    self.etr_harm_qty.config(state = 'normal')
                    self.etr_amplitude.config(state = 'normal')
                    self.etr_amplitude.focus_set()
                    return

                self.str_details.set("Measuring: " + format(sm['freq'][i], ".2f") + " Hz")
                #if DEBUG: print("Measuring: " , format(sm['freq'][i], ".2f") , " Hz")
                self.lbl_details.place(x = 40, y = 880)
                if SIM:
                    value = 0
                    if sm['thd'].notnull()[i] and i > 0: value = sm['thd'][i]
                    value = value + np.random.uniform(-0.2, 0.8)
                    if value < 0: value = 0
                else:
                    self.set_siggen_freq(sm['freq'][i])
                    value = self.measure_thd()

                cond = (self.measurement['id'] == self.plots) & (self.measurement['freq'] == sm['freq'][i])
                self.measurement.loc[cond, 'thd'] = value
                #replot
                self.replot()
            #self.replot()
            self.plots += 1
            self.but_start['text'] = "RUN"
            self.str_details.set("DONE")
            self.etr_points_decade.config(state = 'normal')
            self.etr_maxy.config(state = 'normal')
            self.rad_thd.config(state = 'normal')
            self.rad_thdn.config(state = 'normal')
            self.etr_harm_qty.config(state = 'normal')
            self.etr_amplitude.config(state = 'normal')
            self.etr_amplitude.focus_set()
            if DEBUG: print("DONE")

    def replot(self):
        self.fig.tight_layout()
        ax = self.fig.get_axes()[0]
        #ax.clear()         # clear axes from previous plot !!!!
        #plt.rcParams['toolbar'] = 'None'
        #ax.tick_params(labeltop=False, labelright=True, labelsize=14)
        #ax.set(xscale="log")
        #ax.set_facecolor('xkcd:black')
        #ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
        #ax.set_ylabel('%s, %%' % self.str_measurement_type.get(), fontsize=20, loc='center')
        #ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        #ax.minorticks_on()
        #ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        #ax.set_xlim([20, 20000])
        #ax.yaxis.set_ticks(np.arange(0, float(self.str_maxy.get()), 0.5), fontsize=20, visible=True) # la escala del eje Y cada 0.5 entre 0 y 5
        #ax.yaxis.set_minor_locator(AutoMinorLocator())
        #ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        #ax.set_ylim([0, float(self.str_maxy.get())])
        for id in self.measurement['id'].unique():
            if id < self.plots: continue
            cond = (self.measurement['id'] == id)
            df = self.measurement.loc[cond]
            c = 'white'
            if id == 1: c = 'salmon'
            if id == 2: c = 'deepskyblue'
            if id == 3: c = 'limegreen'
            ax.plot(df['freq'], df['thd'], color=c)
        plt.gcf().canvas.draw_idle()
        plt.gcf().canvas.start_event_loop(0.0001)
        #plt.gcf().canvas.mpl_connect('motion_notify_event', self.motion_hover)

    def plot(self):
        self.fig, ax = plt.subplots(figsize=(14, 9))
        self.fig.tight_layout()
        plt.rcParams['toolbar'] = 'None'
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.set(xscale="log")
        ax.set_facecolor('xkcd:black')
        ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
        ax.set_ylabel('%s, %%' % self.str_measurement_type.get(), fontsize=20, loc='center')
        ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        ax.set_xlim([20, 20000])
        ax.yaxis.set_ticks(np.arange(0, float(self.str_maxy.get()), 0.5), fontsize=20) # la escala del eje Y cada 0.5 entre 0 y 5
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        ax.set_ylim([0, float(self.str_maxy.get())])
        ax.plot(self.measurement['freq'], self.measurement['thd'], color='white')
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().place(relx=.6, rely=.48, anchor="c")
        canvas.draw()
        canvas.start_event_loop(0.05)
        canvas.mpl_connect('motion_notify_event', self.motion_hover)

    def motion_hover(self, event):
        if self.measurement.empty: return
        if self.but_start['text'] == "ABORT": return
        if event.inaxes is not None:
            df = self.measurement
            df['freq'] = df['freq'].astype('float')
            df['freq'] = df['freq'].apply(lambda x: round(x, 2))
            x = event.xdata
            y = format(event.ydata, '.2f')
            freq = df.iloc[(df['freq']-x).abs().argsort()[:1]]['freq'].tolist()[0]

            #show coordinates of cursor
            #self.str_coordinates.set("found %s %s" % (x, y))

            self.str_coordinates.set("freq. %s Hz" % freq)
            for i, r in (df.loc[(df['freq'] == freq)]).iterrows():
                self.str_coordinates.set(self.str_coordinates.get() + " - %s %% THD" % format(r['thd'], '.2f'))

            self.str_coordinates.set(self.str_coordinates.get() + "\n (%s, %s)" % (format(event.xdata, '.2f'),y))

window = Tk()
start = mclass(window)
window.mainloop()
