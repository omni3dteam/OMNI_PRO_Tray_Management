import tray_abstract
from tray_abstract import tool, move
from tray_communication import transcieve
from enum import IntEnum
import time
import json
### This file contains high level API for developing control functions for tray system. ###
class movement_api:
    def __init__(self):
        pass
    def __str__(self):
        pass
# # Perform check for hotend temperature.
    def check_if_is_hot(self, _tool):
        message = """M409 K"'heat.heaters[{}].current"'""".format(_tool.extruder)
        res = tray_abstract.transcieve(message)
        current_temperature = json.loads(res)["result"]
        if current_temperature <= 200: # <-- magic number, fix by getting info from RFID
            print("Cant prime extruder if its not hot")
            return 0
        return 1
# # Perform check for filament presence at extruder.
    def probing_move(self, _tool):
        #local variables.
        is_present = tool.sensor_state.FILAMENT_NOT_PRESENT
        sensors_state = _tool.get_sensors_state()
        # retract some filament and check for state.
        _tool.execut_moves(move("e", 3, 500))
        time.sleep(_tool.calculate_wait_time( 3, 500)/2)
        sensors_state = _tool.get_sensors_state()
        _tool.execut_moves(move("e", -3, 500))
        time.sleep(_tool.calculate_wait_time( 3, 500)/2)
        sensors_state = _tool.get_sensors_state()
        is_present = (sensors_state[tool.sensor_position.EXTRUDER])
        return is_present
# # Load filament.
    def load_filament(self, _tool, _tools_prime_state):
        sensors_state = _tool.get_sensors_state()
        while(sensors_state[tool.sensor_position.LOWER] != tool.sensor_state.FILAMENT_PRESENT):
            # Wait for user to put filament into tube
            sensors_state = _tool.get_sensors_state()
            time.sleep(0.5)
        while(sensors_state[tool.sensor_position.UPPER] != tool.sensor_state.FILAMENT_PRESENT):
            print("Filament not present")
            tool_move = move(_tool.motor_axis, 8, 3000)
            _tool.execut_moves(tool_move)
            sensors_state = _tool.get_sensors_state()
        # Perform small move to check extruder sensor
        print("Filament loaded into a feeder")
        if _tools_prime_state[_tool.neighbour_tool_number].is_set():
            # if other filament is primed, do non-conditional feed
            tool_move = move(_tool.motor_axis, 10, 3000)
            for i in range (0, 80):
                 _tool.execut_moves(tool_move)
                 time.sleep(_tool.calculate_wait_time(10, 3000))
            print("Filament present at extruder")
            return 1
        # Check sensor status
        ref_time = time.time()
        while sensors_state[tool.sensor_position.EXTRUDER] != tool.sensor_state.FILAMENT_PRESENT:
            tool_move = move(_tool.motor_axis, 6, 3000)
            _tool.execut_moves(tool_move)
            if time.time() - ref_time > 30:
                print("Tool {}: Failed to load filament due to timeout".format(_tool.tool_number))
                return 0
            sensors_state = _tool.get_sensors_state()
        print("Filament present at extruder")
        # retract filament to place it just before tee
        tool_move = move(_tool.motor_axis, -55, 1000)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(55, 1000))
        return 1
# # Unload filament.
    def unload_filament(self, _tool):
        sensors_state = _tool.get_sensors_state()
        ref_time = time.time()
        while(sensors_state[tool.sensor_position.LOWER] != tool.sensor_state.FILAMENT_NOT_PRESENT):
            # Wait for filament to be unloaded
            tool_move = move(_tool.motor_axis, -8 , 3000)
            _tool.execut_moves(tool_move)
            if time.time() - ref_time > 30:
                print("Tool {}: Failed to unload filament due to timeout".format(_tool.tool_number))
                return 0
            sensors_state = _tool.get_sensors_state()
        print("Filament Unloaded")

# # Push filament all the way into hotend.
    def prime_extruder(self, _tool, tools_prime_state):
        # Check if other filament is in the way
        if tools_prime_state[_tool.neighbour_tool_number].is_set():
            print("Cant prime because other filament is primed")
            return 0
        # Select tool
        tray_abstract.transcieve("T{}".format(_tool.tool_number))
        # Check if filament is present at extruder
        state = self.probing_move(_tool)
        # Check if its hot
        if self.check_if_is_hot(_tool) != True:
            return 0
        # set extruder to relative mode
        tray_abstract.transcieve("M83")
        sensors_state = _tool.get_sensors_state()
        # Push filament to extruder sensor, if its not there.
        if state != tool.sensor_state.FILAMENT_PRESENT:
            while(sensors_state[tool.sensor_position.EXTRUDER] != tool.sensor_state.FILAMENT_PRESENT):
                print("priming extruder...")
                tool_move = move(_tool.motor_axis, 5, 1500)
                _tool.execut_moves(tool_move)
                sensors_state = _tool.get_sensors_state()
        # else, just prime it.
        # # note that we are passing "e" instead of _tool.motor_axis
        tool_move = move("e", 80, 150)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(80, 150))
        print("extruder primed")
        return 1
# # retract filament from hotend.
    def retract(self, _tool, tools_prime_state):
        # Select tool
        tray_abstract.transcieve("T{}".format(_tool.tool_number))
        # Check if its hot
        if self.check_if_is_hot(_tool) != True:
            return 0
        # Create move command to retract filament from extruder
        tool_move = move("e", -90, 300)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(90, 300))
        # Create move command to retract filament to tee at higher speed
        tool_move = move(_tool.motor_axis, -55, 1500)
        _tool.execut_moves(tool_move)
        time.sleep(_tool.calculate_wait_time(55, 1500))
        print("Filament retracted")
        return 1








