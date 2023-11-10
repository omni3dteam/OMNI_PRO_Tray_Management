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

def sign(num):
    return -1 if num < 0 else 1

# Enum class describing tray. Right tray is the one handling tool 0.
class location(IntEnum):
    RIGHT_TRAY = 0
    LEFT_TRAY = 1
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
    def __init__(self, _condition, _right_motor_distance, _left_motor_distance, _feedrate):
        self.condition = _condition
        self.setpoint = [_right_motor_distance, _left_motor_distance]
        self.feedrate = _feedrate
        self.move_done = False
# abstraction for filament tray system
class tray:
    def __init__(self, _right_motor_drive, _left_motor_drive, _extruder, _right_motor_sensor_number, _left_motor_sensor_number, extruder_sensor_number):
            self.tray_motors = [_right_motor_drive, _left_motor_drive, _extruder]
            self.sensor_gpios = [_right_motor_sensor_number,_left_motor_sensor_number,extruder_sensor_number]
            self.sensors_state = self.get_sensors_state(self.sensor_gpios)
            self.current_position = [0,0,0]
    def __str__(self):
        return f"Tray Sensors state: Right sensor:{self.sensors_state[0]}, Left sensor:{self.sensors_state[1]}, Tool sensor:{self.sensors_state[2]}"
    # read filament tray sensor state
    def get_sensors_state(self, gpios):
        state = [0,0,0]
        res = command_connection.perform_simple_code("""M409 K"'sensors.gpIn"'""")
        parsed_json = json.loads(res)["result"]
        self.sensors_state = [parsed_json[gpios[0]]["value"],parsed_json[gpios[1]]["value"],parsed_json[gpios[2]]["value"]]
        print(self.sensors_state)
    def wait_for_sensor_state(sensor, state_to_wait ,timeout):
        return True
    def return_sensors_state(self):
        return self.sensors_state
    def create_dummy_axis(self, drives):
        res = command_connection.perform_simple_code("M584 U{} V{}".format(drives[0], drives[1]))
        # Allow movement of un-homed axis
        res = command_connection.perform_simple_code("M564 H0")
        # relative extrusion mode
        res = command_connection.perform_simple_code("G91")
    def delete_dummy_axis(tray_motor):
         res = command_connection.perform_simple_code("M584 X30.0 Y40.0:41.0 Z50.0:51.0:52.0 E20.0:21.0:10.0:10.1:11.0:11.1")
    # TODO: Function to execute moves asynchronusly
    def execut_moves(self, new_move):
        left_motor_distance = 0
        right_motor_distance = 0
        if new_move.condition == condition.BY_DISTANCE:
            if(self.current_position[0] != new_move.setpoint[0]):
                right_motor_distance = sign(new_move.setpoint[0])*10
                self.current_position[0] += right_motor_distance
            else:
                right_motor_distance = 0
            if(self.current_position[1] != new_move.setpoint[1]):
                left_motor_distance = sign(new_move.setpoint[1])*10
                self.current_position[1] += left_motor_distance
            else:
                left_motor_distance = 0
        elif new_move.condition == condition.WAIT_FOR_SENSOR:
            pass
        if(left_motor_distance + right_motor_distance == 0):
            self.current_position[0] = 0
            self.current_position[1] = 0
            return True
        else:
            message = "G1 U{} V{} F{}".format(0, 1000, new_move.feedrate)
            res = command_connection.perform_simple_code(message, CodeChannel.SBC, False)
        return False
        # command_connection = CommandConnection(debug=False)
        # command_connection.connect()
        # # Allow cold extrusion
        # command_connection.perform_simple_code("M302 P1")
        # # Set extruder relative mode
        # command_connection.perform_simple_code("M83")
        # # Select proper motor, or both if specified
        # if both == True:
        #     command_connection.perform_simple_code("M563 P0 D{}:{}:{} H{} F{}".format(self.tray_number, self.tray_motor_0, self.tray_motor_1, self.tray_number, self.tray_number))
        # else:
        #     command_connection.perform_simple_code("M563 P0 D{}:{} H{} F{}".format(self.tray_number, motor, self.tray_number, self.tray_number))
        # # Select tool, which corresponds to tray
        # command_connection.perform_simple_code("T{}".format(self.tray_number))
        # # Send move command
        # commanded_move = dir*distance
        # if both == True:
        #     command_connection.perform_simple_code("G0 E0:{}:{} F{}".format(commanded_move, commanded_move, feedrate))
        # else:
        #     command_connection.perform_simple_code("G0 E0:{} F{}".format(commanded_move, feedrate))
        # # Disallow cold extrusion
        # command_connection.perform_simple_code("M302 P0")
        # # Set extruder absolute mode
        # command_connection.perform_simple_code("M82")
        pass
    def sine_move():

        print(math.sin(math.radians()))
