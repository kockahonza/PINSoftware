import datetime

from os import path

import numpy as np

from PINSoftware.Debugger import Debugger
from PINSoftware.Profiler import Profiler


def remove_outliers(data):
    u = np.mean(data)
    s = np.std(data)
    return [e for e in data if (u - 2 * s <= e <= u + 2 * s)]

class DataAnalyser():
    """
    This class takes care of data analysis and storage.

    Once this function is created, you should call `DataAnalyser.append` to add a new data point,
    use `DataAnalyser.ys` to get the raw data, `DataAnalyser.processed` to get the peak voltages,
    `DataAnalyser.processed_timestamps` are timestamps corresponding to the peak voltages,
    `DataAnalyser.averaged_processed_ys` are the averaged peak voltages and `DataAnalyser.averaged_processed_timestamps`
    are timestamps corresponding to the averages. Lastly `DataAnalyser.markers` and `DataAnalyser.marker_timestamps`
    are debug markers and their timestamps, those can be anything and are only adjustable from code, they should
    not be used normally.

    All the timestamps used here are based on the length of `DataAnalyser.ys` at the time. This is very
    useful for two reasons, its easy to calculate so also fast. Bu mostly because later when you plot the data,
    you can plot the `DataAnalyser.ys` with "x0=0" and "dx=1" and then plot the peak averaged directly and the data
    will be correctly scaled on the x axis. The problem is however that this assumes that the data comes at a
    precise frequency but the NI-6002 can offer that so it should be alright.

    Once the `DataAnalyser.on_start` is called a profiler about irregular data is also started, each second
    it prints how many irregular data issues there were.
    """
    def __init__(self, data_frequency : int, plot_buffer_len : int = 200, debugger : Debugger = Debugger(),
            edge_detection_threshold : float = 0.005, average_count : int = 50, correction_func=lambda x: x):
        """
        `data_frequency` is the frequency of the incoming data, this is used for calculating real timestamps
        and is saved if hdf5 saving is enabled.

        `plot_buffer_len` determines how many datapoints should be plotted in the live plot graph (if the
        server has been run with the graphing option).

        `debugger` is the debugger to use.

        `edge_detection_threshold`, `average_count` and `correction_func` are processing parameters. They
        are described in the Help tab of the program.

        `edge_detection_threshold` sets the voltage difference required to find a section transition.

        `average_count` is how many peak voltages should be averaged to get the averaged peak voltages.

        `correction_func` is the function to run the peak voltages through before using them. This is
        to correct some systematic errors or do some calculations.
        """
        self.freq = data_frequency
        self.period = 1 / data_frequency
        self.plot_buffer_len = plot_buffer_len
        self.debugger = debugger

        self.ys = [0, 0, 0]
        self.markers = []
        self.marker_timestamps = []

        self.first_processed_timestamp = None
        self.actual_append = self.actual_append_first

        self.processed_ys = []
        self.processed_timestamps = []
        self.averaged_processed_ys = []
        self.averaged_processed_timestamps = []

        self.edge_detection_threshold = edge_detection_threshold
        self.last_up_section = []
        self.last_down_section = []

        self.correction_func = correction_func

        self.average_count = average_count
        self.average_running_sum = 0
        self.average_index = 0

        self.irregular_data_prof = Profiler("Irregular data", start_delay=0)

        self.ready_to_plot = True

    def on_start(self):

        self.irregular_data_prof.start()

    def actual_append_first(self, new_processed_y):
        """
        This appends the new processed value, works on the averaged processed values and
        possibly appends that too. This is when the first processed value comes in.
        It sets some initial values, after it runs once `DataAnalyser.actual_append_main`
        is called instead.
        """
        self.processed_ys.append(new_processed_y)
        self.first_processed_timestamp = datetime.datetime.now().timestamp()
        self.processed_timestamps.append(len(self.ys))

        self.average_running_sum += new_processed_y
        self.average_index += 1

        self.actual_append = self.actual_append_main

    def actual_append_main(self, new_processed_y):
        """
        This appends the new processed value, works on the averaged processed values and
        possibly appends that too. For the first processed value, `DataAnalyser.actual_append_first`
        is run instead, but afterwards this is.
        """
        self.processed_ys.append(new_processed_y)
        self.processed_timestamps.append(len(self.ys))

        self.average_running_sum += new_processed_y
        self.average_index += 1

        if self.average_index == self.average_count:
            self.averaged_processed_ys.append(self.average_running_sum / self.average_count)
            self.averaged_processed_timestamps.append(self.processed_timestamps[-1] - self.average_count / 2)
            self.average_running_sum = 0
            self.average_index = 0

    def handle_processing(self, new_y):
        """
        This is the main processing function. It gets the new y (which
        at this point is not in `DataAnalyser.ys` yet) and does some processing on it.
        It may add new values to `DataAnalyser.processed` and `DataAnalyser.averaged_processed_ys`
        if new values were found through `DataAnalyser.actual_append`. If the data does not add up
        it is added to irregular data. I won't describe the logic here as it is described in the manual and also
        it may still be best to look through the code.
        """
        diff = new_y - self.ys[-3]
        if abs(diff) > self.edge_detection_threshold:
            if diff < 0 and len(self.last_up_section) > 1 and len(self.last_down_section) > 1:
                last_up_section = remove_outliers(self.last_up_section)
                last_down_section = remove_outliers(self.last_down_section)

                last_up_diffs = [post - pre for pre, post in zip(last_up_section, last_up_section[1:])]
                avg_up_diff = sum(last_up_diffs) / len(last_up_diffs)

                up_avg = sum(last_up_section) / len(last_up_section)

                down_avg = sum(last_down_section) / len(last_down_section)

                if up_avg >= down_avg:
                    spike = (up_avg - avg_up_diff * (len(self.last_up_section) / 2))
                    self.markers.append(spike)
                    self.marker_timestamps.append(len(self.ys))
                    processed_y = self.correction_func(spike - down_avg)
                    self.actual_append(processed_y)
                else:
                    # self.markers.append(down_avg)
                    # self.marker_timestamps.append(len(self.ys))
                    # self.debugger.warning("Irregular data, something may be wrong.")
                    self.irregular_data_prof.add_count()

            if len(self.last_up_section) > 0:
                self.last_down_section = self.last_up_section
                self.last_up_section = []
        else:
            self.last_up_section.append(new_y)

    def append(self, new_y):
        """
        The main apppend function through which new data is added. It just passes
        the value to the processing function and appends it to `DataAnalyser.ys` in the end.
        """
        self.ready_to_plot = False

        self.handle_processing(new_y)

        self.ys.append(new_y)

        self.ready_to_plot = True

    def on_stop(self):
        self.irregular_data_prof.stop()

    def plot(self, plt):
        """This is what plots the data on the raw data graph if graphing is enabled"""
        if self.ready_to_plot:
            plt.plot(self.ys[-self.plot_buffer_len:])
