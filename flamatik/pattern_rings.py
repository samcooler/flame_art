#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import flamatik as ft
from time import sleep
import face_groupings as g

frame_delay = 0.15

def pattern_rings(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    if state.args.frame_delay is not None:
        frame_delay = state.args.frame_delay

    for i in range(len(g.ring_to_idx['lower_star'])):
        state.s.solenoids[g.ring_to_idx['lower_star'][i]] = 1
    sleep(frame_delay)

    for i in range(len(g.ring_to_idx['lower_star'])):
        state.s.solenoids[g.ring_to_idx['lower_star'][i]] = 0
    for i in range(len(g.ring_to_idx['lower_diagonal'])):
        state.s.solenoids[g.ring_to_idx['lower_diagonal'][i]] = 1
    sleep(frame_delay)

    for i in range(len(g.ring_to_idx['lower_diagonal'])):
        state.s.solenoids[g.ring_to_idx['lower_diagonal'][i]] = 0
    for i in range(len(g.ring_to_idx['middle_ring'])):
        state.s.solenoids[g.ring_to_idx['middle_ring'][i]] = 1
    sleep(frame_delay)

    for i in range(len(g.ring_to_idx['middle_ring'])):
        state.s.solenoids[g.ring_to_idx['middle_ring'][i]] = 0
    for i in range(len(g.ring_to_idx['upper_diagonal'])):
        state.s.solenoids[g.ring_to_idx['upper_diagonal'][i]] = 1
    sleep(frame_delay)

    for i in range(len(g.ring_to_idx['upper_diagonal'])):
        state.s.solenoids[g.ring_to_idx['upper_diagonal'][i]] = 0
    for i in range(len(g.ring_to_idx['upper_star'])):
        state.s.solenoids[g.ring_to_idx['upper_star'][i]] = 1
    sleep(frame_delay)

    for i in range(len(g.ring_to_idx['upper_star'])):
        state.s.solenoids[g.ring_to_idx['upper_star'][i]] = 0

    return(True)
