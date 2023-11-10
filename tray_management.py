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
#from systemd.journal import JournalHandler
import traceback
import sys
# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType
from dsf.object_model import MessageType, LogLevel
from dsf.connections import SubscribeConnection, SubscriptionMode

extruder_0_tray = tray_abstract.tray(10.0, 10.1, 20.0, 6, 7, 8)

move_queue = queue.Queue()
def intercept_move_request():
    filters = ["M1101"]
    intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=True)
    intercept_connection.connect()
    try:
        while True:
            # Wait for a code to arrive.
            cde = intercept_connection.receive_code()
            # create tray object for desired tray
            if cde.type == CodeType.MCode and cde.majorNumber == 1101:
                intercept_connection.resolve_code(MessageType.Success)
                new_move = tray_abstract.move(cde.parameter("P").as_int(), cde.parameter("R").as_int(), cde.parameter("L").as_int(), cde.parameter("F").as_int(), 0, 0, 0)
                move_queue.put(new_move)
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
                sensors_state = extruder_0_tray.return_sensors_state()
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

if __name__ == "__main__":
    #Configure everything on entry
    data_request.start()
    move_request.start()

    current_move = 0

    state_machine = state(state.IDLE)

    #Spin
    while(True):
        if(state_machine == state.IDLE):
            extruder_0_tray.get_sensors_state(extruder_0_tray.sensor_gpios)
            if(move_queue.empty() == False):
                state_machine = state.MOVE_INIT
            else:
                print("tray_idling")
                time.sleep(1)
                pass
        elif(state_machine == state.MOVE_INIT):
            extruder_0_tray.prepare_movement()
            state_machine = state.MOVING
            current_move = move_queue.get()
        elif(state_machine == state.MOVING):
            if current_move.move_done != True:
                current_move.move_done = extruder_0_tray.execut_moves(current_move)
            else:
                state_machine = state.MOVE_ENDING
                current_move = 0
            extruder_0_tray.get_sensors_state(extruder_0_tray.sensor_gpios)
        elif(state_machine == state.MOVE_ENDING):
            print("Move ended")
            state_machine = state.IDLE
            time.sleep(1)