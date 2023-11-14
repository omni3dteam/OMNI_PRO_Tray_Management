# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType, CodeChannel
from dsf.object_model import MessageType, LogLevel
from dsf.connections import SubscribeConnection, SubscriptionMode
#Libraries
import json
import math
from enum import IntEnum
# Connect to dsf socket
subscribe_connection = SubscribeConnection(SubscriptionMode.PATCH)
subscribe_connection.connect()
command_connection = CommandConnection(debug=False)
command_connection.connect()

### This file contains abstraction for tray movement and sensors state. ###

# Helper functions
def sign(num):
    return -1 if num < 0 else 1
def resolve_direction(current_state, new_state):
    if current_state < new_state: # current state = 0, and new_state = 1 - so we want to retract
        return -1
    else:
        return 1
# Communication wrapper
def transcieve(message):
    try:
        res = command_connection.perform_simple_code(message)
    except Exception as e:
        print(e)
        return False
    finally:
        if res == '':
            return True
        else:
            print(res)
            return False
# Enum class describing direction of motor movement
class Direction(IntEnum):
    BACKWARD = -1
    FORWARD = 1
# Enum class describing stop condition for motors
class condition(IntEnum):
    BY_DISTANCE = 0
    WAIT_FOR_SENSOR = 1
# abstract stepper move
class move:
    condition = 0
    def __init__(self, _condition, _right_motor_distance, _left_motor_distance, _feedrate, state0, state1, state2):
        self.condition = _condition
        self.setpoint = [_right_motor_distance, _left_motor_distance]
        self.feedrate = _feedrate
        self.move_done = False
        self.desired_sensors_state = [state0, state1, state2]
# abstraction for filament tray system
class tray:
    def __init__(self, _right_motor_drive, _left_motor_drive, _right_motor_axis, _left_motor_axis, _extruder, _right_motor_sensor_number, _left_motor_sensor_number, extruder_sensor_number):
            self.tray_motors = [_right_motor_drive, _left_motor_drive, _extruder]
            self.axis = [_right_motor_axis, _left_motor_axis]
            self.sensor_gpios = [_right_motor_sensor_number,_left_motor_sensor_number,extruder_sensor_number]
            self.sensors_state = self.get_sensors_state()
            self.current_position = [0,0,0]
    def __str__(self):
        return f"Tray Sensors state: Right sensor:{self.sensors_state[0]}, Left sensor:{self.sensors_state[1]}, Tool sensor:{self.sensors_state[2]}"
    # read filament tray sensor state
    def get_sensors_state(self):
        state = [0,0,0]
        try:
            res = command_connection.perform_simple_code("""M409 K"'sensors.gpIn"'""")
        except Exception as e:
            print(e)
            return 0
        parsed_json = json.loads(res)["result"]
        self.sensors_state = [parsed_json[self.sensor_gpios[0]]["value"],parsed_json[self.sensor_gpios[1]]["value"],parsed_json[self.sensor_gpios[2]]["value"]]
        print(self.sensors_state)
    def wait_for_sensor_state(sensor, state_to_wait ,timeout):
        return True
    def return_sensors_state(self):
        return self.sensors_state
    def prepare_movement(self):
        # Allow movement of un-homed axis
        transcieve("M564 H0")
        # relative extrusion mode
        transcieve("G91")
        # select second movement queue
        transcieve("M596 P1")
    def calculate_wait_time(feedrate, distance):
        # feedrate in mm/min
        # return time in seconds
        return ((60*distance)/feedrate)

    def execut_moves(self, new_move):
        # declare local variable
        left_motor_distance = 0
        right_motor_distance = 0
        # Check in which mode we want to move
        ## distance mode - move by 'setpoint' amount of milimeters
        if new_move.condition == condition.BY_DISTANCE:
            # Set setpoint in G1 command
            right_motor_distance = new_move.setpoint[0]
            left_motor_distance = new_move.setpoint[1]
            # Execute G1 and leave
            message = "G1 {}{} {}{} F{}".format(self.axis[0], right_motor_distance, self.axis[1], left_motor_distance, new_move.feedrate)
            transcieve(message)
            return True
        ## condition mode - move until 'condition' in incremental movement
        elif new_move.condition == condition.WAIT_FOR_SENSOR:
            # declare chunk to move
            amount_to_move = 100
            # prepare movement command
            if self.sensors_state[0] != new_move.desired_sensors_state[0]:
                right_motor_distance = resolve_direction(self.sensors_state[0], new_move.desired_sensors_state[0])*amount_to_move
            if self.sensors_state[1] != new_move.desired_sensors_state[1]:
                left_motor_distance = resolve_direction(self.sensors_state[1], new_move.desired_sensors_state[1])*amount_to_move
            # if self.sensors_state[2] != new_move.desired_sensors_state[2]:
            #     right_motor_distance = resolve_direction(self.sensors_state[2], new_move.desired_sensors_state[2])*amount_to_move
            # execute G1 command
            message = "G1 {}{} {}{} F{}".format(self.axis[0], right_motor_distance, self.axis[1], left_motor_distance, new_move.feedrate)
            transcieve(message)
        # go back to default movement queue
        transcieve("M596 P0")
        # disallow movement of unhomed axis
        transcieve("M564 H1")