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

# some settings
UPDATE_INTERVAL=0.2
BOTTOM_DB = -100
PLOT_MAX_HARM = 10
DEFAULT_QTY_HARM = 4
DEBUG = 0

#TODO
##update data structures with DMM output
##continue with DMM LOGGER
##continue with FFT
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
        self.send_cmd('*RST')
        self.send_cmd(':INITiate:CONTinuous OFF;:ABORt')
        # Keithley 2015 seems to drop the first character sent
        # after a reset, so send a dummy command so the IDN isn't
        # corrupt.
        self.send_cmd('*OPC?')
        resp = self.send_cmd('*IDN?')
        print('version: {}'.format(repr(resp)))

        self.send_cmd(':SENS:FUNC \'DIST\'')
        self.send_cmd(':SENS:DIST:TYPE ' + self.rb_values[int(self.rb_var.get())])
        self.send_cmd(':SENS:DIST:HARM ' + "{0:02d}".format(int(self.def_entry_text.get())))
        self.send_cmd(':UNIT:DIST:PERC')
        self.send_cmd(':SENS:DIST:SFIL NONE')
        self.send_cmd(':SENS:DIST:RANG:AUTO ON')
        self.send_cmd(':SENS:DIST:FREQ:AUTO ON')
        self.send_cmd(':READ?')

        #fundamental_freq=self.send_cmd(':SENS:DIST:FREQ:SET?') #;return frequency calculated
        #print(fundamental_freq)
        #fundamental_vrms=self.send_cmd(':SENS:DIST:RMS?') #;return the ACV RMS reading of input waveform
        #print(fundamental_vrms)
        #dist_perc=self.send_cmd(':SENS:DIST:' + self.rb_values[int(self.rb_var.get())] + '?')
        #print(dist_perc)
        #self.send_cmd(':UNIT:DIST:DB')
        #dist_db=self.send_cmd(':SENS:DIST:' + self.rb_values[int(self.rb_var.get())] + '?')
        #print(dist_db)

        #self.send_cmd(':SENS:DIST:HARM:MAGN? 02,02')
        #harm_mag_db=..
        #harm_perc=pow(10, harm_mag_db/20)*100
        #harm_mag_vrms=harm_perc/100*fundamental_vrms

        #self.send_cmd('SENS:DIST:HARM:FREQ? 02,02')   #;valid command?
        #self.send_cmd(':SENS:DIST:HARM:MAGN? 02,' + "{0:02d}".format(int(self.def_entry_text.get())))

        #TODO SINAD is always displayed as dB


    def __init__(self,  window):
        self.window = window
        self.continuePlotting = False
        self.plot_packed = 0 # avoid a re pack when refreshing plot
        np.random.seed(42) # for data sim

        #UI and some data
        self.title = Label(window, text='Keithley 2015 - THD measurement', fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)
        self.lbl_harm_qty = Label(window, text = "Harm. Qty", font='Helvetica 18')
        self.lbl_harm_qty.place(x = 40, y = 100)
        new_text = DEFAULT_QTY_HARM
        self.def_entry_text = StringVar()
        self.def_entry_text.set(new_text)
        self.harm_qty = Entry(window, textvariable=self.def_entry_text, font='Helvetica 18')
        self.harm_qty.focus_set()
        self.harm_qty.icursor(1)
        self.harm_qty.place(x = 230, y = 100)

        self.str_measurement_type = StringVar()
        self.lbl_THD = Label(window, textvariable=self.str_measurement_type, font='Helvetica 18')
        self.lbl_THD.place(x = 40, y = 420)
        def_entry_textdB = StringVar()
        new_textdB = "-50.152312"
        def_entry_textdB.set(new_textdB)
        self.db_THD = Entry(window, textvariable=def_entry_textdB, font='Helvetica 18', width=14, state=DISABLED)
        self.db_THD.place(x = 230, y = 400)
        self.lbl_db = Label(window, text = "dB", font='Helvetica 18')
        self.lbl_db.place(x = 440, y = 400)

        self.lbl_percentage = Label(window, text = "%", font='Helvetica 18')
        self.lbl_percentage.place(x = 440, y = 440)
        new_textperc = "12.17492"
        def_entry_textperc = StringVar()
        def_entry_textperc.set(new_textperc)
        self.perc_THD = Entry(window, textvariable=def_entry_textperc, font='Helvetica 18', width=14, state=DISABLED)
        self.perc_THD.place(x = 230, y = 440)

        self.rb_var = IntVar()
        self.rb_values = ["THD", "THD+N", "SINAD"]
        self.rb_thd = Radiobutton(window, variable=self.rb_var, text=self.rb_values[0], value=0, font='Helvetica 18', command=self.change_measurement_type)
        self.rb_thd.invoke()
        self.rb_thd.select()
        self.rb_thd.place(x = 230, y = 160)
        self.rb_thdn = Radiobutton(window, variable=self.rb_var, text=self.rb_values[1], value=1, font='Helvetica 18', command=self.change_measurement_type)
        self.rb_thdn.place(x = 230, y = 200)
        self.rb_sinad = Radiobutton(window, variable=self.rb_var, text=self.rb_values[2], value=2, font='Helvetica 18', command=self.change_measurement_type)
        self.rb_sinad.place(x = 230, y = 240)

        self.lbl_Fundamental = Label(window, text = "Fundamental", font='Helvetica 18')
        self.lbl_Fundamental.place(x = 40, y = 340)
        new_textHz = "1002.52412"
        def_entry_textHz = StringVar()
        def_entry_textHz.set(new_textHz)
        self.hz = Entry(window, textvariable=def_entry_textHz, font='Helvetica 18', width=14, state=DISABLED)
        self.hz.place(x = 230, y = 320)
        self.lbl_freq = Label(window, text = "Hz", font='Helvetica 18')
        self.lbl_freq.place(x = 440, y = 320)
        self.lbl_vac = Label(window, text = "Vac", font='Helvetica 18')
        self.lbl_vac.place(x = 440, y = 360)
        new_textVac = "1.361287"
        def_entry_textVac = StringVar()
        def_entry_textVac.set(new_textVac)
        self.vac = Entry(window, textvariable=def_entry_textVac, font='Helvetica 18', width=14, state=DISABLED)
        self.vac.place(x = 230, y = 360)


        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18')
        self.button_quit.place(x=110, y=580)

        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18')
        self.button_start.place(x=210, y=580)
        #END UI


    def quit(self):
        self.continuePlotting = False
        Tk().quit()

    def change_measurement_type(self):
        self.str_measurement_type.set(self.rb_values[int(self.rb_var.get())])
        if (self.rb_var.get() == 2): #SINAD
            self.lbl_percentage.place_forget()
            self.perc_THD.place_forget()
        else:
            #self.lbl_percentage.config(state= "normal")
            #self.perc_THD.config(state= "disabled")
            self.lbl_percentage.place(x = 440, y = 440)
            self.perc_THD.place(x = 230, y = 440)



    def replot(self):
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

        ax = self.fig.get_axes()[0]
        ax.clear()         # clear axes from previous plot !!!!
        ax.tick_params(labeltop=False, labelright=True)
        ax.bar(self.data.harm, self.data.dB - BOTTOM_DB, bottom=BOTTOM_DB, color='darkorange', align='center', width=.65, alpha=0.6, picker=True)
        ax.margins(x=0)
        ax.margins(y=0)
        ax.set_ylim([BOTTOM_DB, 0])
        ax.set_xticks(range(PLOT_MAX_HARM))
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
        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
            self.harm_qty.config(state= "normal")
            self.harm_qty.focus_set()
        else:
            res = self.start_serial()
            if res == -1:
                print("error opening serial");
                tkinter.messagebox.showerror("Error", "Error opening serial port")
                #self.quit()
                #return

            #self.measure_thd()
            self.continuePlotting = True
            if (not self.plot_packed): self.plot()
            self.button_start['text'] = "STOP"
            self.harm_qty.config(state= "disabled")
            self.replot_thread()

    def print_harm_details(self, event):
        ax = event.inaxes
        x = event.xdata
        lbls = ax.get_xticklabels()
        idx = int(x.round())
        lbl = lbls[idx]
        print(lbl.get_text())

    def plot(self):
        self.fig = Figure(figsize=(9,9))
        ax = self.fig.add_subplot(111)

        # sim population of data
        self.data = pd.DataFrame({"harm": ["h1", "h2", "h3", "h4"], "dB": [0, -55, -60, -80]})
        if DEBUG:
            print(self.data)
        # end sim

        ax.tick_params(labeltop=False, labelright=True)
        ax.bar(self.data.harm, self.data.dB - BOTTOM_DB, bottom=BOTTOM_DB, color='darkorange', align='center', width=.65, alpha=0.6, picker=True)
        ax.margins(x=0)
        ax.margins(y=0)
        ax.set_ylim([BOTTOM_DB, 0])
        ax.set_xticks(range(PLOT_MAX_HARM))
        ax.set_yticks(range(BOTTOM_DB, 10, 10)) # la escala del eje Y cada 10 entre 0 y -100dB
        ax.set_xticks([x - 0.5 for x in ax.get_xticks()], minor='true')
        ax.set_yticks([y - 0.5 for y in ax.get_yticks()][1:], minor='true')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.set_xlabel('harmonics', fontsize=20, loc='center')
        ax.set_facecolor('xkcd:black')
        ax.grid(color = 'slategray', linestyle = '--', linewidth = 0.5, which='minor')
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().pack(side=BOTTOM, expand=0)
        self.plot_packed = 1
        canvas.mpl_connect('button_press_event', self.print_harm_details)
        canvas.draw()

        #self.continuePlotting = False
        #time.sleep(UPDATE_INTERVAL)


    def _replot_thread(self):
        if DEBUG:
            print("running thread");
        while self.continuePlotting:
            if DEBUG:
                print("re plotting")
            self.replot()
            time.sleep(UPDATE_INTERVAL)
        if DEBUG:
            print("end running thread");

    def replot_thread(self):
        threading.Thread(target=self._replot_thread).start()

window = Tk()
start = mclass(window)
start.replot_thread()
window.mainloop()
