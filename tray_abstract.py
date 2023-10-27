# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType, CodeChannel
from dsf.object_model import MessageType, LogLevel
from dsf.connections import SubscribeConnection, SubscriptionMode
#Libraries
import json
from enum import IntEnum

class Direction(IntEnum):
        BACKWARD = -1
        FORWARD = 1
# Create abstraction for reading filament sensors and controling tray motors.
class tray:

    def __init__(self, _tray_number):
        # TODO Initialize with real state
        self.right_sensor = self.get_sensors_state(6)
        self.left_sensor = self.get_sensors_state(7)
        self.tool_sensor = self.get_sensors_state(8)
        self.tray_number = _tray_number
        if _tray_number == 0:
            self.tray_motor_0 = 2
            self.tray_motor_1 = 3
        elif _tray_number == 1:
            self.tray_motor_0 = 4
            self.tray_motor_1 = 5
        else:
            print("Wrong tray number")
    def __str__(self):
        return f"Tray Sensors state: Right sensor:{self.right_sensor}, Left sensor:{self.left_sensor}, Tool sensor:{self.tool_sensor}"
    # read filament tray sensor state
    def get_sensors_state(self, sensor):
        # Connect to dsf socket
        command_connection = CommandConnection(debug=False)
        command_connection.connect()
        message = """M409 K"'sensors.gpIn[{}]"'""".format(sensor)
        res = command_connection.perform_simple_code(message)
        object_model = json.loads(res)
        return object_model["result"]
    def wait_for_sensor_state(sensor, state_to_wait ,timeout):
        return True
    # Move tray motor by X milimeters in blocking mode
    def move_motor_by(self, both, motor, dir, distance, feedrate):
        command_connection = CommandConnection(debug=False)
        command_connection.connect()
        # Allow cold extrusion
        command_connection.perform_simple_code("M302 P1")
        # Set extruder relative mode
        command_connection.perform_simple_code("M83")
        # Select proper motor, or both if specified
        if both == True:
            command_connection.perform_simple_code("M563 P0 D{}:{}:{} H{} F{}".format(self.tray_number, self.tray_motor_0, self.tray_motor_1, self.tray_number, self.tray_number))
        else:
            command_connection.perform_simple_code("M563 P0 D{}:{} H{} F{}".format(self.tray_number, motor, self.tray_number, self.tray_number))
        # Select tool, which corresponds to tray
        command_connection.perform_simple_code("T{}".format(self.tray_number))
        # Send move command
        commanded_move = dir*distance
        if both == True:
            command_connection.perform_simple_code("G0 E0:{}:{} F{}".format(commanded_move, commanded_move, feedrate))
        else:
            command_connection.perform_simple_code("G0 E0:{} F{}".format(commanded_move, feedrate))
        # Disallow cold extrusion
        command_connection.perform_simple_code("M302 P0")
        # Set extruder absolute mode
        command_connection.perform_simple_code("M82")
    def move_motor_to_condition(self, motor, sensor, state):
        pass