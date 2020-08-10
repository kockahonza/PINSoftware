import os
import sys

class Debugger():
    """
    A very simple IO handler, it is here to make printouts more consistent and easy to find.
    Calling `Debugger.error` is also the correct way to exit on error.
    """
    def __init__(self, exit_on_error=True):
        """If `exit_on_error` is true, then whenever `Debugger.exit` is called, the program halts."""
        self.exit_on_error = exit_on_error

    def info(self, msg):
        print("Info:", msg)

    def warning(self, msg):
        print("Warning:", msg)

    def error(self, msg, n=1):
        print("Error:", msg)
        if self.exit_on_error:
            os._exit(n)
