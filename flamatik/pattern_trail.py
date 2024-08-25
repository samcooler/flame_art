#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import numpy as np
import face_groupings as g
import geometry_math as m

old_gravity = None

# Opens several solenoids facing away from the direction of motion, based in imu.
# The ones facing less directly up will have lower intensity.
# You should repeat this a lot, 20*desired seconds. 200 for 10 seconds.
def pattern_trail(state: ft.LightCurveState) -> bool:
    global old_gravity
    state.fill_solenoids(0)
    state.fill_apertures(0.0)

    if old_gravity == None:
        old_gravity = (state.s.gravity[0], state.s.gravity[1], state.s.gravity[2])
    elif old_gravity[0] != state.s.gravity[0] and old_gravity[1] != state.s.gravity[1] and old_gravity[2] != state.s.gravity[2]:
        motion_direction = (state.s.gravity[0] - old_gravity[0], state.s.gravity[1] - old_gravity[1], state.s.gravity[2] - old_gravity[2])
        old_gravity = (state.s.gravity[0], state.s.gravity[1], state.s.gravity[2])

        motion_direction /= np.linalg.norm(motion_direction)

        for nozzle in g.all_nozzles:
            d = m.dot(m.nozzle_vectors[nozzle], motion_direction)
            if d > 0.0:
                state.s.solenoids[nozzle] = 1
                state.s.apertures[nozzle] = min(d * d, 1.0)

    sleep(0.05)
