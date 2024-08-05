#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep


def pattern_leaks(state: ft.LightCurveState):

    wait = 3.0
    group_size = 5
    n = 0

    print(f'Starting Leaks Pattern (infinite)')
    print(f' secs between groups: {wait} :: size of group {group_size}')

    print(f' Turn OFF servos and solenoids and wait a sec to settle')
    state.fill_solenoids(0)
    state.fill_apertures(0.0)
    sleep(1.0)

    print(f' Turn ON valves and wait a sec to settle')
    state.fill_apertures(1.0)
    sleep(1.0)


    while True:

        start = n
        end = n + group_size
        if end > state.nozzles:
            end = state.nozzles

        print(f'On: {start} to {end}')
        for i in range(start,end):
            state.s.solenoids[i] = 1

        sleep(wait)

        print(f'Off: {start} to {end}')
        for i in range(start,end):
            state.s.solenoids[i] = 0

        n += group_size        
        if n >= state.nozzles:
            n = 0

    print(f'Ending Leaks Pattern')
