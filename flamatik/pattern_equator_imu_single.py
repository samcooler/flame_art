#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g
import geometry_math as m

equator = g.equators[0]

# Opens the solenoid for the face facing the direction the IMU is tilting. You should call this on repeat.
def pattern_equator_imu_single(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    gravity = (state.s.gravity[0], state.s.gravity[1], state.s.gravity[2])
    nozzle = m.closest_nozzle(gravity, equator)
    state.s.solenoids[nozzle] = 1
    sleep(0.1)
