# Some settings
SIM = 0 # do not interact with equipment, just sim data
DEBUG = 1 # print debug data on terminal
UPDATE_INTERVAL=5.0
DEFAULT_QTY_HARM = 4
DEFAULT_WG_FREQ = 1000
BOTTOM_DB = -100 # bottom dB in graph

import matplotlib
import matplotlib.pyplot as plt
#plt.rcParams['toolbar'] = 'None'

from matplotlib.widgets import TextBox
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import *
import pandas as pd

import time
import threading
import tkinter.messagebox
import serial

#for data sim
import numpy as np

#TODO
#replot
#add sig gen amplitude text entry to make it configurable
#option to measure output power with Vac
class mclass:

    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window

        self.continuePlotting = False
        self.plot_packed = 0 # avoid a re pack when refreshing plot
        self.str_measurement_type = StringVar()
        if SIM:
            np.random.seed(42) # for data sim
        else:
            self.start_serial()

        #setup UI
        self.title = Label(window, text='Keithley 2015 - THD measurement', fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)

        self.lbl_harm_qty = Label(window, text = "Measure:", font='Helvetica 18')
        self.lbl_harm_qty.place(x = 40, y = 100)

        self.lbl_harm_qty = Label(window, text = "Harm. Qty", font='Helvetica 18')
        self.lbl_harm_qty.place(x = 40, y = 200)
        self.def_entry_text_qty_harm = StringVar()
        self.def_entry_text_qty_harm.set(DEFAULT_QTY_HARM)
        self.def_entry_textdB = StringVar()
        self.db_THD = Entry(window, textvariable=self.def_entry_textdB, font='Helvetica 18', width=14, state=DISABLED)
        self.harm_qty = Entry(window, textvariable=self.def_entry_text_qty_harm, font='Helvetica 18', width=14)
        self.harm_qty.focus_set()
        self.harm_qty.icursor(1)
        self.harm_qty.place(x = 245, y = 200)

        self.lbl_internalWG = Label(window, text="Use internal SIG GEN", font='Helvetica 18', wraplength=150, justify='left')
        self.lbl_internalWG.place(x = 40, y = 270)
        self.chk_internalWG_var = IntVar()
        self.chk_internalWG = Checkbutton(window, variable=self.chk_internalWG_var, onvalue = 1, offvalue = 0, height=1, width = 1, font='Helvetica 22', command=self.internal_wg_click)
        self.chk_internalWG.place(x = 220, y = 270)
        self.lbl_internalWGfreq = Label(window, text="SIG GEN freq.", font='Helvetica 18', wraplength=150, justify='left')
        self.sv_wg_freq = StringVar()
        self.sv_wg_freq.set(DEFAULT_WG_FREQ)
        self.etr_internalWG = Entry(window, textvariable=self.sv_wg_freq, font='Helvetica 18', width=14, state=DISABLED)

        # measurement results
        self.lbl_Fundamental = Label(window, text = "Fundamental", font='Helvetica 18')
        self.lbl_Fundamental.place(x = 40, y = 440)
        self.def_entry_textHz = StringVar()
        self.hz = Entry(window, textvariable=self.def_entry_textHz, font='Helvetica 18', width=14, state=DISABLED)
        self.hz.place(x = 245, y = 420)
        self.lbl_freq = Label(window, text = "Hz", font='Helvetica 18')
        self.lbl_freq.place(x = 450, y = 425)
        self.lbl_vac = Label(window, text = "Vac rms", font='Helvetica 18')
        self.lbl_vac.place(x = 450, y = 465)
        self.def_entry_textVac = StringVar()
        self.vac = Entry(window, textvariable=self.def_entry_textVac, font='Helvetica 18', width=14, state=DISABLED)
        self.vac.place(x = 245, y = 460)
        self.str_measurement_type = StringVar()
        self.lbl_THD = Label(window, textvariable=self.str_measurement_type, font='Helvetica 18')
        self.lbl_THD.place(x = 40, y = 520)
        self.db_THD.place(x = 245, y = 500)
        self.lbl_db = Label(window, text = "dB", font='Helvetica 18')
        self.lbl_db.place(x = 450, y = 505)
        self.lbl_percentage = Label(window, text = "%", font='Helvetica 18')
        self.lbl_percentage.place(x = 450, y = 545)
        self.def_entry_textperc = StringVar()
        self.perc_THD = Entry(window, textvariable=self.def_entry_textperc, font='Helvetica 18', width=14, state=DISABLED)
        self.perc_THD.place(x = 245, y = 540)

        # TYPE OF MEASUREMENT radio button
        self.rb_var = IntVar()
        self.rb_values = ["THD", "THDN", "SINAD"]
        self.rb_thd = Radiobutton(window, variable=self.rb_var, text=self.rb_values[0], value=0, font='Helvetica 18', command=self.change_measurement_type)
        self.rb_thd.invoke()
        self.rb_thd.select()
        self.rb_thd.place(x = 230, y = 60)
        self.rb_thdn = Radiobutton(window, variable=self.rb_var, text=self.rb_values[1], value=1, font='Helvetica 18', command=self.change_measurement_type)
        self.rb_thdn.place(x = 230, y = 100)
        self.rb_sinad = Radiobutton(window, variable=self.rb_var, text=self.rb_values[2], value=2, font='Helvetica 18', command=self.change_measurement_type)
        self.rb_sinad.place(x = 230, y = 140)

        # buttons
        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18')
        self.button_quit.place(x=120, y=680)

        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18')
        self.button_start.place(x=245, y=680)

        # harmonic details upon click
        self.str_harm_details = StringVar()
        self.lbl_harm_details = Label(window, textvariable=self.str_harm_details, font='Helvetica 18 bold')
        self.lbl_harm_details.place(x = 40, y = 780)
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
            self.send_cmd('DISP:ENAB OFF')
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
            self.def_entry_textHz.set(new_textHz)
            self.def_entry_textVac.set(new_textVac)
            self.def_entry_textdB.set(new_textdB)
            self.def_entry_textperc.set(new_textperc)
        else:
            #self.send_cmd('*RST')
            #self.send_cmd(':INITiate:CONTinuous OFF;:ABORt')
            # Keithley 2015 seems to drop the first character sent
            # after a reset, so send a dummy command so the IDN isn't
            # corrupt.
            #self.send_cmd('*OPC?')
