import  threading

import nidaqmx

from PINDiode.DataUpdaterClasses.BaseDataUpdater import BaseDataUpdater

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

