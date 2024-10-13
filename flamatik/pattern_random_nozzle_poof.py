#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

def pattern_random_nozzle_poof(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    frame_delay = 0.3
    if state.args.frame_delay is not None:
        frame_delay = state.args.frame_delay

    nozzle_index = random.randint(0, len(g.all_nozzles) - 1)

    # Poof selected nozzle
    state.s.solenoids[nozzle_index] = 1
    sleep(frame_delay)
    state.s.solenoids[nozzle_index] = 0
    sleep(frame_delay)
