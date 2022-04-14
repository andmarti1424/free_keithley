import numpy as np
#scipy
from scipy import signal
import matplotlib.pyplot as plt
w, h = signal.freqz([1, 1])
x = w * 44100 * 1.0 / (2 * np.pi)
y = 20 * np.log10(abs(h))

plt.rcParams['toolbar'] = 'None'

f, ax = plt.subplots(figsize=(12, 4))
ax.set(xscale="log")
ax.set_facecolor('xkcd:black')
ax.tick_params(labeltop=False, labelright=True)
ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
ax.set_ylabel('response, dB', fontsize=20, loc='center')
plt.plot(x, y)
plt.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.5)
plt.ylim([-21, 21])
plt.yticks(range(-21, 21, 3)) # la escala del eje Y cada 5 entre 0 y -40dB
_ = plt.xticks([20,50,100,200,500,1000,2000,5000,10000,20000],
        ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])

plt.show()
