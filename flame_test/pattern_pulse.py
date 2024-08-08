#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep


def pattern_pulse(state: ft.LightCurveState) -> bool:

    # seconds to go through a pulse
    period = 5.0
    if state.args.delay is not None:
        period = state.args.delay
        
    # how often to update (in seconds)
    update = 0.2
    # time for the apertures to settle
    settle = 0.1
    print(f'Starting Pulse Pattern')

    group_size = 1
    if state.args.group is not None:
        group_size = state.args.group

    nozzle = state.args.nozzle
    if (nozzle is not None) and (nozzle + group_size > state.nozzles):
        print(f' Poof pattern: nozzle index andor group size too large, exiting')
        return(False)

    if nozzle is not None:
        print(f' pulsing from {nozzle} to {nozzle+group_size-1}')
    else:
        print(f' pulsing all solenoids ')

    wait = 3.0

    print(f' Turn off servos and solenoids')
    state.fill_solenoids(0)
    state.fill_apertures(0.0)
    sleep(settle) # settle

    print(f' Turn on solenoids (leaving apertures closed)')
    state.fill_solenoids(1)
    sleep(settle)

    # open the valves in steps

    while True:

        steps = period / update
        print(f' steps: {steps}')
        for f in range(0,int(steps)):

            print(f' set flow {f / steps }')

            if nozzle is not None:
                for i in range(0,group_size):
                    state.s.apertures[nozzle+i] = f / steps

            else:
                state.fill_apertures(f / steps)

            sleep(update)

    # shut them all down
    state.fill_apertures(0.0)
    sleep(settle)

    print(f'Ending Pulse Pattern')

    return(True)
