import h5py
import matplotlib.pyplot as plt
import numpy as np

def avg(data):
    return sum(data) / len(data)

def show_1(f, adjust_markers=True):
    plt.plot(f['ys'], '+')
    plt.plot(f['processed_timestamps'], np.array(f['processed_ys']) + avg(f['ys'][:25000]) - avg(f['processed_ys'][:500]), '-+')
    plt.plot(np.array(f['marker_timestamps']) - (25 if adjust_markers else 0), f['markers'], 'r.')
    plt.show()

def detect_gaps(f, series="processed_timestamps"):
    for pre, post in zip(f[series], f[series][1:]):
        gap = f.attrs['freq']/1000
        if post - pre != gap:
            print(post - pre, pre, post)
