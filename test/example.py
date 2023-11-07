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
