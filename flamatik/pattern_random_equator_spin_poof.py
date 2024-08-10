#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

def pattern_random_equator_spin_poof(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    equator_index = random.randint(0, len(g.equators) - 1)

    # Repeat 3 times cause it's cool
    for _ in range(3):
        # Poof selected equator one face at a time
        for nozzle in g.equators[equator_index]:
            state.s.solenoids[nozzle] = 1
            sleep(0.2)
            state.s.solenoids[nozzle] = 0

    # Longer sleep at end since it looks better when repeated
    sleep(0.6)
