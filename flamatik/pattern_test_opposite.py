#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g

sleep_between = 0.3

def pattern_test_opposite(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    # Pattern
    for i in range(0, 30):
        state.s.solenoids[i] = 1
        state.s.solenoids[g.opposite[i]] = 1
        sleep(sleep_between)
        state.s.solenoids[i] = 0
        state.s.solenoids[g.opposite[i]] = 0

    # End
    state.fill_solenoids(0)
    sleep(0.3)
