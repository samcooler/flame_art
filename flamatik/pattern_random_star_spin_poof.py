#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

def pattern_random_star_spin_poof(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    star_index = random.randint(0, len(g.stars) - 1)

    spins = 1
    if state.args.spins is not None:
        spins = state.args.spins

    for _ in range(spins):
        # Poof selected star one face at a time
        for nozzle in g.stars[star_index]:
            state.s.solenoids[nozzle] = 1
            sleep(0.2)
            state.s.solenoids[nozzle] = 0

    # Longer sleep at end since it looks better when repeated
    sleep(0.6)
