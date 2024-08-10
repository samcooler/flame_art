#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

def pattern_comet(state: ft.LightCurveState) -> bool:
    # Start
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    equator_index = random.randint(0, len(g.equators) - 1)
    equator = g.equators[equator_index]
    equator_offset = random.randint(0, len(equator) - 1)
    comet_direction = bool(random.randint(0, 1))

    # Poof half of the selected equator one face at a time
    for i in range(5):
        if comet_direction:
            offset_index = equator_offset + i
        else:
            offset_index = equator_offset - i
        nozzle = equator[offset_index % len(equator)]
        state.s.solenoids[nozzle] = 1
        sleep(0.2)
        state.s.solenoids[nozzle] = 0

    # Sleep a somewhat random time between comet repetitions
    sleep(0.3 + 0.7 * random.random())
