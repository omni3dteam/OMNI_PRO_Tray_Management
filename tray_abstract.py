
#Libraries
import json
from enum import IntEnum
# Connect to dsf socket
from tray_communication import transcieve
### This file contains abstraction for tray movement and sensors state. ###
# abstract steppers move. Move describes new commands for single tool.
class move:
    condition = 0
    def __init__(self, _axis, _setpoint  ,_feedrate):
        self.axis = _axis
        self.setpoint = _setpoint
        self.feedrate = _feedrate
# abstraction for tool
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
        return f"None"
# # Get state for tool sensors
    def get_sensors_state(self):
        try:
            res = transcieve("""M409 K"'sensors.gpIn"'""")
        except Exception as e:
            print(e)
            return 0
        try:
            parsed_json = json.loads(res)["result"]
            sensors_state =      [parsed_json[self.lower_sensor]   ["value"],
                              parsed_json[self.upper_sensor]   ["value"],
                              parsed_json[self.extruder_sensor]["value"]]
            return sensors_state
        except Exception as e:
            print("Exception druing parsing Json")
            return self.get_sensors_state()
# # Prepare trays for movement
    def prepare_movement(self):
        # Allow movement of un-homed axis
        transcieve("M564 H0 S0")
        # relative movement
        transcieve("G91")
        # select second movement queue
        transcieve("M596 P1")
        # relative extrusion
        transcieve("M83")
# # Prepare trays for movement
    def calculate_wait_time(self,distance, feedrate):
        # feedrate in mm/min
        # return time in seconds
        return ((60*distance)/feedrate)
# # Execute movement
    def execut_moves(self, trays_moves):
        message = "G1 {}{} F{}".format(trays_moves.axis, trays_moves.setpoint, trays_moves.feedrate)
        transcieve(message)