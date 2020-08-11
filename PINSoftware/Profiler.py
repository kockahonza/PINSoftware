import threading
import time

class Profiler(threading.Thread):
    """
    A very simple profiler. It keeps an internal counter and every second it prints
    out its value and resets it. `Profiler.add_count` is used to increment the counter.
    """
    def __init__(self, name : str = "PROFILER", start_delay : float = 1):
        """
        `name` is the name of the profiler, this is used when printing out so that the output is clear.

        `start_delay` is the time to wait after `Profiler.start` was called before actually starting.
        """
        super().__init__()
        self.should_stop = False
        self.start_delay = start_delay
        self.msg = "Profiler: \"" + name + "\""
        self.counts = 0
        self.log = []

    def add_count(self, counts=1):
        """Call this to increase the counter by `counts`"""
        self.counts += counts

    def run(self):
        """"""
        time.sleep(self.start_delay)
        self.counts = 0
        print(self.msg + " starting")
        next_call = time.time()
        while not self.should_stop:
            next_call += 1
            time.sleep(max(0, next_call - time.time()))
            self.log.append(self.counts)
            self.counts = 0
            print(self.msg + " counts: " + str(self.log[-1]))
        if self.log:
            print(self.msg + " run average: "+ str(sum(self.log[:-1])/len(self.log[:-1])))
        print(self.msg + " stopping")

    def stop(self):
        """Simple setter to stop the profiler"""
        self.should_stop = True
