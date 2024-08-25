#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g
import geometry_math as m

# Opens several solenoids facing up, based in imu. The ones facing less directly up will have lower intensity.
# You should repeat this a lot, 20*desired seconds. 200 for 10 seconds.
def pattern_trail_up(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(0.0)

    reverse_gravity = (-state.s.gravity[0], -state.s.gravity[1], -state.s.gravity[2])
    for nozzle in g.all_nozzles:
        d = m.dot(m.nozzle_vectors[nozzle], reverse_gravity)
        if d > 0.0:
            state.s.solenoids[nozzle] = 1
            state.s.apertures[nozzle] = d
    sleep(0.05)
