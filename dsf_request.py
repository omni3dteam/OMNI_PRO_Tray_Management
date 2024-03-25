import json
from threading import Thread
# Python dsf API
from dsf.connections import InterceptConnection, InterceptionMode, CommandConnection, SubscribeConnection, SubscriptionMode
from dsf.commands.code import CodeType
from dsf.object_model import MessageType
# import singletons
from tray_abstract import tools, tools_queue
from tray_api import api

class dsf_request:
    def __init__(self):
        self.move_request = Thread(target=self.intercept_move_request).start()
        self.data_request = Thread(target=self.intercept_data_request).start()
        self.owc_request  = Thread(target=self.intercept_owc_request).start()
    def __str__(self):
        pass
    def intercept_owc_request(self):
        filters = ["M2222", "M2223"]
        intercept_connection = InterceptConnection(InterceptionMode.PRE, filters=filters, debug=False)
        intercept_connection.connect()
        # Create synchronous api object
        try:
            while True:
                # Wait for a code to arrive.
                cde = intercept_connection.receive_code()
                # Tray 0 command handling:
                if cde.type == CodeType.MCode and cde.majorNumber == 2222:
                    try:
                        command = cde.parameter("P").as_int()
                        action  = cde.parameter("S").as_int()
                        if command == 0:
                            if action == 0:
                                res = api.Synchronous_filament_change(0,2)
                            else:
                                res = api.Synchronous_filament_change(2,0)
                        else:
                            if action == 0:
                                res = api.Synchronous_filament_change(1,3)
                            else:
                                res = api.Synchronous_filament_change(3,1)
                        intercept_connection.resolve_code(res[0], res[1])       
                    except Exception as e:
                        intercept_connection.resolve_code(MessageType.Error, "Exception while processing M2222: {}".format(e))
                        intercept_connection.close_connection()
                elif cde.type == CodeType.MCode and cde.majorNumber == 2223:
                    res = api.Start_probe()
                else:
                    intercept_connection.ignore_code()
        except Exception as e:
            print("Closing connection: ", e)
            intercept_connection.close()

    # Gcode callback for data request
    def intercept_data_request(self):
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
                        "T0": tools[0].current_state,
                        "T1": tools[1].current_state,
                        "T2": tools[2].current_state,
                        "T3": tools[3].current_state
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
    def intercept_move_request(self):
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
                        try:
                            async_mode = cde.parameter("A").as_int()
                        except:
                            async_mode = 0
                        if async_mode == 1:
                            intercept_connection.resolve_code(MessageType.Success)
                            tools_queue[tool].put(command)               
                        else:
                            res, message = tools[tool].basic_move(command)
                            intercept_connection.resolve_code(res, message)
                    except:
                        intercept_connection.resolve_code(MessageType.Error)
                else:
                    intercept_connection.ignore_code()
        except Exception as e:
            print("Closing connection: ", e)
            intercept_connection.close()

request = dsf_request()