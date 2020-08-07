import datetime
import threading
import time

from os import path
from enum import Enum

import h5py


class Filetype(Enum):
    Csv = 0
    Hdf5 = 1

    def get_ext(self):
        if self == Filetype.Csv:
            return "csv"
        else:
            return "hdf5"

    @staticmethod
    def from_str(string):
        if string == "csv":
            return Filetype.Csv
        elif string == "hdf5":
            return Filetype.Hdf5
        else:
            return None

class SavingException(Exception):
    pass

class BaseDataSaver(threading.Thread):
    def __init__(self, data, full_filename, save_interval=1):
        super().__init__()
        self.should_stop = False
        self.data = data
        self.debugger = self.data.debugger
        self.full_filename = full_filename
        self.save_interval = save_interval

    def do_single_save(self):
        pass

    def close(self):
        pass
    
    def run(self):
        self.debugger.info("BaseDataSaver: Starting")
        next_call = time.time()
        while not self.should_stop:
            next_call += self.save_interval
            time.sleep(max(0, next_call - time.time()))
            self.do_single_save()
        self.close()
        self.debugger.info("BaseDataSaver: Stopped successfully")

    def stop(self):
        self.should_stop = True

class CsvDataSaver(BaseDataSaver):
    def __init__(self, data, save_folder, save_base_filename, **kwargs):
        full_filename = path.join(save_folder, save_base_filename + datetime.datetime.now().strftime("%y%m%d-%H%M%S") + ".csv")
        super().__init__(data, full_filename, **kwargs)
        try:
            self.csv_file = open(full_filename, 'w')
            self.debugger.info("CsvDataSaver: Successfully created csv file \"" + full_filename + "\"")
            self.csv_file.write("timestamps,processed_ys\n")
        except:
            raise SavingException("Could not open file \"" + full_filename + "\" to log data in.")
        self.index = 0

    def do_single_save(self):
        new_index = len(self.data.processed_ys)
        for pro_y, pro_times in zip(self.data.processed_ys[self.index:], self.data.processed_timestamps[self.index:]):
            self.csv_file.write(str(pro_times) + "," + str(pro_y) + "\n")
        self.index = new_index

    def close(self):
        self.do_single_save()
        self.csv_file.close()

class Hdf5DataSaver(BaseDataSaver):
    def __init__(self, data, save_folder, save_base_filename, items, **kwargs):
        full_filename = path.join(save_folder, save_base_filename + datetime.datetime.now().strftime("%y%m%d-%H%M%S") + ".hdf5")
        super().__init__(data, full_filename, **kwargs)
        try:
            self.hdf_file = h5py.File(full_filename, 'w')
            self.debugger.info("Hdf5DataSaver: Successfully created hdf5 file \"" + full_filename + "\"")

            self.hdf_file.attrs['freq'] = self.data.freq
            self.hdf_file.attrs['edge_detection_threshold'] = self.data.edge_detection_threshold
            self.hdf_file.attrs['average_count'] = self.data.average_count

            self.hdf_datasets = []
            self.indices = []
            self.data_sources = []

            if "ys" in items:
                self.hdf_datasets.append(self.hdf_file.create_dataset("ys", (0,), chunks=True, maxshape=(None,), dtype='f4'))
                self.indices.append(0)
                self.data_sources.append(self.data.ys)
            if "processed_ys" in items:
                self.hdf_datasets.append(self.hdf_file.create_dataset("processed_ys", (0,), chunks=True, maxshape=(None,), dtype='f4'))
                self.hdf_datasets.append(self.hdf_file.create_dataset("processed_timestamps", (0,), chunks=True, maxshape=(None,), dtype='f8'))
                self.indices.append(0)
                self.indices.append(0)
                self.data_sources.append(self.data.processed_ys)
                self.data_sources.append(self.data.processed_timestamps)
            if "averaged_processed_ys" in items:
                self.hdf_datasets.append(self.hdf_file.create_dataset("averaged_processed_ys", (0,), chunks=True, maxshape=(None,), dtype='f4'))
                self.hdf_datasets.append(self.hdf_file.create_dataset("averaged_processed_timestamps", (0,), chunks=True, maxshape=(None,), dtype='f8'))
                self.indices.append(0)
                self.indices.append(0)
                self.data_sources.append(self.data.averaged_processed_ys)
                self.data_sources.append(self.data.averaged_processed_timestamps)
            if "markers" in items:
                self.hdf_datasets.append(self.hdf_file.create_dataset("markers", (0,), chunks=True, maxshape=(None,), dtype='f4'))
                self.hdf_datasets.append(self.hdf_file.create_dataset("marker_timestamps", (0,), chunks=True, maxshape=(None,), dtype='f8'))
                self.indices.append(0)
                self.indices.append(0)
                self.data_sources.append(self.data.markers)
                self.data_sources.append(self.data.marker_timestamps)
        except:
            raise SavingException("Could not open file \"" + full_filename + "\" to log data in.")

    def do_single_save(self):
        new_indices = [len(source) for source in self.data_sources]
        for dataset, index, source, new_index in zip(self.hdf_datasets, self.indices, self.data_sources, new_indices):
            dataset.resize((new_index,))
            dataset[index:new_index] = source[index:new_index]
        self.indices = new_indices

    def close(self):
        self.hdf_file.close()
