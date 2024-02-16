# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType, CodeChannel
from dsf.object_model import MessageType, LogLevel
from dsf.connections import SubscribeConnection, SubscriptionMode
from threading import Event

# subscribe_connection = SubscribeConnection(SubscriptionMode.PATCH)
# subscribe_connection.connect()
command_connection = CommandConnection(debug=False)
command_connection.connect()

# Communication wrapper
def transcieve(message, tool_command_connection):
    try:
        res = tool_command_connection.perform_simple_code(message)
    except Exception as e:
        print(e)
        return False
    finally:
        if res == '':
            return True
        else:
            return res
def send_message(message, message_type):
    try:
        res = command_connection.write_message(message_type, message, True, LogLevel.Info)
    except Exception as e:
        print(e)
