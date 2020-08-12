# PINDiode

PINDiode is software for using the xPIN + Sample and Hold + NI-6002 setup in ELI Beamlines, developed at ELI Beamlines.
It is based on [dash](https://dash.plotly.com/), is using [nidaqmx-python](https://github.com/ni/nidaqmx-python) as the driver for NI-6002 and heavily uses [dash bootstrap components](https://github.com/facultyai/dash-bootstrap-components).
The code is entirely in python and runs on all platforms where its dependencies run (most importantly the nidaqmx drivers).

## Install

The program can be packaged into a pip package, so you will need [pip](https://pypi.org/project/pip) to install it.
You can either download a prebuilt package from the releases (download the .whl file for new versions of pip) or you can build it yourself.
To build it yourself you will need `setuptools` and `wheel` installed, you can install them by running `pip install setuptools wheel`
Then to build it run `python setup.py sdist bdist_wheel`, that will create a bunch of folders and the .whl file you need is in the dist directory.
To install the .whl file run `pip install filename.whl` where filename is the name of the .whl file.

## Running

To run the server run `python -m PINSoftware`.
There are some command line options so you might want to run `python -m PINSoftware --help` first which gives an overview.
In short, the most important is the dummy option, this is for when you want to test the software on a computer without access to the hardware.
When you run it in dummy mode, you should also specify dummy_data as currently there isn't a working default, this is a path to a data file, in the root directory of the repository there is a file called `dummy_data`, you can use that, also, make sure you enter the full path, otherwise it may not work.
The graph option shows a graph of the raw data on the host computer and the profiler option runs a profiler which will print profiling information to standard output, both of those are fairly self explanatory once you run them.

## Documentation

Documentation about the hardware and the setup can be found in the [PINManual](https://github.com/kockahonza/PINManual).
Technical documentation is in the docstrings and a web page built from them can be found [here](https://kockahonza.github.io/PINSoftware).
A pdf is also build from them which can be found in the `docs` folder (named `doc.pdf`).

The web page is being built using [pdoc3](https://pdoc3.github.io/pdoc/), if you need to rebuild the page after changing the source you can run it using `pdoc --html --output-dir docs --template-dir docs/templates ./PINSoftware`.
This builds the webpages in `docs/PINSoftware/`.

## Troubleshooting

#### `s.libnipalu.so failed to initialize, Verify that nipalk.ko is built and loaded.`
This most definitely means that the nidaqmx drivers aren't installed or working.

#### `ModuleNotFoundError: No module named ??`
While pip should install all the dependencies, there might be some missing in the specification, if this happens, search and install the package that provides the module.

