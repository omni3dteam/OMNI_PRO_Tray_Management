#Libraries
from enum import IntEnum
import time
from threading import Thread, Event
import queue
# Modules
from tray_abstract import tool
from tray_communication import send_message
import tray_api
from tray_api import log
#from systemd.journal import JournalHandler
import traceback
# Python dsf API
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType
from dsf.object_model import MessageType
# Define tools
tool_0 = tool(0, 1, 10.0, "U", 0, 13, 15, 16)
tool_1 = tool(2, 0, 10.1, "V", 0, 17, 19, 21)
tool_2 = tool(1, 3, 11.0, "W", 1, 18, 20, 16)
tool_3 = tool(3, 3, 11.1, "A", 1, 12, 14, 21)
tools_prime_state = [Event(), Event(), Event(), Event()]
# Define command queues for each tools
tools_queue = [queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()]
# Enum describing commands
class Command(IntEnum):
    LOAD = 0,
    PRIME = 1,
    RETRACT = 2,
    UNLOAD = 3,
    PROBE = 4,
# Gcode callback for command request
def intercept_move_request():
    filters = ["M1101", "M1103"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=False)
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
            elif cde.type == CodeType.MCode and cde.majorNumber == 1103:
                    intercept_connection.resolve_code(MessageType.Success)
                    tools_queue[0].put(Command.PROBE)
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        traceback.print_exc()
        intercept_connection.close()
# Tool main loop
def tool_main_loop(_tool, tools_prime_state):
    api = tray_api.movement_api()
    print("Tool {}: Curren state: {}".format(_tool.tool_number, _tool.current_state))
    while(True):
        new_command = tools_queue[_tool.tool_number].get()
        if new_command == Command.LOAD:
            _tool.prepare_movement()
            log.info("Tool {}: Starting loading".format(_tool.tool_number))
            if api.load_filament(_tool, tools_prime_state) == 1:
                _tool.current_state = tool.state.FILAMENT_PRESENT
            else:
                log.info("Error while loading filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_NOT_PRESENT
        elif new_command == Command.PRIME:
            _tool.prepare_movement()
            log.info("Tool {}: priming".format(_tool.tool_number))
            if api.prime_extruder(_tool, tools_prime_state) == 1:
                _tool.current_state = tool.state.FILAMENT_PRIMED
                tools_prime_state[_tool.tool_number].set()
            else:
                log.info("Error while priming filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRESENT
        elif new_command == Command.RETRACT:
            _tool.prepare_movement()
            log.info("Tool {}: Starting retraction".format(_tool.tool_number))
            if api.retract(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_PRESENT
                tools_prime_state[_tool.tool_number].clear()
            else:
                log.info("Error while retracting filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRIMED
        elif new_command == Command.UNLOAD:
            _tool.prepare_movement()
            if _tool.current_state == tool.state.FILAMENT_PRIMED:
                log.info("Need to retract before unloading")
                api.retract(_tool, tools_prime_state)
            log.info("Tool {}: Starting unloading".format(_tool.tool_number))
            if api.unload_filament(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_NOT_PRESENT
            else:
                log.info("Error while unloading filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRESENT
        elif new_command == Command.PROBE:
             _tool.prepare_movement()
             if api.probing_move(_tool) ==  tool.sensor_state.FILAMENT_PRESENT:
                _tool.current_state = tool.state.FILAMENT_PRIMED

        else:
            log.info("Error, wrong command received")
        time.sleep(1)
        print("Tool {}: Current state: {}".format(_tool.tool_number, _tool.current_state))

# Program entry
move_request = Thread(target=intercept_move_request)
# Create thread for each tool
tool_0_thread = Thread(target=tool_main_loop, args=(tool_0, tools_prime_state,)).start()
tool_1_thread = Thread(target=tool_main_loop, args=(tool_1, tools_prime_state,)).start()
tool_2_thread = Thread(target=tool_main_loop, args=(tool_2, tools_prime_state,)).start()
tool_3_thread = Thread(target=tool_main_loop, args=(tool_3, tools_prime_state,)).start()

if __name__ == "__main__":
    #Configure everything on entry
    api = tray_api.movement_api()
    move_request.start()
    log.info("Starting Tray logger")
    while(True):
        print("Tools state: Tool 0: {}, Tool 1: {}, Tool 2: {}, Tool 3: {}".format(tool_0.current_state, tool_1.current_state, tool_2.current_state, tool_3.current_state))
        time.sleep(20)