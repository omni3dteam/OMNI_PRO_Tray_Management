# Libraries
import time
# Modules
from tray_abstract import tray
# Program entry

if __name__ == "__main__":
    #Configure everything on entry

    # Create tray object
    extruder_0_tray = tray(0)

    #Spin
    while(True):
        # 1. Check for new commands

        # 2. report trays status

        time.sleep(1)