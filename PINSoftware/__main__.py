import os
from PINSoftware.main import main

if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.join(__file__, os.path.pardir)))
    main()
