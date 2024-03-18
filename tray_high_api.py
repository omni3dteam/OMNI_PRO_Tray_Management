from tray_abstract import tools
from dsf.object_model import MessageType
from tray_api import movement_api
from tray_abstract import tool
### This file contains high level API for developing SYNCHRONOUS operations using movement_api methods. ###
class synchronous_api:
    def __init__(self):
        pass
    def __str__(self):
        pass
    def Synchronous_filament_change(self, tool_to_change, neighbour_tool):
        #Check if its already primed
        if tools[0].current_state == 3:
            return MessageType.Warning, "Tool {} is already primed"
        # if its not primed, check if its loaded
        elif tools[0].current_state == 2:
            # retract other tool just in case
            if self.api.retract(tools[2]) == 1:
                tools[2].current_state = tool.state.FILAMENT_LOADED
            else:
                tools[2].current_state = tool.state.FILAMENT_NOT_PRESENT
                return MessageType.Error, "Error while retracting filament"
            # Try to prime selected tool
            if self.api.prime_extruder(tools[0], tools[2].current_state) == 1:
                tools[0].current_state = tool.state.FILAMENT_PRIMED
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

high_api = synchronous_api()

