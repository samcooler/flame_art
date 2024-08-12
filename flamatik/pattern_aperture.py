#!/usr/bin/env python3

# Author: chatgpt at the instruction of Sam Cooler as translated into python by BB

# want the globals and helper functions from flametest
import flamatik as ft
from time import sleep
import numpy as np

# multiwave controls the apertures
# have a wave size less than the number of nozzles
# create an array with the pattern
# move the pattern through the nozzles



def pattern_aperture(state: ft.LightCurveState) -> bool:
  print(f'See range of aperture on some nozzles')
  num_steps = 20
  if state.args.delay is not None:
    duration = state.args.delay
  else:
    duration = 3.0

  group_size = 1
  if state.args.group is not None:
    group_size = state.args.group

  nozzle = state.args.nozzle

  if (nozzle is not None) and (nozzle + group_size > state.nozzles):
    print(f' Nozzle index andor group size too large, exiting')
    return (False)

  print(f' Turn off valves & solenoids')
  state.fill_solenoids(0)
  state.fill_apertures(0)
  sleep(0.5)

  while state.args.repeat > 0:
    # solenoids ON
    state.set_solenoid(nozzle, 1)
    print('fire on...')
    sleep(2)

    for t in np.linspace(0, 1, num_steps):
      # state.s.apertures[nozzle] = t
      state.fill_apertures(t)
      print(f'set ap {nozzle} to {t}')
      sleep(duration / num_steps)

    print('MAX')
    sleep(2)
    state.fill_solenoids(0)
    print('OFF')
    sleep(1)

    #now open again, and run down the ramp instead
    state.set_solenoid(nozzle, 1)
    sleep(1.0)
    for t in np.linspace(1, 0, num_steps):
      # state.s.apertures[nozzle] = t
      state.fill_apertures(t)
      print(f'set ap {nozzle} to {t}')
      sleep(duration / num_steps)

    sleep(2)

    # solenoids off
    print(f' off All solenoids')
    state.fill_solenoids(0)
    state.fill_apertures(0)

    sleep(1)

    state.args.repeat -= 1

  return (True)