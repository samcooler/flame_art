#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g
import geometry_math as m

# Opens the solenoid for the face closest to facing straight up, based in imu. You
# should repeat this a lot, 20*desired seconds. 200 for 10 seconds.
def pattern_point_up(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    reverse_gravity = (-state.s.gravity[0], -state.s.gravity[1], -state.s.gravity[2])
    nozzle_opposite_to_imu_direction = m.closest_nozzle(reverse_gravity, g.all_nozzles)
    state.s.solenoids[nozzle_opposite_to_imu_direction] = 1
    sleep(0.05)
