#Libraries
import json
from enum import IntEnum
import time
import logging
import time
import threading
# Modules
import tray_communication
from tray_abstract import tray, location
#from systemd.journal import JournalHandler
import traceback
import sys
# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType
from dsf.object_model import MessageType, LogLevel
from dsf.connections import SubscribeConnection, SubscriptionMode

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
                data = {
                    "sensor_R_0": extruder_0_tray.sensors_state[0],
                    "sensor_R_1": extruder_0_tray.sensors_state[1],
                    "sensor_R_2": extruder_0_tray.sensors_state[2],
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
extruder_0_tray = tray(location.RIGHT_TRAY)

if __name__ == "__main__":
    #Configure everything on entry

    data_request.start()
    # Create tray object

    #Spin
    while(True):
        # 1. Check for new commands

        # 2. report trays status

        time.sleep(1)