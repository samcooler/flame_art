#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

def pattern_random_star_with_opposites_poof(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    star_index = random.randint(0, len(g.stars) - 1)

    # Poof selected star
    for nozzle in g.stars[star_index]:
        state.s.solenoids[nozzle] = 1
        state.s.solenoids[g.opposite[nozzle]] = 1
    sleep(0.3)
    for nozzle in g.stars[star_index]:
        state.s.solenoids[nozzle] = 0
        state.s.solenoids[g.opposite[nozzle]] = 0
    # Longer sleep at end since it looks better when repeated
    sleep(0.6)
