import threading
import time

from PINDiode.DataUpdaterClasses.BaseDataUpdater import BaseDataUpdater

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
