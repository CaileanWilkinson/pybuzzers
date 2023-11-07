import time

import pybuzzers


buzzers = pybuzzers.get_all_buzzers()
buzzer = buzzers[0]

buzzer.set_lights_on()
buzzer.set_lights_off()


def onStateChange(_, state):
    print(f"STATE: {state}")


def onBuzz(_, buzzer):
    print(f"BUZZ {buzzer}")


def onButton(_, buzzer, button):
    print(f"BUTTON DOWN {pybuzzers.COLOURS[button]} on {buzzer}")


def onButtonUp(_, buzzer, button):
    print(f"BUTTON UP {pybuzzers.COLOURS[button]} on {buzzer}")


buzzer.on_buzz(onBuzz)
buzzer.on_button_down(onButton)
buzzer.on_button_up(onButtonUp)
buzzer.start_listening()

input()
buzzer.stop_listening()
i = -1
try:
    while True:
        i = (i + 1) % 6
        if i < 4:
            buzzer.set_lights([True if i == j else False for j in range(4)])
        elif i == 4:
            buzzer.set_lights_on()
        elif i == 5:
            buzzer.set_lights_off()

        time.sleep(1)
except (Exception, KeyboardInterrupt, SystemExit) as e:
    buzzer.set_lights_off()
    raise e