#            resp = self.send_cmd('*IDN?')
#            if DEBUG:
#                print('version: {}'.format(repr(resp)))

            self.send_cmd(':SENS:FUNC \'DIST\'')
            self.send_cmd(':SENS:DIST:TYPE ' + self.rb_values[int(self.rb_var.get())])
            self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(int(self.def_entry_text_qty_harm.get())))
            self.send_cmd(':UNIT:DIST PERC')
            self.send_cmd(':SENS:DIST:SFIL NONE')
            self.send_cmd(':SENS:DIST:RANG:AUTO ON')
            self.send_cmd(':SENS:DIST:FREQ:AUTO ON')

            #set internal WG
            if self.chk_internalWG_var.get() == 1:
                #self.send_cmd(':SENS:DIST:FREQ:AUTO OFF')
                self.send_cmd(':OUTP:FREQ ' + self.sv_wg_freq.get()) #;set frequency
                self.send_cmd(':OUTP:IMP HIZ') #;set high impedance source
                self.send_cmd(':OUTP:AMPL 1') #;set 1 Vrms TODO make this configurable
                self.send_cmd(':OUTP:CHAN2 ISINE') #;select inverted sine
                self.send_cmd(':OUTP ON') #;turn on source

            # return dist in percent
            res = self.send_cmd(':READ?')
            res = format(float(res), '.6f')
            if DEBUG:
                print("% dist: " + res)

            # return fundamental amplitude in Vrms
            res = self.send_cmd(':SENS:DIST:RMS?')
            self.fundamental_vrms = float(res)
            res = format(self.fundamental_vrms, '.6f')
            self.def_entry_textVac.set(res)
            if DEBUG:
                print("fundamental amplitude in Vrms: " + res)


            # return frequency calculated
            res =  self.send_cmd(':SENS:DIST:FREQ:SET?')
            self.fundamental_freq = format(float(res), '.6f')
            self.def_entry_textHz.set(self.fundamental_freq)
            if DEBUG:
                print("fundamental freq in Hz: " + self.fundamental_freq)

            # return THD/THDN %
            self.dist_perc = format(float(self.send_cmd(':SENS:DIST:' + self.rb_values[int(self.rb_var.get())] + '?')), '.6f')
            self.def_entry_textperc.set(self.dist_perc)
            if DEBUG:
                print("measured " + self.rb_values[int(self.rb_var.get())] + ": " + self.dist_perc + " %")

            # return THD/THDN in dB
            self.send_cmd(':UNIT:DIST DB')
            res = self.send_cmd(':READ?')
            res = format(float(res), '.6f')
            self.def_entry_textdB.set(res)
            if DEBUG:
                print("dist in dB: " + res)

            self.dist_db = format(float(self.send_cmd(':SENS:DIST:' + self.rb_values[int(self.rb_var.get())] + '?')), '.6f')
            if DEBUG:
                print("measured " + self.rb_values[int(self.rb_var.get())] + ": " + self.dist_db + " dB")

            # measure each harm
            self.data = pd.DataFrame(columns = ['harm', 'dB'])
            self.data = pd.concat([self.data, pd.DataFrame({'harm' : ['h1'], 'dB' : [0]})], ignore_index=True)
            for h in range(2, int(self.def_entry_text_qty_harm.get())+1):
                res = self.send_cmd(':SENS:DIST:HARM:MAGN? {str_h},{str_h}'.format(str_h="{0:02d}".format(int(h))))
                res = format(float(res), '.6f')
                harm_mag_db = float(res)
                harm_perc=pow(10, harm_mag_db/20)*100
                harm_mag_vrms=harm_perc/100*self.fundamental_vrms
                #harm_fq = float(self.send_cmd('SENS:DIST:HARM:FREQ? 02,02'))   #;not valid command?
                if DEBUG:
                    print("harm %d magnitude: " % h + format(harm_mag_db, '.6f') + " dB")
                    print("harm %d magnitude: " % h  + format(harm_perc, '.6f') + " %")
                    print("harm %d magnitude: " % h + format(harm_mag_vrms, '.6f') + " Vrms")
                    #print("harm %d freq: " % h + format(harm_fq, '.6f') + " Hz")
                self.data = pd.concat([self.data, pd.DataFrame({'harm' : ['h%d' % h], 'dB' : [float(format(harm_mag_db, '.6f'))]})], ignore_index=True)



    def internal_wg_click(self):
        if self.chk_internalWG_var.get() == 0:
            self.etr_internalWG.config(state = 'disabled')
            self.lbl_internalWGfreq.place_forget()
            self.etr_internalWG.place_forget()
        else:
            self.etr_internalWG.config(state = 'normal')
            self.lbl_internalWGfreq.place(x = 40, y = 350)
            self.etr_internalWG.place(x = 245, y = 350)
            self.etr_internalWG.icursor(len(self.sv_wg_freq.get()))
            self.etr_internalWG.focus_set()

    def change_measurement_type(self):
        self.str_measurement_type.set(self.rb_values[int(self.rb_var.get())])
        if (self.rb_var.get() == 2): #SINAD
            self.lbl_percentage.place_forget()
            self.perc_THD.place_forget()
        else:
            self.lbl_percentage.place(x = 450, y = 545)
            self.perc_THD.place(x = 245, y = 540)

    def quit(self):
        if (not SIM and self.ser.isOpen()):
            self.ser.close()
        if self.continuePlotting == True:
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
        ax.tick_params(labeltop=False, labelright=True)
        ax.bar(self.data.harm, self.data.dB - BOTTOM_DB, bottom=BOTTOM_DB, color='darkorange', align='center', width=.65, alpha=0.6, picker=True)
        ax.margins(x=0)
        ax.margins(y=0)
        ax.set_ylim([BOTTOM_DB, 0])
        #ax.set_xticks(range(PLOT_MAX_HARM))
        ax.set_xticks(range(int(self.def_entry_text_qty_harm.get())+1))
        ax.set_yticks(range(BOTTOM_DB, 10, 10)) # la escala del eje Y cada 10 entre 0 y -100dB
        ax.set_xticks([x - 0.5 for x in ax.get_xticks()], minor='true')
        ax.set_yticks([y - 0.5 for y in ax.get_yticks()][1:], minor='true')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.set_xlabel('harmonics', fontsize=20, loc='center')
        ax.set_facecolor('xkcd:black')
        ax.grid(color = 'slategray', linestyle = '--', linewidth = 0.5, which='minor')
        self.fig.canvas.mpl_connect('button_press_event', self.print_harm_details)
        self.fig.canvas.draw()

    def change_state(self):
        ## TODO: check here that internal WG freq is valid
        ## TODO: check qty of harm is numberic

        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
            self.harm_qty.config(state= "normal")
            self.chk_internalWG.config(state = 'normal')
            self.rb_thd.config(state = 'normal')
            self.rb_thdn.config(state = 'normal')
            self.rb_sinad.config(state = 'normal')
            self.etr_internalWG.config(state = 'normal')
            self.harm_qty.focus_set()
        else:
            self.measure_thd()
            self.continuePlotting = True
            if (not self.plot_packed): self.plot()
            self.button_start['text'] = "STOP"
            self.harm_qty.config(state = 'disabled')
            self.chk_internalWG.config(state = 'disabled')
            self.rb_thd.config(state = 'disabled')
            self.etr_internalWG.config(state = 'disabled')
            self.rb_thdn.config(state = 'disabled')
            self.rb_sinad.config(state = 'disabled')
            self.replot_thread()

    def print_harm_details(self, event):
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
            self.rb_values[int(self.rb_var.get())])

    def plot(self):
        self.fig = Figure(figsize=(8,8))
        ax = self.fig.add_subplot(111)

        # sim population of data
        if SIM:
            self.data = pd.DataFrame({"harm": ["h1", "h2", "h3", "h4"], "dB": [0, -55, -60, -80]})
        # end sim

        if DEBUG:
            print(self.data)

        ax.tick_params(labeltop=False, labelright=True)
        ax.bar(self.data.harm, self.data.dB - BOTTOM_DB, bottom=BOTTOM_DB, color='darkorange', align='center', width=.65, alpha=0.6, picker=True)
        ax.margins(x=0)
        ax.margins(y=0)
        ax.set_ylim([BOTTOM_DB, 0])
        #ax.set_xticks(range(PLOT_MAX_HARM))
        ax.set_xticks(range(int(self.def_entry_text_qty_harm.get())+1))
        ax.set_yticks(range(BOTTOM_DB, 10, 10)) # la escala del eje Y cada 10 entre 0 y -100dB
        ax.set_xticks([x - 0.5 for x in ax.get_xticks()], minor='true')
        ax.set_yticks([y - 0.5 for y in ax.get_yticks()][1:], minor='true')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.set_xlabel('harmonics', fontsize=20, loc='center')
        ax.set_facecolor('xkcd:black')
        ax.grid(color = 'slategray', linestyle = '--', linewidth = 0.5, which='minor')
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        #canvas.get_tk_widget().pack(anchor=tkinter.CENTER, expand=0)
        canvas.get_tk_widget().place(relx=.6, rely=.5, anchor="c")
        self.plot_packed = 1
        canvas.mpl_connect('button_press_event', self.print_harm_details)
        canvas.draw()

    def _replot_thread(self):
        if DEBUG:
            print("running replot thread");
        while self.continuePlotting:
            if DEBUG:
                print("re plotting")
            self.replot()
            time.sleep(UPDATE_INTERVAL)
        if DEBUG:
            print("end running replot thread");

    def replot_thread(self):
        self.thread = threading.Thread(target=self._replot_thread)
        self.thread.start()

window = Tk()
start = mclass(window)
start.replot_thread()
window.mainloop()
