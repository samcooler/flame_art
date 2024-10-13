#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g

frame_delay = 0.3

def pattern_test_opposite(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    if state.args.frame_delay is not None:
        frame_delay = state.args.frame_delay

    # Pattern
    for i in range(0, 30):
        state.s.solenoids[i] = 1
        state.s.solenoids[g.opposite[i]] = 1
        sleep(frame_delay)
        state.s.solenoids[i] = 0
        state.s.solenoids[g.opposite[i]] = 0

    # End
    state.fill_solenoids(0)
    sleep(0.3)
