import random
import threading
import time

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
