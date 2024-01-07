import threading
from typing import Callable, Iterable, Optional

import hid


class BuzzerSet:
    """
        Class representing a single set of 4 Buzz! buzzers.
        
        Attributes
        ----------
        label Optional[str]: A label identifying this BuzzerSet for your use. Not used internally.
        path bytes: The path to the USB connection for this BuzzerSet.
    """
    __existing_buzzer_sets = {}
    __initialised = False
    __thread: threading.Thread
    
    __on_change: dict[str, Callable[["BuzzerSet", list[list[bool]]], None]]
    __on_buzz: dict[str, Callable[["BuzzerSet", int], None]]
    __on_button_down: dict[str, Callable[["BuzzerSet", int, int], None]]
    __on_button_up: dict[str, Callable[["BuzzerSet", int, int], None]]
    
    label: Optional[str]
    path: bytes
    __interface_lock: threading.Lock
    __interface: hid.device
    
    __stateLock: threading.Lock
    __state: list[list[bool]]
    
    __lights: list[bool]
    
    def __new__(cls, path: bytes):
        """
            Only one object is allowed to exist per buzzer set,
            so return a reference to the old one if it already exists
        """
        # Only one BuzzerSet instance can exist per set so return any existing instance
        if path in BuzzerSet.__existing_buzzer_sets:
            return BuzzerSet.__existing_buzzer_sets[path]
        
        # Otherwise create a new instance
        instance = super(BuzzerSet, cls).__new__(cls)
        BuzzerSet.__existing_buzzer_sets[path] = instance
        return instance
    
    def __init__(self, path: bytes, label: Optional[str] = None):
        if self.__initialised:
            return
        
        self.__initialised = True
        self.path = path
        self.label = label
        
        self.__lights = 4 * [False]
        self.__stateLock = threading.Lock()
        self.__state = 4 * [5 * [False]]
        
        self.__on_change = { }
        self.__on_buzz = { }
        self.__on_button_down = { }
        self.__on_button_up = { }
        
        self.__interface_lock = threading.Lock()
        with self.__interface_lock:
            self.__interface = hid.device()
            self.__interface.open_path(self.path)
        self.set_lights_off()  # Set all lights to off at start so we know what state is
    
    def set_label(self, label: str):
        """Associate this BuzzerSet with an ID label"""
        self.label = label
    
    # State methods
    def get_buttons_state(self) -> list[list[int]]:
        """
        Return the last-received state of the buttons.
        
        Returns a 2-d list where element (i,j) represents button j on buzzer i.
        Buttons are indexed according to COLOURS array or RED/BLUE/ORANGE/GREEN/YELLOW constants
        """
        with self.__stateLock:
            return self.__state
    
    def get_lights_state(self) -> list[bool]:
        """Return the state of the lights as a list where element i represents the state of the light on buzzer i."""
        return self.__lights
    
    # Handlers
    def on_change(self,
                  handler: Callable[["BuzzerSet", list[list[bool]]], None],
                  label: Optional[str] = None) -> str:
        """
        Register a handler to be fired any time the state of the system changes.

        Handler accepts two parameters,
            - BuzzerSet: A reference to this buzzer set
            - list[list[bool]] The new state of the system
        Set label optionally to reference this handler in remove_handler method.

        Returns the label for this handler, auto-generated if not given.
        """
        label = label or str(handler)
        self.__on_change[label] = handler
        return label
    
    def on_buzz(self,
                handler: Callable[["BuzzerSet", int], None],
                label: Optional[str] = None) -> str:
        """
        Register a handler to be fired when a buzzer is pressed.
        
        Handler accepts two parameters,
            - BuzzerSet: A reference to this buzzer set
            - int: The index of the buzzer pressed
        Set label optionally to reference this handler in remove_handler method.
        
        Returns the label for this handler, auto-generated if not given.
        """
        label = label or str(handler)
        self.__on_buzz[label] = handler
        return label
    
    def on_button_down(self,
                       handler: Callable[["BuzzerSet", int, int], None],
                       label: Optional[str] = None) -> str:
        """
        Register a handler to be fired when a button is pressed. Also fires for buzzer presses.

        Handler accepts three parameters,
            - BuzzerSet: A reference to this buzzer set
            - int: The index of the buzzer
            - int: The index of the button. See COLOURS constant.
        Set label optionally to reference this handler in remove_handler method.

        Returns the label for this handler, auto-generated if not given.
        """
        label = label or str(handler)
        self.__on_button_down[label] = handler
        return label
    
    def on_button_up(self,
                     handler: Callable[["BuzzerSet", int, int], None],
                     label: Optional[str] = None) -> str:
        """
        Register a handler to be fired when a button is released.

        Handler accepts three parameters,
            - BuzzerSet: A reference to this buzzer set
            - int: The index of the buzzer
            - int: The index of the button. See COLOURS constant.
        Set label optionally to reference this handler in remove_handler method.

        Returns the label for this handler, auto-generated if not given.
        """
        label = label or str(handler)
        self.__on_button_up[label] = handler
        return label
    
    def remove_handler(self, label: str):
        """Remove the handler with given label."""
        self.__on_change.pop(label, None)
        self.__on_buzz.pop(label, None)
        self.__on_button_down.pop(label, None)
        self.__on_button_up.pop(label, None)
    
    def clear_handlers(self):
        """Remove all handlers"""
        self.__on_change = {}
        self.__on_buzz = {}
        self.__on_button_up = {}
        self.__on_button_down = {}
    
    # Listen loop
    def start_listening(self):
        """Start listening for events from the buzzers in a new thread."""
        self.__thread = threading.Thread(target=self.__listen_loop)
        self.__thread.start()
    
    def stop_listening(self):
        """Stop listening for events from the buzzers and closes the thread."""
        # Close & reopen the connection to force interface to stop reading
        # This will trigger the break in __listen_loop to finish the thread
        with self.__interface_lock:
            self.__interface.close()
            self.__interface = hid.device()
            self.__interface.open_path(self.path)
    
    def __listen_loop(self):
        """
        Run a loop listening for events from the buzzers, and passing to any registered handlers
        
        Called from a new thread created in start_listening method.
        Will exit automatically when `stop_listening` is called.
        """
        while True:
            try:
                # Do not use __interface_lock as we want this to fail when the interface is closed in the main thread.
                data = self.__interface.read(64)
                new_state = BuzzerSet.__decode_state(data)
                self.__handle_event(new_state)
            except OSError:  # OSError triggered when connection is closed - see stop_listening method
                break
    
    @staticmethod
    def __decode_state(data: list[int]) -> list[list[bool]]:
        """Decode the raw data from the buzzers into state list."""
        data = [bool(num & 2 ** i) for num in data[2:5] for i in range(8)]  # Convert integers to boolean list
        return [
            [
                data[0],
                data[4],
                data[3],
                data[2],
                data[1]
            ],
            [
                data[5],
                data[9],
                data[8],
                data[7],
                data[6]
            ],
            [
                data[10],
                data[14],
                data[13],
                data[12],
                data[11]
            ],
            [
                data[15],
                data[19],
                data[18],
                data[17],
                data[16]
            ]
        ]
    
    def __handle_event(self, new_state: list[list[bool]]):
        """Fire all appropriate handlers for state change"""
        old_state = self.__state
        
        # Update state
        with self.__stateLock:
            self.__state = new_state
        
        # Identify any changed button states. Return early if no change.
        button_downs = [(buzzer, button) for buzzer in range(4) for button in range(5)
                        if new_state[buzzer][button] and not old_state[buzzer][button]]
        button_ups = [(buzzer, button) for buzzer in range(4) for button in range(5)
                      if not new_state[buzzer][button] and old_state[buzzer][button]]
        if not any(button_ups) and not any(button_downs):
            return
        
        # fire all on_change events
        for event in self.__on_change.values():
            event(self, new_state)
        
        for (buzzer, button) in button_downs:
            # Fire new button presses
            for event in self.__on_button_down.values():
                event(self, buzzer, button)
            
            # Fire new buzzes
            if button == 0:
                for event in self.__on_buzz.values():
                    event(self, buzzer)
        
        for (buzzer, button) in button_ups:
            # Fire new button ups
            for event in self.__on_button_up.values():
                event(self, buzzer, button)
    
    # LIGHTS
    def set_lights(self, lights: list[bool]):
        """Set the lights to a new state, given as list of one boolean for each buzzer."""
        self.__lights = lights
        binLights = [0xFF if light else 0x00 for light in lights]
        
        with self.__interface_lock:
            self.__interface.write([0x0, 0x0, *binLights, 0x0, 0x0])
    
    def set_light(self, buzzer: int, light: bool):
        """Change the state of one light, leaving the other buzzers as they are."""
        self.__lights[buzzer] = light
        self.set_lights(self.__lights)
    
    def set_lights_on(self):
        """Set all lights on."""
        self.set_lights(4 * [True])
    
    def set_lights_off(self):
        """Set all lights off."""
        self.set_lights(4 * [False])
