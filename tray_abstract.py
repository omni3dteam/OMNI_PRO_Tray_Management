#Libraries
import json
import time
from enum import IntEnum
from threading import Thread

from tray_communication import transcieve, send_message
from dsf.object_model import MessageType
from tray_logging import log

import queue
tools_queue = [queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()]

from dsf.connections import SubscribeConnection, SubscriptionMode, CommandConnection
subscribe_connection = SubscribeConnection(SubscriptionMode.FULL)
subscribe_connection.connect()

### This file contains abstraction for tray movement and sensors state. ###
# abstract steppers move. Move describes new commands for single tool.
class move:
    condition = 0
    def __init__(self, _axis, _setpoint  ,_feedrate):
        self.axis = _axis
        self.setpoint = _setpoint
        self.feedrate = _feedrate
# abstraction for tool
class tool:
    class state(IntEnum):
        UNDEFINED = -1
        FILAMENT_PRESENT = 0
        FILAMENT_NOT_PRESENT = 1
        FILAMENT_LOADED = 2
        FILAMENT_PRIMED = 3
    class sensor_position(IntEnum):
        LOWER = 0
        UPPER = 1
        EXTRUDER = 2
    class sensor_state(IntEnum):
        FILAMENT_PRESENT = 1
        FILAMENT_NOT_PRESENT = 0
    class Command(IntEnum):
        LOAD = 0,
        PRIME = 1,
        RETRACT = 2,
        UNLOAD = 3,
        PROBE = 4,
        RETRACT_AND_UNLOAD = 5
    def __init__(self, _tool_number, _neighbour_tool_number,_motor_drive, _motor_axis, _extruder,_lower_sensor, _upper_sensor, _extruder_sensor):
        self.tool_number = _tool_number
        self.neighbour_tool_number = _neighbour_tool_number
        self.motor_drive = _motor_drive
        self.motor_axis =  _motor_axis
        self.extruder = _extruder
        self.lower_sensor = _lower_sensor
        self.upper_sensor = _upper_sensor
        self.extruder_sensor = _extruder_sensor
        self.current_state = self.state.UNDEFINED
        self.command_connection = CommandConnection(debug=False)
        self.command_connection.connect()
        self.tool_thread = Thread(target=self.tool_main_loop).start()
    def __str__(self) -> str:
        return f"None"
# # Get state for tool sensors
    def get_sensors_state(self):
        try:
            sensors_gpln = transcieve("""M409 K"'sensors.gpIn"'""", self.command_connection)
            # sensors_gpln = subscribe_connection.get_object_model().sensors.gp_in
            time.sleep(0.2)
            sensors_filament_runout = transcieve("""M409 K"'sensors.filamentMonitors"'""", self.command_connection)
            time.sleep(0.2)
            # sensors_filament_runout = subscribe_connection.get_object_model().sensors.filament_monitors
        except Exception as e:
            print(e)
            return 0
        try:
            parsed_sensors_gpln = json.loads(sensors_gpln)["result"]
            parsed_sensors_filament_runout = json.loads(sensors_filament_runout)["result"]
            if len(parsed_sensors_filament_runout) == 6 and len(parsed_sensors_gpln) == 22:
                tray_fr_state = 0
                if parsed_sensors_filament_runout[self.lower_sensor]["status"] == 'ok':
                    tray_fr_state = 1
                sensors_state =   [tray_fr_state,
                                  parsed_sensors_gpln[self.upper_sensor]["value"],
                                  parsed_sensors_gpln[self.extruder_sensor]["value"]]
                if sensors_state != None:
                    return sensors_state
            else:
                self.get_sensors_state()
        except Exception as e:
            print("Exception druing parsing Json")
            return self.get_sensors_state()
