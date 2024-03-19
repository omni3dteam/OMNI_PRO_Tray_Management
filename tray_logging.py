import logging
# from systemd.journal import JournalHandler

class logger:
    def __init__(self):
        pass
        # self.log_handler = logging.getLogger('Tray logger')
        # self.log_handler.addHandler(JournalHandler())
        # self.log_handler.setLevel(logging.INFO)
    def __str__(self):
        pass
    def send_waring_log(self, message):
        pass
        # self.log_handler.warning(message)
    def send_error_log(self, message):
        pass
        # self.log_handler.error(message)
    def send_info_log(self, message):
        pass
        # self.log_handler.info(message)
    def send_debug_log(self, message):
        pass
        # self.log_handler.debug(message)

log = logger()


