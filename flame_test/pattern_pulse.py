#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep


def pattern_pulse(state: ft.LightCurveState):

    # seconds to go through a pulse
    period = 5.0
    # how often to update (in seconds)
    update = 0.2
    # time for the apertures to settle
    settle = 0.1
    print(f'Starting Pulse Pattern')

    wait = 1.0

    print(f' Turn off servos and solenoids')
    state.fill_solenoids(0)
    state.fill_apertures(0.0)
    sleep(settle) # settle

    print(f' Turn on solenoids (leaving apertures closed)')
    state.fill_solenoids(1)
    sleep(0.1)

    # open the valves in steps

    steps = period / update
    print(f' steps: {steps}')
    for f in range(0,int(steps)):
        print(f' set flow {f / steps }')
        state.fill_apertures(f / steps )
        sleep(update)

    # shut them all down
    state.fill_apertures(0.0)
    sleep(settle)

    print(f'Ending Pulse Pattern')
