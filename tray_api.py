import tray_abstract

### This file contains high level API for developing control functions for tray system. ###

class movement:
    def __init__(self):
        self.right_tray = tray_abstract.tray(10.0, 10.1, "U","V" ,20.0, 6, 7, 8)
        self.left_tray = tray_abstract.tray(11.0, 11.1, "W","A" ,21.0, 6, 7, 8)

        pass
    def __str__(self):
        pass
