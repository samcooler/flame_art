#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep

def pattern_fast(state: ft.LightCurveState) -> bool:

    print(f'starting pattern fast')

    state.fill_solenoids(0)
    state.fill_apertures(1.0)
    sleep(0.3)

    index = 0
    for j in range(state.nozzles * 3):
        for i in range(state.nozzles):
            if i == index:
                state.s.solenoids[i] = 1
            else:
                state.s.solenoids[i] = 0
        sleep(0.3)
        index = (index + 1) % state.nozzles

    state.fill_solenoids(0)
    sleep(0.3)

    print(f' Ending pattern fast')

    return(True)
