#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flame_test as ft
from time import sleep
import utils as u

sleep_between = 0.15

def pattern_rings(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)
    sleep(0.5)

    index = 0

    for reps in range(5):
        for i in range(len(u.lower_star)):
            state.s.solenoids[u.lower_star[i]] = 1
        sleep(sleep_between)

        for i in range(len(u.lower_star)):
            state.s.solenoids[u.lower_star[i]] = 0
        for i in range(len(u.lower_diagonal)):
            state.s.solenoids[u.lower_diagonal[i]] = 1
        sleep(sleep_between)

        for i in range(len(u.lower_diagonal)):
            state.s.solenoids[u.lower_diagonal[i]] = 0
        for i in range(len(u.middle_ring)):
            state.s.solenoids[u.middle_ring[i]] = 1
        sleep(sleep_between)

        for i in range(len(u.middle_ring)):
            state.s.solenoids[u.middle_ring[i]] = 0
        for i in range(len(u.upper_diagonal)):
            state.s.solenoids[u.upper_diagonal[i]] = 1
        sleep(sleep_between)

        for i in range(len(u.upper_diagonal)):
            state.s.solenoids[u.upper_diagonal[i]] = 0
        for i in range(len(u.upper_star)):
            state.s.solenoids[u.upper_star[i]] = 1
        sleep(sleep_between)

        for i in range(len(u.upper_star)):
            state.s.solenoids[u.upper_star[i]] = 0

    state.fill_solenoids(0)
    sleep(0.3)

    return(True)
