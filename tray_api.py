import tray_abstract
from tray_abstract import tool, move
from tray_communication import transcieve
from enum import IntEnum
from tray_management import tray_system
import time
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
    def move_check(self):
        tool_0_move =  tray_abstract.move(1,100,500,[0,0,0])
        tool_1_move =  tray_abstract.move(0,100,500,[0,0,0])
        tool_2_move =  tray_abstract.move(0,100,500,[0,0,0])
        tool_3_move =  tray_abstract.move(0,100,500,[0,0,0])
        moves_to_execute = [tool_0_move, tool_1_move, tool_2_move, tool_3_move]
        tray_system.execut_moves(moves_to_execute)
    def conditional_move_check(self, tool):
        # move that we want to execute for this tool
        tool_move =  tray_abstract.move(1, 100, 500, tool.extruder_sensor, tray_abstract.tool.sensor_state.FILAMENT_PRESENT)
        amount_to_move = tray_system.check_for_conditioned_move(tool, tray_abstract.tool.sensor_position.EXTRUDER, tray_abstract.tool.sensor_state.FILAMENT_PRESENT)
        if amount_to_move == 0:
            return 0
        tray_system.execut_moves([amount_to_move,0,0,0])

    def load_filament(self, _tray, _tool):
        sensors_state = _tool.get_sensors_state()
        while(sensors_state[tool.sensor_position.LOWER] != tool.sensor_state.FILAMENT_PRESENT):
            # Wait for user to put filament into tube
            sensors_state = _tool.get_sensors_state()
            time.sleep(0.5)
        while(sensors_state[tool.sensor_position.UPPER] != tool.sensor_state.FILAMENT_PRESENT):
            print("Filament not present")
            tool_move = move(_tool.motor_axis, 0, 8, 3000, 0, 0)
            tray_system.execut_moves(tool_move)
            sensors_state = _tool.get_sensors_state()
        # Perform small move to check extruder sensor
        print("Filament loaded into a feeder")
        tool_move = move(_tool.motor_axis, 0, -8, 3000, 0, 0)
        sensors_state = _tool.get_sensors_state()
        tray_system.execut_moves(tool_move)
        #tray_system.move_queue.put(tool_move) <-- future feature
        # Check sensor status
        while sensors_state[tool.sensor_position.EXTRUDER] != tool.sensor_state.FILAMENT_PRESENT:
            tool_move = move(_tool.motor_axis, 0, 6, 3000, 0, 0)
            tray_system.execut_moves(tool_move)
            sensors_state = _tool.get_sensors_state()
        print("Filament present at extruder")
        return 1
        #tool_move =  move(1, 0, 0, _tool.extruder_sensor, tray_abstract.tool.sensor_state.FILAMENT_PRESENT)
    def unload_filament(self, _tray, _tool):
        sensors_state = _tool.get_sensors_state()
        while(sensors_state[tool.sensor_position.LOWER] != tool.sensor_state.FILAMENT_NOT_PRESENT):
            # Wait for filament to be unloaded
            tool_move = move(_tool.motor_axis, 0, -8 , 3000, 0, 0)
            tray_system.execut_moves(tool_move)
            sensors_state = _tool.get_sensors_state()
        print("Filament Unloaded")
