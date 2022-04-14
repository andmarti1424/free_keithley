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
REFRESH_TIME = 0.25 # in seconds

class mclass:
    def __init__(self,  window):
        self.window = window
        self.continuePlotting = False
        np.random.seed(42)

        self.button_start = Button(window, text="START", command=self.change_state, font='Helvetica 18 bold')
        self.button_start.place(x=210, y=40)
        self.button_quit = Button(window, text="QUIT", command=self.quit, font='Helvetica 18 bold')
        self.button_quit.place(x=350, y=40)

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
        self.fig = Figure(figsize=(9,9))
        ax = self.fig.add_subplot(111)

        df = pd.DataFrame({'ms': [], 'value': []})
        ax.plot(df.ms, df.value)
        canvas = FigureCanvasTkAgg(self.fig, master=window)
        canvas.get_tk_widget().pack(side=BOTTOM, expand=0)
        canvas.draw()

        #ax.clear() # clear axes from previous plot !!!!
        while(self.continuePlotting):
            # data sim
            value = np.random.random()
            if (round(time.time() * 1000) - plot_start_time > 30000):
                value *= -10
            if (round(time.time() * 1000) - plot_start_time > 20000):
                value *= 10
            mytime = round(time.time() * 1000) - plot_start_time
            #end of data sim

            dfn = pd.DataFrame({'ms': [mytime], 'value': [value]})
            df = pd.concat([df, dfn])
            ax = self.fig.get_axes()[0]
            ax.plot(df.ms, df.value)
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            time.sleep(REFRESH_TIME)

window = Tk()
start = mclass(window)
window.mainloop()
