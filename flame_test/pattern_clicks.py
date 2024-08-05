#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep


def pattern_clicks(state: ft.LightCurveState):

    print(f'Starting Clicks Pattern (infinite)')

    wait = 3.0

    while True:

        print(f' Turn on servos and solenoids')
        state.fill_solenoids(1)
        state.fill_apertures(1.0)

        sleep(wait)

        print(f' Turn OFF servos and solenoids')
        state.fill_solenoids(0)
        state.fill_apertures(0.0)

        sleep(wait)


    print(f'Ending Pulse Pattern')
