#Libraries
import json
import time
from enum import IntEnum
# Connect to dsf socket
from tray_communication import transcieve

from dsf.connections import SubscribeConnection, SubscriptionMode, CommandConnection

subscribe_connection = SubscribeConnection(SubscriptionMode.FULL)
subscribe_connection.connect()

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
        UNDEFINED = -1
        FILAMENT_PRESENT = 0
        FILAMENT_NOT_PRESENT = 1
        FILAMENT_LOADED = 2
        FILAMENT_PRIMED = 3
    class sensor_position(IntEnum):
        LOWER = 0
        UPPER = 1
        EXTRUDER = 2
    class sensor_state(IntEnum):
        FILAMENT_PRESENT = 1
        FILAMENT_NOT_PRESENT = 0
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
        self.command_connection = CommandConnection(debug=False)
        self.command_connection.connect()
    def __str__(self) -> str:
        return f"None"
# # Get state for tool sensors
    def get_sensors_state(self):
        try:
            sensors_gpln = transcieve("""M409 K"'sensors.gpIn"'""", self.command_connection)
            sensors_gpln = subscribe_connection.get_object_model().sensors.gp_in
            time.sleep(0.2)
            sensors_filament_runout = transcieve("""M409 K"'sensors.filamentMonitors"'""", self.command_connection)
            time.sleep(0.2)
            # sensors_filament_runout = subscribe_connection.get_object_model().sensors.filament_monitors
        except Exception as e:
            print(e)
            return 0
        try:
            parsed_sensors_gpln = json.loads(sensors_gpln)["result"]
            parsed_sensors_filament_runout = json.loads(sensors_filament_runout)["result"]
            if len(parsed_sensors_filament_runout) == 6 and len(parsed_sensors_gpln) == 22:
                tray_fr_state = 0
                if parsed_sensors_filament_runout[self.lower_sensor]["status"] == 'ok':
                    tray_fr_state = 1
                sensors_state =   [tray_fr_state,
                                  parsed_sensors_gpln[self.upper_sensor]["value"],
                                  parsed_sensors_gpln[self.extruder_sensor]["value"]]
                if sensors_state != None:
                    return sensors_state
            else:
                self.get_sensors_state()
        except Exception as e:
            print("Exception druing parsing Json")
            return self.get_sensors_state()

    def evaluate_state(self, sensors_state):
        if sensors_state[tool.sensor_position.UPPER] == tool.sensor_state.FILAMENT_PRESENT:
            return tool.state.FILAMENT_LOADED
        else:
            return tool.state.FILAMENT_NOT_PRESENT

# # Prepare trays for movement
    def check_for_presence(self):
        sensors_state = self.get_sensors_state()
        if (sensors_state[tool.sensor_position.LOWER]):
            return tool.sensor_state.FILAMENT_PRESENT
        else:
            return tool.sensor_state.FILAMENT_NOT_PRESENT
    def prepare_movement(self):
        # Allow movement of un-homed axis
        transcieve("M564 H0 S0", self.command_connection)
        # relative movement
        transcieve("G91", self.command_connection)
        # select second movement queue
        transcieve("M596 P1", self.command_connection)
        # relative extrusion
        transcieve("M83", self.command_connection)
# # Prepare trays for movement
    def calculate_wait_time(self,distance, feedrate):
        # feedrate in mm/min
        # return time in seconds
        return ((60*distance)/feedrate)
# # Execute movement
    def execut_moves(self, trays_moves):
        message = "G1 {}{} F{}".format(trays_moves.axis, trays_moves.setpoint, trays_moves.feedrate)
        transcieve(message, self.command_connection)