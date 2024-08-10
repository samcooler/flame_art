#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flamatik as ft
from time import sleep


def pattern_appoof(state: ft.LightCurveState) -> bool:

    print(f'Aperature based Poof Pattern')

    if state.args.delay is not None:
        wait = state.args.delay
    else:
        wait = 3.0

    group_size = 1
    if state.args.group is not None:
        group_size = state.args.group

    nozzle = state.args.nozzle

    if (nozzle is not None) and (nozzle + group_size > state.nozzles):
        print(f' Poof pattern: nozzle index andor group size too large, exiting')
        return(False)

    print(f' Turn on valves off solenoids')
    state.fill_solenoids(0)
    state.fill_apertures(1.0)
    sleep(0.5)

    while state.args.repeat > 0: 

        if nozzle is not None:
            for i in range(group_size):
                print(f' Poof {nozzle+i}')
                state.s.apertures[nozzle+i] = 1
        else:
            print(f' Poof All')
            state.fill_apertures(1)

        sleep(wait)

        if nozzle is not None:
            for i in range(0,group_size):
                print(f' unPoof {nozzle+i}')
                state.s.apertures[nozzle+i] = 0
        else:
            print(f' unPoof All')
            state.fill_apertures(0)

        sleep(wait)

        state.args.repeat -= 1

    return(True)
