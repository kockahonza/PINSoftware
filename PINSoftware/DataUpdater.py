import random
import threading
import time

import nidaqmx

from PINSoftware.Profiler import Profiler
from PINSoftware.Debugger import Debugger
from PINSoftware.DataAnalyser import DataAnalyser


class BaseDataUpdater(threading.Thread):
    """
    Base class for `PINSoftware.DataUpdater.DataUpdater`s, it takes care of the profiler, stopping
    lays out the main loop (`BaseDataUpdater.run`) and so on. It provides a common interface.
    """
    def __init__(self, data : DataAnalyser, debugger : Debugger = Debugger(), profiler : Profiler = None):
        """
        `data` is the `PINSoftware.DataAnalyser.DataAnalyser` to add the new data to.

        `debugger` is the `PINSoftware.Debugger.Debugger` to use for printouts.

        `profiler` is the `PINSoftware.Profiler.Profiler` to use (or None if a profiler should not be run).
        """
        super().__init__()
        self.should_stop = False
        self.data = data
        self.debugger = debugger
        self.profiler = profiler

    def on_start(self):
        """
        This is called when the `BaseDataUpdater.run` method is called. This method is meant to be
        overridden and is a way to run some code at the beginning of the run, it.
        """
        pass

    def loop(self):
        """
        This should be overridden by the actual data loading. This will be called continuously as the
        `PINSoftware.DataUpdater` runs. It should return the number of datapoints added (for the Profiler to use).
        """
        return 1

    def on_stop(self):
        """
        This is called when the `BaseDataUpdater.run` method is finishing. This method is meant to be
        overridden and is a way to run some code at the end of the run, it.
        """
        pass

    def run(self):
        """
        This method provides the main loop. This method is called when `BaseDataUpdater.start` is called.
        """
        self.debugger.info("Starting the DataUpdater")
        self.on_start()
        if self.profiler:
            self.profiler.start()
            while not self.should_stop:
                counts = self.loop()
                self.profiler.add_count(counts)
            self.profiler.stop()
        else:
            while not self.should_stop:
                self.loop()
        self.on_stop()
        self.debugger.info("Stopping the DataUpdater")

    def stop(self):
        """Just a simple setter, it is here to be consistent with starting by calling `BaseDataUpdater.start`"""
        self.should_stop = True


class LoadedDataUpdater(BaseDataUpdater):
    """
    This `PINSoftware.DataUpdater` is used for the "dummy" mode. It reads data from a text file and
    adds it to the `PINSoftware.DataAnalyser.DataAnalyser` at the specified frequency.
    """
    def __init__(self, filename : str, *args, freq : int = 50000, **kwargs):
        """
        `filename` is the path to the file to read the data from. The file should be a text file with a number
        on each line, those numbers are the ones added to the `PINSoftware.DataAnalyser.DataAnalyser`.

        `freq` is the frequency is the simulated source, it will add this many datapoints per second.

        `args` and `kwargs` are passed to the `BaseDataUpdater`.
        """
        super().__init__(*args, **kwargs)
        try:
            self.file = open(filename)
            while True:
                line = self.file.readline()
                if line[0] != "#":
                    break
        except Exception as e:
            self.debugger.error("Couldn't open file: " + filename)
            raise e

        self.timedelta = 1 / freq

    def on_start(self):
        self.next_call = time.time()

    def loop(self):
        try:
            new_y = float(self.file.readline())
        except ValueError:
            if self.file.readline() == "":
                self.debugger.error("Reached end of file")
                return
        except:
            self.debugger.warning("Couldn't parse line")
        self.data.append(new_y)
        self.next_call += self.timedelta
        time.sleep(max(0, self.next_call - time.time()))
        return 1

    def on_stop(self):
        self.file.close()


class NiDAQmxDataUpdater(BaseDataUpdater):
    """
    This is the most important `PINSoftware.DataUpdater`, this is the one actually reading from the NI-6002.
    It first checks if there is exactly one device and if the device is the NI-6002, if not, the app crashes.
    If it is, then it sets up a `nidaqmx.Task` and adds the correct channel to it. It then sets the `task` to continuous
    acquisition and reads the data.
    """
    def __init__(self, *args, **kwargs):
        """
        `args` and `kwargs` are passed to the `BaseDataUpdater`.
        """
        super().__init__(*args, **kwargs)

        self.system = nidaqmx.system.System.local()
        if len(self.system.devices) != 1:
            self.debugger.warning("There should be exactly one device connected, but there is: " + str(len(self.system.devices)) + ", the program may not work correctly")
        self.device = self.system.devices[0]
        if self.device.product_type != 'USB-6002':
            self.debugger.error("Incorrect device connected, exiting.")
            raise Exception
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(self.device.ai_physical_chans[0].name)
        self.task.timing.cfg_samp_clk_timing(50000, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

    def on_start(self):
        self.task.start()

    def loop(self):
        new_data = self.task.read(nidaqmx.constants.READ_ALL_AVAILABLE)
        for new_y in new_data:
            self.data.append(new_y)
        return len(new_data)

    def on_stop(self):
        self.task.stop()
        self.task.close()
