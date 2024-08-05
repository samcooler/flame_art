#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep

# use a wave pattern through the sculpture numerically but 
# only use the solinoids, with the flame wide open

def pattern_soliwave(state: ft.LightCurveState) -> bool:

    period = 0.200
    if state.args.delay is not None:
        period = state.args.delay

    print(f'Staring wave solenoids pattern')

    # Close all solenoids open all flow settle
    state.fill_solenoids(0)
    state.fill_apertures(1.0)
    sleep(0.500)

    # turn on all the solonoids one by one
    for i in range(state.nozzles):
        print(f'turn on solinoid {i}')
        state.s.solenoids[i] = 1
        sleep(period)

    # close them in the same order
    for i in range(state.nozzles):
        print(f'turn off solinoid {i}')        
        state.s.solenoids[i] = 0
        sleep(period)

    # open them in reverse
    for i in range(state.nozzles-1,-1,-1):
        print(f'turn on solinoid {i}')
        state.s.solenoids[i] = 1
        sleep(period)

    # close them in reverse
    for i in range(state.nozzles-1,-1,-1):
        print(f'turn off solinoid {i}')
        state.s.solenoids[i] = 0
        sleep(period)

    print(f'Ending wave solenoids pattern')

    return(True)
