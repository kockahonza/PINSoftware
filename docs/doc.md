---
description: |
    API documentation for modules: PINSoftware, PINSoftware.DashApp, PINSoftware.DashComponents, PINSoftware.DataAnalyser, PINSoftware.DataSaver, PINSoftware.DataUpdater, PINSoftware.Debugger, PINSoftware.MachineState, PINSoftware.Profiler, PINSoftware.main, PINSoftware.util.

lang: en

classoption: oneside
geometry: margin=1in
papersize: a4

linkcolor: blue
links-as-notes: true
...


    
# Module `PINSoftware` {#PINSoftware}

Here is a short overall description. When the program is run, it creates an instance of <code>[MachineState](#PINSoftware.MachineState.MachineState "PINSoftware.MachineState.MachineState")</code>
(it will be referred to as <code>ms</code>) which represents all the hardware and data analysis. It also gets a dash app (a <code>dash.Dash</code> instance)
from <code>[get\_app()](#PINSoftware.DashApp.get\_app "PINSoftware.DashApp.get\_app")</code>. It then runs the app in a server.

Then a user can connect and look through the app, however to start getting data he need to grab control.
When he does this a field of <code>ms</code> is set to his unique id and he can now run an experiment. When the user
clicks the start button in the user interface the <code>[MachineState.start\_experiment()](#PINSoftware.MachineState.MachineState.start\_experiment "PINSoftware.MachineState.MachineState.start\_experiment")</code>
method of <code>ms</code> is called. When this happens <code>ms</code> creates a new instance of <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> (<code>data</code>)
and a new <code>[PINSoftware.DataUpdater](#PINSoftware.DataUpdater "PINSoftware.DataUpdater")</code>. The <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> is like a buffer, but whenever a new datapoint is added to it
(using <code>[DataAnalyser.append()](#PINSoftware.DataAnalyser.DataAnalyser.append "PINSoftware.DataAnalyser.DataAnalyser.append")</code>), it first does some processing on it and then appends new values to multiple
datasets it has as its fields. To be exact, the <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> stores the raw data, the "peak voltages"
and the "averaged peak voltages" mentioned in the manual and the Help tab of the software. The <code>[PINSoftware.DataUpdater](#PINSoftware.DataUpdater "PINSoftware.DataUpdater")</code> is either
a <code>[NiDAQmxDataUpdater](#PINSoftware.DataUpdater.NiDAQmxDataUpdater "PINSoftware.DataUpdater.NiDAQmxDataUpdater")</code> (when the hardware is being used) or <code>[LoadedDataUpdater](#PINSoftware.DataUpdater.LoadedDataUpdater "PINSoftware.DataUpdater.LoadedDataUpdater")</code>
(when in dummy mode).  What it does is, in a separate thread from the server it keeps loading data from the instrument as fast
as possible and calls the <code>[DataAnalyser.append()](#PINSoftware.DataAnalyser.DataAnalyser.append "PINSoftware.DataAnalyser.DataAnalyser.append")</code> method of <code>data</code>. This way <code>data</code> keeps aggregating all
the data and the server (or anything else) can easily retrieve it from it.
If data saving was turned on, the <code>ms</code> will also get a <code>[PINSoftware.DataSaver](#PINSoftware.DataSaver "PINSoftware.DataSaver")</code> (either <code>[CsvDataSaver](#PINSoftware.DataSaver.CsvDataSaver "PINSoftware.DataSaver.CsvDataSaver")</code> or <code>[Hdf5DataSaver](#PINSoftware.DataSaver.Hdf5DataSaver "PINSoftware.DataSaver.Hdf5DataSaver")</code>)
and starts it in another thread. Those check in regular intervals for new data in the <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> and save them.
Lastly the <code>[Profiler](#PINSoftware.Profiler.Profiler "PINSoftware.Profiler.Profiler")</code> also works in the same way, if it was enabled, the <code>ms</code> creates a new instance and starts it.
Whenever the <code>[PINSoftware.DataUpdater](#PINSoftware.DataUpdater "PINSoftware.DataUpdater")</code> adds new data it triggers the <code>[Profiler](#PINSoftware.Profiler.Profiler "PINSoftware.Profiler.Profiler")</code> and it then counts those triggers
every second and prints them out.

A note on naming, in the documentation I ofter refer to "peak voltage", in code I call that "processed_y", and "raw data" is just called "ys" in code.


    
## Sub-modules

* [PINSoftware.DashApp](#PINSoftware.DashApp)
* [PINSoftware.DashComponents](#PINSoftware.DashComponents)
* [PINSoftware.DataAnalyser](#PINSoftware.DataAnalyser)
* [PINSoftware.DataSaver](#PINSoftware.DataSaver)
* [PINSoftware.DataUpdater](#PINSoftware.DataUpdater)
* [PINSoftware.Debugger](#PINSoftware.Debugger)
* [PINSoftware.MachineState](#PINSoftware.MachineState)
* [PINSoftware.Profiler](#PINSoftware.Profiler)
* [PINSoftware.main](#PINSoftware.main)
* [PINSoftware.util](#PINSoftware.util)






    
# Module `PINSoftware.DashApp` {#PINSoftware.DashApp}






    
## Functions


    
### Function `linear_correct_func` {#PINSoftware.DashApp.linear_correct_func}




>     def linear_correct_func(
>         cor_a,
>         cor_b
>     )


Get a linear function with <code>a</code> and <code>b</code> as its coefficients

    
### Function `get_app` {#PINSoftware.DashApp.get_app}




>     def get_app(
>         ms: PINSoftware.MachineState.MachineState
>     ) ‑> dash.dash.Dash


Creates the Dash app and creates all the callbacks.
<code>ms</code> is the MachineState instance to which callbacks should be connected.
Returns a <code>dash.Dash</code> instance to be run.




    
# Module `PINSoftware.DashComponents` {#PINSoftware.DashComponents}

This file has all the custom dash components used for the app. Some of the
most important ones are the graphs so I will give a bit of explanation to them.

There are two types of graphs defined here - <code>[FullRedrawGraph()](#PINSoftware.DashComponents.FullRedrawGraph "PINSoftware.DashComponents.FullRedrawGraph")</code> and <code>[ExtendableGraph()](#PINSoftware.DashComponents.ExtendableGraph "PINSoftware.DashComponents.ExtendableGraph")</code>.
The difference being that only the ExtendableGraph can be extended without resending all the data.
Both graphs are created in a container with a title, controls and an interval. Both have
at least two switches, the "Show graph" and the "Update graph" buttons. When "Show graph" is
off the graph is not rendered and its "Update graph" button is disabled. The "Update graph"
toggles the interval, when it is enabled the interval runs, otherwise not. Each type uses the
interval differently but both use it to update. More on in their respective documentations.




    
## Functions


    
### Function `SingleSwitch` {#PINSoftware.DashComponents.SingleSwitch}




>     def SingleSwitch(
>         id_,
>         label,
>         default=False
>     )


This returns a dash component containing a single switch (a nice looking checkbox)
(not a part of a Checklist) using bootstrap.

<code>id</code> is the id of the Checkbox component inside.

<code>label</code> is the label shown beside it.

<code>default</code> is the default value of the switch.

    
### Function `get_base_graph_callbacks` {#PINSoftware.DashComponents.get_base_graph_callbacks}




>     def get_base_graph_callbacks(
>         app: dash.dash.Dash,
>         name: str
>     )


This adds the most basic callbacks to a graph. It takes car of two things.
Disabling the interval when the "Update graph" switch is off and disabling the
"Update graph" when the "Show graph" button is off.

    
### Function `BaseGraph` {#PINSoftware.DashComponents.BaseGraph}




>     def BaseGraph(
>         app: dash.dash.Dash,
>         name: str,
>         title: str,
>         interval: int = 2000,
>         additional_controls=[],
>         base_fig={}
>     )


This creates a dash component with the most basic stuff for an updating graph.
It sets up the container, the controls and the <code>dash\_core\_components.Interval</code>.
It also sets up the basic callbacks using <code>[get\_base\_graph\_callbacks()](#PINSoftware.DashComponents.get\_base\_graph\_callbacks "PINSoftware.DashComponents.get\_base\_graph\_callbacks")</code>.

<code>app</code> is the app to add the callbacks to.

<code>name</code> is the <code>dash\_core\_components.Graph</code> component id.

<code>title</code> is the title of the graph, shown at the top of the container.

<code>interval</code> is the <code>dash\_core\_components.Interval</code> interval in milliseconds.

<code>additional\_controls</code> is a list of dash components with should be added in the container,
this is useful when you want to add additional controls to the graph.

<code>base\_fig</code> is what to set the <code>figure</code> property of the <code>dash\_core\_components.Graph</code> (it can be changed later though).

    
### Function `get_full_redraw_graph_callbacks` {#PINSoftware.DashComponents.get_full_redraw_graph_callbacks}




>     def get_full_redraw_graph_callbacks(
>         app: dash.dash.Dash,
>         ms: PINSoftware.MachineState.MachineState,
>         name: str,
>         fig_func,
>         **kwargs
>     )


Adds callbacks to a <code>[FullRedrawGraph()](#PINSoftware.DashComponents.FullRedrawGraph "PINSoftware.DashComponents.FullRedrawGraph")</code>. Specifically, whenever the <code>dash\_core\_components.Interval</code>
triggers, if there is <code>ms.data</code> then the <code>figure\_func</code> is called and its result is set as the new figure.

<code>app</code> the dash app to add the callbacks to.

If <code>fig\_func\_output</code> is a keyword argument, then its value is set as the output of the interval
trigger callback (this is the one where <code>fig\_func</code> is used).

If <code>fig\_func\_state</code> is a keyword argument, then its value is set as the state of the interval
trigger callback (this is the one where <code>fig\_func</code> is used).

The only thing that is fixed is the callback inputs.

    
### Function `FullRedrawGraph` {#PINSoftware.DashComponents.FullRedrawGraph}




>     def FullRedrawGraph(
>         app: dash.dash.Dash,
>         ms: PINSoftware.MachineState.MachineState,
>         name: str,
>         title: str,
>         fig_func,
>         interval: int = 2000,
>         additional_controls=[],
>         **kwargs
>     )


Get a graph which whenever it is updated, the whole figure is changed and passed over the network.

<code>app</code> the dash app to add the callbacks to.

<code>ms</code> the <code>[MachineState](#PINSoftware.MachineState.MachineState "PINSoftware.MachineState.MachineState")</code> to use for checking for data.

<code>name</code> is the <code>dash\_core\_components.Graph</code> component id.

<code>title</code> is the title of the graph, shown at the top of the container.

<code>fig\_func</code> is the function to call on update. It is only called when <code>ms.data</code> is not None.
Its output is the graph figure by default but can be changed using the <code>fig\_func\_output</code> keyword
argument. It can also get more arguments, the callback state can be changed by the <code>fig\_func\_state</code>
keyword argument.

<code>interval</code> is the <code>dash\_core\_components.Interval</code> interval in milliseconds.

<code>additional\_controls</code> is a list of dash components with should be added in the container,
this is useful when you want to add additional controls to the graph.

    
### Function `get_extendable_graph_callbacks` {#PINSoftware.DashComponents.get_extendable_graph_callbacks}




>     def get_extendable_graph_callbacks(
>         app: dash.dash.Dash,
>         ms: PINSoftware.MachineState.MachineState,
>         name: str,
>         extend_func,
>         base_fig,
>         **kwargs
>     )


Adds callbacks to a <code>[ExtendableGraph()](#PINSoftware.DashComponents.ExtendableGraph "PINSoftware.DashComponents.ExtendableGraph")</code>. It adds two callbacks, Firstly, whenever
the "Stop" button is enabled, the graphs figure is set to <code>base\_fig</code>. The second one is
that whenever the interval triggers, the graph is extended using <code>extend\_func</code>.

<code>app</code> the dash app to add the callbacks to.

If <code>extend\_func\_output</code> is a keyword argument, then its value is set as the output of the callback
using <code>extend\_func</code> (the interval one). The default is the graph 'extendData'.

If <code>extend\_func\_state</code> is a keyword argument, then its value is set as the state of the callback
using <code>extend\_func</code> (the interval one). The default is an empty list.

The only thing that is fixed is the callback inputs.

    
### Function `ExtendableGraph` {#PINSoftware.DashComponents.ExtendableGraph}




>     def ExtendableGraph(
>         app: dash.dash.Dash,
>         ms: PINSoftware.MachineState.MachineState,
>         name: str,
>         title: str,
>         base_fig,
>         extend_func,
>         interval: int = 2000,
>         additional_controls=[],
>         **kwargs
>     )


Get a graph to which new data is added instead of redrawing it completely. Its figure
is first set to <code>base\_fig</code> and is then updated using <code>extend\_func</code>

<code>app</code> the dash app to add the callbacks to.

<code>ms</code> the <code>[MachineState](#PINSoftware.MachineState.MachineState "PINSoftware.MachineState.MachineState")</code> to use for checking for data.

<code>name</code> is the <code>dash\_core\_components.Graph</code> component id.

<code>title</code> is the title of the graph, shown at the top of the container.

<code>base\_fig</code> is the basic figure. This is what the figure property of the <code>dash\_core\_components.Graph</code>
is set to when the page loads and whenever the "Stop" button becomes enabled (this is to reset when the
next acquisition starts) (however this means that it will not reset on new data acquisition for users who
are not controlling the setup at that point! Just keep that in mind).

<code>extend\_func</code> is the function to call on 'update', this is whenever the interval triggers. Its output
is what is sent to the <code>dash\_core\_components.Graph</code>s <code>extendData</code> property by default but can be
changed using the <code>extend\_func\_output</code> keyword argument.  It can also get more arguments, the callback
state can be changed by the <code>extend\_func\_state</code> keyword argument.

<code>interval</code> is the <code>dash\_core\_components.Interval</code> interval in milliseconds.

<code>additional\_controls</code> is a list of dash components with should be added in the container,
this is useful when you want to add additional controls to the graph.




    
# Module `PINSoftware.DataAnalyser` {#PINSoftware.DataAnalyser}






    
## Functions


    
### Function `remove_outliers` {#PINSoftware.DataAnalyser.remove_outliers}




>     def remove_outliers(
>         data
>     )





    
## Classes


    
### Class `DataAnalyser` {#PINSoftware.DataAnalyser.DataAnalyser}




>     class DataAnalyser(
>         data_frequency: int,
>         plot_buffer_len: int = 200,
>         debugger: PINSoftware.Debugger.Debugger = <PINSoftware.Debugger.Debugger object>,
>         edge_detection_threshold: float = 0.005,
>         average_count: int = 50,
>         correction_func=<function DataAnalyser.<lambda>>
>     )


This class takes care of data analysis and storage.

Once this function is created, you should call <code>[DataAnalyser.append()](#PINSoftware.DataAnalyser.DataAnalyser.append "PINSoftware.DataAnalyser.DataAnalyser.append")</code> to add a new data point,
use <code>DataAnalyser.ys</code> to get the raw data, <code>DataAnalyser.processed</code> to get the peak voltages,
<code>DataAnalyser.processed\_timestamps</code> are timestamps corresponding to the peak voltages,
<code>DataAnalyser.averaged\_processed\_ys</code> are the averaged peak voltages and <code>DataAnalyser.averaged\_processed\_timestamps</code>
are timestamps corresponding to the averages. Lastly <code>DataAnalyser.markers</code> and <code>DataAnalyser.marker\_timestamps</code>
are debug markers and their timestamps, those can be anything and are only adjustable from code, they should
not be used normally.

All the timestamps used here are based on the length of <code>DataAnalyser.ys</code> at the time. This is very
useful for two reasons, its easy to calculate so also fast. Bu mostly because later when you plot the data,
you can plot the <code>DataAnalyser.ys</code> with "x0=0" and "dx=1" and then plot the peak averaged directly and the data
will be correctly scaled on the x axis. The problem is however that this assumes that the data comes at a
precise frequency but the NI-6002 can offer that so it should be alright.

<code>data\_frequency</code> is the frequency of the incoming data, this is used for calculating real timestamps
and is saved if hdf5 saving is enabled.

<code>plot\_buffer\_len</code> determines how many datapoints should be plotted in the live plot graph (if the
server has been run with the graphing option).

<code>debugger</code> is the debugger to use.

<code>edge\_detection\_threshold</code>, <code>average\_count</code> and <code>correction\_func</code> are processing parameters. They
are described in the Help tab of the program.

<code>edge\_detection\_threshold</code> sets the voltage difference required to find a section transition.

<code>average\_count</code> is how many peak voltages should be averaged to get the averaged peak voltages.

<code>correction\_func</code> is the function to run the peak voltages through before using them. This is
to correct some systematic errors or do some calculations.







    
#### Methods


    
##### Method `on_start` {#PINSoftware.DataAnalyser.DataAnalyser.on_start}




>     def on_start(
>         self
>     )




    
##### Method `actual_append_first` {#PINSoftware.DataAnalyser.DataAnalyser.actual_append_first}




>     def actual_append_first(
>         self,
>         new_processed_y
>     )


This appends the new processed value, works on the averaged processed values and
possibly appends that too. This is when the first processed value comes in.
It sets some initial values, after it runs once <code>[DataAnalyser.actual\_append\_main()](#PINSoftware.DataAnalyser.DataAnalyser.actual\_append\_main "PINSoftware.DataAnalyser.DataAnalyser.actual\_append\_main")</code>
is called instead.

    
##### Method `actual_append_main` {#PINSoftware.DataAnalyser.DataAnalyser.actual_append_main}




>     def actual_append_main(
>         self,
>         new_processed_y
>     )


This appends the new processed value, works on the averaged processed values and
possibly appends that too. For the first processed value, <code>[DataAnalyser.actual\_append\_first()](#PINSoftware.DataAnalyser.DataAnalyser.actual\_append\_first "PINSoftware.DataAnalyser.DataAnalyser.actual\_append\_first")</code>
is run instead, but afterwards this is.

    
##### Method `handle_processing` {#PINSoftware.DataAnalyser.DataAnalyser.handle_processing}




>     def handle_processing(
>         self,
>         new_y
>     )


This is the main processing function. It gets the new y (which
at this point is not in <code>DataAnalyser.ys</code> yet) and does some processing on it.
It may add new values to <code>DataAnalyser.processed</code> and <code>DataAnalyser.averaged\_processed\_ys</code>
if new values were found through <code>DataAnalyser.actual\_append</code>. If the data does not add up
a warning is printed. I won't describe the logic here as it is described in the manual and also
it may still be best to look through the code.

    
##### Method `append` {#PINSoftware.DataAnalyser.DataAnalyser.append}




>     def append(
>         self,
>         new_y
>     )


The main apppend function through which new data is added. It just passes
the value to the processing function and appends it to <code>DataAnalyser.ys</code> in the end.

    
##### Method `on_stop` {#PINSoftware.DataAnalyser.DataAnalyser.on_stop}




>     def on_stop(
>         self
>     )




    
##### Method `plot` {#PINSoftware.DataAnalyser.DataAnalyser.plot}




>     def plot(
>         self,
>         plt
>     )


This is what plots the data on the raw data graph if graphing is enabled



    
# Module `PINSoftware.DataSaver` {#PINSoftware.DataSaver}

This file is somewhat similar to <code>[PINSoftware.DashComponents](#PINSoftware.DashComponents "PINSoftware.DashComponents")</code> in that there are a few support
definitions and then two implementations of the same thing along with a base class they both
inherit from and which sets a common interface. A <code>[PINSoftware.DataSaver](#PINSoftware.DataSaver "PINSoftware.DataSaver")</code> here is an object
whose instance runs in a separate thread and periodically checks the
<code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> for new data and then saves it.





    
## Classes


    
### Class `Filetype` {#PINSoftware.DataSaver.Filetype}




>     class Filetype(
>         value,
>         names=None,
>         *,
>         module=None,
>         qualname=None,
>         type=None,
>         start=1
>     )


An enum to get the possible saving options reliably


    
#### Ancestors (in MRO)

* [enum.Enum](#enum.Enum)



    
#### Class variables


    
##### Variable `Csv` {#PINSoftware.DataSaver.Filetype.Csv}






    
##### Variable `Hdf5` {#PINSoftware.DataSaver.Filetype.Hdf5}









    
### Class `SavingException` {#PINSoftware.DataSaver.SavingException}




>     class SavingException(
>         ...
>     )


A general exception to be raised when an error occurred during saving


    
#### Ancestors (in MRO)

* [builtins.Exception](#builtins.Exception)
* [builtins.BaseException](#builtins.BaseException)






    
### Class `BaseDataSaver` {#PINSoftware.DataSaver.BaseDataSaver}




>     class BaseDataSaver(
>         data: PINSoftware.DataAnalyser.DataAnalyser,
>         full_filename: str,
>         save_interval: float = 1
>     )


This class creates a common interface for all <code>[PINSoftware.DataSaver](#PINSoftware.DataSaver "PINSoftware.DataSaver")</code>s. A new saver
should inherit from this class and override the <code>[BaseDataSaver.do\_single\_save()](#PINSoftware.DataSaver.BaseDataSaver.do\_single\_save "PINSoftware.DataSaver.BaseDataSaver.do\_single\_save")</code> method
to something which does the saving action itself. It can also possibly override the
<code>[BaseDataSaver.close()](#PINSoftware.DataSaver.BaseDataSaver.close "PINSoftware.DataSaver.BaseDataSaver.close")</code> method which is called on ending the saving (usually you may want
to close the file objects there).

<code>data</code> is the <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> from which the data should be saved.

<code>full\_filename</code> is the full path to the file where the data should be saved (with the extension).

<code>save\_interval</code> is the interval in which the <code>[PINSoftware.DataSaver](#PINSoftware.DataSaver "PINSoftware.DataSaver")</code> should check for new data.


    
#### Ancestors (in MRO)

* [threading.Thread](#threading.Thread)


    
#### Descendants

* [PINSoftware.DataSaver.CsvDataSaver](#PINSoftware.DataSaver.CsvDataSaver)
* [PINSoftware.DataSaver.Hdf5DataSaver](#PINSoftware.DataSaver.Hdf5DataSaver)





    
#### Methods


    
##### Method `do_single_save` {#PINSoftware.DataSaver.BaseDataSaver.do_single_save}




>     def do_single_save(
>         self
>     )


This method should be overridden. This method should check for new data
and save it.

    
##### Method `close` {#PINSoftware.DataSaver.BaseDataSaver.close}




>     def close(
>         self
>     )


This method may be overridden, it is called at the end of saving

    
##### Method `run` {#PINSoftware.DataSaver.BaseDataSaver.run}




>     def run(
>         self
>     )


This method is called when <code>BaseDataSaver.start</code> is called, it is the main loop

    
##### Method `stop` {#PINSoftware.DataSaver.BaseDataSaver.stop}




>     def stop(
>         self
>     )


This is a simple setter, it is here to be analogous with the way the thread was started (<code>BaseDataSaver.start</code>)

    
### Class `CsvDataSaver` {#PINSoftware.DataSaver.CsvDataSaver}




>     class CsvDataSaver(
>         data: PINSoftware.DataAnalyser.DataAnalyser,
>         save_folder: str,
>         save_base_filename: str,
>         **kwargs
>     )


This is a very simple <code>[PINSoftware.DataSaver](#PINSoftware.DataSaver "PINSoftware.DataSaver")</code> with very few options. It saves the peak voltages
(<code>PINSoftware.DataAnalyser.DataAnalyser.processed</code>) along with their timestamps in a csv file.
The csv file format doesn't allow for storing multiple unrelated data easily so this is all.

Everything except <code>save\_folder</code> and <code>save\_base\_filename</code> is passed to the <code>[BaseDataSaver](#PINSoftware.DataSaver.BaseDataSaver "PINSoftware.DataSaver.BaseDataSaver")</code>.
<code>save\_folder</code> and <code>save\_base\_filename</code> are combined along with a timestamp into the
<code>full\_filename</code> which is passed to <code>[BaseDataSaver](#PINSoftware.DataSaver.BaseDataSaver "PINSoftware.DataSaver.BaseDataSaver")</code>. An attempt is also made to open the file,
if it fails <code>[SavingException](#PINSoftware.DataSaver.SavingException "PINSoftware.DataSaver.SavingException")</code> is raised.


    
#### Ancestors (in MRO)

* [PINSoftware.DataSaver.BaseDataSaver](#PINSoftware.DataSaver.BaseDataSaver)
* [threading.Thread](#threading.Thread)






    
#### Methods


    
##### Method `do_single_save` {#PINSoftware.DataSaver.CsvDataSaver.do_single_save}




>     def do_single_save(
>         self
>     )


.

    
##### Method `close` {#PINSoftware.DataSaver.CsvDataSaver.close}




>     def close(
>         self
>     )


.

    
### Class `Hdf5DataSaver` {#PINSoftware.DataSaver.Hdf5DataSaver}




>     class Hdf5DataSaver(
>         data: PINSoftware.DataAnalyser.DataAnalyser,
>         save_folder: str,
>         save_base_filename: str,
>         items: List[str],
>         **kwargs
>     )


This is the main saver, it can save all the data in an hdf5 file. The processing parameters are saved as
attributes. It it possible to choose what data is saved using the <code>items</code> argument.

<code>data</code> and <code>kwargs</code> are passed to <code>[BaseDataSaver](#PINSoftware.DataSaver.BaseDataSaver "PINSoftware.DataSaver.BaseDataSaver")</code>.

<code>save\_folder</code> and <code>save\_base\_filename</code> are combined along with a timestamp and extension to form the
<code>full\_filename</code>. The file is them opened, if that failed a <code>[SavingException](#PINSoftware.DataSaver.SavingException "PINSoftware.DataSaver.SavingException")</code> is raised.

<code>items</code> determine what data gets saved. It is a list of strings and if certain strings are in there,
some data gets saved. If it contains "ys" raw data gets saved, "processed_ys" means peak voltages
along with their timestamps, "averaged_processed_ys" means averaged peak voltages and their timestamps.
Finally "markers" means markers and their timestamps.


    
#### Ancestors (in MRO)

* [PINSoftware.DataSaver.BaseDataSaver](#PINSoftware.DataSaver.BaseDataSaver)
* [threading.Thread](#threading.Thread)






    
#### Methods


    
##### Method `do_single_save` {#PINSoftware.DataSaver.Hdf5DataSaver.do_single_save}




>     def do_single_save(
>         self
>     )


.

    
##### Method `close` {#PINSoftware.DataSaver.Hdf5DataSaver.close}




>     def close(
>         self
>     )


.



    
# Module `PINSoftware.DataUpdater` {#PINSoftware.DataUpdater}







    
## Classes


    
### Class `BaseDataUpdater` {#PINSoftware.DataUpdater.BaseDataUpdater}




>     class BaseDataUpdater(
>         data: PINSoftware.DataAnalyser.DataAnalyser,
>         debugger: PINSoftware.Debugger.Debugger = <PINSoftware.Debugger.Debugger object>,
>         profiler: PINSoftware.Profiler.Profiler = None
>     )


Base class for <code>PINSoftware.DataUpdater.DataUpdater</code>s, it takes care of the profiler, stopping
lays out the main loop (<code>[BaseDataUpdater.run()](#PINSoftware.DataUpdater.BaseDataUpdater.run "PINSoftware.DataUpdater.BaseDataUpdater.run")</code>) and so on. It provides a common interface.

<code>data</code> is the <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> to add the new data to.

<code>debugger</code> is the <code>[Debugger](#PINSoftware.Debugger.Debugger "PINSoftware.Debugger.Debugger")</code> to use for printouts.

<code>profiler</code> is the <code>[Profiler](#PINSoftware.Profiler.Profiler "PINSoftware.Profiler.Profiler")</code> to use (or None if a profiler should not be run).


    
#### Ancestors (in MRO)

* [threading.Thread](#threading.Thread)


    
#### Descendants

* [PINSoftware.DataUpdater.LoadedDataUpdater](#PINSoftware.DataUpdater.LoadedDataUpdater)
* [PINSoftware.DataUpdater.NiDAQmxDataUpdater](#PINSoftware.DataUpdater.NiDAQmxDataUpdater)





    
#### Methods


    
##### Method `on_start` {#PINSoftware.DataUpdater.BaseDataUpdater.on_start}




>     def on_start(
>         self
>     )


This is called when the <code>[BaseDataUpdater.run()](#PINSoftware.DataUpdater.BaseDataUpdater.run "PINSoftware.DataUpdater.BaseDataUpdater.run")</code> method is called. This method is meant to be
overridden and is a way to run some code at the beginning of the run, it.

    
##### Method `loop` {#PINSoftware.DataUpdater.BaseDataUpdater.loop}




>     def loop(
>         self
>     ) ‑> int


This should be overridden by the actual data loading. This will be called continuously as the
<code>[PINSoftware.DataUpdater](#PINSoftware.DataUpdater "PINSoftware.DataUpdater")</code> runs. It should return the number of datapoints added (for the Profiler to use).

    
##### Method `on_stop` {#PINSoftware.DataUpdater.BaseDataUpdater.on_stop}




>     def on_stop(
>         self
>     )


This is called when the <code>[BaseDataUpdater.run()](#PINSoftware.DataUpdater.BaseDataUpdater.run "PINSoftware.DataUpdater.BaseDataUpdater.run")</code> method is finishing. This method is meant to be
overridden and is a way to run some code at the end of the run, it.

    
##### Method `run` {#PINSoftware.DataUpdater.BaseDataUpdater.run}




>     def run(
>         self
>     )


This method provides the main loop. This method is called when <code>BaseDataUpdater.start</code> is called.

    
##### Method `stop` {#PINSoftware.DataUpdater.BaseDataUpdater.stop}




>     def stop(
>         self
>     )


Just a simple setter, it is here to be consistent with starting by calling <code>BaseDataUpdater.start</code>

    
### Class `LoadedDataUpdater` {#PINSoftware.DataUpdater.LoadedDataUpdater}




>     class LoadedDataUpdater(
>         filename: str,
>         *args,
>         freq: int = 50000,
>         **kwargs
>     )


This <code>[PINSoftware.DataUpdater](#PINSoftware.DataUpdater "PINSoftware.DataUpdater")</code> is used for the "dummy" mode. It reads data from a text file and
adds it to the <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> at the specified frequency.

<code>filename</code> is the path to the file to read the data from. The file should be a text file with a number
on each line, those numbers are the ones added to the <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code>.

<code>freq</code> is the frequency is the simulated source, it will add this many datapoints per second.

<code>args</code> and <code>kwargs</code> are passed to the <code>[BaseDataUpdater](#PINSoftware.DataUpdater.BaseDataUpdater "PINSoftware.DataUpdater.BaseDataUpdater")</code>.


    
#### Ancestors (in MRO)

* [PINSoftware.DataUpdater.BaseDataUpdater](#PINSoftware.DataUpdater.BaseDataUpdater)
* [threading.Thread](#threading.Thread)






    
### Class `NiDAQmxDataUpdater` {#PINSoftware.DataUpdater.NiDAQmxDataUpdater}




>     class NiDAQmxDataUpdater(
>         *args,
>         **kwargs
>     )


This is the most important <code>[PINSoftware.DataUpdater](#PINSoftware.DataUpdater "PINSoftware.DataUpdater")</code>, this is the one actually reading from the NI-6002.
It first checks if there is exactly one device and if the device is the NI-6002, if not, the app crashes.
If it is, then it sets up a <code>nidaqmx.Task</code> and adds the correct channel to it. It then sets the <code>task</code> to continuous
acquisition and reads the data.

<code>args</code> and <code>kwargs</code> are passed to the <code>[BaseDataUpdater](#PINSoftware.DataUpdater.BaseDataUpdater "PINSoftware.DataUpdater.BaseDataUpdater")</code>.


    
#### Ancestors (in MRO)

* [PINSoftware.DataUpdater.BaseDataUpdater](#PINSoftware.DataUpdater.BaseDataUpdater)
* [threading.Thread](#threading.Thread)








    
# Module `PINSoftware.Debugger` {#PINSoftware.Debugger}







    
## Classes


    
### Class `Debugger` {#PINSoftware.Debugger.Debugger}




>     class Debugger(
>         exit_on_error=True
>     )


A very simple IO handler, it is here to make printouts more consistent and easy to find.
Calling <code>[Debugger.error()](#PINSoftware.Debugger.Debugger.error "PINSoftware.Debugger.Debugger.error")</code> is also the correct way to exit on error.

If <code>exit\_on\_error</code> is true, then whenever <code>Debugger.exit</code> is called, the program halts.







    
#### Methods


    
##### Method `info` {#PINSoftware.Debugger.Debugger.info}




>     def info(
>         self,
>         msg
>     )




    
##### Method `warning` {#PINSoftware.Debugger.Debugger.warning}




>     def warning(
>         self,
>         msg
>     )




    
##### Method `error` {#PINSoftware.Debugger.Debugger.error}




>     def error(
>         self,
>         msg,
>         n=1
>     )






    
# Module `PINSoftware.MachineState` {#PINSoftware.MachineState}







    
## Classes


    
### Class `MachineState` {#PINSoftware.MachineState.MachineState}




>     class MachineState(
>         plt,
>         dummy: bool,
>         dummy_data_file: str,
>         profiler: bool = False,
>         plot_update_interval: int = 100,
>         log_directory: str = 'logs'
>     )


This is the main class covering all hardware control and data analysis (everything except the UI).
There should always be only one instance at a time and the program keeps it for the whole duration
of the run.

<code>plt</code> should be the <code>matplotlib.pyplot</code> module or something equivalent, this is for plotting the live
data graph on the host machine when the graphing option is enabled.

<code>dummy</code> determines whether the data should be grabbed from the NI-6002 or a dummy file. If <code>dummy</code> is
True, <code>dummy\_data\_file</code> should be specified otherwise the program will crash.

<code>dummy\_data\_file</code> is a path to the data to use for dummy mode.

<code>profiler</code> is whether the DataUpdater should be profiled.

<code>plot\_update\_interval</code> is the update interval of the live data graph.

<code>log\_directory</code> is the directory where to put saved data.







    
#### Methods


    
##### Method `init_graph` {#PINSoftware.MachineState.MachineState.init_graph}




>     def init_graph(
>         self
>     )


Setup for the live graphing

    
##### Method `animate` {#PINSoftware.MachineState.MachineState.animate}




>     def animate(
>         self,
>         i
>     )


The animate function for the <code>animation.FuncAnimation</code> class

    
##### Method `onKeyPress` {#PINSoftware.MachineState.MachineState.onKeyPress}




>     def onKeyPress(
>         self,
>         event
>     )


The function to call when a key is pressed in the live graph window

    
##### Method `run_graphing` {#PINSoftware.MachineState.MachineState.run_graphing}




>     def run_graphing(
>         self
>     )


This runs the actual graphing, this hangs until the window is closed

    
##### Method `grab_control` {#PINSoftware.MachineState.MachineState.grab_control}




>     def grab_control(
>         self,
>         controller_sid
>     )


Wrapper around the <code>MachineState.controller</code> field where extra effects can be added,
called when someone grabs control.

    
##### Method `release_control` {#PINSoftware.MachineState.MachineState.release_control}




>     def release_control(
>         self
>     )


Wrapper around the <code>MachineState.controller</code> field where extra effects can be added,
called when the control is released.

    
##### Method `start_experiment` {#PINSoftware.MachineState.MachineState.start_experiment}




>     def start_experiment(
>         self,
>         save_base_filename: str = None,
>         save_filetype: PINSoftware.DataSaver.Filetype = Filetype.Csv,
>         items: List[str] = ['ys', 'processed_ys'],
>         **kwargs
>     )


This starts a data acquisition run. It creates a new <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> and an appropriate <code>DataUpdater</code>.
Then it may also create and start a <code>DataSaver</code> and/or a <code>Profiler</code> based on the situation.

<code>save\_base\_filename</code> is the base part of the filename for the new log file. The <code>save\_base\_filename</code>
is appended with a timestamp and an appropriate file extension and that makes up the filename.

<code>save\_filetype</code> determines the <code>DataSaver</code> type, more information in <code>[PINSoftware.DataSaver](#PINSoftware.DataSaver "PINSoftware.DataSaver")</code>.

<code>items</code> is used when <code>save\_filetype</code> is <code>[Filetype.Hdf5](#PINSoftware.DataSaver.Filetype.Hdf5 "PINSoftware.DataSaver.Filetype.Hdf5")</code> and is passed to the
<code>[Hdf5DataSaver](#PINSoftware.DataSaver.Hdf5DataSaver "PINSoftware.DataSaver.Hdf5DataSaver")</code>.

<code>kwargs</code> are passed to the new <code>[DataAnalyser](#PINSoftware.DataAnalyser.DataAnalyser "PINSoftware.DataAnalyser.DataAnalyser")</code> instance.

More information on how it all works look in the module documentation: <code>[PINSoftware](#PINSoftware "PINSoftware")</code>.

    
##### Method `stop_experiment` {#PINSoftware.MachineState.MachineState.stop_experiment}




>     def stop_experiment(
>         self
>     )


This stops the current experiment and all the threads working on it

    
##### Method `stop_everything` {#PINSoftware.MachineState.MachineState.stop_everything}




>     def stop_everything(
>         self
>     )


This currently just calls <code>stop\_experiment</code> but there might be stuff added here,
this is meant to be a sort of stop all button

    
##### Method `delete_logs` {#PINSoftware.MachineState.MachineState.delete_logs}




>     def delete_logs(
>         self
>     )






    
# Module `PINSoftware.Profiler` {#PINSoftware.Profiler}







    
## Classes


    
### Class `Profiler` {#PINSoftware.Profiler.Profiler}




>     class Profiler(
>         name: str = 'PROFILER',
>         start_delay: float = 1
>     )


A very simple profiler. It keeps an internal counter and every second it prints
out its value and resets it. <code>[Profiler.add\_count()](#PINSoftware.Profiler.Profiler.add\_count "PINSoftware.Profiler.Profiler.add\_count")</code> is used to increment the counter.

<code>name</code> is the name of the profiler, this is used when printing out so that the output is clear.

<code>start\_delay</code> is the time to wait after <code>Profiler.start</code> was called before actually starting.


    
#### Ancestors (in MRO)

* [threading.Thread](#threading.Thread)






    
#### Methods


    
##### Method `add_count` {#PINSoftware.Profiler.Profiler.add_count}




>     def add_count(
>         self,
>         counts=1
>     )


Call this to increase the counter by <code>counts</code>

    
##### Method `run` {#PINSoftware.Profiler.Profiler.run}




>     def run(
>         self
>     )




    
##### Method `stop` {#PINSoftware.Profiler.Profiler.stop}




>     def stop(
>         self
>     )


Simple setter to stop the profiler



    
# Module `PINSoftware.main` {#PINSoftware.main}






    
## Functions


    
### Function `main` {#PINSoftware.main.main}




>     def main()


The program entrypoint, here the arguments are parser and the program is started.
If graphing is enabled, then the web server goes in a non-main thread, otherwise otherwise.




    
# Module `PINSoftware.util` {#PINSoftware.util}

This file isn't a part of the server! This is just useful functions for working with the produced data.
For example after the data has been recorded in an hd5 file, some functions plot the data in a nice way
and so on.




    
## Functions


    
### Function `avg` {#PINSoftware.util.avg}




>     def avg(
>         data
>     )


Get the average of a list

    
### Function `show_1` {#PINSoftware.util.show_1}




>     def show_1(
>         f,
>         adjust_markers=True
>     )


Plots the files data. Moves the processed_ys to be at the same height as ys.
Also plots debug markers, assumes that they are the peak voltage spikes - very useful for debugging.

    
### Function `detect_gaps` {#PINSoftware.util.detect_gaps}




>     def detect_gaps(
>         f,
>         series='processed_timestamps',
>         t=1
>     )


This goes through the file and prints all the spots where the time between two successive data
isn't <code>t</code>.



-----
Generated by *pdoc* 0.8.4 (<https://pdoc3.github.io>).
