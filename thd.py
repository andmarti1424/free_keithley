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

#for data sim
import numpy as np

# some settings
UPDATE_INTERVAL=0.2
BOTTOM_DB = -100
PLOT_MAX_HARM = 10
DEFAULT_QTY_HARM = 4
DEBUG = 0

#TODO
#set start as default button
##continue with DMM LOGGER
##continue with FFT
class mclass:

    def __init__(self,  window):
        self.window = window
        self.continuePlotting = False
        np.random.seed(42) # for data sim

        #UI and some data
        self.title = Label(window, text='Keithley 2015 - THD measurement', fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)

        self.lbl_harm_qty = Label(window, text = "Harm. Qty", font='Helvetica 20 bold')
        self.lbl_harm_qty.place(x = 40, y = 60)
        new_text = DEFAULT_QTY_HARM
        def_entry_text = StringVar()
        def_entry_text.set(new_text)
        self.harm_qty = Entry(window, textvariable=def_entry_text, font='Helvetica 18 bold')
        self.harm_qty.place(x = 230, y = 60)

        self.lbl_THD = Label(window, text = "THD", font='Helvetica 20 bold')
        self.lbl_THD.place(x = 40, y = 240)
        self.lbl_Fundamental = Label(window, text = "Fundamental", font='Helvetica 20 bold')
        self.lbl_Fundamental.place(x = 40, y = 160)

        new_textHz = "1002.52412"
        def_entry_textHz = StringVar()
        def_entry_textHz.set(new_textHz)
        self.hz = Entry(window, textvariable=def_entry_textHz, font='Helvetica 18 bold', width=14, state=DISABLED)
        self.hz.place(x = 230, y = 140)

        new_textVac = "1.361287"
        def_entry_textVac = StringVar()
        def_entry_textVac.set(new_textVac)
        self.vac = Entry(window, textvariable=def_entry_textVac, font='Helvetica 18 bold', width=14, state=DISABLED)
        self.vac.place(x = 230, y = 180)

        new_textdB = "-50.152312"
        def_entry_textdB = StringVar()
        def_entry_textdB.set(new_textdB)
        self.db_THD = Entry(window, textvariable=def_entry_textdB, font='Helvetica 18 bold', width=14, state=DISABLED)
        self.db_THD.place(x = 230, y = 220)

        new_textperc = "12.17492"
        def_entry_textperc = StringVar()
        def_entry_textperc.set(new_textperc)
        self.perc_THD = Entry(window, textvariable=def_entry_textperc, font='Helvetica 18 bold', width=14, state=DISABLED)
        self.perc_THD.place(x = 230, y = 260)

        self.lbl_freq = Label(window, text = "Hz", font='Helvetica 18 bold')
        self.lbl_freq.place(x = 440, y = 140)
        self.lbl_vac = Label(window, text = "Vac", font='Helvetica 18 bold')
        self.lbl_vac.place(x = 440, y = 180)
        self.lbl_percentage = Label(window, text = "%", font='Helvetica 18 bold')
        self.lbl_percentage.place(x = 440, y = 260)
        self.lbl_db = Label(window, text = "dB", font='Helvetica 18 bold')
        self.lbl_db.place(x = 440, y = 220)
        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18 bold')
        self.button_quit.place(x=110, y=340)
        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18 bold')
        self.button_start.place(x=210, y=340)
        #END UI

    def quit(self):
        self.continuePlotting = False
        Tk().quit()

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
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.draw()

    def change_state(self):
        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
        else:
            self.continuePlotting = True
            self.plot()
            self.button_start['text'] = "STOP"
            self.replot_thread()

    def on_click(self, event):
        ax = event.inaxes
        x = event.xdata
        lbls = ax.get_xticklabels()
        idx = int(x.round())
        lbl = lbls[idx]
        print(lbl.get_text())
        #self.fig.canvas.draw_idle()

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
        canvas.mpl_connect('button_press_event', self.on_click)
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
