#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

equator = g.equators[0]
count = len(equator)
fade_period = 1.0
frames_per_period = 25
min_aperture = 0.0
max_aperture = 1.0
aperture_range = max_aperture - min_aperture

def pattern_random_star_fade(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(min_aperture)

    star_index = random.randint(0, len(g.stars) - 1)

    # Open solenoids for selected star
    for nozzle in g.stars[star_index]:
        state.s.solenoids[nozzle] = 1

    # Grow
    for progress in range(frames_per_period):
        prog = progress / frames_per_period
        for nozzle in g.stars[star_index]:
            state.s.apertures[nozzle] = min_aperture + prog * aperture_range
        sleep(fade_period / frames_per_period)

    # Shrink
    for progress in range(frames_per_period):
        prog = progress / frames_per_period
        for nozzle in g.stars[star_index]:
            state.s.apertures[nozzle] = max_aperture - prog * aperture_range
        sleep(fade_period / frames_per_period)

    # Close solenoids for selected star
    for nozzle in g.stars[star_index]:
        state.s.solenoids[nozzle] = 0
