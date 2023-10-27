# Libraries
import time
# Modules
from tray_abstract import tray, Direction
# Program entry

if __name__ == "__main__":
    extruder_0_tray = tray(0)

    extruder_0_tray.move_motor_by(False, extruder_0_tray.tray_motor_0, Direction.FORWARD, 200, 2000)
    extruder_0_tray.move_motor_by(True, extruder_0_tray.tray_motor_0, Direction.FORWARD, 200, 2000)
    extruder_0_tray.move_motor_by(False, extruder_0_tray.tray_motor_1, Direction.FORWARD, 200, 2000)

    time.sleep(2000)

    while(True):
        time.sleep(1)