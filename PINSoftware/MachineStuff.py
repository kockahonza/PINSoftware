import os

import matplotlib.animation as animation

from PINSoftware.Debugger import Debugger
from PINSoftware.Profiler import Profiler
from PINSoftware.DataAnalyser import DataAnalyser
from PINSoftware.DataSaver import CsvDataSaver, Hdf5DataSaver, Filetype, SavingException
from PINSoftware.DataUpdaterClasses.LoadedDataUpdater import LoadedDataUpdater
from PINSoftware.DataUpdaterClasses.NiDAQmxDataUpdater import NiDAQmxDataUpdater

class MachineStuff():
    def __init__(self, plt, dummy, dummy_data_file, profiler=False, plot_update_interval=10, log_directory="logs"):
        self.plt = plt
        self.dummy = dummy
        self.dummy_data_file = dummy_data_file
        self.profiler = profiler
        self.plot_update_interval = plot_update_interval
        self.log_directory = os.path.join(os.path.curdir, log_directory)

        self.init_graph()

        self.debugger = Debugger()
        self.controller = None
        self.du = None
        self.data = None
        self.saver = None
        self.experiment_running = False

        if not os.path.exists(self.log_directory):
            os.mkdir(self.log_directory)

    def init_graph(self):
        self.fig = self.plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)

        self.pause = False

    def animate(self, i):
        if not self.pause and self.du:
            if self.du.data:
                self.ax.clear()
                self.du.data.plot(self.plt)

    def onClick(self, event):
        if event.key == "p":
            self.pause = not self.pause

    def run_graphing(self):
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=self.plot_update_interval)
        self.fig.canvas.mpl_connect('key_press_event', self.onClick)
        self.plt.show()

    def grab_control(self, controller_info):
        self.controller = controller_info
        self.stop_experiment()

    def release_control(self):
        self.controller = None
        self.stop_experiment()

    def start_experiment(self, save_base_filename=None, save_filetype=Filetype.Csv, items=["ys","processed_ys"], **kwargs):
        self.data = DataAnalyser(50000, plot_buffer_len=200, debugger=self.debugger, **kwargs)
        if save_base_filename:
            if save_filetype == Filetype.Csv:
                self.saver = CsvDataSaver(self.data, self.log_directory, save_base_filename)
            elif save_filetype == Filetype.Hdf5:
                self.saver = Hdf5DataSaver(self.data, self.log_directory, save_base_filename, items=items)
        else:
            self.saver = None
        if self.dummy:
            self.du = LoadedDataUpdater(self.dummy_data_file, self.data, freq=50000, debugger=self.debugger)
        else:
            self.du = NiDAQmxDataUpdater(self.data, debugger=self.debugger)
        if self.profiler:
            self.du.profiler = Profiler(name="DataUpdater RPS", start_delay=3)
        self.du.start()
        if self.saver:
            self.saver.start()
        self.experiment_running = True

    def stop_experiment(self):
        if self.du:
            self.du.stop()
        if self.saver:
            self.saver.stop()
        self.experiment_running = False

    def stop_everything(self):
        self.stop_experiment()
