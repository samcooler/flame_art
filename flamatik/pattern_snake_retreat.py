#!/usr/bin/env python3

# Author: Eric Harper-Gauderman

import random
import flamatik as ft
from time import sleep
import face_groupings as g

equator = g.equators[0]
count = len(equator)
one_step_period_seconds = 0.5
frames_per_period = 25
min_aperture = 0.1
max_aperture = 1.0
aperture_range = max_aperture - min_aperture
steps = 10

snake = [0]
snake_length = 4

# Snake that emerges then retreats after `steps` steps
def pattern_snake_retreat(state: ft.LightCurveState) -> bool:
    state.fill_solenoids(0)
    state.fill_apertures(min_aperture)

    snake[0] = random.randint(0, 29)

    for step in range(steps):
        ## Render current snake
        
        # Open solenoids for current snake
        state.fill_solenoids(0)
        for nozzle in snake:
            state.s.solenoids[nozzle] = 1

        # Over a span of one_step_period_seconds, set apertures correctly
        for progress in range(frames_per_period):
            prog = progress / frames_per_period

            if step <= steps - snake_length:
                # Grow front of snake (end of list)
                state.s.apertures[snake[-1]] = min_aperture + prog * aperture_range
            if step >= snake_length - 1:
                # Shrink back of snake (beginning of list)
                state.s.apertures[snake[0]] = max_aperture - prog * aperture_range

            # Make sure middle of snake is not overridden with front or back
            for i in range(1, len(snake) - 1):
                state.s.apertures[snake[i]] = max_aperture

            sleep(one_step_period_seconds / frames_per_period)

        # Update snake before next step
        if step < snake_length - 1:
            grow()
        elif step <= steps - snake_length - 1:
            move()
        elif step < steps - 1:
            shrink()

    state.fill_solenoids(0)
    state.fill_apertures(min_aperture)

def grow():
    neighbors = g.neighbors[snake[-1]].copy()
    random.shuffle(neighbors)
    for neighbor in neighbors:
        if neighbor not in snake:
            snake.append(neighbor)
            return

def shrink():
    snake.pop(0)

def move():
    shrink()
    grow()