# # Prepare trays for movement
    def check_for_presence(self):
        sensors_state = self.get_sensors_state()
        if (sensors_state[tool.sensor_position.LOWER]):
            return tool.sensor_state.FILAMENT_PRESENT
        else:
            return tool.sensor_state.FILAMENT_NOT_PRESENT
    def prepare_movement(self):
        # Allow movement of un-homed axis
        # transcieve("M564 H0 S0", self.command_connection)
        # relative movement
        transcieve("G91", self.command_connection)
        # select second movement queue
        # transcieve("M596 P1", self.command_connection)
        # relative extrusion
        transcieve("M83", self.command_connection)
# # Prepare trays for movement
    def calculate_wait_time(self,distance, feedrate):
        # feedrate in mm/min, return time in seconds
        return ((60*distance)/feedrate)
# # Execute movement
    def execut_moves(self, trays_moves):
        message = "G1 {}{} F{}".format(trays_moves.axis, trays_moves.setpoint, trays_moves.feedrate)
        transcieve(message, self.command_connection)
# # Perform check for hotend temperature.
    def check_if_is_hot(self):
        message = """M409 K"'heat.heaters[{}].current"'""".format(self.extruder)
        res = transcieve(message, self.command_connection)
        current_temperature = json.loads(res)["result"]
        # current_temperature = subscribe_connection.get_object_model().heat.heaters[self.extruder].current
        if current_temperature <= 200: # <-- magic number, fix by getting info from RFID
            log.info("Cant prime extruder if its not hot")
            send_message("Tool {}: extruder is not hot!".format(self.tool_number), MessageType.Error)
            return 0
        return 1
# # Perform check for filament presence at extruder.
    def probing_move(self):
        #local variables.
        self.command_connection.perform_simple_code("T{}".format(self.tool_number))
        sensors_state = self.get_sensors_state()
        # retract some filament and check for state.
        for i in range(0,3):
            self.execut_moves(move(self.motor_axis, -8, 500))
            time.sleep(self.calculate_wait_time( 10, 500)/2)
            sensors_state = self.get_sensors_state()
            if (sensors_state[tool.sensor_position.EXTRUDER]) == 1:
                self.current_state = self.sensor_state.FILAMENT_PRESENT
                return tool.sensor_state.FILAMENT_PRESENT
            self.execut_moves(move(self.motor_axis, 8, 500))
            time.sleep(self.calculate_wait_time( 10, 500)/2)
            sensors_state = self.get_sensors_state()
            if (sensors_state[tool.sensor_position.EXTRUDER]) == 1:
                self.current_state = self.sensor_state.FILAMENT_PRESENT
                return tool.sensor_state.FILAMENT_PRESENT
        self.current_state = self.sensor_state.FILAMENT_NOT_PRESENT
        return tool.sensor_state.FILAMENT_NOT_PRESENT
# # Load filament without extruder sensor.
    def load_filament_wo_sensor(self):
        sensors_state = self.get_sensors_state()
        ref_time = time.time()
        while(sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_NOT_PRESENT):
            # Wait for user to put filament into tube
            sensors_state = self.get_sensors_state()
            time.sleep(0.2)
            if time.time() - ref_time > 60:
                log.info("Tool {}: Timeout while loading filament into feeder".format(self.tool_number))
                send_message("Tool {}: Timeout while loading filament into feeder".format(self.tool_number), MessageType.Error)
                return 0
        log.info("Filament loaded into a feeder")
        for i in range (0, 76):
            self.execut_moves(move(self.motor_axis, 10, 3000))
            time.sleep(self.calculate_wait_time(10, 3000))
        log.info("Tool {}: Filament loaded into a feeder".format(self.tool_number))
        return 1
# # Unload filament.
    def unload_filament(self):
        sensors_state = self.get_sensors_state()
        ref_time = time.time()
        while(sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_PRESENT):
            # Wait for filament to be unloaded
            tool_move = move(self.motor_axis, -40 , 5000)
            self.execut_moves(tool_move)
            if time.time() - ref_time > 70:
                log.info("Tool {}: Failed to unload filament due to timeout".format(self.tool_number))
                send_message("Tool {}: Failed to unload filament due to timeout".format(self.tool_number), MessageType.Error)
                return 0
            sensors_state = self.get_sensors_state()
        # sensors_state = self.get_sensors_state()
        # while(sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_PRESENT):
        #     tool_move = move(self.motor_axis, -10 , 3000)
        #     self.execut_moves(tool_move)
        log.info("Filament Unloaded")
        return 1
