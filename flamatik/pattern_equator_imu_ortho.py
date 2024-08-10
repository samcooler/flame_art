#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g
import geometry_math as m

equator = g.equators[0]
approx_orthogonals_within_equator = {}
for i in range(len(equator)):
    nozzle = equator[i]
    approx_orthogonals_within_equator[nozzle] = [equator[(i - 2) % len(equator)], equator[(i + 2) % len(equator)]]

# Opens the solenoid for the faces approximately orthogonal (within the equator, so they won't be
# truly orthogonal since the number of faces in the equator is not divisible by 4) to the one
# facing the direction the IMU is tilting. You should call this on repeat.
def pattern_equator_imu_ortho(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    gravity = (state.s.gravity[0], state.s.gravity[1], state.s.gravity[2])
    nozzle_in_imu_direction = m.closest_nozzle(gravity, equator)
    for nozzle in approx_orthogonals_within_equator[nozzle_in_imu_direction]:
        state.s.solenoids[nozzle] = 1
    sleep(0.1)
