#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flame_test as ft
from time import sleep
import utils as u

sleep_between = 0.3

def pattern_test_neighbors(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    # Pattern
    for neighbor in u.neighbors:
        for nozzle in neighbor:
            state.s.solenoids[nozzle] = 1

        sleep(sleep_between)

        for nozzle in neighbor:
            state.s.solenoids[nozzle] = 0

        sleep(sleep_between)

    # End
    state.fill_solenoids(0)
    sleep(0.3)
