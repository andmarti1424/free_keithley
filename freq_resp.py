# some config
SIM = 1
DEBUG = 0
DISPLAY = 1 # display on or off
DEFAULT_POINTS_PER_DECADE = 3  #4 means for instance that between 20hz and 30hz you will have 2 other points: [22.89 Hz and 26.21 Hz]
DEFAULT_INPUT_SIGNAL_AMPLITUDE = 1 # default amplitude for input signal in Vrms
DEFAULT_MAXY = 9 # max value in y axis: 10dB
DEFAULT_MINY = -9 # min value in y axis: 10dB
DEFAULT_YSTEPS = 3


import matplotlib.pyplot as plt
from tkinter import *
import time
import serial
#from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import MultipleLocator
# for simulation
import numpy as np
#scipy
from scipy import signal
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


#TODO]
#test with eq
#multiple plots
#hover

class mclass:

    def __init__(self,  window):
        self.ser = serial.Serial()
        self.window = window
        self.plots = 0 # number of plots done. can be up to 4
        self.abort = 0

        # setup UI
        self.str_title = StringVar()

        # title
        self.str_title.set("Keithley 2015 - Freq. response")
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

        # y max
        self.lbl_maxy = Label(window, text="max value in Y axis", font='Helvetica 18')
        self.lbl_maxy.place(x = 40, y = 323)
        self.lbl_maxy = Label(window, text="dB", font='Helvetica 18')
        self.lbl_maxy.place(x = 330, y = 323)
        self.str_maxy = StringVar()
        self.str_maxy.set(DEFAULT_MAXY)
        self.etr_maxy = Entry(window, textvariable=self.str_maxy, font='Helvetica 18', width=3)
        self.etr_maxy.place(x = 280, y = 320)
        #self.etr_maxy.focus_set()
        self.etr_maxy.icursor(1)

        # y min
        self.lbl_miny = Label(window, text="min value in Y axis", font='Helvetica 18')
        self.lbl_miny.place(x = 40, y = 383)
        self.lbl_miny = Label(window, text="dB", font='Helvetica 18')
        self.lbl_miny.place(x = 330, y = 383)
        self.str_miny = StringVar()
        self.str_miny.set(DEFAULT_MINY)
        self.etr_miny = Entry(window, textvariable=self.str_miny, font='Helvetica 18', width=3)
        self.etr_miny.place(x = 280, y = 380)
        #self.etr_miny.focus_set()
        self.etr_miny.icursor(1)

        # y steps
        self.lbl_ysteps = Label(window, text="steps in Y axis", font='Helvetica 18')
        self.lbl_ysteps.place(x = 40, y = 443)
        self.str_ysteps = StringVar()
        self.str_ysteps.set(DEFAULT_YSTEPS)
        self.etr_ysteps = Entry(window, textvariable=self.str_ysteps, font='Helvetica 18', width=3)
        self.etr_ysteps.place(x = 280, y = 440)
        #self.etr_ysteps.focus_set()
        self.etr_ysteps.icursor(1)

        # details - Freq measured
        #self.str_details = StringVar()
        #self.lbl_details = Label(window, textvariable=self.str_details, font='Helvetica 18 bold')
        #self.lbl_details.place(x = 40, y = 880)

        # coordinates
        #self.str_coordinates = StringVar()
        #self.lbl_coordinates = Label(window, textvariable=self.str_coordinates, font='Helvetica 18 bold')
        #self.lbl_coordinates.place(x = 440, y = 1000)

        # buttons
        self.but_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18')
        self.but_quit.place(x=40, y=680)
        self.but_start = Button(window, text="RUN", command=self.change_state, font='Helvetica 18')
        self.but_start.place(x=165, y=680)
        #self.but_clear = Button(window, text="CLEAR", command=self.clear, font='Helvetica 18')
        #self.but_clear.place(x=280, y=680)
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

    def quit(self):
        if (not SIM and self.ser.isOpen()):
            self.ser.close()
        Tk().quit()

    def change_state(self):
        if (self.but_start['text'] == "ABORT"): self.abort = 1
        self.plot()

    def plot(self):
        # plot
        #plt.rcParams['toolbar'] = 'None'
        #f, ax = plt.subplots(figsize=(12, 4))
        #ax.set(xscale="log")
        #ax.set_facecolor('xkcd:black')
        #ax.tick_params(labeltop=False, labelright=True)
        #ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
        #ax.set_ylabel('response, dB', fontsize=20, loc='center')
        #plt.plot(x, y)
        #plt.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.5)
        #plt.ylim([DEFAULT_MINY, DEFAULT_MAXY])
        #plt.yticks(range(DEFAULT_MINY, DEFAULT_MAXY, DEFAULT_YSTEPS)) # la escala del eje Y cada 5 entre 0 y -40dB
        #_ = plt.xticks([20,50,100,200,500,1000,2000,5000,10000,20000],
        #        ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        #plt.show()

        self.fig, ax = plt.subplots(figsize=(12, 7))
        self.fig.tight_layout(rect=[0.05, 0.08, 0.97, 0.95])
        plt.rcParams['toolbar'] = 'None'
        ax.tick_params(labeltop=False, labelright=True,  labelsize=14)
        ax.set(xscale="log")
        ax.set_facecolor('xkcd:black')
        ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
        ax.set_ylabel('response, dB', fontsize=20, loc='center')
        ax.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.7)
        ax.set_xticks([20,50,100,200,500,1000,2000,5000,10000,20000], ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
        ax.set_xlim([20, 20000])
        ax.set_ylim([float(self.str_miny.get()), float(self.str_maxy.get())])
        ax.yaxis.set_ticks(range(int(self.str_miny.get()), int(self.str_maxy.get()), int(self.str_ysteps.get()))) # Y scale
        #ax.yaxis.set_major_locator(plt.MaxNLocator(6))
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        #ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(axis='y', which='minor', length=6, width='1', left='true', right='true')
        #ax.plot(self.measurement['freq'], self.measurement['thd'], color='white')
        ax.plot(self.x, self.y, color='white')
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().place(relx=.6, rely=.48, anchor="c")
        canvas.draw()
        canvas.start_event_loop(0.05)
        #canvas.mpl_connect('motion_notify_event', self.motion_hover)

window = Tk()
start = mclass(window)
window.mainloop()
