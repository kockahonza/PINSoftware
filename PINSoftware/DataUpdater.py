import random
import threading
import time

import nidaqmx

from PINSoftware.Debugger import Debugger
from PINSoftware.DataAnalyser import DataAnalyser

class BaseDataUpdater(threading.Thread):
    def __init__(self, data, debugger=Debugger(), profiler=None):
        super().__init__()
        self.should_stop = False
        self.data = data
        self.debugger = debugger
        self.profiler = profiler

    def on_start(self):
        # This function is meant to be overridden
        pass

    def loop(self):
        # This function is meant to be overridden
        pass

    def on_stop(self):
        # This function is meant to be overridden
        pass

    def run(self):
        self.debugger.info("Starting the DataUpdater")
        self.on_start()
        if self.profiler:
            self.profiler.start()
            while not self.should_stop:
                counts = self.loop()
                self.profiler.add_count(counts)
        else:
            while not self.should_stop:
                self.loop()
        self.on_stop()
        self.debugger.info("Stopping the DataUpdater")

    def stop(self):
        self.should_stop = True
        if self.profiler:
            self.profiler.stop()


class LoadedDataUpdater(BaseDataUpdater):
    def __init__(self, filename, *args, freq=50000, **kw):
        super().__init__(*args, **kw)
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
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

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

