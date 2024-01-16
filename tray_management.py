#Libraries
from enum import IntEnum
import json
import time
from threading import Thread, Event, Lock
import queue
# Modules
from tray_abstract import tool
from tray_communication import send_message
import tray_api
from tray_api import log
# Python dsf API
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType
from dsf.object_model import MessageType
# Define tools
tool_0 = tool(0, 2, 11.0, "W", 0, 5, 15, 16)
tool_1 = tool(1, 3, 10.0, "U", 1, 3, 20, 21)
tool_2 = tool(2, 0, 11.1, "A", 0, 4, 19, 16)
tool_3 = tool(3, 1, 10.1, "V", 1, 2, 14, 21)
# Declare global stuff
tools_prime_state = [Event(), Event(), Event(), Event()]
# Define command queues for each tools
tools_queue = [queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()]
tools_state_queue = queue.Queue()
tools_state = [-1, -1, -1, -1]
# Enum describing commands
class Command(IntEnum):
    LOAD = 0,
    PRIME = 1,
    RETRACT = 2,
    UNLOAD = 3,
    PROBE = 4,
# Gcode callback for data request
def intercept_data_request():
    filters = ["M1102"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=False)
    intercept_connection.connect()
    try:
        while True:
            # Wait for a code to arrive.
            cde = intercept_connection.receive_code()
            # Tray 0 command handling:
            if cde.type == CodeType.MCode and cde.majorNumber == 1102:
                try:
                    data =  {
                    "Tool_0": tools_state[0],
                    "Tool_1": tools_state[1],
                    "Tool_2": tools_state[2],
                    "Tool_3": tools_state[3]
                    }
                    message = json.dumps(data)
                    intercept_connection.resolve_code(MessageType.Success, message)
                except:
                    intercept_connection.resolve_code(MessageType.Error)
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        intercept_connection.close()
# Gcode callback for command request
def intercept_move_request():
    filters = ["M1101"]
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
                    intercept_connection.resolve_code(MessageType.Error)
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        intercept_connection.close()
# Tool main loop
def tool_main_loop(_tool, tools_prime_state):
    global tools_global_state
    api = tray_api.movement_api()
    print("Tool {}: Current state: {}".format(_tool.tool_number, _tool.current_state))
    if _tool.check_for_presence() == tool.sensor_state.FILAMENT_PRESENT:
            _tool.current_state = tool.state.FILAMENT_LOADED
    else:
            _tool.current_state = tool.state.FILAMENT_NOT_PRESENT
    tools_state_queue.put([_tool.tool_number,  _tool.current_state])
    sensors_state = _tool.get_sensors_state()
    while(True):
        # while sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_NOT_PRESENT:
        #     sensors_state = _tool.get_sensors_state()
        #     time.sleep(1)
        #     if sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_PRESENT:
        #         api.load_filament_wo_sensor(_tool, tools_prime_state)
        new_command = tools_queue[_tool.tool_number].get()
        if new_command == Command.LOAD:
            _tool.prepare_movement()
            log.info("Tool {}: Starting loading".format(_tool.tool_number))
            if api.load_filament_wo_sensor(_tool, tools_prime_state) == 1:
                _tool.current_state = tool.state.FILAMENT_LOADED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
            else:
                log.info("Error while loading filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_NOT_PRESENT
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
        elif new_command == Command.PRIME:
            _tool.prepare_movement()
            log.info("Tool {}: priming".format(_tool.tool_number))
            if api.prime_extruder(_tool, tools_prime_state) == 1:
                _tool.current_state = tool.state.FILAMENT_PRIMED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
                tools_prime_state[_tool.tool_number].set()
            else:
                log.info("Error while priming filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_LOADED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
        elif new_command == Command.RETRACT:
            _tool.prepare_movement()
            log.info("Tool {}: Starting retraction".format(_tool.tool_number))
            if api.retract(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_LOADED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
                tools_prime_state[_tool.tool_number].clear()
            else:
                log.info("Error while retracting filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_PRIMED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
        elif new_command == Command.UNLOAD:
            _tool.prepare_movement()
            if _tool.current_state == tool.state.FILAMENT_PRIMED:
                log.info("Need to retract before unloading")
                api.retract(_tool, tools_prime_state)
                api.retract(_tool, tools_prime_state)
            log.info("Tool {}: Starting unloading".format(_tool.tool_number))
            if api.unload_filament(_tool) == 1:
                _tool.current_state = tool.state.FILAMENT_PRESENT
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
            else:
                log.info("Error while unloading filament on tool: {}".format(_tool.tool_number))
                _tool.current_state = tool.state.FILAMENT_LOADED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
        elif new_command == Command.PROBE:
             _tool.prepare_movement()
             if api.probing_move(_tool) == tool.sensor_state.FILAMENT_PRESENT:
                _tool.current_state = tool.state.FILAMENT_PRIMED
                tools_state_queue.put([_tool.tool_number,  _tool.current_state])
        else:
            log.info("Error, wrong command received")
        time.sleep(1)
        # print("Tool {}: Current state: {}".format(_tool.tool_number, _tool.current_state))

# Program entry
move_request = Thread(target=intercept_move_request)
data_request = Thread(target=intercept_data_request)
# Create thread for each tool, delay start of each thread to avoid overlapping dcs requests
tool_0_thread = Thread(target=tool_main_loop, args=(tool_0, tools_prime_state,)).start()
time.sleep(1)
tool_1_thread = Thread(target=tool_main_loop, args=(tool_1, tools_prime_state,)).start()
time.sleep(1)
tool_2_thread = Thread(target=tool_main_loop, args=(tool_2, tools_prime_state,)).start()
time.sleep(1)
tool_3_thread = Thread(target=tool_main_loop, args=(tool_3, tools_prime_state,)).start()
# Create thread for receiving sensors state
# tool_state_thread =  Thread(target=tool.get_sensors_state, ).start()

if __name__ == "__main__":
    #Configure everything on entry
    api = tray_api.movement_api()
    move_request.start()
    data_request.start()
    log.info("Starting Tray logger")
    time.sleep(0.5)
    while(True):
        state = tools_state_queue.get()
        tools_state[state[0]] = state[1]
        # print("Tools state: Tool 0: {}, Tool 1: {}, Tool 2: {}, Tool 3: {}".format(tool_0.current_state, tool_1.current_state, tool_2.current_state, tool_3.current_state))
        time.sleep(3)
