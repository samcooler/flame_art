#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g


def pattern_test_halos(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)
    
    frame_delay = 0.3

    if state.args.frame_delay is not None:
        frame_delay = state.args.frame_delay

    # Pattern
    for halo in g.halos:
        for nozzle in halo:
            state.s.solenoids[nozzle] = 1

        sleep(frame_delay)

        for nozzle in halo:
            state.s.solenoids[nozzle] = 0

        sleep(frame_delay)

    # End
    state.fill_solenoids(0)
    sleep(0.3)
