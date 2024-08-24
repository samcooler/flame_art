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
step = 0

snake = [random.randint(0, 29)]
snake_length = 4

# Snake that emerges then crawls one step forward on every repetition
def pattern_snake(state: ft.LightCurveState) -> bool:
    global step
    state.fill_apertures(min_aperture)

    ## Render current snake
    
    # Start out snake with open apertures
    for i in range(len(snake)):
        state.s.apertures[snake[i]] = max_aperture

    # Over a span of one_step_period_seconds, set apertures correctly
    for progress in range(frames_per_period):
        prog = progress / frames_per_period

        # Grow front of snake (end of list)
        if progress == 0:
            state.s.solenoids[snake[-1]] = 1
        state.s.apertures[snake[-1]] = min_aperture + prog * aperture_range

        # If not the first few steps while snake is emerging, shrink back of snake (beginning of list)
        if step >= snake_length - 1:
            state.s.apertures[snake[0]] = max_aperture - prog * aperture_range
            if progress == frames_per_period - 1:
                state.s.solenoids[snake[0]] = 0

        sleep(one_step_period_seconds / frames_per_period)

    # Update snake before next step
    if step < snake_length - 1:
        grow()
    else:
        move()
    step = step + 1

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
