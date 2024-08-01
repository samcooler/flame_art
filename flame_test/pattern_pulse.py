#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep


def pattern_pulse(state: ft.LightCurveState):

    print(f'Starting Pulse Pattern')

    wait = 1.0

    print(f' Turn on servos and solenoids')
    state.fill_solenoids(1)
    state.fill_apertures(1.0)
    sleep(wait)

    # open the valves in steps

    for f in range(0,11):
        print(f' set flow {f / 10.0 }')
        state.fill_apertures(f / 10.0)
        sleep(wait)

    # Close all solenoids, wait, and then close them
    state.fill_solenoids(0)
    sleep(wait)

    print(f'Ending Pulse Pattern')
