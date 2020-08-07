class Debugger():
    def __init__(self, exit_on_error=False):
        self.exit_on_error = exit_on_error

    def info(self, msg):
        print("Info: " + msg)

    def warning(self, msg):
        print("Warning: " + msg)

    def error(self, msg):
        print("Error: " + msg)
        if self.exit_on_error:
            # TODO: implement the exit
            pass
