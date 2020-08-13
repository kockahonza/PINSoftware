"""
This file isn't a part of the server! This is just useful functions for working with the produced data.
For example after the data has been recorded in an hd5 file, some functions plot the data in a nice way
and so on.

"""


import h5py
import matplotlib.pyplot as plt
import numpy as np

def avg(data):
    """Get the average of a list"""
    return sum(data) / len(data)

def show_1(f, adjust_markers=True):
    """
    Plots the files data. Moves the processed_ys to be at the same height as ys.
    Also plots debug markers, assumes that they are the peak voltage spikes - very useful for debugging.
    """
    plt.plot(f['ys'], '+')
    plt.plot(f['processed_timestamps'], np.array(f['processed_ys']) + avg(f['ys'][:25000]) - avg(f['processed_ys'][:500]), '-+')
    plt.plot(np.array(f['marker_timestamps']) - (25 if adjust_markers else 0), f['markers'], 'r.')
    plt.show()

def detect_gaps(f, series="processed_timestamps", t=1):
    """
    This goes through the file and prints all the spots where the time between two successive data
    isn't `t`.
    """
    for pre, post in zip(f[series], f[series][1:]):
        gap = f.attrs['freq'] * (t / 1000)
        if post - pre != gap:
            print(post - pre, pre, post)
