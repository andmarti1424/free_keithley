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

# settings
REFRESH_TIME = 0.10 # in seconds

class mclass:
    def __init__(self,  window):
        self.window = window
        self.continuePlotting = False
        self.plot_packed = False
        self.fig = Figure(figsize=(9,9))
        self.ax = self.fig.add_subplot(111)
        self.fig.canvas = FigureCanvasTkAgg(self.fig, master=window)
        np.random.seed(42)

        self.title = Label(window, text='Keithley 2015 - Logger', fg='#1C5AAC', font=('Helvetica 24 bold'))
        self.title.pack(ipady=15, expand=False, side=TOP)
        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18 bold')
        self.button_start.place(x=350, y=85)
        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18 bold')
        self.button_quit.place(x=210, y=85)

    def change_state(self):
        if self.continuePlotting == True:
            self.continuePlotting = False
            self.button_start['text'] = "START"
        else:
            self.continuePlotting = True
            self.button_start['text'] = "STOP"
            self.plot()

    def quit(self):
        self.continuePlotting = False
        Tk().quit()

    def plot(self):
        plot_start_time = round(time.time() * 1000)

        df = pd.DataFrame({'ms': [], 'value': []})

        self.ax.clear() # clear previous plot !!!!
        self.ax.tick_params(labeltop=False, labelright=True)
        self.ax.plot(df.ms, df.value)
        if not self.plot_packed:
            self.fig.canvas.get_tk_widget().pack(side=BOTTOM, expand=0)
        self.plot_packed = 1
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


        while(self.continuePlotting):
            # data sim
            value = np.random.random()
            if (round(time.time() * 1000) - plot_start_time > 15000):
                value *= -10
            if (round(time.time() * 1000) - plot_start_time > 10000):
                value *= 10
            mytime = round(time.time() * 1000) - plot_start_time
            #end of data sim

            dfn = pd.DataFrame({'ms': [mytime], 'value': [value]})
            df = pd.concat([df, dfn])
            self.ax.set_xlabel('ms', fontsize=20, loc='right')
            self.ax.set_ylabel('Vrms', fontsize=20, loc='center')
            ax = self.fig.get_axes()[0]
            ax.tick_params(labeltop=False, labelright=True)
            ax.plot(df.ms, df.value)
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            time.sleep(REFRESH_TIME)

window = Tk()
start = mclass(window)
window.mainloop()
