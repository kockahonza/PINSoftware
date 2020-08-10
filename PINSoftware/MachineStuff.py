import os

from typing import List

import matplotlib.animation as animation

from PINSoftware.Debugger import Debugger
from PINSoftware.Profiler import Profiler
from PINSoftware.DataAnalyser import DataAnalyser
from PINSoftware.DataSaver import CsvDataSaver, Hdf5DataSaver, Filetype, SavingException
from PINSoftware.DataUpdaterClasses.LoadedDataUpdater import LoadedDataUpdater
from PINSoftware.DataUpdaterClasses.NiDAQmxDataUpdater import NiDAQmxDataUpdater

class MachineStuff():
    """
    This is the main class covering all hardware control and data analysis (everything except the UI).
    There should always be only one instance at a time and the program keeps it for the whole duration
    of the run.
    """
    def __init__(self, plt, dummy : bool, dummy_data_file : str, profiler : bool = False,
            plot_update_interval : int = 100, log_directory : str = "logs"):
        """
        `plt` should be the `matplotlib.pyplot` module or something equivalent, this is for plotting the live
        data graph on the host machine when the graphing option is enabled. `dummy` determines whether
        the data should be grabbed from the NI-6002 or a dummy file. If `dummy` is True, `dummy_data_file` should
        be specified otherwise the program will crash, `dummy_data_file` is a path to the data to use for dummy mode.
        `profiler` is whether the DataUpdater should be profiled, `plot_update_interval` is the update interval of
        the live data graph and `log_directory` is the directory where to put saved data.
        """
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
        """Setup for the live graphing"""
        self.fig = self.plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)

        self.pause = False

    def animate(self, i):
        """The animate function for the `animation.FuncAnimation` class"""
        if not self.pause and self.du:
            if self.du.data:
                self.ax.clear()
                self.du.data.plot(self.plt)

    def onKeyPress(self, event):
        """The function to call when a key is pressed in the live graph window"""
        if event.key == "p":
            self.pause = not self.pause

    def run_graphing(self):
        """This runs the actual graphing, this hangs until the window is closed"""
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=self.plot_update_interval)
        self.fig.canvas.mpl_connect('key_press_event', self.onKeyPress)
        self.plt.show()

    def grab_control(self, controller_info):
        """
        Wrapper around the `MachineStuff.controller` field where extra effects can be added,
        called when someone grabs control.
        """
        self.controller = controller_info
        self.stop_experiment()

    def release_control(self):
        """
        Wrapper around the `MachineStuff.controller` field where extra effects can be added,
        called when the control is released.
        """
        self.controller = None
        self.stop_experiment()

    def start_experiment(self, save_base_filename : str = None, save_filetype : Filetype = Filetype.Csv,
            items : List[str] = ["ys","processed_ys"], **kwargs):
        """
        This starts a data acquisition run. It creates a new `PINSoftware.DataAnalyser.DataAnalyser` and an appropriate `DataUpdater`.
        Then it may also start a `DataSaver` and or a `Profiler` based on the situation.

        `save_base_filename` is the base part of the filename for the
        new log file. The `save_base_filename` is appended with a timestamp and an appropriate file extension
        and that makes up the filename. `save_filetype` determines the `DataSaver` type, more information in
        `PINSoftware.DataSaver`. `items` is used when `save_filetype` is `PINSoftware.DataSaver.Filetype.Hdf5` and is passed to the
        `PINSoftware.DataSaver.Hdf5DataSaver`. The rest of the keyword arguments are passed to the `PINSoftware.DataAnalyser.DataAnalyser`.
        """
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
        """This stops the current experiment and all the threads working on it"""
        if self.du:
            self.du.stop()
        if self.saver:
            self.saver.stop()
        self.experiment_running = False

    def stop_everything(self):
        """This currently just calls `stop_experiment` but there might be stuff added here,
        this is meant to be a sort of stop all button"""
        self.stop_experiment()
