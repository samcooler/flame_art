#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g

sleep_between = 0.3

def pattern_test_orthogonals(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    # Pattern
    for orthogonal in g.orthogonals:
        for nozzle in orthogonal:
            state.s.solenoids[nozzle] = 1

        sleep(sleep_between)

        for nozzle in orthogonal:
            state.s.solenoids[nozzle] = 0

        sleep(sleep_between)

    # End
    state.fill_solenoids(0)
    sleep(0.3)
