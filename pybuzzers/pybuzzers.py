import hid
from .BuzzerSet import BuzzerSet


RED = 0
BLUE = 1
ORANGE = 2
GREEN = 3
YELLOW = 4
COLOUR = {RED: "Red", BLUE: "Blue", ORANGE: "Orange", GREEN: "Green", YELLOW: "Yellow"}
BUTTONLABEL = {RED: "Buzz!", BLUE: "Blue", ORANGE: "Orange", GREEN: "Green", YELLOW: "Yellow"}

def list_connected_buzzers() -> list[dict]:
    """Return details for all connected Buzz! devices, without opening them."""
    return [device for device in hid.enumerate() if "BUZZ" in device["product_string"].upper()]


def get_all_buzzers() -> list[BuzzerSet]:
    """Open all connected Buzz! devices and return a BuzzerSet object for each."""
    return [BuzzerSet(device["path"]) for device in list_connected_buzzers()]
