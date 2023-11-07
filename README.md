# `pybuzzers` - Event-driven Python interface for Sony Buzz! buzzer sets.

## Installation
Available on PyPi at https://pypi.org/project/pybuzzers/

Install via pip with `pip3 install pybuzzers`

**Requires** [hidapi](https://pypi.org/project/hidapi/)

## Usage (The `BuzzerSet` class)
Each connected Buzz! set is interfaced through an instance of the `BuzzerSet` class. Note that the USB interface to the Buzz! set is 'owned' by this instance, and so only one instance can exist per attached Buzz! set. Attempting to create a new instance for a set that already exists will return a reference to the existing instance instead.

If you know the path to the Buzz! set, you can instantiate this class directly with

    buzzer_set = BuzzerSet(path)

Otherwise, the function `get_all_buzzers() -> list[BuzzerSet]` will find every Buzz! set connected to the computer, and return a BuzzerSet object representing each one.

### Labels
You can label each instance of `BuzzerSet` through the `.set_label(label: str)` method, which can then be referenced through the `.label` parameter. `.label` is `None` if not set.

### Buzzer Lights
Each buzzer has a single light under the red Buzz button. The on/off state of the lights can be set collectively using `.set_lights(lights: list[bool])`, or individually using `.set_light(buzzer: int, light: bool)`. 

Convenience methods `.set_lights_on()` and `.set_lights_off()` set the states of all buzzers at once.

The current state of the lights can be queried using `.get_lights_state() -> list[bool]`.

### Buzzer buttons
Buttons are numbered `0 -> 4` from top to bottom. Convenience constants
`RED = 0`, `BLUE = 1`, `ORANGE = 2`, `GREEN = 3`, `YELLOW = 4` are provided to decode button states in a readable way.

Dictionary `COLOUR: {int, str}` maps in reverse from the button index to a string describing the button colour.

The current state of the buttons can be queried with the `.get_buttons_state()` method. The state is returned as a 2-d list of booleans, where the `(i,j)` element of the list represents the state of the `j`th button in the `i`th buzzer. `True` indicates button is currently pressed down, `False` indicates button is currently released.

### Responding to button presses 
The `BuzzerSet` class launches its own thread to listen for button presses in the background, and uses event handlers to respond to button events.

The background thread can be launched using `.start_listening()` and stopped using `.stop_listening()`.

To respond to button presses, you must register event handlers with the `BuzzerSet` instance through the `.on_change`, `.on_buzz`, `.on_button_down`, and `.on_button_up` methods. Each of these methods takes as input a function to be called whenever the event fires, and an optional label to be used to identify the handler. Multiple handlers can be registered for each event type, and all will be called in sequence when the event fires. These events are:

#### `.on_change(handler: Callable[["BuzzerSet", list[list[bool]]], None], label: Optional[str] = None) -> str`
Called every time the button state changes. Handler must be function of the form

    f(buzzer_set: BuzzerSet, state: list[list[bool]])

where `state` is a 2-d list where element `(i, j)` contains the state of button `j` in buzzer `i`.

#### `.on_button_down(handler: Callable[["BuzzerSet", int, int], None], label: Optional[str] = None) -> str`

Called every time a button is pressed (including red Buzz button) . Handler must be function of the form

    f(buzzer_set: BuzzerSet, buzzer: int, button: int)

where `buzzer` is the index of the buzzer in the set of 4, and `button` is the index of the button on the buzzer, counting down from the top. See [Buzzer buttons](#buzzer-buttons).

#### `.on_button_up(handler: Callable[["BuzzerSet", int, int], None], label: Optional[str] = None) -> str`

Called every time a button (including red Buzz button) is released. Handler must be function of the form

    f(buzzer_set: BuzzerSet, buzzer: int, button: int)

where `buzzer` is the index of the buzzer in the set of 4, and `button` is the index of the button on the buzzer, counting down from the top. See [Buzzer buttons](#buzzer-buttons).

#### `.on_buzz(handler: Callable[["BuzzerSet", int], None], label: Optional[str] = None)`
Called every time a red Buzz button is pressed. Handler must be function of the form 

    f(buzzer_set: BuzzerSet, buzzer: int)

where `buzzer` is the index of the buzzer in the set of 4.

**Important note:** Event handler functions will be called in the background thread. You must ensure that event handlers act in a thread-safe way when they use variables also used by the main thread. Event handlers also block the background thread (meaning further events cannot be listened for) while they run, so should be kept short. Long-running responses to events should be further delegated to a different thread.

You can remove and event handler by passing its label to the `.remove_handler(label: str)` method, or remove all handlers with the `.clear_handlers()` method.

## Example

```python
import pybuzzers, time

# Get a list of all connected buzzers, and pick out the first one
buzzer = pybuzzers.get_all_buzzers()[0]

# Set all but the third buzzer light on
buzzer.set_lights([True, True, False, True])

# Now set that light on too
buzzer.set_light(2, True)

# Define an event handler we want to run every time a button is pressed
def respond_to_press(buzzer_set: pybuzzers.BuzzerSet, buzzer: int, button: int):
    button_colour = pybuzzers.COLOUR[button]
    print(f"{button_colour} button pressed on buzzer {buzzer}!")

# Register this event handler with the BuzzerSet instance
buzzer.on_button_down(respond_to_press)

# Start the background thread
buzzer.start_listening()

# From this point on any button presses will be passed to our event handler function

# While we are responding to button events in the background thread,
# let's set the light's to go on and off in sequence
while True:
    for i in range(4):
        buzzer.set_light(i, True)
        time.sleep(0.5)

    for i in range(4):
        buzzer.set_light(i, False)
        time.sleep(0.5)
```
## Acknowledgements
Thank you to [coolacid](https://github.com/coolacid/python_buzz/) for figuring out how to decode the data from the Buzz! buzzers. 
