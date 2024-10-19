#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
from math import cos
from math import tau
import face_groupings as g

equator = g.equators[0]
count = len(equator)
rotation_period = 2.0
frames = 4 * count
min_aperture = 0.0
max_aperture = 1.0
half_aperture_range = (max_aperture - min_aperture) / 2
aperture_mean = min_aperture + half_aperture_range

def pattern_equator_wave(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(min_aperture)
    
    # Open all solenoids in the equator
    for nozzle in equator:
        state.s.solenoids[nozzle] = 1

    # One rotation around the equator
    for rotation_offset in range(frames):
        rotation_progress = rotation_offset / frames
        for nozzle in equator:
            val = aperture_mean + half_aperture_range * cos((nozzle / count + rotation_progress) * tau)
            val = max(0.0, val)
            # print(val) if nozzle == 10 else 0
            state.s.apertures[nozzle] = val
        sleep(rotation_period / frames)
