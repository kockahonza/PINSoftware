# PINDiode

PINDiode is software for using the xPIN + Sample and Hold + NI-6002 setup in ELI Beamlines, developed at ELI Beamlines.
It is based on [dash](https://dash.plotly.com/), is using [nidaqmx-python](https://github.com/ni/nidaqmx-python) as the driver for NI-6002 and heavily uses [dash bootstrap components](https://github.com/facultyai/dash-bootstrap-components).
The code is entirely in python and runs on all platforms where its dependencies run (most importantly the nidaqmx drivers).

## Install

First you need to build the package by running `python setup.py sdist bdist_wheel` in the repo root directory.

Then go into the `dist` directory (`cd dist`) and pip install it (`pip install PINSoftware-<version>-py3-none-any.whl` where \<version\> is the current version).
This should also install all the dependencies (unless I missed some).

## Running

To run the server run `python -m PINSoftware`.
There are some command line options so you might want to run `python -m PINSoftware --help` first which gives an overview.
In short, the most important is the dummy option, this is for when you want to test the software on a computer without access to all the hardware.
When you run it in dummy mode, you should also specify dummy_data as currently there isn't a working default, this is a path to a data file, in the root directory of the repository there is a file called `dummy_data` use that one and make sure you enter the full path.
The graph option shows a graph of the raw data on the host computer and the profiler option runs a profiler which will print profiling information to standard output.
