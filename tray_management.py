#Libraries
import json
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
from dsf.connections import SubscribeConnection, SubscriptionMode

#extruder_0_tray = tray_abstract.tray(11.0, 11.1, "W","A" ,20.0,  7,  8,  9, 10, 11)
#extruder_1_tray = tray_abstract.tray(10.0, 10.1, "U","V" ,21.0, 12, 13, 14, 15, 16)

    # define tray 0
tool_0 = tray_abstract.tool(0, 10.0, "U", 0, 13, 15, 11)
tool_1 = tray_abstract.tool(1, 10.1, "V", 0, 12, 14, 11)
# tray_0 = tray_abstract.tray(0, tool_0, tool_1, 20.0)
# define tray 1
tool_2 = tray_abstract.tool(2, 11.0, "W", 1,8,10,16)
tool_3 = tray_abstract.tool(3, 11.1, "A", 1,7,9,16)
# tray_1 = tray_abstract.tray(1, tool_2, tool_3, 21.0)
# define whole tray system
# tray_system = tray_abstract.system(tray_0, tray_1)

tool_0_queue = queue.Queue()
tool_1_queue = queue.Queue()
tool_2_queue = queue.Queue()
tool_3_queue = queue.Queue()

class Command(IntEnum):
    LOAD = 0,
    PRIME = 1,
    RETRACT = 2,
    UNLOAD = 3,

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
                    # TODO: do something better here:
                    if tool == tool_0.tool_number:
                        tool_0_queue.put(command)
                    elif tool == tool_1.tool_number:
                        tool_1_queue.put(command)
                    elif tool == tool_2.tool_number:
                        tool_2_queue.put(command)
                    elif tool == tool_3.tool_number:
                        tool_3_queue.put(command)
                except:
                    print()
                    intercept_connection.resolve_code(MessageType.Error)
            # Tray 1 command handling:
            # elif cde.type == CodeType.MCode and cde.majorNumber == 1103:
            #     intercept_connection.resolve_code(MessageType.Success)
            #     new_move = tray_abstract.move(cde.parameter("P").as_int(), cde.parameter("R").as_int(), cde.parameter("L").as_int(), cde.parameter("F").as_int(), cde.parameter("S"), cde.parameter("B"))
            #     move_queue.put(new_move)
            #     current_tray = extruder_1_tray
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        traceback.print_exc()
        intercept_connection.close()

def intercept_data_request():
    filters = ["M1102"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=False)
    intercept_connection.connect()

    try:
        while True:
            # Wait for a code to arrive.
            cde = intercept_connection.receive_code()
            # create tray object for desired tray
            if cde.type == CodeType.MCode and cde.majorNumber == 1102:
                sensors_state = extruder_1_tray.return_sensors_state()
                data = {
                    "sensor_R_0": sensors_state[0],
                    "sensor_R_1": sensors_state[1],
                    "sensor_R_2": sensors_state[2],
                    # "sensor_L_0": sensors_state_L[0],
                    # "sensor_L_1": sensors_state_L[1],
                    # "sensor_L_2": sensors_state_L[2],
                    }
                message = json.dumps(data)
                intercept_connection.resolve_code(MessageType.Success, message)
            # We did not handle it so we ignore it and it will be continued to be processed
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        traceback.print_exc()
        intercept_connection.close()

# Program entry
data_request = threading.Thread(target=intercept_data_request)
move_request = threading.Thread(target=intercept_move_request)

def tool_main_loop(_tool):
    api = tray_api.movement_api()
    print("Tool {}: Curren state: {}".format(_tool.tool_number, _tool.current_state))
    while(True):
        new_command = tool_0_queue.get()
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
tool_0_thread = threading.Thread(target=tool_main_loop, args=(tool_0,)).start()

if __name__ == "__main__":
    #Configure everything on entry
    data_request.start()
    move_request.start()
    # api = tray_api.movement_api()
    # #Spin
    # tray = tray_system.trays[1].tools[1]
    # tray_system.prepare_movement()
    while(True):
        #api.conditional_move_check(tray)
        # api.load_filament(tray_0, tool_0)
        # api.unload_filament(tray_0, tool_0)
        #tray_system.execut_moves(tray_system.move_queue.get())
        time.sleep(2)
        # if(state_machine == state.IDLE):
        #     #extruder_0_tray.get_sensors_state()
        #     extruder_1_tray.get_sensors_state()
        #     if(move_queue.empty() == False):
        #         state_machine = state.MOVE_INIT
        #     else:
        #         print("tray_idling")
        #         time.sleep(1)
        #         pass
        # elif(state_machine == state.MOVE_INIT):
        #     current_tray.prepare_movement()
        #     state_machine = state.MOVING
        #     current_move = move_queue.get()
        # elif(state_machine == state.MOVING):
        #     if current_move.move_done != True:
        #         current_move.move_done = current_tray.execut_moves(current_move)
        #     else:
        #         state_machine = state.MOVE_ENDING
        #         current_move = 0
        #     current_tray.get_sensors_state()
        # elif(state_machine == state.MOVE_ENDING):
        #     print("Move ended")
        #     state_machine = state.IDLE
        #     time.sleep(1)