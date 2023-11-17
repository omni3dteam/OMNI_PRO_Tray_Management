#Libraries
import json
from enum import IntEnum
import time
import logging
import time
import threading
# Modules5
import tray_abstract
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
tool_0 = tray_abstract.tool(0, 10.0, "U", 13,15, 11)
tool_1 = tray_abstract.tool(1, 10.1, "V", 12,14, 11)
tray_0 = tray_abstract.tray(0, tool_0, tool_1, 20.0)
# define tray 1
tool_2 = tray_abstract.tool(2, 11.0, "W", 8,10,16)
tool_3 = tray_abstract.tool(3, 11.1, "A", 7,9,16)
tray_1 = tray_abstract.tray(1, tool_2, tool_3, 21.0)
# define whole tray system
tray_system = tray_abstract.system(tray_0, tray_1)

def intercept_move_request():
    filters = ["M1101", "M1103"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=True)
    intercept_connection.connect()
    global current_tray
    try:
        while True:
            # Wait for a code to arrive.
            cde = intercept_connection.receive_code()
            # Tray 0 command handling:
            if cde.type == CodeType.MCode and cde.majorNumber == 1101:
                pass
                # intercept_connection.resolve_code(MessageType.Success)
                # new_move = tray_abstract.move(cde.parameter("P").as_int(), cde.parameter("R").as_int(), cde.parameter("L").as_int(), cde.parameter("F").as_int(), cde.parameter("S"), cde.parameter("B"))
                # move_queue.put(new_move)
                # current_tray = extruder_0_tray
            # Tray 1 command handling:
            elif cde.type == CodeType.MCode and cde.majorNumber == 1103:
                intercept_connection.resolve_code(MessageType.Success)
                new_move = tray_abstract.move(cde.parameter("P").as_int(), cde.parameter("R").as_int(), cde.parameter("L").as_int(), cde.parameter("F").as_int(), cde.parameter("S"), cde.parameter("B"))
                move_queue.put(new_move)
                current_tray = extruder_1_tray
            else:
                intercept_connection.ignore_code()
    except Exception as e:
        print("Closing connection: ", e)
        traceback.print_exc()
        intercept_connection.close()

def intercept_data_request():
    filters = ["M1102"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=True)
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

class state(IntEnum):
    IDLE = 0
    MOVE_INIT = 1
    MOVING = 2
    MOVE_ENDING = 3

# def tool_main_loop(tool):
#     while(True):
#         print(tool)
# tool_0_thread = threading.Thread(target=tool_main_loop, args=(tool_0,)).start()

if __name__ == "__main__":
    #Configure everything on entry
    data_request.start()
    move_request.start()
    api = tray_api.movement_api()
    #Spin
    tray = tray_system.trays[1].tools[1]
    tray_system.prepare_movement()
    while(True):
        #api.conditional_move_check(tray)
        api.load_filament(tray_0, tool_0)
        api.unload_filament(tray_0, tool_0)
        #tray_system.execut_moves(tray_system.move_queue.get())
        pass
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