# # Push filament all the way into hotend.
    def prime_extruder(self, tools_prime_state):
        # Check if other filament is in the way
        if tools_prime_state[self.neighbourself_number].is_set():
            log.info("Cant prime because other Extruder is primed")
            send_message("Cant prime because other Extruder is primed", MessageType.Error)
            return 0
        # Select tool
        transcieve("T{}".format(self.tool_number), self.command_connection)
        # Check if filament is present at extruder
        # Check if its hot
        if self.check_if_is_hot(self) != True:
            return 0
        # set extruder to relative mode
        transcieve("M83", self.command_connection)
        sensors_state = self.get_sensors_state()
        state = self.probing_move(self)
        if state == tool.sensor_state.FILAMENT_PRESENT:
            send_message("Tool already primed", MessageType.Success)
            return 1
        # Push filament to extruder sensor, if its not there.
        ref_time = time.time()
        if state != tool.sensor_state.FILAMENT_PRESENT:
            while(sensors_state[tool.sensor_position.EXTRUDER] != tool.sensor_state.FILAMENT_PRESENT):
                print("priming extruder...")
                tool_move = move("e", 10, 1000)
                self.execut_moves(tool_move)
                sensors_state = self.get_sensors_state()
                if time.time() - ref_time > 50:
                    log.info("Tool {}: Failed to prime filament due to timeout".format(self.tool_number))
                    send_message("Tool {}: Failed to prime filament due to timeout".format(self.tool_number), MessageType.Error)
                    return 0
        # else, just prime it.
        # # note that we are passing "e" instead of self.motor_axis
        # # # Start quick
        tool_move = move("e", 90, 1500)
        self.execut_moves(tool_move)
        time.sleep(self.calculate_wait_time(90, 1500))
        # Finish slow
        tool_move = move("e", 40, 700)
        self.execut_moves(tool_move)
        time.sleep(self.calculate_wait_time(90, 700))
        log.info("extruder primed")
        return 1
