import datetime

from os import path

from PINSoftware.Debugger import Debugger


class DataAnalyser():
    def __init__(self, data_frequency, plot_buffer_len=200, debugger=Debugger(),
            edge_detection_threshold=0.005, average_count=50, correction_func=lambda x: x):
        self.freq = data_frequency
        self.period = 1 / data_frequency
        self.plot_buffer_len = plot_buffer_len
        self.debugger = debugger

        self.ys = [0]
        self.markers = []
        self.marker_timestamps = []

        self.first_processed_timestamp = None
        self.actual_append = self.actual_append_first

        self.processed_ys = []
        self.processed_timestamps = []
        self.averaged_processed_ys = []
        self.averaged_processed_timestamps = []

        self.edge_detection_threshold = edge_detection_threshold
        self.last_up_sum = 0
        self.last_up_diff_sum = 0
        self.last_up_count = 0
        self.last_down_sum = 0
        self.last_down_diff_sum = 0
        self.last_down_count = 0

        self.correction_func = correction_func

        self.average_count = average_count
        self.average_running_sum = 0
        self.average_index = 0

        self.ready_to_plot = True

    def actual_append_first(self, new_processed_y):
        self.processed_ys.append(new_processed_y)
        self.first_processed_timestamp = datetime.datetime.now().timestamp()
        self.processed_timestamps.append(len(self.ys))

        self.average_running_sum += new_processed_y
        self.average_index += 1

        self.actual_append = self.actual_append_real

    def actual_append_real(self, new_processed_y):
        self.processed_ys.append(new_processed_y)
        self.processed_timestamps.append(len(self.ys))

        self.average_running_sum += new_processed_y
        self.average_index += 1

        if self.average_index == self.average_count:
            self.averaged_processed_ys.append(self.average_running_sum / self.average_count)
            self.averaged_processed_timestamps.append(self.processed_timestamps[-1])
            self.average_running_sum = 0
            self.average_index = 0

    def handle_processing(self, new_y):
        up_avg = self.last_up_sum / self.last_up_count if self.last_up_count else self.ys[-1]
        diff = new_y - up_avg
        if abs(diff) > self.edge_detection_threshold:
            if diff < 0 and self.last_up_count > 0 and self.last_down_count > 0:
                avg_up_diff = self.last_up_diff_sum / self.last_up_count

                down_avg = self.last_down_sum / self.last_down_count

                if up_avg >= down_avg:
                    spike = (up_avg - avg_up_diff * (self.last_up_count / 2))
                    self.markers.append(spike)
                    self.marker_timestamps.append(len(self.ys))
                    processed_y = self.correction_func(spike - down_avg)
                    self.actual_append(processed_y)
                else:
                    self.debugger.warning("Irregular data, something may be wrong.")

            if self.last_up_count > 0:
                self.last_down_sum = self.last_up_sum
                self.last_down_diff_sum = self.last_up_diff_sum
                self.last_down_count = self.last_up_count
                self.last_up_sum = 0
                self.last_up_diff_sum = 0
                self.last_up_count = 0
        else:
            self.last_up_sum += new_y
            self.last_up_diff_sum += new_y - self.ys[-1]
            self.last_up_count += 1

    def append(self, new_y):
        self.ready_to_plot = False

        self.handle_processing(new_y)

        self.ys.append(new_y)

        self.ready_to_plot = True

    def plot(self, plt):
        if self.ready_to_plot:
            plt.plot(self.ys[-self.plot_buffer_len:])
