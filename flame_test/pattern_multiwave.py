#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep

# multiwave controls the apertures
# have a wave size less than the number of nozzles
# create an array with the pattern
# move the pattern through the nozzles

def pattern_multiwave(state: ft.LightCurveState):

  waveSteps = 20  # Total steps in the wave (up and down), even number
  pattern = [0.0] * waveSteps;

  # Initialize the wave pattern
  for i in range(int(waveSteps / 2)):
    pattern[i] = i / (waveSteps / 2)
    pattern[waveSteps-i-1] = pattern[i]

  print(f'Starting multiwave pattern')

  # Open solenoids close valves
  print(f'open solenoids close valves')
  state.fill_apertures(0.0)
  state.fill_solenoids(1)
  sleep(0.100)

  # overlay the pattern
  for i in range(state.nozzles):

    for j in range(waveSteps):
        state.s.apertures[ (i + j) % state.nozzles] = pattern[j]

    print(f'wave offset: {i} shifting: apertures')
    # since state is shared,
    # print(state.apertures)

    sleep(0.500)

  # close valves at and
  state.fill_apertures(0.0)

  print(f'Ending multiwave pattern')

