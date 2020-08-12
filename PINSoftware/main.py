import argparse
import os
import sys
import threading

import matplotlib.pyplot as plt

from PINSoftware.MachineState import MachineState
from PINSoftware.DashApp import get_app

from waitress import serve


def main():
    """
    The program entrypoint, here the arguments are parser and the program is started.
    If graphing is enabled, then the web server goes in a non-main thread, otherwise otherwise.
    """
    parser = argparse.ArgumentParser(
            description='Server for the control of NI-6002 in use with a Sample and Hold amplifier and an xPIN diode, made at ELI Beamlines.')
    parser.add_argument("--dummy", "-d", dest="dummy", action="store_true", help="Run the server in dummy mode - do not actually use the NI-6002 but instead use data from a file.")
    parser.add_argument("--dummy-data", "-dd", dest="dummy_data", action="store", default="dummy_data", help="Name of the file to read the dummy data from.")
    parser.add_argument("--graph", "-g", dest="graph", action="store_true", help="Show the raw data graph.")
    parser.add_argument("--profiler", "-p", dest="profiler", action="store_true", help="Run a profiler along to monitor performance.")
    args = parser.parse_args()

    ms = MachineState(plt, args.dummy, dummy_data_file=args.dummy_data, profiler=args.profiler)

    app = get_app(ms)

    if args.graph:
        # Another way to run the server
        # dashT = threading.Thread(target=app.run_server)
        # dashT.run()
        waitressT = threading.Thread(target=serve, args=[app.server], kwargs={'port': 8050})
        waitressT.start()
        ms.run_graphing()
        waitressT.join()
        ms.stop_everything()
    else:
        serve(app.server, port=8050)
        ms.stop_everything()
