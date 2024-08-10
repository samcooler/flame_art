#!/usr/bin/env python3

# Author: Brian Bulkowski brian@bulkowski.org

# want the globals and helper functions from flametest
import flame_test as ft
from time import sleep

def pattern_start(state: ft.LightCurveState) -> bool:

    print('Turning on Aperatures (solenoids off)')

    # Close all solenoids
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    # don't really have a way to make certain the state has been transmitted, going to just
    # use a delay and hope
    sleep(0.5)

    return(True)