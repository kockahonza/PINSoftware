import random
import threading
import time

from PINSoftware.DataUpdaterClasses.BaseDataUpdater import BaseDataUpdater

class RandomDataUpdater(BaseDataUpdater):
    def __init__(self, data, **kw):
        super().__init__(data, **kw)

    def loop(self):
        self.data.append(random.randint(0, 20))
        time.sleep(0.001)

