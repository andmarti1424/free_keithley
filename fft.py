#SOURCE
#https://download.tek.com/manual/2015-900-01(F-Aug2003)(User).pdf
#https://www.head-case.org/forums/topic/21432-the-keithley-2015-and-2016-audio-analysing-multi-meters-guide-to-behaviour-limitations-and-issues/
#https://www.eevblog.com/forum/testgear/keithley-2015-thd-with-fft-and-harmonic-graphs/
#https://www.eevblog.com/forum/testgear/continuing-the-keithley-2015-2015p-saga/

#to avoid the need of start serial with sudo
#stat /dev/ttyUSB0
#sudo usermod -a -G uucp mongo
#sudo reboot

"""
TODO

#1. click and move over plot to change start or end value
fig.canvas.mpl_connect('button_press_event', button_press_callback)
fig.canvas.mpl_connect('button_release_event', button_release_callback)
fig.canvas.mpl_connect('motion_notify_event', motion_notify_callback)

#2. add check to enable/disable LCD

#3. in change state, add same validations, just as
# check here that internal WG freq is valid
# check qty of harm is numeric
# check ohms is numeric and 4, 8 or 16 ohms

#max FFT freq: 20460Hz

#Keithley 2015 does not allow to change OUTPUT data format to SREAL to increase FFT speed if using RS232! :(
my RS232 times are:
    17.6s with 19200 baudrate
    26.0s with 9600 baudrate
"""

# Some settings
SIM = 1 # do not interact with equipment, just sim data
DEBUG = 0 # print debug data on terminal
DISPLAY = 0 # display on or off
UPDATE_INTERVAL= 1 # only used on sim.

DEFAULT_QTY_HARM = 8 # default number of harmonics to plot in graph
DEFAULT_SIGGEN_FREQ = 1000 # in Hz
DEFAULT_SIGGEN_AMP = 1 # in Vrms
DEFAULT_DUMMY_RESISTANCE = 8 # in ohms
BOTTOM_DB = -100 # bottom dB in graph
BINS_BY_INPUT_FRQ={20:1023, 40:1023, 60:833, 80:1023, 100:1000, 120:833, 200:1000, 500:900, 1000:750, 4500:733, 10000:735, 20000:732}

fft_bin_width = 20
non_50_m = 68.4758620689655
non_50_b = 22.5241379310355
non_50_m = ((50000-20)/748.0)
non_50_b = 20

import matplotlib
from matplotlib.widgets import TextBox
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from tkinter import *
from tkinter import ttk
import pandas as pd
import time
import math
import threading
from tkinter import messagebox
import serial
import numpy as np #for data sim
from heapq import nsmallest, nlargest
from scipy.signal import find_peaks
import operator

