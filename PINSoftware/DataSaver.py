"""
This file is somewhat similar to `PINSoftware.DashComponents` in that there are a few support
definitions and then two implementations of the same thing along with a base class they both
inherit from and which sets a common interface. A `PINSoftware.DataSaver` here is an object
whose instance runs in a separate thread and periodically checks the
`PINSoftware.DataAnalyser.DataAnalyser` for new data and then saves it.
"""
import datetime
import threading
import time

from os import path
from enum import Enum
from typing import List

import h5py

from PINSoftware.DataAnalyser import DataAnalyser


class Filetype(Enum):
    """An enum to get the possible saving options reliably"""
    Csv = 0
    Hdf5 = 1

    def get_ext(self):
        """Returns the appropriate file extension for the file type"""
        if self == Filetype.Csv:
            return "csv"
        else:
            return "hdf5"

    @staticmethod
    def from_str(string):
        """A static method to get a `Filetype` from a string, it may return None if the string invalid"""
        if string == "csv":
            return Filetype.Csv
        elif string == "hdf5":
            return Filetype.Hdf5
        else:
            return None

class SavingException(Exception):
    """A general exception to be raised when an error occurred during saving"""
    pass

class BaseDataSaver(threading.Thread):
    """
    This class creates a common interface for all `PINSoftware.DataSaver`s. A new saver
    should inherit from this class and override the `BaseDataSaver.do_single_save` method
    to something which does the saving action itself. It can also possibly override the
    `BaseDataSaver.close` method which is called on ending the saving (usually you may want
    to close the file objects there).
    """
    def __init__(self, data : DataAnalyser, full_filename : str, save_interval : float = 1):
        """
        `data` is the `PINSoftware.DataAnalyser.DataAnalyser` from which the data should be saved.

        `full_filename` is the full path to the file where the data should be saved (with the extension).

        `save_interval` is the interval in which the `PINSoftware.DataSaver` should check for new data.
        """
        super().__init__()
        self.should_stop = False
        self.data = data
        self.debugger = self.data.debugger
        self.full_filename = full_filename
        self.save_interval = save_interval

    def do_single_save(self):
        """
        This method should be overridden. This method should check for new data
        and save it.
        """
        pass

    def close(self):
        """This method may be overridden, it is called at the end of saving"""
        pass
    
    def run(self):
        """This method is called when `BaseDataSaver.start` is called, it is the main loop"""
        self.debugger.info("BaseDataSaver: Starting")
        next_call = time.time()
        while not self.should_stop:
            next_call += self.save_interval
            time.sleep(max(0, next_call - time.time()))
            self.do_single_save()
        self.close()
        self.debugger.info("BaseDataSaver: Stopped successfully")

    def stop(self):
        """This is a simple setter, it is here to be analogous with the way the thread was started (`BaseDataSaver.start`)"""
        self.should_stop = True

class CsvDataSaver(BaseDataSaver):
    """
    This is a very simple `PINSoftware.DataSaver` with very few options. It saves the peak voltages
    (`PINSoftware.DataAnalyser.DataAnalyser.processed`) along with their timestamps in a csv file.
    The csv file format doesn't allow for storing multiple unrelated data easily so this is all.
    """
    def __init__(self, data : DataAnalyser, save_folder : str, save_base_filename : str, **kwargs):
        """
        Everything except `save_folder` and `save_base_filename` is passed to the `BaseDataSaver`.
        `save_folder` and `save_base_filename` are combined along with a timestamp into the
        `full_filename` which is passed to `BaseDataSaver`. An attempt is also made to open the file,
        if it fails `SavingException` is raised.
        """
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
        """."""
        new_index = len(self.data.processed_ys)
        for pro_y, pro_times in zip(self.data.processed_ys[self.index:], self.data.processed_timestamps[self.index:]):
            self.csv_file.write(str(pro_times) + "," + str(pro_y) + "\n")
        self.index = new_index

    def close(self):
        """."""
        self.do_single_save()
        self.csv_file.close()

class Hdf5DataSaver(BaseDataSaver):
    """
    This is the main saver, it can save all the data in an hdf5 file. The processing parameters are saved as
    attributes. It it possible to choose what data is saved using the `items` argument.
    """
    def __init__(self, data : DataAnalyser, save_folder : str, save_base_filename : str, items : List[str], **kwargs):
        """
        `data` and `kwargs` are passed to `BaseDataSaver`.

        `save_folder` and `save_base_filename` are combined along with a timestamp and extension to form the
        `full_filename`. The file is them opened, if that failed a `SavingException` is raised.

        `items` determine what data gets saved. It is a list of strings and if certain strings are in there,
        some data gets saved. If it contains "ys" raw data gets saved, "processed_ys" means peak voltages
        along with their timestamps, "averaged_processed_ys" means averaged peak voltages and their timestamps.
        Finally "markers" means markers and their timestamps.
        """
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
        """."""
        new_indices = [len(source) for source in self.data_sources]
        for dataset, index, source, new_index in zip(self.hdf_datasets, self.indices, self.data_sources, new_indices):
            dataset.resize((new_index,))
            dataset[index:new_index] = source[index:new_index]
        self.indices = new_indices

    def close(self):
        """."""
        self.hdf_file.close()
