#!/usr/bin/env python3

# Author: Brian Bulkowski brian@bulkowski.org

# want the globals and helper functions from flametest
import flamatik as ft
from time import sleep

def pattern_manual(state: ft.LightCurveState) -> bool:

    print('Solenoids off aperatures on allows good manual control')

    # Close all solenoids
    state.fill_solenoids(0)
    state.fill_apertures(1.0)

    # don't really have a way to make certain the state has been transmitted, going to just
    # use a delay and hope
    sleep(0.5)

    return(True)
