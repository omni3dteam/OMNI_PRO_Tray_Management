#Libraries
from enum import IntEnum
import time
import logging
import time
import threading
import queue
# Modules
import tray_abstract
from tray_abstract import tool
import tray_api
#from systemd.journal import JournalHandler
import traceback
# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType
from dsf.object_model import MessageType, LogLevel
# Define tools
tool_0 = tray_abstract.tool(0, 1, 10.0, "U", 0, 13, 15, 11)
tool_1 = tray_abstract.tool(1, 0, 10.1, "V", 0, 12, 14, 11)
tool_2 = tray_abstract.tool(2, 3, 11.0, "W", 1, 8, 10, 16)
tool_3 = tray_abstract.tool(3, 3, 11.1, "A", 1, 7, 9, 16)
# Define command queues for each tools
tools_queue = [queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()]
# Enum describing commands
class Command(IntEnum):
    LOAD = 0,
    PRIME = 1,
    RETRACT = 2,
    UNLOAD = 3,
# Gcode callback for command request
def intercept_move_request():
    filters = ["M1101"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=True)
    intercept_connection.connect()
    global current_tray
    try:
        while True:
            # Wait for a code to arrive.
            cde = intercept_connection.receive_code()
            # Tray 0 command handling:
            if cde.type == CodeType.MCode and cde.majorNumber == 1101:
                try:
                    tool = cde.parameter("P").as_int()
                    command = cde.parameter("S").as_int()
                    intercept_connection.resolve_code(MessageType.Success)
                    tools_queue[tool].put(command)
                except:
                    print()
                    intercept_connection.resolve_code(MessageType.Error)
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        traceback.print_exc()
        intercept_connection.close()
# Tool main loop
def tool_main_loop(_tool):
    api = tray_api.movement_api()
    global tool_states
    print("Tool {}: Curren state: {}".format(_tool.tool_number, _tool.current_state))
    while(True):
        new_command = tools_queue[_tool.tool_number].get()
        if new_command == Command.LOAD:
            _tool.prepare_movement()
            print("Tool {}: Starting loading".format(_tool.tool_number))
            if api.load_filament(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_PRESENT
            else:
                print("Error while loading filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_NOT_PRESENT
        elif new_command == Command.PRIME:
            _tool.prepare_movement()
            print("Tool {}: Starting priming".format(_tool.tool_number))
            if api.prime_extruder(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_PRIMED
            else:
                print("Error while priming filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRESENT
                tool_states[_tool.tool_number] = _tool.current_state
        elif new_command == Command.RETRACT:
            _tool.prepare_movement()
            print("Tool {}: Starting retraction".format(_tool.tool_number))
            if api.retract(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_PRESENT
            else:
                print("Error while retracting filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRIMED
        elif new_command == Command.UNLOAD:
            _tool.prepare_movement()
            print("Tool {}: Starting unloading".format(_tool.tool_number))
            if api.unload_filament(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_NOT_PRESENT
            else:
                print("Error while unloading filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRESENT
        else:
            print("Error, wrong command received")
        time.sleep(1)
        print("Tool {}: Curren state: {}".format(_tool.tool_number, _tool.current_state))

# Program entry
move_request = threading.Thread(target=intercept_move_request)
# Create thread for each tool
tool_0_thread = threading.Thread(target=tool_main_loop, args=(tool_0,)).start()
tool_1_thread = threading.Thread(target=tool_main_loop, args=(tool_1,)).start()

if __name__ == "__main__":
    #Configure everything on entry
    move_request.start()
    while(True):
        time.sleep(2)