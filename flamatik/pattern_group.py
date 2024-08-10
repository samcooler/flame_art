#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flamatik as ft
from time import sleep


def pattern_group(state: ft.LightCurveState) -> bool:

    if state.args.delay is not None:
        wait = state.args.delay
    else:
        wait = 3.0

    group_size = 5
    if state.args.group is not None:
        group_size = state.args.group
        if (group_size > state.nozzles):
            print('Group size too large')
            return(False)

    n = 0

    print(f'Starting Groups Pattern (infinite)')
    print(f' secs between groups: {wait} :: size of group {group_size}')

    print(f' Turn OFF servos and solenoids and wait a sec to settle')
    state.fill_solenoids(0)
    state.fill_apertures(0.0)
    sleep(1.0)

    print(f' Turn ON valves and wait a sec to settle')
    state.fill_apertures(1.0)
    sleep(1.0)

    while state.args.repeat > 0:

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

        state.args.repeat -= 1

    print(f'Ending Groups Pattern')

    return(True)
