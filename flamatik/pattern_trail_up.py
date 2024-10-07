#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import numpy as np
import face_groupings as g
import geometry_math as m

# Opens several solenoids facing up, based in imu. The ones facing less directly up will have lower intensity.
# You should repeat this a lot, 20*desired seconds. 200 for 10 seconds.
def pattern_trail_up(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(0.0)

    # testing value for no imu: reverse_gravity = np.array([4.0, 0.1, 9.8])
    reverse_gravity = np.array([-state.s.gravity[0], -state.s.gravity[1], -state.s.gravity[2]])
    reverse_gravity /= np.linalg.norm(reverse_gravity)
    for nozzle in g.all_nozzles:
        d = m.dot(m.nozzle_vectors[nozzle], (reverse_gravity[0], reverse_gravity[1], reverse_gravity[2]))
        if d > 0.0:
            state.s.solenoids[nozzle] = 1
            print(d)
            state.s.apertures[nozzle] = min(d * d, 1.0)
    sleep(0.05)
    