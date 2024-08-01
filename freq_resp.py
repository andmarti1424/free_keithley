#SOURCE:
#https://download.tek.com/manual/2015-900-01(F-Aug2003)(User).pdf

# Modification 18/01/2023:
# reference at 0dB is amplification at 1000Hz. Not the input signal voltage.
# added csv data export

#TODO:
#add validations of input values. see change_state function
#test case in which you change points per decade or miny/maxy between two different plots

# some config
SIM = 1
DEBUG = 0
DISPLAY = 0 # display on or off
DEFAULT_POINTS_PER_DECADE = 3  #4 means for instance that between 20hz and 30hz you will have 2 other points: [22.89 Hz and 26.21 Hz]
DEFAULT_INPUT_SIGNAL_AMPLITUDE = 1 # default amplitude for input signal in Vrms
DEFAULT_MAXY = 9 # max value in y axis: 10dB
DEFAULT_MINY = -9 # min value in y axis: 10dB
DEFAULT_YSTEPS = 3


import matplotlib.pyplot as plt
from tkinter import *
from tkinter import messagebox
import time
import serial
from matplotlib.ticker import MultipleLocator
# for simulation
import numpy as np
#scipy
from scipy import signal
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from math import log10
from math import ceil

class mclass:

    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window
        self.plots = 0 # number of plots done. can be up to 4
        self.abort = 0

        # setup UI
        #self.window['bg'] = 'silver'
        self.colors=['white', 'salmon', 'deepskyblue', 'limegreen']
        self.str_title = StringVar()

        # title
        self.str_title.set("Keithley 2015 - Freq. response")
        self.lbl_title = Label(window, textvariable=self.str_title, fg='#1C5AAC', font=('Courier New', 24, 'bold'), background=self.window['bg'])
        self.lbl_title.pack(ipady=15, expand=False, side=TOP)

        # amplitude
        self.lbl_amplitude = Label(window, text="input signal amplitude", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_amplitude.place(x = 40, y = 203)
        self.str_amplitude = StringVar()
        self.str_amplitude.set(DEFAULT_INPUT_SIGNAL_AMPLITUDE)
        self.etr_amplitude = Entry(window, textvariable=self.str_amplitude, font=('Courier New', 18), width=6)
        self.etr_amplitude.place(x = 360, y = 200)
        self.etr_amplitude.focus_set()
        self.etr_amplitude.icursor(1)
        self.lbl_amplitude_vrms = Label(window, text="Vrms", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_amplitude_vrms.place(x = 460, y = 203)

        # points per decade
        self.lbl_points_decade = Label(window, text="points per decade", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_points_decade.place(x = 40, y = 263)
        self.str_points_decade = StringVar()
        self.str_points_decade.set(DEFAULT_POINTS_PER_DECADE)
        self.etr_points_decade = Entry(window, textvariable=self.str_points_decade, font=('Courier New', 18), width=3)
        self.etr_points_decade.place(x = 360, y = 260)
        #self.etr_points_decade.focus_set()
        self.etr_points_decade.icursor(1)

        # y max
        self.lbl_maxy = Label(window, text="Y scale increase", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_maxy.place(x = 40, y = 323)
        self.lbl_maxy = Label(window, text="dB", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_maxy.place(x = 460, y = 323)
        self.str_maxy = StringVar()
        self.str_maxy.set(DEFAULT_MAXY)
        self.etr_maxy = Entry(window, textvariable=self.str_maxy, font=('Courier New', 18), width=6)
        self.etr_maxy.place(x = 360, y = 320)
        #self.etr_maxy.focus_set()
        self.etr_maxy.icursor(1)

        # y min
        self.lbl_miny = Label(window, text="Y scale decrease", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_miny.place(x = 40, y = 383)
        self.lbl_miny = Label(window, text="dB", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_miny.place(x = 460, y = 383)
        self.str_miny = StringVar()
        self.str_miny.set(DEFAULT_MINY)
        self.etr_miny = Entry(window, textvariable=self.str_miny, font=('Courier New', 18), width=6)
        self.etr_miny.place(x = 360, y = 380)
        #self.etr_miny.focus_set()
        self.etr_miny.icursor(1)

        # y steps
        self.lbl_ysteps = Label(window, text="Y axis ticks interval", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_ysteps.place(x = 40, y = 443)
        self.str_ysteps = StringVar()
        self.str_ysteps.set(DEFAULT_YSTEPS)
        self.etr_ysteps = Entry(window, textvariable=self.str_ysteps, font=('Courier New', 18), width=6)
        self.etr_ysteps.place(x = 360, y = 440)
        #self.etr_ysteps.focus_set()
        self.etr_ysteps.icursor(1)

        # details - Freq measured
        self.str_details = StringVar()
        self.lbl_details = Label(window, textvariable=self.str_details, font=('Courier New', 18, 'bold'), background=self.window['bg'])
        self.lbl_details.place(x = 40, y = 900)

        # coordinates
        self.str_coordinates = StringVar()
        self.lbl_coordinates = Label(window, textvariable=self.str_coordinates, font=('Courier New', 18, 'bold'), background=self.window['bg'])
        self.lbl_coordinates.place(x = 710, y = 900)

        # VFD display
        fm = Frame(window)
        self.lbl_display = Label(fm, text="VFD display", font=('Courier New', 12), wraplength=150, justify='left', background=self.window['bg'])
        self.chk_display_var = IntVar()
        self.chk_display = Checkbutton(fm, variable=self.chk_display_var, onvalue = 1, offvalue = 0, height=1, width = 1, font=('Courier New', 12), command=self.chk_display_click, background=self.window['bg'])
        if DISPLAY: self.chk_display.select()
        self.chk_display.pack(side=RIGHT)
        self.lbl_display.pack(side=RIGHT)
        # debug check
        self.lbl_debug = Label(fm, text="debug", font=('Courier New', 12), wraplength=150, justify='left', background=self.window['bg'])
        self.chk_debug_var = IntVar()
        self.chk_debug = Checkbutton(fm, variable=self.chk_debug_var, onvalue = 1, offvalue = 0, height=1, width = 1, font=('Courier New', 12), command=self.chk_debug_click, background=self.window['bg'])
        if DEBUG: self.chk_debug.select()
        self.chk_debug.pack(side=RIGHT)
        self.lbl_debug.pack(side=RIGHT)
        fm.pack(side=BOTTOM, anchor="se", padx=10, pady=20)

        # buttons
        self.but_quit = Button(window, text="QUIT", command=self.quit, font=('Courier New', 18))
        self.but_quit.place(x=40, y=680)
        self.but_start = Button(window, text=" RUN ", command=self.change_state, font=('Courier New', 18))
        self.but_start.place(x=160, y=680)
        self.but_clear = Button(window, text="CLEAR", command=self.clear, font=('Courier New', 18))
        self.but_clear.place(x=293, y=680)
        self.but_export = Button(window, text="EXPORT", command=self.export, font=('Courier New', 18))
        self.but_export.place(x=420, y=680)
        #end of ui

        if SIM:
            #np.random.seed(42) # for data sim
            self.w, self.h = signal.freqz([1, 1])
            self.x = self.w * 44100 * 1.0 / (2 * np.pi)
            self.y = 20 * np.log10(abs(self.h))
        else:
            self.start_serial()

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
            #self.send_cmd(':OUTP:IMP HIZ') #;set high impedance source
            #self.send_cmd(':OUTP:AMPL ' + self.str_amplitude.get()) #;set amplitude in Vrms
            #self.send_cmd(':OUTP:CHAN2 ISINE') #;select inverted sine
            self.send_cmd(':OUTP:FREQ ' + str(freq)) #;set frequency in Hz
            self.send_cmd(':OUTP ON') #;turn on source

    def quit(self):
        if (not SIM and self.ser.isOpen()):
            self.ser.close()
        Tk().quit()

    def setup_vca_measurement(self):
        if DEBUG: print("setup VCA measurement")
        if SIM: return
        self.send_cmd(':SENS:FUNC \'VOLT:AC\'')
        self.send_cmd(':SENS:VOLT:AC:RANG:AUTO ON')
        self.send_cmd(':SENS:VOLT:AC:DIG 7') # must be 4-7
        #self.send_cmd(':SENS:VOLT:AC:DET:BAND 300') # 300Hz-300kHz
        #self.send_cmd(':SENS:VOLT:AC:NPLC 1') # FAST is 0.1 in AC. 1 is MED and 10 is SLOW.
        self.send_cmd(':SENS:VOLT:AC:AVER:STAT OFF')

    #measure Vca in equipment - with VCA mode
    def measure_vca(self):
        self.send_cmd(':TRIG:COUN 1')
        res = self.send_cmd(':READ?')
        return res

    def change_state(self):
        if (self.but_start['text'] == "ABORT"): self.abort = 1

        if (self.plots == 4):
            self.str_details.set("Please clear plot before making a new measurement")
            return

        if (self.but_start['text'] == " RUN "):
            self.etr_amplitude.config(state = 'disabled')
            self.etr_ysteps.config(state = 'disabled')
            self.etr_miny.config(state = 'disabled')
            self.etr_maxy.config(state = 'disabled')
            self.etr_points_decade.config(state = 'disabled')
            self.but_start['text'] = "ABORT"
            self.but_quit.config(state = 'disabled')
            self.but_clear.config(state = 'disabled')
            self.but_export.config(state = 'disabled')

            #store each decade freq (range)
            self.decades_freq = pd.DataFrame(columns = ['freq'])
            #if not self.plots: self.measurement = pd.DataFrame(columns = ['id', 'freq', 'vca'])
            #-----------------------------------------------------
            # to get rid of concating to empty dataframe A
            #FIXME THIS HACK
            if not self.plots: self.measurement = pd.DataFrame({'id': -1, 'freq': -1, 'vca': -1}, index=[0])
            #if not self.plots: self.measurement = self.measurement._append({'id': -1, 'freq': -1, 'vca': -1}, ignore_index=True)
            #-----------------------------------------------------

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

            #-----------------------------------------------------
            #FIXME THIS HACK
            # to get rid of concating to empty dataframe B
            self.measurement.drop(self.measurement[self.measurement['id'] == -1].index, inplace = True)
            #-----------------------------------------------------

            #fill empty values of id with self.plots
            #self.measurement['id'].fillna(self.plots, inplace=True)
            self.measurement['id'] = self.measurement['id'].astype(float)
            self.measurement.fillna({'id': self.plots}, inplace=True)

            if not self.plots: self.plot()

            #enable siggen
            if not SIM: self.enable_siggen()

            #setup equipment for measurement VCA
            if not SIM: self.setup_vca_measurement()

            # reference at 0dB is amplification at 1000Hz
            if not SIM:
                self.set_siggen_freq(1000)
                value = format(float(self.measure_vca()), '.6f')
                ref = value

            #print(self.measurement)
            # for each frequency, measure THD, save it in data structure and plot
            sm = self.measurement.loc[(self.measurement['id'] == self.plots)]
            for i, row in sm.iterrows():
                if self.abort:
                    # remove points from aborted measurements
                    cond = (self.measurement['id'] == self.plots)
                    self.measurement.loc[cond, 'vca'] = float(0)

                    self.str_details.set("ABORTED")
                    self.but_start['text'] = " RUN "
                    self.abort = 0
                    self.etr_amplitude.config(state = 'normal')
                    self.etr_ysteps.config(state = 'normal')
                    self.etr_miny.config(state = 'normal')
                    self.etr_maxy.config(state = 'normal')
                    self.etr_points_decade.config(state = 'normal')
                    self.etr_amplitude.focus_set()
                    self.but_quit.config(state = 'normal')
                    self.but_clear.config(state = 'normal')
                    self.but_export.config(state = 'normal')
                    return

                self.str_details.set("Measuring: " + format(sm['freq'][i], ".2f") + " Hz")
                if DEBUG: print("Measuring: " , format(sm['freq'][i], ".2f") , " Hz")
                self.lbl_details.place(x = 40, y = 900)

                #3. set freq.
                if not SIM: self.set_siggen_freq(sm['freq'][i])

                #4. measure Vca
                if not SIM: value = format(float(self.measure_vca()), '.6f')
                #to test:
                #if not SIM: value = format(float(self.measure_vca()) * 5.62341, '.6f')

                #take SIGGEN output signal as reference
                #ref = format(float(self.str_amplitude.get()), '.6f')
                #Se comenta lo anterior. ref debe ser la respuesta en 1000Hz.

                if not SIM:
                    #if DEBUG: print("value: " + value)
                    #if DEBUG: print("inp: " + inp)
                    #db = 20 * np.log10(float(ref) / float(value))
                    db = 20 * np.log10(float(value) / float(ref))
                    cond = (self.measurement['id'] == self.plots) & (self.measurement['freq'] == sm['freq'][i])
                    #if DEBUG: print("dB: %s" % format(db, '.2f'))
                    self.measurement.loc[cond, 'vca'] = db

                #replot
                if not SIM: self.replot()

        self.plots += 1
        self.but_start['text'] = " RUN "
        self.str_details.set("DONE")
        self.etr_amplitude.config(state = 'normal')
        self.etr_ysteps.config(state = 'normal')
        self.etr_miny.config(state = 'normal')
        self.etr_maxy.config(state = 'normal')
        self.etr_points_decade.config(state = 'normal')
        self.but_quit.config(state = 'normal')
        self.but_clear.config(state = 'normal')
        self.but_export.config(state = 'normal')

    def export(self):
        if not len(self.measurement):
            messagebox.showerror("Export error", "No data to export")
        else:
            self.measurement.to_csv('freq_resp.csv', index=False)
            messagebox.showinfo("Export", "Export completed - %s" % 'freq_resp.csv')

    def chk_display_click(self):
        if SIM: return
        if int(self.chk_display_var.get()):
            self.send_cmd('DISP:ENAB ON')
        else:
            self.send_cmd('DISP:ENAB OFF')

    def chk_debug_click(self):
        global DEBUG
        DEBUG = not DEBUG

    def clear(self):
        if not self.plots: self.measurement = pd.DataFrame(columns = ['id', 'freq', 'vca'])

        self.measurement = pd.DataFrame(columns = ['id', 'freq', 'vca'])
        self.plots = 0 # number of plots done. can be up to 4
        self.plot()

    def plot(self):
        self.fig, ax = plt.subplots(figsize=(12, 7))
        self.fig.set_facecolor(self.window['bg'])
        self.fig.tight_layout(rect=[0.05, 0.08, 0.95, 0.95])
        plt.rcParams['toolbar'] = 'None'
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.set(xscale="log")
        ax.set_facecolor('xkcd:black')
        ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        ax.set_xlim([20, 20000])

        mean = ymin = ymax = 0
        if self.measurement['vca'].any():
             mean = ceil(self.measurement['vca'].max())
             ymin = self.measurement['vca'].min()
             ymax = self.measurement['vca'].max()
        ax.set_ylim([ymin+float(self.str_miny.get()), ymax+float(self.str_maxy.get())])
        ax.yaxis.set_ticks(np.arange(mean+float(self.str_miny.get()), mean+float(self.str_maxy.get()), float(self.str_ysteps.get()))) # Y scale

        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        if SIM:
            ax.plot(self.x, self.y, color=self.colors[0])
        else:
            ax.plot(self.measurement['freq'], self.measurement['vca'], self.colors[0])

        # set legend color
        ax.legend(self.measurement['id'].astype('int').unique())
        leg = ax.get_legend()
        for i, j in enumerate(leg.legend_handles):
            j.set_color(self.colors[i])

        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().place(relx=.6, rely=.48, anchor="c")
        canvas.draw()
        canvas.start_event_loop(0.05)
        canvas.mpl_connect('motion_notify_event', self.motion_hover)

    def replot(self):
        self.fig.tight_layout()
        ax = self.fig.get_axes()[0]
        ax.yaxis.set_minor_locator(MultipleLocator(1))

        mean = ymin = ymax = 0
        if self.measurement['vca'].any():
             mean = ceil(self.measurement['vca'].max())
             ymin = self.measurement['vca'].min()
             ymax = self.measurement['vca'].max()
        ax.set_ylim([ymin+float(self.str_miny.get()), ymax+float(self.str_maxy.get())])
        ax.yaxis.set_ticks(np.arange(mean+float(self.str_miny.get()), mean+float(self.str_maxy.get()), float(self.str_ysteps.get()))) # Y scale

        for id in self.measurement['id'].unique():
            if id < self.plots: continue
            cond = (self.measurement['id'] == id)
            df = self.measurement.loc[cond]
            ax.plot(df['freq'], df['vca'], color=self.colors[int(id)])

        # set legend color
        ax.legend(self.measurement['id'].astype('int').unique())
        leg = ax.get_legend()
        for i, j in enumerate(leg.legend_handles):
            j.set_color(self.colors[i])

        plt.gcf().canvas.draw_idle()
        plt.gcf().canvas.start_event_loop(0.01)
        plt.gcf().canvas.mpl_connect('motion_notify_event', self.motion_hover)

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
                self.str_coordinates.set(self.str_coordinates.get() + " - %s %% dB" % format(r['vca'], '.2f'))

            self.str_coordinates.set(self.str_coordinates.get() + "\n (%s, %s)" % (format(event.xdata, '.2f'),y))

window = Tk()
start = mclass(window)
window.mainloop()
