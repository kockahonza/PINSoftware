import threading
import time

class Profiler(threading.Thread):
    def __init__(self, name="PROFILER", start_delay=1):
        super().__init__()
        self.should_stop = False
        self.start_delay = start_delay
        self.msg = "Profiler: \"" + name + "\""
        self.counts = 0
        self.log = []

    def add_count(self, counts=1):
        self.counts += counts

    def run(self):
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
        self.should_stop = True
