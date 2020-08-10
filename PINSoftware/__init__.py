"""
Here is a short overall description. When the program is run, it creates an instance of `PINSoftware.MachineStuff.MachineStuff`
(it will be referred to as `ms`) which represents all the hardware and data analysis. It also gets a dash app (a `dash.Dash` instance)
from `PINSoftware.DashApp.get_app`. It then runs the app in a server.

Then a user can connect and look through the app, however to start getting data he need to grab control.
When he does this a field of `ms` is set to his unique id and he can now run an experiment. When the user
clicks the start button in the user interface the `PINSoftware.MachineStuff.MachineStuff.start_experiment`
method of `ms` is called. When this happens `ms` creates a new instance of `PINSoftware.DataAnalyser.DataAnalyser` (`data`)
and a new `PINSoftware.DataUpdater`. The `PINSoftware.DataAnalyser.DataAnalyser` is like a buffer, but whenever a new datapoint is added to it
(using `PINSoftware.DataAnalyser.DataAnalyser.append`), it first does some processing on it and then appends new values to multiple
datasets it has as its fields. To be exact, the `PINSoftware.DataAnalyser.DataAnalyser` stores the raw data, the "peak voltages"
and the "averaged peak voltages" mentioned in the manual and the Help tab of the software. The `PINSoftware.DataUpdater` is either
a `PINSoftware.DataUpdater.NiDAQmxDataUpdater` (when the hardware is being used) or `PINSoftware.DataUpdater.LoadedDataUpdater`
(when in dummy mode).  What it does is, in a separate thread from the server it keeps loading data from the instrument as fast
as possible and calls the `PINSoftware.DataAnalyser.DataAnalyser.append` method of `data`. This way `data` keeps aggregating all
the data and the server (or anything else) can easily retrieve it from it.
If data saving was turned on, the `ms` will also get a `DataSaver` (either `PINSoftware.DataSaver.CsvDataSaver` or `PINSoftware.DataSaver.Hdf5DataSaver`)
and starts it in another thread. Those check in regular intervals for new data in the `PINSoftware.DataAnalyser.DataAnalyser` and save them.
Lastly the `PINSoftware.Profiler.Profiler` also works in the same way, if it was enabled, the `ms` creates a new instance and starts it.
Whenever the `PINSoftware.DataUpdater` adds new data it triggers the `PINSoftware.Profiler.Profiler` and it then counts those triggers
every second and prints them out.

"""
