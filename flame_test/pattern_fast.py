#!/usr/bin/env python3

# Author: Eric Gauderman

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep

def pattern_fast(state: ft.LightCurveState):
    print(f'Starting fast pattern - all solenoids')
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
    print(f'Ending fast pattern')
