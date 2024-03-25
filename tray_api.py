from tray_abstract import tools
from dsf.object_model import MessageType
from tray_abstract import tool
### This file contains high level API for developing SYNCHRONOUS operations using movement_api methods. ###
class tray_api:
    def __init__(self):
        pass
    def __str__(self):
        pass
    def Synchronous_filament_change(self, tool_to_change, neighbour_tool):
        #Check if its already primed
        if tools[tool_to_change].current_state == 3:
            return MessageType.Warning, "Tool {} is already primed".format(tool_to_change)
        # if its not primed, check if its loaded
        elif tools[tool_to_change].current_state == 2:
            # retract other tool just in case
            if tools[neighbour_tool].retract() == 1:
                tools[neighbour_tool].current_state = tool.state.FILAMENT_LOADED
            else:
                tools[neighbour_tool].current_state = tool.state.FILAMENT_NOT_PRESENT
            # Try to prime selected tool
            if tools[tool_to_change].prime_extruder() == 1:
                tools[tool_to_change].current_state = tool.state.FILAMENT_PRIMED
            else:
                tools[tool_to_change].current_state = tool.state.FILAMENT_LOADED
                return MessageType.Error, "Error while priming Tool {}".format(tool_to_change)
        else:
            #pointless to continues
            return MessageType.Warning, "No filament loaded"
        return MessageType.Success, ""
    def Start_probe(self):
        try:
            for _tool in tools:
                if _tool.current_state == 2:
                    _tool.probing_move()
            return MessageType.Success, ""
        except Exception as e:
            return MessageType.Error, e

api = tray_api()

