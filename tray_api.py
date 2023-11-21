import tray_abstract
from tray_abstract import tool, move
from tray_communication import transcieve
from tray_management import return_neighbour_state
from enum import IntEnum
import time
import json
### This file contains high level API for developing control functions for tray system. ###
class tools(IntEnum):
    TOOL_0 = 0
    TOOL_1 = 1
    TOOL_2 = 2
    TOOL_3 = 3

class movement_api:
    def __init__(self):

        pass
    def __str__(self):
        pass
# # Perform check for filament presence at extruder.
#     def filament_check_at_extruder(self, _tool, direction):
#         #local variables.
#         is_present = tool.sensor_state.FILAMENT_NOT_PRESENT
#         sensors_state = _tool.get_sensors_state()
#         # TODO: Do it only if extruder is hot.
#         # retract some filament and check for state.
#         _tool.execut_moves(move(_tool.motor_axis, direction*8, 3000, 0, 0))
#         sensors_state = _tool.get_sensors_state()
#         is_present = sensors_state[tool.sensor_position.EXTRUDER]
#         # Feed same amount and check.
#         _tool.execut_moves(move(_tool.motor_axis, -1*direction*8, 3000, 0, 0))
#         sensors_state = _tool.get_sensors_state()
#         is_present = sensors_state[tool.sensor_position.EXTRUDER]
#         # return true if filament was detected, false if not.
#         return is_present

    def load_filament(self, _tool):
        sensors_state = _tool.get_sensors_state()
        while(sensors_state[tool.sensor_position.LOWER] != tool.sensor_state.FILAMENT_PRESENT):
            # Wait for user to put filament into tube
            sensors_state = _tool.get_sensors_state()
            time.sleep(0.5)
        while(sensors_state[tool.sensor_position.UPPER] != tool.sensor_state.FILAMENT_PRESENT):
            print("Filament not present")
            tool_move = move(_tool.motor_axis, 8, 3000, 0, 0)
            _tool.execut_moves(tool_move)
            sensors_state = _tool.get_sensors_state()
        # Perform small move to check extruder sensor
        print("Filament loaded into a feeder")
        tool_move = move(_tool.motor_axis, -8, 3000, 0, 0)
        sensors_state = _tool.get_sensors_state()
        _tool.execut_moves(tool_move)
        # Check sensor status
        ref_time = time.time()
        while sensors_state[tool.sensor_position.EXTRUDER] != tool.sensor_state.FILAMENT_PRESENT:
            tool_move = move(_tool.motor_axis, 6, 3000, 0, 0)
            _tool.execut_moves(tool_move)
            if time.time() - ref_time > 30:
                print("Tool {}: Failed to load filament due to timeout".format(_tool.tool_number))
                return 0
            sensors_state = _tool.get_sensors_state()
        print("Filament present at extruder")
        # retract filament to place it just before tee
        tool_move = move(_tool.motor_axis, -55, 1000, 0, 0)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(55, 1000))
        return 1

    def unload_filament(self, _tool):
        sensors_state = _tool.get_sensors_state()
        ref_time = time.time()
        while(sensors_state[tool.sensor_position.LOWER] != tool.sensor_state.FILAMENT_NOT_PRESENT):
            # Wait for filament to be unloaded
            tool_move = move(_tool.motor_axis, -8 , 3000, 0, 0)
            _tool.execut_moves(tool_move)
            if time.time() - ref_time > 30:
                print("Tool {}: Failed to unload filament due to timeout".format(_tool.tool_number))
                return 0
            sensors_state = _tool.get_sensors_state()
        print("Filament Unloaded")

    def prime_extruder(self, _tool):
        # Check if filament is present at extruder
        tray_abstract.transcieve("T{}".format(_tool.tool_number))
        # Check if its hot
        message = """M409 K"'heat.heaters[{}].current"'""".format(_tool.tool_number%2)
        res = tray_abstract.transcieve("""M409 K"'heat.heaters[{}].current"'""".format(_tool.tool_number%2))
        current_temperature = json.loads(res)["result"]
        if current_temperature <= 200: # <-- magic number, fix by getting info from RFID
            print("Cant prime extruder if its not hot")
            return 0
        # If all conditions are met, retract filament to the point where filament cant detetc it no more.
        sensors_state = _tool.get_sensors_state()
        while(sensors_state[tool.sensor_position.EXTRUDER] != tool.sensor_state.FILAMENT_PRESENT):
            print("priming extruder...")
            tool_move = move(_tool.motor_axis, 8, 3000, 0, 0)
            _tool.execut_moves(tool_move)
            sensors_state = _tool.get_sensors_state()
        # Switch to relative extrusion
        tray_abstract.transcieve("M83")
        print("filament reached extruder sensor")
        # if we succesfully reached extruder sensor, prime it
        tool_move = move("e", 80, 150, 0, 0)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(80, 150))
        # note that we are passing "e" instead of _tool.motor_axis
        print("extruder primed")
        return 1
    def retract(self, _tool):
        # Select tool
        tray_abstract.transcieve("T{}".format(_tool.tool_number))
        # Check if its hot
        message = """M409 K"'heat.heaters[{}].current"'""".format(_tool.tool_number%2)
        res = tray_abstract.transcieve("""M409 K"'heat.heaters[{}].current"'""".format(_tool.tool_number%2))
        current_temperature = json.loads(res)["result"]
        if current_temperature <= 200: # <-- magic number, fix by getting info from RFID
            print("Cant prime extruder if its not hot")
            return 0
        # Create move command to retract filament from extruder
        tool_move = move("e", -90, 300, 0, 0)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(90, 300))
        # Create move command to retract filament to tee at higher speed
        tool_move = move(_tool.motor_axis, -55, 3000, 0, 0)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(55, 3000))
        print("Filament retracted")
        return 1








