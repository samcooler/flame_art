#!/usr/bin/env python3

# Author: Eric Gauderman

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep

def pattern_fast(xmit: ft.LightCurveTransmitter, recv: ft.OSCReceiver):
    print(f'Starting fast pattern')
    xmit.fill_solenoids(0)
    xmit.fill_apertures(1.0)

    index = 0
    for j in range(xmit.nozzles * 3):
        for i in range(xmit.nozzles):
            if i == index:
                xmit.solenoids[i] = 1
            else:
                xmit.solenoids[i] = 0
        sleep(0.3)
        index = (index + 1) % xmit.nozzles

    xmit.fill_solenoids(0)
    sleep(0.3)
    print(f'Ending fast pattern')