# # retract filament from hotend.
    def retract(self):
        # Check if its primed, else abort
        if self.current_state == tool.state.FILAMENT_PRIMED or self.current_state == tool.state.FILAMENT_LOADED :
            # Select tool
            transcieve("T{}".format(self.tool_number), self.command_connection)
            # Check if its hot
            if self.check_if_is_hot(self) != True:
                return 0
            # Do a small push
            tool_move = move("e", 10, 800)
            self.execut_moves(tool_move)
            time.sleep(self.calculate_wait_time(10, 800))
            # Create move command to retract filament from nozzle and wait for filament to cool down
            tool_move = move("e", -30, 1500)
            self.execut_moves(tool_move)
            time.sleep(self.calculate_wait_time(30, 1500))
            time.sleep(1)
            # retract from extruder
            tool_move = move("e", -60, 1500)
            self.execut_moves(tool_move)
            time.sleep(self.calculate_wait_time(60, 1500))
            # Create move command to retract filament to tee at higher speed
            tool_move = move(self.motor_axis, -55, 2500)
            self.execut_moves(tool_move)
            time.sleep(self.calculate_wait_time(55, 2500))
            log.info("Filament retracted")
        else:
            return 0
        return 1

    def retract_and_unload(self):
        self.retract(self)
        time.sleep(1)
        self.unload_filament(self)
        return 1

    # Tool main loop
    def tool_main_loop(self):
        global tools_global_state
        print("Tool {}: Current state: {}".format(self.tool_number, self.current_state))
        if self.check_for_presence() == tool.sensor_state.FILAMENT_PRESENT:
                self.current_state = tool.state.FILAMENT_LOADED
        else:
                self.current_state = tool.state.FILAMENT_NOT_PRESENT
        sensors_state = self.get_sensors_state()
        while(True):
            sensors_state = self.get_sensors_state()
            while sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_NOT_PRESENT:
                sensors_state = self.get_sensors_state()
                time.sleep(1)
                if sensors_state[tool.sensor_position.LOWER] == tool.sensor_state.FILAMENT_PRESENT:
                    self.prepare_movement()
                    self.load_filament_wo_sensor(self)
                    self.current_state = tool.state.FILAMENT_LOADED
            new_command = tools_queue[self.tool_number].get()
            if new_command == self.Command.LOAD:
                if self.current_state != tool.state.FILAMENT_LOADED:
                    self.prepare_movement()
                    log.info("Tool {}: Starting loading".format(self.tool_number))
                    if self.load_filament_wo_sensor(self) == 1:
                        self.current_state = tool.state.FILAMENT_LOADED
                    else:
                        log.info("Error while loading filament on tool: {}".format(self.tool_number))
                        self.current_state = tool.state.FILAMENT_NOT_PRESENT
                else:
                    print("filament already loaded")
            elif new_command == self.Command.PRIME:
                self.prepare_movement()
                log.info("Tool {}: priming".format(self.tool_number))
                if self.prime_extruder(self, tools[self.neighbourself_number].current_state) == 1:
                    self.current_state = tool.state.FILAMENT_PRIMED
                else:
                    log.info("Error while priming filament on tool: {}".format(self.tool_number))
                    self.current_state = tool.state.FILAMENT_LOADED
            elif new_command == self.Command.RETRACT:
                self.prepare_movement()
                log.info("Tool {}: Starting retraction".format(self.tool_number))
                if self.retract(self) == 1:
                    self.current_state = tool.state.FILAMENT_LOADED
                else:
                    log.info("Error while retracting filament on tool: {}".format(self.tool_number))
                    self.current_state = tool.state.FILAMENT_PRIMED
            elif new_command == self.Command.UNLOAD:
                self.prepare_movement()
                if self.current_state == tool.state.FILAMENT_PRIMED:
                    log.info("Need to retract before unloading")
                log.info("Tool {}: Starting unloading".format(self.tool_number))
                if self.unload_filament(self) == 1:
                    self.current_state = tool.state.FILAMENT_PRESENT
                else:
                    log.info("Error while unloading filament on tool: {}".format(self.tool_number))
                    self.current_state = tool.state.FILAMENT_LOADED
            elif new_command == self.Command.PROBE:
                 self.prepare_movement()
                 if self.probing_move(self) == tool.sensor_state.FILAMENT_PRESENT:
                    self.current_state = tool.state.FILAMENT_PRIMED

            elif new_command == self.Command.RETRACT_AND_UNLOAD:
                self.prepare_movement()
                if self.current_state == tool.state.FILAMENT_PRIMED:
                    if self.retract(self) == 1:
                        self.current_state = tool.state.FILAMENT_LOADED
                        if self.unload_filament(self) == 1:
                            self.current_state = tool.state.FILAMENT_PRESENT
                        else:
                            log.info("Error while unloading filament on tool: {}".format(self.tool_number))
                            self.current_state = tool.state.FILAMENT_LOADED
                    else:
                        log.info("Error while retracting filament on tool: {}".format(self.tool_number))
                        self.current_state = tool.state.FILAMENT_PRIMED
                else:
                    if self.unload_filament(self) == 1:
                        self.current_state = tool.state.FILAMENT_PRESENT
                    else:
                        log.info("Error while unloading filament on tool: {}".format(self.tool_number))
                        self.current_state = tool.state.FILAMENT_LOADED
            else:
                log.info("Error, wrong command received")
            time.sleep(1)
# Declare four tools with desired parameters, and use them globally
tools = [tool(0, 2, 11.1, "A", 0, 3, 19, 16),
         tool(1, 3, 10.1, "V", 1, 2, 14, 21),
         tool(2, 0, 11.0, "W", 0, 5, 15, 16),
         tool(3, 1, 10.0, "U", 1, 4, 20, 21),]

