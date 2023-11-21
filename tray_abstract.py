
#Libraries
import json
import math
from enum import IntEnum
import queue
# Connect to dsf socket
from tray_communication import transcieve
### This file contains abstraction for tray movement and sensors state. ###

# abstract steppers move. Move describes new commands for single tool.
class move:
    condition = 0
    def __init__(self, _axis, _setpoint  ,_feedrate,_sensor_to_trigger ,_desired_sensor_state):
        self.axis = _axis
        self.setpoint = _setpoint
        self.feedrate = _feedrate
        self.sensor_to_trigger = _sensor_to_trigger
        self.desired_sensors_state = _desired_sensor_state
        self.move_done = False
# abstraction for filament tray system
class tool:
    class state(IntEnum):
        UNDEFINED = 0
        FILAMENT_NOT_PRESENT = 1
        FILAMENT_PRESENT = 2
        FILAMENT_PRIMED = 3
    class sensor_position(IntEnum):
        LOWER = 0
        UPPER = 1
        EXTRUDER = 2
    class sensor_state(IntEnum):
        FILAMENT_PRESENT = 1
        FILAMENT_NOT_PRESENT = 0
    class direction(IntEnum):
        FORWARD = 1
        BACKWARD = -1
    def __init__(self, _tool_number, _neighbour_tool_number,_motor_drive, _motor_axis, _extruder,_lower_sensor, _upper_sensor, _extruder_sensor):
        self.tool_number = _tool_number
        self.neighbour_tool_number = _neighbour_tool_number
        self.motor_drive = _motor_drive
        self.motor_axis =  _motor_axis
        self.extruder = _extruder
        self.lower_sensor = _lower_sensor
        self.upper_sensor = _upper_sensor
        self.extruder_sensor = _extruder_sensor
        self.current_state = self.state.UNDEFINED
    def __str__(self) -> str:
        return f"tray"
    def get_sensors_state(self):
        try:
            res = transcieve("""M409 K"'sensors.gpIn"'""")
        except Exception as e:
            print(e)
            return 0
        parsed_json = json.loads(res)["result"]
        sensors_state =      [parsed_json[self.lower_sensor]   ["value"],
                              parsed_json[self.upper_sensor]   ["value"],
                              parsed_json[self.extruder_sensor]["value"]]
        return sensors_state

    def prepare_movement(self):
        # Allow movement of un-homed axis
        transcieve("M564 H0 S0")
        # relative movement
        transcieve("G91")
        # select second movement queue
        transcieve("M596 P1")
        # relative extrusion
        transcieve("M83")
    def calculate_wait_time(self,distance, feedrate):
        # feedrate in mm/min
        # return time in seconds
        return ((60*distance)/feedrate)
    def execut_moves(self, trays_moves):
        message = "G1 {}{} F{}".format(trays_moves.axis, trays_moves.setpoint, trays_moves.feedrate)
        transcieve(message)

# class tray:
#     def __init__(self, _tray,_tool_0, _tool_1):
#         self.tray = _tray
#         self.tools = [_tool_0, _tool_1]
#     def __str__(self):
#         return f"Tray Sensors state: Right sensor:{self.sensors_state[0]}, Left sensor:{self.sensors_state[1]}, Tool sensor:{self.sensors_state[2]}"
#     def check_for_colision(_caller_tool):
#         if

from tray_management import tool_states