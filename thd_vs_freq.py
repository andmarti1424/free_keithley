import numpy as np
import matplotlib.pyplot as plt
x = [20, 50, 100, 200, 500, 1000, 5000, 10000, 20000]
y = [3, 2, 1, 0.5, 0.47, 0.3, 0.2, 1, 2.5]

plt.rcParams['toolbar'] = 'None'

f, ax = plt.subplots(figsize=(12, 4))
ax.set(xscale="log")
ax.set_facecolor('xkcd:black')
ax.tick_params(labeltop=False, labelright=True)
ax.set_xlabel('frequency, Hz', fontsize=20, loc='center')
ax.set_ylabel('THD+N, %', fontsize=20, loc='center')
plt.plot(x, y)
plt.grid(which="both", axis='both', color='slategray', linestyle='--', linewidth=0.5)
ax.yaxis.set_ticks(np.arange(0, 5.5, 0.5)) # la escala del eje Y cada 0.5 entre 0 y 5
_ = plt.xticks([20,50,100,200,500,1000,2000,5000,10000,20000],
        ["20", "50", "100", "200", "500", "1K", "2K", "5K", "10K", "20K"])
plt.xlim([20, 20000])

plt.show()
