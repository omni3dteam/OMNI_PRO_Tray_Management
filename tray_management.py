#Libraries
import time
# Initialize tools by importing tray_abstract module
from tray_abstract import tools
# Import logging module
from tray_logging import log

if __name__ == "__main__":
    #Configure everything on entry
    log.send_info_log("Starting Tray management")
    while(True):
        # TODO: Periodically send tools state to object model

        # command_connection = CommandConnection(debug=False)
        # command_connection.connect()

        # data =  {
        #     "T0": tools[0].current_state,
        #     "T1": tools[1].current_state,
        #     "T2": tools[2].current_state,
        #     "T3": tools[3].current_state,
        # }
        # message = json.dumps(data)

        # command_connection.perform_simple_code(f' set global.={message}')
        time.sleep(3)
