# Some settings
SIM = 0 # do not interact with equipment, just sim data
DEBUG = 0 # print debug data on terminal
DISPLAY = 1 # display on or off
UPDATE_INTERVAL= 1 # only used on sim.
DEFAULT_QTY_HARM = 4 # default number of harmonics to plot in graph
DEFAULT_SIGGEN_FREQ = 1000 # in Hz
DEFAULT_SIGGEN_AMP = 2 # in Vrms
DEFAULT_DUMMY_RESISTANCE = 8 # in ohms
BOTTOM_DB = -100 # bottom dB in graph

import matplotlib
from matplotlib.widgets import TextBox
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import *
import pandas as pd
import time
import math
import threading
import tkinter.messagebox
import serial
import numpy as np #for data sim

class mclass:
    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window

        self.running = False
        self.plot_packed = 0 # avoid a re pack when refreshing plot
        self.fundamental_vrms = float(0) # set some initial value

        self.str_measurement_type = StringVar()
        if SIM:
            np.random.seed(42) # for data sim
        else:
            self.start_serial()

        #setup UI
        self.window['bg'] = 'silver'

        self.lbl_title = Label(window, text='Keithley 2015 - THD measurement', fg='#1C5AAC', font=('Courier New', 24, 'bold'), background=self.window['bg'])
        self.lbl_title.pack(ipady=15, expand=False, side=TOP)

        self.lbl_harm_qty = Label(window, text = "Measure:", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_harm_qty.place(x = 40, y = 100)

        self.lbl_harm_qty = Label(window, text = "Harm. Qty", font=('Courier New', 18), background=self.window['bg'])
        self.lbl_harm_qty.place(x = 40, y = 200)
        self.str_harm_qty = StringVar()
        self.str_harm_qty.set(DEFAULT_QTY_HARM)
        self.str_dB = StringVar()
        self.etr_THD = Entry(window, textvariable=self.str_dB, font=('Courier New', 18), width=14, state=DISABLED)
        self.etr_harm_qty = Entry(window, textvariable=self.str_harm_qty, font=('Courier New', 18), width=14)
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
        self.lbl_SIGGEN_hz = Label(self.siggenFrame, text="Hz", font=('Courier New', 18), wraplength=150, justify='left')
        self.str_SIGGEN_freq = StringVar()
        self.str_SIGGEN_freq.set(DEFAULT_SIGGEN_FREQ)
        self.etr_SIGGEN_freq = Entry(self.siggenFrame, textvariable=self.str_SIGGEN_freq, font=('Courier New', 18), width=14, state=DISABLED)
        self.lbl_SIGGEN_amp = Label(self.siggenFrame, text="SIG-GEN amplitude", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.str_SIGGEN_amp = StringVar()
        self.str_SIGGEN_amp.set(DEFAULT_SIGGEN_AMP)
        self.etr_SIGGEN_amp = Entry(self.siggenFrame, textvariable=self.str_SIGGEN_amp, font=('Courier New', 18), width=14, state=DISABLED)
        self.lbl_SIGGEN_Vrms = Label(self.siggenFrame, text="Vrms", font=('Courier New', 18), wraplength=150, justify='left', background=self.window['bg'])
        self.internal_SIGGEN_click()

        self.powerFrame = LabelFrame(window, text="", height=180, width=520, background=self.window['bg'])
        self.powerFrame.place(x = 30, y = 700)
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
        self.etr_resistance = Entry(self.powerFrame, textvariable=self.str_resistance, font=('Courier New', 18), width=14, state=DISABLED)
        self.chk_power_click()

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
        self.but_quit.place(x=120, y=980)
        self.but_start = Button(window, text="START", command=self.change_state, font=('Courier New', 18))
        self.but_start.place(x=245, y=980)

        # harmonic details upon click
        self.str_harm_details = StringVar()
        self.lbl_harm_details = Label(window, textvariable=self.str_harm_details, font=('Courier New', 18, 'bold'), background=self.window['bg'])
        self.lbl_harm_details.place(x = 1080, y = 920)

        # power details
        self.str_power_calculated = StringVar()
        self.lbl_power_calculated = Label(window, textvariable=self.str_power_calculated, font=('Courier New', 18, 'bold'), foreground='red', background=self.window['bg'])
        self.lbl_power_calculated.place(x = 1280, y = 965)

        #focus
        self.etr_harm_qty.icursor(1)
        self.etr_harm_qty.focus_set()
        #self.but_start.focus_set()
        #END UI

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
        #TODO
        #self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(int(self.str_harm_qty.get())))
        self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(DEFAULT_QTY_HARM))
        self.send_cmd(':UNIT:DIST PERC')
        self.send_cmd(':SENS:DIST:SFIL NONE')
        self.send_cmd(':SENS:DIST:RANG:AUTO ON')
        self.send_cmd(':SENS:DIST:FREQ:AUTO ON')

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
            #this was moved to setup_thd_measurement()
            #self.send_cmd(':SENS:FUNC \'DIST\'')
            #self.send_cmd(':SENS:DIST:TYPE ' + self.rad_values[int(self.rad_var.get())])
            #self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(int(self.str_harm_qty.get())))
            self.send_cmd(':UNIT:DIST PERC')
            #self.send_cmd(':SENS:DIST:SFIL NONE')
            #self.send_cmd(':SENS:DIST:RANG:AUTO ON')
            #self.send_cmd(':SENS:DIST:FREQ:AUTO ON')

            # return dist in percent
            res = self.send_cmd(':READ?')
            res = format(float(res), '.6f')
            if DEBUG: print("% dist: " + res)

            # return fundamental amplitude in Vrms
            res = self.send_cmd(':SENS:DIST:RMS?')
            self.fundamental_vrms = float(res)
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
            if DEBUG:
                print("dist in dB: " + res)
                print("measured [dB] " + self.rad_values[int(self.rad_var.get())] + ": " + self.dist_db + " dB")

            # measure each harm
            self.data = pd.DataFrame(columns = ['harm', 'dB'])
            self.data = pd.concat([self.data, pd.DataFrame({'harm' : ['h1'], 'dB' : [0]})], ignore_index=True)
            for h in range(2, int(self.str_harm_qty.get())+1):
                res = self.send_cmd(':SENS:DIST:HARM:MAGN? {str_h},{str_h}'.format(str_h="{0:02d}".format(int(h))))
                res = format(float(res), '.6f')
                harm_mag_db = float(res)
                harm_perc=pow(10, harm_mag_db/20)*100
                harm_mag_vrms=harm_perc/100*self.fundamental_vrms
                #TODO
                #harm_fq = float(self.send_cmd('SENS:DIST:HARM:FREQ? 02,02'))   #;not valid command?
                if DEBUG:
                    print("harm %d magnitude: " % h + format(harm_mag_db, '.6f') + " dB")
                    print("harm %d magnitude: " % h  + format(harm_perc, '.6f') + " %")
                    print("harm %d magnitude: " % h + format(harm_mag_vrms, '.6f') + " Vrms")
                    #print("harm %d freq: " % h + format(harm_fq, '.6f') + " Hz")
                self.data = pd.concat([self.data, pd.DataFrame({'harm' : ['h%d' % h], 'dB' : [float(format(harm_mag_db, '.6f'))]})], ignore_index=True)

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
            self.lbl_ohms.place(x = 420, y = 80)
            self.etr_resistance.place(x = 215, y = 80)

    def internal_SIGGEN_click(self):
        if self.chk_SIGGEN_var.get() == 0:
            self.etr_SIGGEN_freq.config(state = 'disabled')
            self.lbl_SIGGEN_freq.place_forget()
            self.etr_SIGGEN_freq.place_forget()
            self.etr_SIGGEN_amp.config(state = 'disabled')
            self.lbl_SIGGEN_amp.place_forget()
            self.etr_SIGGEN_amp.place_forget()
            self.lbl_SIGGEN_hz.place_forget()
            self.lbl_SIGGEN_Vrms.place_forget()
        else:
            self.etr_SIGGEN_freq.config(state = 'normal')
            self.lbl_SIGGEN_freq.place(x = 10, y = 80)
            self.etr_SIGGEN_freq.place(x = 215, y = 80)
            self.etr_SIGGEN_freq.icursor(len(self.str_SIGGEN_freq.get()))
            self.etr_SIGGEN_freq.focus_set()
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

    def replot(self):
        if SIM:
            #sim change in data
            value = np.random.uniform(-1,1)
            self.data.iloc[1, self.data.columns.get_loc('dB')] += 15 * value
            value = np.random.uniform(-1,1)
            self.data.iloc[2, self.data.columns.get_loc('dB')] += 8 * value
            value = np.random.uniform(-1,1)
            self.data.iloc[3, self.data.columns.get_loc('dB')] += 12 * value
            if self.data.iloc[1, self.data.columns.get_loc('dB')] >= 0:
                self.data.iloc[1, self.data.columns.get_loc('dB')] = -75
            if self.data.iloc[2, self.data.columns.get_loc('dB')] >= 0:
                self.data.iloc[2, self.data.columns.get_loc('dB')] = -90
            if self.data.iloc[3, self.data.columns.get_loc('dB')] >= 0:
                self.data.iloc[3, self.data.columns.get_loc('dB')] = -80
            if self.data.iloc[1, self.data.columns.get_loc('dB')] <= -100:
                self.data.iloc[1, self.data.columns.get_loc('dB')] = -75
            if self.data.iloc[2, self.data.columns.get_loc('dB')] <= -100:
                self.data.iloc[2, self.data.columns.get_loc('dB')] = -90
            if self.data.iloc[3, self.data.columns.get_loc('dB')] <= -100:
                self.data.iloc[3, self.data.columns.get_loc('dB')] = -80
            if DEBUG:
                print("---------")
                print(self.data.dB)
                print("---------")
            #end of data sim

        #now replot
        ax = self.fig.get_axes()[0]
        ax.clear()         # clear axes from previous plot !!!!
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.bar(self.data.harm, self.data.dB - BOTTOM_DB, bottom=BOTTOM_DB, color='darkorange', align='center', width=.65, alpha=0.6, picker=True)
        ax.margins(x=0)
        ax.margins(y=0)
        ax.set_ylim([BOTTOM_DB, 0])
        #ax.set_xticks(range(PLOT_MAX_HARM))
        ax.set_xticks(range(int(self.str_harm_qty.get())+1))
        ax.set_yticks(range(BOTTOM_DB, 10, 10)) # la escala del eje Y cada 10 entre 0 y -100dB
        ax.set_xticks([x - 0.5 for x in ax.get_xticks()], minor='true')
        ax.set_yticks([y - 0.5 for y in ax.get_yticks()][1:], minor='true')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.set_xlabel('harmonics', fontsize=20, loc='center')
        ax.set_facecolor('xkcd:black')
        ax.grid(color = 'slategray', linestyle = '--', linewidth = 0.5, which='minor')
        #self.fig.canvas.mpl_connect('button_press_event', self.print_harm_details)
        self.fig.canvas.mpl_connect('motion_notify_event', self.print_harm_details)
        self.fig.canvas.draw()

    def change_state(self):
        ## TODO: check here that internal WG freq is valid
        ## TODO: check qty of harm is numberic
        ## TODO: check ohms is numeric and 4, 8 or 16 ohms

        if self.running == True:
            self.running = False
            self.but_start['text'] = "START"
            self.etr_harm_qty.config(state= "normal")
            self.chk_SIGGEN.config(state = 'normal')
            self.chk_power.config(state = 'normal')
            self.rad_thd.config(state = 'normal')
            self.rad_thdn.config(state = 'normal')
            self.rad_sinad.config(state = 'normal')
            self.etr_SIGGEN_freq.config(state = 'normal')
            self.etr_SIGGEN_amp.config(state = 'normal')
            self.etr_resistance.config(state = 'normal')
            self.etr_harm_qty.focus_set()
        else:
            self.measure_vca()
            self.enable_siggen()
            self.setup_thd_measurement()
            self.measure_thd()
            self.running = True
            if (not self.plot_packed): self.plot()
            self.but_start['text'] = "STOP "
            self.etr_harm_qty.config(state = 'disabled')
            self.chk_SIGGEN.config(state = 'disabled')
            self.chk_power.config(state = 'disabled')
            self.rad_thd.config(state = 'disabled')
            self.etr_SIGGEN_freq.config(state = 'disabled')
            self.etr_SIGGEN_amp.config(state = 'disabled')
            self.rad_thdn.config(state = 'disabled')
            self.rad_sinad.config(state = 'disabled')
            self.etr_resistance.config(state = 'disabled')
            self.replot_thread()

    def print_harm_details(self, event):
        """for use with click event
        ax = event.inaxes
        x = event.xdata
        lbls = ax.get_xticklabels()
        idx = int(x.round())
        lbl = lbls[idx]

        if lbl.get_text() == "h1":
            self.str_harm_details.set(lbl.get_text() + '\n' + self.fundamental_freq + " Hz" + '\n' + format(self.fundamental_vrms, '.6f') + " Vrms")
        else:
            db = self.data.iat[idx, 1]
            self.str_harm_details.set(lbl.get_text() + '\n' + format(db, '.6f') + "dB" + '\n' + format(pow(10, db/20)*100, '.6f') + " %" + '\n' +
            self.rad_values[int(self.rad_var.get())])
        """
        #for use with hover over
        ax = self.fig.get_axes()[0]
        if ax is None: return
        if event.inaxes == ax:
            x = math.floor(event.xdata + 0.5)
            ax = event.inaxes
            y = format(event.ydata, '.6f')
            lbls = ax.get_xticklabels()
            lbl = lbls[x]
            if lbl.get_text() == "": return
            elif lbl.get_text() == "h1":
                self.str_harm_details.set('h1\n' + self.fundamental_freq + " Hz" + '\n' + format(self.fundamental_vrms, '.6f') + " Vrms")
            else:
                if x >= int(self.str_harm_qty.get()): return
                db = self.data.iat[x, 1]
                self.str_harm_details.set(lbl.get_text() + '\n' + format(db, '.6f') + "dB" + '\n' + format(pow(10, db/20)*100, '.6f') + " %" + '\n' + self.rad_values[int(self.rad_var.get())])

    def plot(self):
        self.fig = Figure(figsize=(8,8))
        ax = self.fig.add_subplot(111)

        # sim population of data
        if SIM:
            self.data = pd.DataFrame({"harm": ["h1", "h2", "h3", "h4"], "dB": [0, -55, -60, -80]})
        # end sim

        if DEBUG:
            print(self.data)

        self.fig.set_facecolor(self.window['bg'])
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.bar(self.data.harm, self.data.dB - BOTTOM_DB, bottom=BOTTOM_DB, color='darkorange', align='center', width=.65, alpha=0.6, picker=True)
        ax.margins(x=0)
        ax.margins(y=0)
        ax.set_ylim([BOTTOM_DB, 0])
        #ax.set_xticks(range(PLOT_MAX_HARM))
        ax.set_xticks(range(int(self.str_harm_qty.get())+1))
        ax.set_yticks(range(BOTTOM_DB, 10, 10)) # la escala del eje Y cada 10 entre 0 y -100dB
        ax.set_xticks([x - 0.5 for x in ax.get_xticks()], minor='true')
        ax.set_yticks([y - 0.5 for y in ax.get_yticks()][1:], minor='true')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.set_xlabel('harmonics', fontsize=20, loc='center')
        ax.set_facecolor('xkcd:black')
        ax.grid(color = 'slategray', linestyle = '--', linewidth = 0.5, which='minor')
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        #canvas.get_tk_widget().pack(anchor=tkinter.CENTER, expand=0)
        canvas.get_tk_widget().place(relx=.6, rely=.48, anchor="c")
        self.plot_packed = 1
        #canvas.mpl_connect('button_press_event', self.print_harm_details)
        canvas.mpl_connect('motion_notify_event', self.print_harm_details)
        canvas.draw()

    def _replot_thread(self):
        if DEBUG: print("THD replot thread running");

        while self.running:
            if DEBUG: print("calculate power");
            self.measure_vca()

            if DEBUG: print("remeasuring THD");
            self.measure_thd()

            if DEBUG: print("re plotting")
            self.replot()

            if SIM:
                time.sleep(UPDATE_INTERVAL)

        if DEBUG: print("END running THD replot thread");

    def replot_thread(self):
        self.thread = threading.Thread(target=self._replot_thread)
        self.thread.start()

window = Tk()
start = mclass(window)
start.replot_thread()
window.mainloop()
