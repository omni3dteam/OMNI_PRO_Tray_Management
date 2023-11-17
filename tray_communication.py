# Python dsf API
from dsf.connections import CommandConnection
from dsf.connections import InterceptConnection, InterceptionMode
from dsf.commands.code import CodeType, CodeChannel
from dsf.object_model import MessageType, LogLevel
from dsf.connections import SubscribeConnection, SubscriptionMode

subscribe_connection = SubscribeConnection(SubscriptionMode.PATCH)
subscribe_connection.connect()
command_connection = CommandConnection(debug=False)
command_connection.connect()
# Communication wrapper
def transcieve(message):
    try:
        res = command_connection.perform_simple_code(message)
    except Exception as e:
        print(e)
        return False
    finally:
        if res == '':
            return True
        else:
            return res