class mclass:
    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window

        self.running = False
        self.plot_packed = 0 # avoid a re pack when refreshing plot
        self.fundamental_vrms = float(0) # set some initial value
        self.avoid_exit=0 # just in case we are waiting for FFT bins and try to exit before getting the entire response
        self.on_mouse_routine = 0
        self.leftb=0 #mouse button pressed
        self.xinit_pos=0
        self.xcurr_pos=0

        self.str_measurement_type = StringVar()
        if SIM:
            np.random.seed(42) # for data sim
        else:
            self.start_serial()

        # FFT data for plot
        self.x1 = []
        self.y1 = []
        if SIM:
            #self.x1 = [20, 50, 100, 200, 500, 900, 1000, 1060, 1080, 2000, 5000, 7500, 10000, 20000]
            #self.y1 = [-80, -70, -60, -82, -56, -75, 0, -70, -65, -70, -85, -82, -92, -75]
            df=pd.read_csv("fft_testdata.csv")
            self.x1 = df["bin"].values.tolist()
            self.y1 = df["dB"].values.tolist()

        #setup UI
        #self.window['bg'] = 'silver'

        self.lbl_title = Label(window, text='Keithley 2015 - FFT measurement', fg='#1C5AAC', font=('Courier New', 24, 'bold'), background=self.window['bg'])
        self.lbl_title.pack(ipady=15, expand=False, side=TOP)

        self.lbl_harm_qty = Label(window, text = "Measure:", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_harm_qty.place(x = 40, y = 100)

        self.lbl_harm_qty = Label(window, text = "Harm. Qty", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_harm_qty.place(x = 40, y = 200)
        self.str_harm_qty = StringVar()
        self.str_harm_qty.set(DEFAULT_QTY_HARM)
        self.str_dB = StringVar()
        self.etr_THD = Entry(window, textvariable=self.str_dB, font=('Courier New', 18), width=14, state=DISABLED)
        self.etr_harm_qty = Entry(window, textvariable=self.str_harm_qty, font=('Courier New', 18), width=4)
        self.etr_harm_qty.place(x = 245, y = 200)

        self.siggenFrame = LabelFrame(window, text="", height=210, width=520, background=self.window['bg'])
        self.siggenFrame.place(x = 30, y = 270)
        self.lbl_SIGGEN = Label(self.siggenFrame, text="Use internal SIG-GEN", font=('Courier New', 18), wraplength=200, justify='left', background=self.window['bg'])
        self.lbl_SIGGEN.place(x = 10, y = 10)
        self.chk_SIGGEN_var = IntVar()
        self.chk_SIGGEN = Checkbutton(self.siggenFrame, variable=self.chk_SIGGEN_var, onvalue = 1, offvalue = 0, height=1, width = 1, font='Helvetica 22', command=self.internal_SIGGEN_click, background=self.window['bg'])
        self.chk_SIGGEN.select()
        self.chk_SIGGEN.place(x = 190, y = 10)
        self.lbl_SIGGEN_freq = Label(self.siggenFrame, text="SIG-GEN frequency", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.lbl_SIGGEN_hz = Label(self.siggenFrame, text="Hz", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])

        self.str_SIGGEN_freq = StringVar()
        self.str_SIGGEN_freq.set(DEFAULT_SIGGEN_FREQ)
        self.cmb_SIGGEN_freq = ttk.Combobox(self.siggenFrame, values=list(BINS_BY_INPUT_FRQ.keys()), textvariable=self.str_SIGGEN_freq, font=('Courier New', 18), width=13)
        self.cmb_SIGGEN_freq['state'] = 'readonly'


        self.lbl_SIGGEN_amp = Label(self.siggenFrame, text="SIG-GEN amplitude", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.str_SIGGEN_amp = StringVar()
        self.str_SIGGEN_amp.set(DEFAULT_SIGGEN_AMP)
        self.etr_SIGGEN_amp = Entry(self.siggenFrame, textvariable=self.str_SIGGEN_amp, font=('Courier New', 18), width=14, state=DISABLED)
        self.lbl_SIGGEN_Vrms = Label(self.siggenFrame, text="Vrms", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.internal_SIGGEN_click()

        self.powerFrame = LabelFrame(window, text="", height=180, width=520, background=self.window['bg'])
        self.powerFrame.place(x = 40, y = 840)
        self.lbl_power = Label(self.powerFrame, text="Calculate power", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.lbl_power.place(x = 10, y = 10)
        self.chk_power_var = IntVar()
        self.chk_power = Checkbutton(self.powerFrame, variable=self.chk_power_var, onvalue = 1, offvalue = 0, height=1, width = 1, font='Helvetica 22', command=self.chk_power_click, background=self.window['bg'])
        self.chk_power.select()
        self.chk_power.place(x = 190, y = 10)
        self.lbl_resistance = Label(self.powerFrame, text="dummy load resistance", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.str_resistance = StringVar()
        self.str_resistance.set(DEFAULT_DUMMY_RESISTANCE)
        self.lbl_ohms = Label(self.powerFrame, text="ohms", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.etr_resistance = Entry(self.powerFrame, textvariable=self.str_resistance, font=('Courier New', 18), width=4, state=DISABLED)
        self.chk_power_click()
        # power details
        self.str_power_calculated = StringVar()
        self.lbl_power_calculated = Label(self.powerFrame, textvariable=self.str_power_calculated, font=('Courier New', 18), foreground='blue', background=self.window['bg'])
        self.lbl_power_calculated.place(x = 215, y = 140)


        #y axis bottom value
        self.str_ybottom = StringVar()
        self.str_ybottom.set(BOTTOM_DB)
        self.cmb_ybottom = ttk.Combobox(window, values=[-60, -65, -70, -75, -80,-85, -90, -95, -100, -105, -110, -115, -120], textvariable=self.str_ybottom, font=('Courier New', 18), width=13)
        self.cmb_ybottom['state'] = 'readonly'
        self.cmb_ybottom.place(x = 245, y = 700)
        self.lbl_db2 = Label(window, text = "dB", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_db2.place(x = 450, y = 700)
        self.lbl_ybottom = Label(window, text="Y axis bottom", font=('Courier New', 18), wraplength=200, justify='left', background=self.window['bg'])
        self.lbl_ybottom.place(x = 40, y = 700)

        #start freq
        self.str_startfreq = StringVar()
        self.str_startfreq.set(20)
        self.cmb_startfreq = ttk.Combobox(window, values=[20, 40, 50, 100, 200, 400, 500, 1000], textvariable=self.str_startfreq, font=('Courier New', 18), width=13)
        self.cmb_startfreq['state'] = 'readonly'
        self.cmb_startfreq.place(x = 245, y = 740)
        self.lbl_Hz2 = Label(window, text = "Hz", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_Hz2.place(x = 450, y = 740)
        self.lbl_ystartfreq = Label(window, text="start freq.", font=('Courier New', 18), wraplength=200, justify='left', background=self.window['bg'])
        self.lbl_ystartfreq.place(x = 40, y = 740)

        #stop freq
        self.str_stopfreq = StringVar()
        self.str_stopfreq.set(20000)
        self.cmb_stopfreq = ttk.Combobox(window, values=[2000, 4000, 5000, 10000, 20000], textvariable=self.str_stopfreq, font=('Courier New', 18), width=13)
        self.cmb_stopfreq['state'] = 'readonly'
        self.cmb_stopfreq.place(x = 245, y = 780)
        self.lbl_Hz3 = Label(window, text = "Hz", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_Hz3.place(x = 450, y = 780)
        self.lbl_ystopfreq = Label(window, text="stop  freq.", font=('Courier New', 18), wraplength=200, justify='left', background=self.window['bg'])
        self.lbl_ystopfreq.place(x = 40, y = 780)


        # measurement results
        self.lbl_Fundamental = Label(window, text = "Fundamental", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_Fundamental.place(x = 40, y = 520)
        self.str_hz = StringVar()
        self.etr_hz = Entry(window, textvariable=self.str_hz, font=('Courier New', 18), width=14, state=DISABLED)
        self.etr_hz.place(x = 245, y = 500)
        self.lbl_freq = Label(window, text = "Hz", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_freq.place(x = 450, y = 505)
        self.lbl_vac = Label(window, text = "Vac rms", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_vac.place(x = 450, y = 545)
        self.str_vac = StringVar()
        self.etr_vac = Entry(window, textvariable=self.str_vac, font=('Courier New', 18), width=14, state=DISABLED)
        self.etr_vac.place(x = 245, y = 540)
        self.str_measurement_type = StringVar()

        self.lbl_THD = Label(window, textvariable=self.str_measurement_type, font=('Courier New', 18), background=self.window['bg'])
        self.lbl_THD.place(x = 40, y = 600)
        self.etr_THD.place(x = 245, y = 580)
        self.lbl_db = Label(window, text = "dB", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_db.place(x = 450, y = 585)
        self.lbl_percentage = Label(window, text = "%", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_percentage.place(x = 450, y = 545)
        self.str_perc = StringVar()
        self.etr_perc_THD = Entry(window, textvariable=self.str_perc, font=('Courier New', 18), width=14, state=DISABLED)
        self.etr_perc_THD.place(x = 245, y = 620)

        # TYPE OF MEASUREMENT radio button
        self.rad_var = IntVar()
        self.rad_values = ["THD", "THDN", "SINAD"]
        self.rad_thd = Radiobutton(window, variable=self.rad_var, text=self.rad_values[0], value=0, font=('Courier New', 18), command=self.change_measurement_type, background=self.window['bg'])
        self.rad_thd.invoke()
        self.rad_thd.select()
        self.rad_thd.place(x = 230, y = 60)
        self.rad_thdn = Radiobutton(window, variable=self.rad_var, text=self.rad_values[1], value=1, font=('Courier New', 18), command=self.change_measurement_type, background=self.window['bg'])
        self.rad_thdn.place(x = 230, y = 100)
        self.rad_sinad = Radiobutton(window, variable=self.rad_var, text=self.rad_values[2], value=2, font=('Courier New', 18), command=self.change_measurement_type, background=self.window['bg'])
        self.rad_sinad.place(x = 230, y = 140)

        # buttons
        self.but_quit = Button(window, text="QUIT", command=self.quit, font=('Courier New', 18))
        self.but_quit.place(x=620, y=980)
        self.but_start = Button(window, text="START", command=self.change_state, font=('Courier New', 18))
        self.but_start.place(x=760, y=980)
        self.but_export = Button(window, text="EXPORT", command=self.export, font=('Courier New', 18))
        self.but_export.place(x=900, y=980)

        # label for cursor location
        self.str_harm_details = StringVar()
        self.lbl_harm_details = Label(window, textvariable=self.str_harm_details, font=('Courier New', 18, 'bold'), background=self.window['bg'])
        self.lbl_harm_details.place(x = 600, y = 840)
        self.vline = None
        self.annotate = None
        self.plotline = None
        self.plotpeaks = None
        self.current_peak = None

        #focus
        self.etr_harm_qty.icursor(1)
        self.etr_harm_qty.focus_set()
        #self.but_start.focus_set()
        #END UI

    def start_serial(self):
        if SIM: return
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

    def measure_vca(self):
        if self.chk_power_var.get() == 0: return

        if not SIM:
            #measure Vca in equipment - with VCA mode
            #self.send_cmd(':SENS:FUNC \'VOLT:AC\'')
            #self.send_cmd(':SENS:VOLT:AC:RANG:AUTO ON')
            #self.send_cmd(':SENS:VOLT:AC:DET:BAND 300') # 300Hz-300kHz
            #self.send_cmd(':SENS:VOLT:AC:NPLC 1') # FAST is 0.1 in AC. 1 is MED and 10 is SLOW.
            #self.send_cmd(':SENS:VOLT:AC:DIG 4') # must be 4-7
            #self.send_cmd(':SENS:VOLT:AC:AVER:STAT OFF')
            #self.send_cmd(':TRIG:COUN 1')
            #res = self.send_cmd(':READ?')

            #take Vca from previous measurement - taken on DIST mode
            res = format(self.fundamental_vrms, '.3f')


            resp = float(res) ** 2 / int(self.str_resistance.get())
            self.str_power_calculated.set(format(float(res), '.3f') + "Vrms - " + format(resp, '.2f') + "Wrms")
        else:
            self.str_power_calculated.set("1.52 Wrms")


    #enable en setup internal SIG GEN
    def enable_siggen(self):
        if not SIM and self.chk_SIGGEN_var.get() == 1:
            if DEBUG: print("Setting up internal SIGGEN")
            #self.send_cmd(':SENS:DIST:FREQ:AUTO OFF')
            self.send_cmd(':OUTP:FREQ ' + self.str_SIGGEN_freq.get()) #;set frequency in Hz
            self.send_cmd(':OUTP:IMP HIZ') #;set high impedance source
            self.send_cmd(':OUTP:AMPL ' + self.str_SIGGEN_amp.get()) #;set amplitude in Vrms
            self.send_cmd(':OUTP:CHAN2 ISINE') #;select inverted sine
            self.send_cmd(':OUTP ON') #;turn on source

    def setup_thd_measurement(self):
        if DEBUG: print("setup THD measurement")
        if SIM: return
        self.send_cmd(':SENS:FUNC \'DIST\'')
        self.send_cmd(':SENS:DIST:TYPE ' + self.rad_values[int(self.rad_var.get())])
        self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(int(self.str_harm_qty.get())))
        self.send_cmd(':UNIT:DIST PERC')
        self.send_cmd(':SENS:DIST:SFIL NONE')
        self.send_cmd(':SENS:DIST:RANG:AUTO ON')
        #self.send_cmd(':SENS:DIST:FREQ:AUTO ON')

    # FFT Bin number to frequency midpoint empirically derived
    # since I can't find documentation on the FFT:BINS cmd
    #
    def bin_to_freq_mid(self, x):
        if fft_bin_width == 20:
            m = 20
            b = 20
        else:
            m = non_50_m
            b = non_50_b

        return m*x + b


#    def freq_to_bin(x):
#        if fft_bin_width == 20:
#            m = 1.0/20.0
#            b = -1.0
#        else:
#            m = 1.0/non_50_m
#            b = - non_50_b/non_50_m
#        return int(m*x + b)


    def measure_thd(self):
        """
        *RST                                       ;start from defaults
        :SENS:FUNC 'DIST'                          ;select distortion function
        :SENS:DIST:TYPE THD                        ;select THD type
        #:SENS:DIST:TYPE THDN                       ;select THDN type
        #:SENS:DIST:TYPE SINAD                      ;select SINAD type
        :SENS:DIST:HARM 06                         ;set highest harmonic to 6
        :UNIT:DIST:PERC                            ;select percent distortion
        #:SENS:DIST:FREQ:ACQuire                    ;acquire the frequency once
        :SENS:DIST:FREQ:AUTO ON                    ;turn AUTO on or off
        :SENS:DIST:SFIL NONE                       ;no shaping filter
        :SENS:DIST:RANG:AUTO ON                    ;turn on autoranging
        #:SENS:DIST:DIG 6')                         ; resolution - 4 to 7.
        :READ?                                     ;trigger one reading, the distortion measurement can be read from the bus
        #:SENS:DIST:FREQ:SET?                       ;return frequency calculated
        #:SENS:DIST:RMS?                            ;return the ACV RMS reading of input waveform
        :SENS:DIST:THD?                            ;return the THD reading for the last triggered reading
        #:UNIT:DIST:DB                              ;select DB distortion
        #:SENS:DIST:THDN?                           ;return the THD+N reading (number of harmonics depends on the last setting of harmonic number)
        #:SENS:DIST:HARM:MAGN? 02,06                ;query individual harmonic levels
        """
        if SIM:
            new_textHz = "1002.52412"
            new_textVac = "1.361287"
            new_textdB = "-50.152312"
            new_textperc = "12.17492"
            self.str_hz.set(new_textHz)
            self.str_vac.set(new_textVac)
            self.str_dB.set(new_textdB)
            self.str_perc.set(new_textperc)
            self.fundamental_vrms = float(new_textVac)
            self.fundamental_freq = new_textHz
        else:

            self.setup_thd_measurement()
            #if self.str_SIGGEN_freq != "20" and fft_bin_width != 20: self.send_cmd(':SENS:DIST:FREQ:AUTO ON')
            self.send_cmd(':SENS:DIST:FREQ:AUTO ON')

            self.send_cmd(':UNIT:DIST PERC')

            # return dist in percent
            res = self.send_cmd(':READ?')
            if DEBUG: print("## returned dist %", res)
            if res != '': res = format(float(res), '.6f')
            if DEBUG: print("% dist: " + res)

            # return fundamental amplitude in Vrms
            res = self.send_cmd(':SENS:DIST:RMS?')
            if res != '': self.fundamental_vrms = float(res)
            res = format(self.fundamental_vrms, '.6f')
            self.str_vac.set(res)
            if DEBUG: print("fundamental amplitude in Vrms: " + res)

            # return frequency calculated
            res =  self.send_cmd(':SENS:DIST:FREQ:SET?')
            self.fundamental_freq = format(float(res), '.6f')
            self.str_hz.set(self.fundamental_freq)
            if DEBUG: print("fundamental freq in Hz: " + self.fundamental_freq)

            # return THD/THDN %
            self.dist_perc = format(float(self.send_cmd(':SENS:DIST:' + self.rad_values[int(self.rad_var.get())] + '?')), '.6f')
            self.str_perc.set(self.dist_perc)
            if DEBUG: print("measured [%] " + self.rad_values[int(self.rad_var.get())] + ": " + self.dist_perc + " %")

            # return THD/THDN in dB
            self.send_cmd(':UNIT:DIST DB')
            res = self.send_cmd(':READ?')
            res = format(float(res), '.6f')
            self.str_dB.set(res)
            self.dist_db = format(float(self.send_cmd(':SENS:DIST:' + self.rad_values[int(self.rad_var.get())] + '?')), '.6f')
            #if DEBUG:
            #    print("dist in dB: " + res)
            #    print("measured [dB] " + self.rad_values[int(self.rad_var.get())] + ": " + self.dist_db + " dB")

            self.setup_thd_measurement()
            #if self.str_SIGGEN_freq == "20" and fft_bin_width == 20:
            #if fft_bin_width == 20:
            self.send_cmd(':SENS:DIST:FREQ 20') # attempt 20 Hz bins
            self.send_cmd(':INIT')
            self.send_cmd('*OPC?')

            #res = self.send_cmd(':SENS:DIST:RMS?')
            #res = format(res, '.6f')
            #if DEBUG: print("new RMS amplitude in Vrms: " + res)

            self.avoid_exit=1
            #TODO1
            if DEBUG: print("input freq: " , self.str_SIGGEN_freq.get())
            if DEBUG: print("bins: " , BINS_BY_INPUT_FRQ[int(self.str_SIGGEN_freq.get())])
            binsn = BINS_BY_INPUT_FRQ[int(self.str_SIGGEN_freq.get())]
            #bins_raw = [float(i) for i in self.send_cmd(':DIST:FFT:BINS? 1,1023')]
            bins_raw = [float(i) for i in self.send_cmd(':DIST:FFT:BINS? 1,%s' % binsn)]

            self.avoid_exit=0
            # For some reason, the Keithley 2015 returns 9.91e+37 when it's out of
            # range, prune these values
            for i in range(0, len(bins_raw)):
                x = bins_raw[i]
                if x > 200:
                    print("Pruning FFT bins after and including {}".format(i))
                    bins_raw=bins_raw[0:i]
                    break

            max_mag = max(bins_raw)
            if DEBUG: print("Maximum magnitude of FFT = {}".format(max_mag))
            # Normalize FFT
            bins = [i - max_mag for i in bins_raw]
            self.x1 = []
            self.y1 = []
            bin_ref = 0
            bin_freq = 0

            for i in range(0, len(bins)):
                freq = self.bin_to_freq_mid(i)
                if math.isclose(bins[i], 0, rel_tol=1e-5):
                    bin_ref = i
                    bin_freq = freq
                #print("{}, {}, {}".format(i, freq, bins[i]))
                self.x1.append(freq)
                self.y1.append(bins[i])

             # bnoise is garbage at bin width = 20
             #if fft_bin_width != 20:
             #    bnoise = float(dmm.cmd(':SENSe:DISTortion:BNoIse?'))
             #else:
             #    bnoise = 0
             #bnoise_uv = bnoise * 1E6
             #print('Background Noise: {} uVrms'.format(float(bnoise_uv)))


    def chk_power_click(self):
        if self.chk_power_var.get() == 0:
            self.lbl_resistance.place_forget()
            self.lbl_ohms.place_forget()
            self.etr_resistance.config(state = 'disabled')
            self.etr_resistance.place_forget()
            self.str_power_calculated.set("")
        else:
            self.etr_resistance.config(state = 'normal')
            self.etr_resistance.icursor(len(self.str_resistance.get()))
            self.etr_resistance.focus_set()
            self.lbl_resistance.place(x = 10, y = 80)
            self.lbl_ohms.place(x = 280, y = 80)
            self.etr_resistance.place(x = 215, y = 80)

    def internal_SIGGEN_click(self):
        if self.chk_SIGGEN_var.get() == 0:
            #self.etr_SIGGEN_freq.config(state = 'disabled')
            self.cmb_SIGGEN_freq.config(state = 'disabled')
            self.lbl_SIGGEN_freq.place_forget()
            #self.etr_SIGGEN_freq.place_forget()
            self.cmb_SIGGEN_freq.place_forget()
            self.etr_SIGGEN_amp.config(state = 'disabled')
            self.lbl_SIGGEN_amp.place_forget()
            self.etr_SIGGEN_amp.place_forget()
            self.lbl_SIGGEN_hz.place_forget()
            self.lbl_SIGGEN_Vrms.place_forget()
        else:
            #self.etr_SIGGEN_freq.config(state = 'normal')
            self.cmb_SIGGEN_freq.config(state = 'readonly')
            self.lbl_SIGGEN_freq.place(x = 10, y = 80)
            #self.etr_SIGGEN_freq.place(x = 215, y = 80)
            self.cmb_SIGGEN_freq.place(x = 215, y = 80)
            ##self.etr_SIGGEN_freq.icursor(len(self.str_SIGGEN_freq.get()))
            #self.etr_SIGGEN_freq.focus_set()
            self.cmb_SIGGEN_freq.focus_set()
            self.etr_SIGGEN_amp.config(state = 'normal')
            self.lbl_SIGGEN_amp.place(x = 10, y = 140)
            self.etr_SIGGEN_amp.place(x = 215, y = 140)
            self.lbl_SIGGEN_hz.place(x = 420, y = 80)
            self.lbl_SIGGEN_Vrms.place(x = 420, y = 140)

    def change_measurement_type(self):
        self.str_measurement_type.set(self.rad_values[int(self.rad_var.get())])
        if (self.rad_var.get() == 2): #SINAD
            self.lbl_percentage.place_forget()
            self.etr_perc_THD.place_forget()
        else:
            self.lbl_percentage.place(x = 450, y = 625)
            self.etr_perc_THD.place(x = 245, y = 620)

    def quit(self):
        if (not SIM and self.ser.isOpen()):
            self.ser.close()
        if self.running == True:
            self.change_state()
        #self.thread.join()
        Tk().quit()

    def change_state(self):
        #while (self.avoid_exit):
        #    self.fig.canvas.draw_idle()
            #self.fig.canvas.draw()

        if self.running == True:
            if not SIM and self.chk_SIGGEN_var.get() == 1:
                if DEBUG: print("Turning off SIGGEN")
                self.send_cmd(':OUTP OFF') #;turn off source
                time.sleep(2)
            self.running = False
            self.but_start['text'] = "START"
            self.etr_harm_qty.config(state= "normal")
            self.chk_SIGGEN.config(state = 'normal')
            self.chk_power.config(state = 'normal')
            self.rad_thd.config(state = 'normal')
            self.rad_thdn.config(state = 'normal')
            self.rad_sinad.config(state = 'normal')
            self.cmb_SIGGEN_freq.config(state = 'readonly')
            self.etr_SIGGEN_amp.config(state = 'normal')
            self.etr_resistance.config(state = 'normal')
            self.etr_harm_qty.focus_set()

        else:
            self.measure_vca()
            self.enable_siggen()
            self.measure_thd() #and get fft bins
            self.running = True
            if (not self.plot_packed): self.plot()
            self.but_start['text'] = "STOP "
            self.etr_harm_qty.config(state = 'disabled')
            self.chk_SIGGEN.config(state = 'disabled')
            self.chk_power.config(state = 'disabled')
            self.rad_thd.config(state = 'disabled')
            self.cmb_SIGGEN_freq.config(state = 'disabled')
            self.etr_SIGGEN_amp.config(state = 'disabled')
            self.rad_thdn.config(state = 'disabled')
            self.rad_sinad.config(state = 'disabled')
            self.etr_resistance.config(state = 'disabled')
            self.replot_thread()
            self.measure_thread()

    def plot(self):
        self.fig, ax = plt.subplots(figsize=(13, 7))
        #self.fig.tight_layout()
        plt.rcParams['toolbar'] = 'None'
        self.fig.set_facecolor(self.window['bg'])
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.set(xscale="log")
        ax.set_facecolor('xkcd:black')
        ax.set_ylabel('FFT Bin Magnitude, dB', fontsize=12, loc='center')
        ax.set_xlabel('Frequency, Hz', fontsize=12, loc='center')
        ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        #ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        ax.set_xlim([20, 20000])
        ax.yaxis.set_ticks(np.arange(int(self.str_ybottom.get()), 0, 10), fontsize=20) # la escala del eje Y cada 0.5 entre 0 y 5
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        #ax.tick_params(axis='x',which='minor',direction='out',bottom=True,length=5)
        ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        ax.set_ylim([int(self.str_ybottom.get()), 0])

        #self.plotdata = ax.semilogx(self.x1, self.y1, '-', color='limegreen')
        #ax.semilogx(self.x1, self.y1, '-', color='tab:blue')
        ax.semilogx(self.x1, self.y1, '-', color='dodgerblue')
        # this set xticks have to be after semilogx
        ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        self.plotline = ax.lines[len(ax.lines)-1]
        self.peaks_indexes, peak_dict = find_peaks(self.y1, height=(None, None), prominence=5)
        self.plot_packed = 1

        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().place(relx=.65, rely=.46, anchor="c")
        canvas.mpl_connect('scroll_event', self.mousewheel_move)
        canvas.mpl_connect('motion_notify_event', self.print_details)

        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)

        canvas.draw()
        canvas.flush_events()
        #canvas.draw_idle()
        #do not use:
        #canvas.start_event_loop(0.05)

        #ax.figure.canvas.draw()
        #ax.figure.canvas.start_event_loop(0.05)
        #ax.figure.canvas.draw()
        #ax.figure.canvas.flush_events()
        return

    def replot(self):
        ax = self.fig.get_axes()[0]
        try:
            if self.on_mouse_routine == 0: self.fig.tight_layout()
        except:
             #print("error 2 tight layout")
             pass

        #ax.lines.pop(0) #remove first line from graph insted of clearing
        if self.plotline is not None:
            try:
                ax.lines.pop(ax.lines.index(self.plotline))
            except:
                #print("error 3 replot_")
                #print(ax.lines.index(self.plotline))
                pass

        #plot peak points
        left, right = ax.get_xlim()
        l_nearest = self.find_nearest(self.x1, value=left)
        r_nearest = self.find_nearest(self.x1, value=right)
        l_index = self.x1.index(l_nearest)
        r_index = self.x1.index(r_nearest)
        self.peaks_indexes, peak_dict = find_peaks(self.y1[l_index:r_index+1], height=(None, None), prominence=5)

        #self.peaks_indexes, peak_dict = find_peaks(self.y1, height=(None, None))
        #prom = peak_dict['prominences']
        peak_heights = peak_dict['peak_heights']

        #tenmax = nlargest(10, prom)
        tenmax = nlargest(10, peak_heights)

        if tenmax != None:
            self.peaks_indexes = np.take(self.peaks_indexes, np.where(np.isin(peak_heights, tenmax))[0])

            # remove current peak annotation
            if self.annotate is not None:
                self.annotate.remove()
                self.annotate = None

            if len(self.peaks_indexes) > 0:
                if self.plotpeaks is not None:
                    for p in self.plotpeaks:
                        p.remove()
                self.plotpeaks = ax.plot( operator.itemgetter(*self.peaks_indexes.tolist())(self.x1[l_index:r_index+1]),
                                          operator.itemgetter(*self.peaks_indexes.tolist())(self.y1[l_index:r_index+1]) , "P", color='cyan');

                if self.current_peak is not None and self.y1[self.x1.index(self.current_peak)] != 0:
                    # plot current peak annotation
                    self.annotate = ax.annotate("%s, %s" % ( str(self.current_peak), format(self.y1[self.x1.index(self.current_peak)], '.2f')),
                            xy = (self.current_peak, self.y1[self.x1.index(self.current_peak)]),
                            xytext = (self.current_peak, self.y1[self.x1.index(self.current_peak)]+5), color='cyan', fontsize=12)


        #redraw FFT curve
        left, right = ax.get_xlim()
        #ax.semilogx(self.x1, self.y1, '-', color='limegreen')
        #ax.semilogx(self.x1, self.y1, '-', color='tab:blue')
        ax.semilogx(self.x1, self.y1, '-', color='dodgerblue')
        ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        ax.set_xlim([left, right])
        self.plotline = ax.lines[len(ax.lines)-1]
        ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        ax.yaxis.set_ticks(np.arange(int(self.str_ybottom.get()), 0, 10), fontsize=20) # la escala del eje Y cada 0.5 entre 0 y 5
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.set_ylim([int(self.str_ybottom.get()), 0])
        ax.set_xlim([float(self.str_startfreq.get()), float(self.str_stopfreq.get())])
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))

        try:
            if self.on_mouse_routine == 0 and ax != None:
                ax.figure.canvas.draw()
        except:
            print("error 2 replot redrawing")
            pass

    def export(self):
        if not len(self.x1):
            messagebox.showerror("Export error", "No data to export")
        else:
            dict = {'bin': self.x1,'dB': self.y1}
            pd.DataFrame(dict).to_csv('fft.csv', index=False)
            messagebox.showinfo("Export", "Export completed - %s" % 'fft.csv')

    def _measure_thread(self):
        while self.running:
            if DEBUG: print("calculate power");
            self.measure_vca()
            if DEBUG: print("remeasuring THD");
            self.measure_thd() #and get fft bins

    def _replot_thread(self):
        if DEBUG: print("THD replot thread running");

        while self.running:
            if DEBUG: print("re plotting")

            if SIM:
                 #time.sleep(UPDATE_INTERVAL)
                 self.y1[2]-= 2
                 if self.y1[2] <= -90: self.y1[2]-= -75

            self.replot()

        if DEBUG: print("END running THD replot thread");


    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    def replot_thread(self):
        self.thread = threading.Thread(target=self._replot_thread)
        self.thread.start()

    def measure_thread(self):
        self.mthread = threading.Thread(target=self._measure_thread)
        self.mthread.start()

    def button_press_callback(self, event):
        self.leftb=1
        self.xinit_pos=event.xdata
        #print(event)

    def button_release_callback(self, event):
        self.leftb=0
        self.xinit_pos=0
        #print(event)

    def print_details(self, event):
        if not len(self.x1): return
        if self.but_start['text'] == "ABORT": return
        ax = self.fig.get_axes()[0]

        #mouse left button pressed. changing left and right limits
        if self.leftb == 1:
            freq_list = list()
            for d in range(1, 5, 1):
                for x in range(2, 11, 1):
                    freq_list.append(x * (10 ** d))
                    if d == 4 and x == 2: break

            self.xcurr_pos = event.xdata
            if self.xinit_pos == None or self.xcurr_pos == None: return
            #print(self.xinit_pos)
            #print(self.xcurr_pos)
            left, right = ax.get_xlim()

            #muevo para la derecha. disminuye derecha e izq
            if (self.xcurr_pos >= self.xinit_pos):
                span=self.xcurr_pos - self.xinit_pos
                #print("der")
                new_right = right-span
                if new_right > 20000: new_right = 20000
                if right != new_right and left != new_right:
                    ax.set_xlim(right=new_right)
                    self.str_stopfreq.set(new_right)

            #muevo para la izq. aumento el de la derecha e izq.
            else:
                span=self.xinit_pos - self.xcurr_pos
                #print("izq")
                new_left = left+span
                if new_left < 20: new_left = 20
                if left != new_left and new_left != right:
                    ax.set_xlim(left=new_left)
                    self.str_startfreq.set(new_left)

            return

        self.on_mouse_routine = 1
        if event.inaxes is not None:
            #show coordinates of cursor
            #x = event.xdata
            #y = format(event.ydata, '.2f')

            #keep track of 4 closest x values around cursor
            closest = nsmallest(4, self.x1, key=lambda x: abs(x-event.xdata))
            #if DEBUG: print("input freq: " , self.str_SIGGEN_freq.get())

            # the closest 1
            #xval = min(self.x1, key=lambda xval:abs(xval-event.xdata))
            xval = closest[0]
            x_pos = self.x1.index(xval)
            y = self.y1[x_pos]

            self.str_harm_details.set("cursor: " + str(xval).rjust(6, " ") + " Hz" + ', '
                                      + str('{0:.2f}'.format(y)).ljust(4, " ") + " dB")

            # draw line over closest peak around cursor
            left, right = ax.get_xlim()
            l_nearest = self.find_nearest(self.x1, value=left)
            r_nearest = self.find_nearest(self.x1, value=right)
            l_index = self.x1.index(l_nearest)
            r_index = self.x1.index(r_nearest)
            self.peaks_indexes, peak_dict = find_peaks(self.y1[l_index:r_index+1], height=(None, None), prominence=5)
            peak_heights = peak_dict['peak_heights']
            tenmax = nlargest(10, peak_heights)
            if tenmax != None: self.peaks_indexes = np.take(self.peaks_indexes, np.where(np.isin(peak_heights, tenmax))[0])
            if len(self.peaks_indexes.tolist())>1:
                peaksx = operator.itemgetter( *self.peaks_indexes.tolist())( self.x1[l_index:r_index+1])
                xpeak = min(peaksx, key=lambda xval:abs(xval-event.xdata))

                #remove current peaks line in graph
                if self.vline is not None: self.vline.remove()

                #plot the vertical line over peak
                #TODO move this to replot?
                self.vline = ax.axvline(x=xpeak, color='red', ls=':', lw=2)

                new_data = "\n%s %s Hz, %s dB" % ("peak:".ljust(7, " "), str(xpeak).rjust(6, " "), str('{0:.2f}'.format(self.y1[self.x1.index(xpeak)])).rjust(6, " "))
                self.str_harm_details.set(self.str_harm_details.get() + new_data)

                self.current_peak = xpeak

            #window.after(500, self.fig.canvas.draw())
            #ax.figure.canvas.draw()
            #fig = plt.figure()
            #fig.canvas.flush_events()
            #plt.pause(0.000000000001)
            #self.fig.canvas.draw()
            self.on_mouse_routine = 0

    def mousewheel_move(self, event):
        self.on_mouse_routine = 1
        freq_list = list()
        for d in range(1, 5, 1):
            for x in range(2, 11, 1):
                freq_list.append(x * (10 ** d))
                if d == 4 and x == 2: break

        ax = self.fig.get_axes()[0]
        left, right = ax.get_xlim()

        #sit in valid position according to previous freq_list values
        difference = lambda freq_list : abs(freq_list - left)
        left = min(freq_list, key=difference)
        difference = lambda freq_list : abs(freq_list - right)
        right = min(freq_list, key=difference)
        le = freq_list.index(left)
        ri = freq_list.index(right)

        new_left = left
        new_right = right

        #TODO
        #se divide la pantalla en 4 |-|-|-|-|
        #si está en extremo izq, no se mueve left y si right
        #si está en extremo derecho, no se mueve right y si left
        #en los otros dos se aumentan y disminuyen ambos
        #width = right - left
        #forth = width / 4
        #xcursor = event.x
        #print("\n\nleft:%d, xcursor:%d, width:%d, forth: %d, pos:%d" % (left, xcursor, width, forth, position))

        if event.button == "up":
            if le < len(freq_list): new_left = freq_list[le+1]
            if ri+1 > 0: new_right = freq_list[ri-1]

        if event.button == "down":
            if le > 0: new_left = freq_list[le-1]
            if ri+1 < len(freq_list): new_right = freq_list[ri+1]

        if new_left > new_right:
            print("cannot zoom no longer")
            return

        if left != new_left and right != new_right and new_left != new_right:
            ax.set_xlim(left=new_left)
            self.str_startfreq.set(new_left)
        if left != new_left and right != new_right and new_left != new_right:
            ax.set_xlim(right=new_right)
            self.str_stopfreq.set(new_right)
        self.on_mouse_routine = 0


window = Tk()
start = mclass(window)
start.measure_thread()
start.replot_thread()
window.mainloop()
