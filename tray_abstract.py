
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
    def __init__(self, _tool_number ,_motor_drive, _motor_axis, _extruder,_lower_sensor, _upper_sensor, _extruder_sensor):
        self.tool_number = _tool_number
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
# class tray:
#     def __init__(self, _tray,_tool_0, _tool_1, _extruder_drive):
#         self.tray = _tray
#         self.tools = [_tool_0, _tool_1]
#         self.extruder_drive = _extruder_drive
#     def __str__(self):
#         return f"Tray Sensors state: Right sensor:{self.sensors_state[0]}, Left sensor:{self.sensors_state[1]}, Tool sensor:{self.sensors_state[2]}"
# class system:
#     # Enum class describing direction of motor movement
#     class Direction(IntEnum):
#         BACKWARD = -1
#         FORWARD = 1
#     # Enum class describing stop condition for motors
#     class condition(IntEnum):
#         BY_DISTANCE = 0
#         WAIT_FOR_SENSOR = 1
#     move_queue = queue.Queue()
#     def __init__(self, _tray_0, _tray_1):
#         self.trays = [_tray_0, _tray_1]
#     def __str__(self):
#         pass
#     # Helper functions
#     def sign(num):
#         return -1 if num < 0 else 1
#     def resolve_direction(self, current_state, new_state):
#         if current_state < new_state: # current state = 0, and new_state = 1 - so we want to retract
#             return 1
#         elif current_state == new_state:
#             return 0
#         else:
#             return -1
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
        # local variables
        # axis_moves = [0,0,0,0]
        # axis_feedrate = [0,0,0,0]
        # iterator = 0
        # for tray_move in trays_moves:
        #     if tray_move.condition == self.condition.BY_DISTANCE:
        #         axis_moves[iterator] = tray_move.setpoint
        #         axis_feedrate[iterator] = tray_move.feedrate
        #         tray_move.move_done = True
        #         iterator+=1
        # self.prepare_movement()
        message = "G1 {}{} F{}".format(trays_moves.axis, trays_moves.setpoint, trays_moves.feedrate)
        transcieve(message)
    # def check_for_conditioned_move(self, tool, sensor, state):
    #     current_sensor_state = tool.get_sensors_state()
    #     move_chunk = self.resolve_direction(current_sensor_state[sensor], state)* 2.5 # <-- magic number!
    #     return move_chunk
        # # declare local variable
        # left_motor_distance = 0
        # right_motor_distance = 0
        # # Check in which mode we want to move
        # ## distance mode - move by 'setpoint' amount of milimeters
        # if new_move.condition == condition.BY_DISTANCE:
        #     # Set setpoint in G1 command
        #     right_motor_distance = new_move.setpoint[0]
        #     left_motor_distance = new_move.setpoint[1]
        #     # Execute G1 and leave
        #     message = "G1 {}{} {}{} F{}".format(self.axis[0], right_motor_distance, self.axis[1], left_motor_distance, new_move.feedrate)
        #     transcieve(message)
        #     return True
        # ## condition mode - move until 'condition' in incremental movement
        # elif new_move.condition == condition.WAIT_FOR_SENSOR:
        #     # declare chunk to move
        #     amount_to_move = 100
        #     # prepare movement command
        #     if self.sensors_state[sensor_position.UPPER_LEFT] != new_move.desired_sensors_state[sensor_position.UPPER_LEFT]:
        #         left_motor_distance = resolve_direction(self.sensors_state[sensor_position.UPPER_LEFT], new_move.desired_sensors_state[sensor_position.UPPER_LEFT])*amount_to_move
        #     if self.sensors_state[sensor_position.UPPER_RIGHT] != new_move.desired_sensors_state[sensor_position.UPPER_RIGHT]:
        #         right_motor_distance = resolve_direction(self.sensors_state[sensor_position.UPPER_RIGHT], new_move.desired_sensors_state[sensor_position.UPPER_RIGHT])*amount_to_move
        #     if self.sensors_state[sensor_position.LOWER_LEFT] != new_move.desired_sensors_state[sensor_position.LOWER_LEFT]:
        #         left_motor_distance = resolve_direction(self.sensors_state[sensor_position.LOWER_LEFT], new_move.desired_sensors_state[sensor_position.LOWER_LEFT])*amount_to_move
        #     if self.sensors_state[sensor_position.LOWER_RIGHT] != new_move.desired_sensors_state[sensor_position.LOWER_RIGHT]:
        #         right_motor_distance = resolve_direction(self.sensors_state[sensor_position.LOWER_RIGHT], new_move.desired_sensors_state[sensor_position.LOWER_RIGHT])*amount_to_move
        #     if self.sensors_state[sensor_position.EXTRUDER] != new_move.desired_sensors_state[sensor_position.EXTRUDER]:
        #         right_motor_distance = resolve_direction(self.sensors_state[sensor_position.EXTRUDER], new_move.desired_sensors_state[sensor_position.EXTRUDER])*amount_to_move
        #     # execute G1 command
        #     if(right_motor_distance == 0 & left_motor_distance == 0):
        #         new_move.move_done = True
        #     message = "G1 {}{} {}{} F{}".format(self.axis[0], right_motor_distance, self.axis[1], left_motor_distance, new_move.feedrate)
        #     transcieve(message)
        # # go back to default movement queue
        # transcieve("M596 P0")
        # # disallow movement of unhomed axis
        # transcieve("M564 H1")