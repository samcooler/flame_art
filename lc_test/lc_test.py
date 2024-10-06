#!/usr/bin/env python3


# Generally coded with python 3.12, but also works with Python 3.10,
# as one of the older laptops we use is Ubuntu

# lc_test is intended to send raw values for both
# apertures and solenoids, to allow testing.

# while this can also be done with `flamatik`, at some point a
# simple interface to do simple things is better.

# In this case, we want to easily calibrate the servos.
# this program runs all in one thread, doesn't have a plugin architecture,
# doesn't listen for OSC, etc etc. Just sends artnet.

# since we do want to have the `nozzel` configuration of the sculpture,
# we do read the same configuration file.



# Author: brian@bulkowski.org Brian Bulkowski 2024 Copyright assigned to Sam Cooler

import socket
from time import sleep, time
import argparse
import json
import math


import netifaces
import importlib

import glob 
import os
import sys

from types import SimpleNamespace

import logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


OSC_PORT = 6511 # a random number. there is no OSC port because OSC is not a protocol

ARTNET_PORT = 6454
ARTNET_UNIVERSE = 0
ARTNET_HEADER_SIZE = 18

NOZZLE_BUTTON_LEN = 30
CONTROL_BUTTON_LEN = 3

debug = False

# artnet packet format: ( 18 bytes )
# 8 bytes header: 'Art-Net0'
# 2 bytes: 00 0x50 (artdmx)
# 2 bytes: proto version 0 0x14
# 1 byte: sequence
# 1 byte: physical
# 2 bytes universe (little endian)
# 2 bytes length big endian
# data

def _artnet_packet(universe: int, sequence: int, packet: bytearray ):

    # print(f'Artnet_packet: building') if debug else None

    if len(packet) < 18:
        print(f'Artnet Packet: must provide packet at least 18 bytes long, skipping')
        raise Exception("artnet packet builder: too short input packet")
        return

    # print_bytearray(packet)

    packet[0:12] = b'Art-Net\x00\x00\x50\x00\x14'

    packet[12] = sequence & 0xff
    packet[13] = 0
    packet[14] = universe & 0xff
    packet[15] = (universe >> 8) & 0xff

    l = len(packet) - ARTNET_HEADER_SIZE
    packet[16] = (l >> 8) & 0xff
    packet[17] = l & 0xff

    # print_bytearray(packet)



class LightCurveState:

    def __init__(self, args):

        self.controllers = args.controllers
        self.nozzles = args.nozzles
        self.aperture_calibration = args.aperture_calibration

# we really don't need a namespace here but I'm feeling a little lazy
        self.s = SimpleNamespace()
        s = self.s
        s.apertures =  [0.0] * self.nozzles
        s.raw_apertures = [-1] * self.nozzles
        s.solenoids =  [0] * self.nozzles

        self.debug = debug

        # validate the solenoid and aperture maps, make sure every nozzle is mapped
        solenoid_map = [-1] * self.nozzles
        aperture_map = [-1] * self.nozzles

        for c in self.controllers:
            controller_s_map = c['solenoid_map']
            controller_a_map = c['aperture_map']
            for i in range(c['nozzles']):

                # validate for range - these are not recoverable
                if controller_s_map[i] >= self.nozzles:
                    print(f' solenoid map entry out of range: controller {c["name"]} entry {i} should be less than {self.nozzles}')
                    raise Exception(" solenoid map entry out of range ")
                if controller_a_map[i] >= self.nozzles:
                    print(f' aperture map entry out of range: controller {c["name"]} entry {i} should be less than {self.nozzles}')
                    raise Exception(" aperture map entry out of range ")

                # validate for duplicates - these are recoverable
                if solenoid_map[controller_s_map[i]] != -1:
                    print(f' solenoid map: duplicate entry: controller {c["name"]} entry {i} value {controller_s_map[i]} is a dup')
                solenoid_map[controller_s_map[i]] = controller_s_map[i]
                if aperture_map[controller_a_map[i]] != -1:
                    print(f' aperture map: duplicate entry: controller {c["name"]} entry {i} value {controller_a_map[i]} is a dup')
                aperture_map[controller_a_map[i]] = controller_a_map[i]


    def fill_apertures(self, val: float):
        self.s.apertures[:] = [val] * self.nozzles

    def fill_solenoids(self, val: int):
        self.s.solenoids[:] = [val] * self.nozzles

    def print_aperture(self):
        print(self.s.apertures)

    def print_solenoid(self):
        print(self.s.solenoids)


class LightCurveTransmitter:

    def __init__(self, state: LightCurveState) -> None:

        print('initialize light curve transmitter')

        self.state = state
        # override this if you want just the transmitter debugging
        self.debug = state.debug

        # create outbound socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # this takes the 0 to 1 value from the pattern,
    # applies the per nozzle calibration, and returns the corrected
    # value for sending to the controller, using the table 
    # in the config file

    def nozzle_apply_calibration(self, nozzle: int, val: float ) -> float:

        correction = self.state.aperture_calibration[str(nozzle)]
        start = correction[0]
        stop = correction[1]
        return ((stop-start) * val) + start


# note about the mapping.
# Each controller contains an array called "solenoid_map" and "aperture_map".
# this becomes an indirection table.


    # call each time
    def transmit(self) -> None:

        print(f'transmit') if self.debug else None

        for c in self.state.controllers:

            # allocate the packet TODO allocate a packet once
            packet = bytearray( ( self.state.nozzles * 2) + ARTNET_HEADER_SIZE)

            # fill in the artnet part
            _artnet_packet(ARTNET_UNIVERSE, 0, packet)

            aperture_map = c['aperture_map']
            solenoid_map = c['solenoid_map']

            # fill in the data bytes
            for i in range(c['nozzles']):

                solenoid = solenoid_map [ i ]
                aperture = aperture_map [ i ]

                # print(f'c: {c['name']} packet solenoid {i} model solenoid {solenoid}')
                # print(f'c: {c['name']} packet aperture {i} model aperture {aperture}')

                # validation. Could make optional.
                if (self.debug and 
                        ( self.state.s.solenoids[solenoid] < 0) or (self.state.s.solenoids[solenoid] > 1)):
                    print(f'active at {i+offset} out of range {self.state.s.solenoids[solenoid]} skipping')
                    return
                if (self.debug and 
                        (self.state.s.apertures[aperture] < 0.0) or (self.state.s.apertures[aperture] > 1.0)):
                    print(f'flow at {i+offset} out of range {self.state.s.apertures[aperture]} skipping')

# FILTER
# In the case where the solenoid and aperture are mapped to the same physical device,
# it is useful to turn off the solenoid when the aperture value is small. However, before mapping,
# it doesn't work, because the apertures and nozzles are not the same physical device.

#                if self.state.s.apertures[i+offset] < 0.10:
#                    print(f'force to 0 solenoid {i+offset}')
#                    packet[ARTNET_HEADER_SIZE + (i*2) ] = 0
#                else:

                packet[ARTNET_HEADER_SIZE + (i*2) ] = self.state.s.solenoids[solenoid]

                if (self.state.s.raw_apertures[aperture] == -1):

                    packet[ARTNET_HEADER_SIZE + (i*2) + 1] = math.floor(self.nozzle_apply_calibration( aperture, self.state.s.apertures[aperture] ) )

                else:

                    packet[ARTNET_HEADER_SIZE + (i*2) + 1] = self.state.s.raw_apertures[aperture]


            # transmit
            if self.debug:
                print(f' sending packet to {c["ip"]} for {c["name"]}')
                print_bytearray(packet)

            self.sock.sendto(packet, (c['ip'], ARTNET_PORT))




# useful helper function
def print_bytearray(b: bytearray) -> None:
    l = len(b)
    o = 0
    while (l > 0):
        if (l >= 8):
            print('{:4x}: {:2x} {:2x} {:2x} {:2x} {:2x} {:2x} {:2x} {:2x}'.format(o, b[o+0],b[o+1],b[o+2],b[o+3],b[o+4],b[o+5],b[o+6],b[o+7]))
            l -= 8
            o += 8
        elif l == 7:
            print('{:4x}: {:2x} {:2x} {:2x} {:2x} {:2x} {:2x} {:2x} '.format(o, b[o+0], b[o+1], b[o+2], b[o+3], b[o+4], b[o+5], b[o+6]))
            l -= 7
            o += 7
        elif l == 6:
            print('{:4x}: {:2x} {:2x} {:2x} {:2x} {:2x} {:2x}'.format(o, b[o+0], b[o+1], b[o+2], b[o+3], b[o+4], b[o+5]))
            l -= 6
            o += 6
        elif l == 5:
            print('{:4x}: {:2x} {:2x} {:2x} {:2x} {:2x}'.format(o, b[o+0], b[o+1], b[o+2], b[o+3], b[o+4] ))
            l -= 5
            o += 5
        elif l == 4:
            print('{:4x}: {:2x} {:2x} {:2x} {:2x}'.format(o, b[o+0], b[o+1], b[o+2], b[o+3] ))
            l -= 4
            o += 4
        elif l == 3:
            print('{:4x}: {:2x} {:2x} {:2x}'.format(o, b[o+0], b[o+1], b[o+2]))
            l -= 3
            o += 3
        elif l == 2:
            print('{:4x}: {:2x} {:2x} '.format(o, b[o+0], b[o+1]))
            l -= 2
            o += 2
        elif l == 1:
            print('{:4x}: {:2x}'.format(o, b[o+0]))
            l -= 1
            o += 1


# stop all the things just using the solenoids not touching the aperturs
# which might or might not have good configuration and calibration

def pattern_stop(state: LightCurveState, xmit: LightCurveTransmitter):
    state.fill_solenoids(0)
    xmit.transmit()


# set a single servo to a raw value
# but use the nozzle map to make it more comprehensible
# turn all the solenoids off other than that one

def pattern_aperture_value(state: LightCurveState, xmit: LightCurveTransmitter, solenoid: int, servo: int, flow: int, hold: bool) -> bool :

    if solenoid is None:
        print(f'Specify a solenoid to use')
        return(False)
    if servo is None:
        print(f'Specify a servo to use')
        return(False)
    if flow is None:
        print(f'Specify a flow to use')
        return(False)

    if (solenoid >= state.nozzles):
        print(f'Solenoid out of range is {solenoid} must be less than {state.nozzles}')
        return(False)
    if (servo >= state.nozzles):
        print(f'Servo out of range is {servo} must be less than {state.nozzles}')
        return(False)
    if (flow > 255) or (flow < 0):
        print(f'Flow out of range must be 255 or less, and positive, is {flow}')
        return(False)

    print(f'Setting servo {servo} to raw value {flow} and solenoid {solenoid}')
    print(f' all other to their 0')
    print(f' and all solenoids off')

    state.fill_solenoids(0)
    state.s.solenoids[solenoid] = 1

    state.s.raw_apertures[servo] = flow

    if hold == True:
        while True:
            xmit.transmit()
            sleep(0.1)
    else:
        xmit.transmit()


    return(True)

def pattern_click(state: LightCurveState, xmit: LightCurveTransmitter, solenoid: int) -> bool :

    if solenoid is None:
        print(f'Specify a solenoid to use clicker')
        return(False)

    if (solenoid >= state.nozzles):
        print(f'Solenoid out of range is {solenoid} must be less than {state.nozzles}')
        return(False)

    print(f'Clicking {solenoid} ')
    print(f' all other things to their calibrated 0')
    print(f' and all solenoids off')

    state.fill_solenoids(0)

    delay = 0.01

    while True:

        state.s.solenoids[solenoid] = 1

        xmit.transmit()

        sleep(delay)

        state.s.solenoids[solenoid] = 0

        xmit.transmit()

        sleep(delay)


    return(True)


# set a single servo to a raw value
# but use the nozzle map to make it more comprehensible
# turn all the solenoids off other than that one

def pattern_aperture_sweep(state: LightCurveState, xmit: LightCurveTransmitter, solenoid: int, servo: int) -> bool :

    if solenoid is None:
        print(f'Specify a solenoid to use')
        return(False)
    if servo is None:
        print(f'Specify a servo to use')
        return(False)

    if (solenoid >= state.nozzles):
        print(f'Solenoid out of range is {solenoid} must be less than {state.nozzles}')
        return(False)
    if (servo >= state.nozzles):
        print(f'Servo out of range is {servo} must be less than {state.nozzles}')
        return(False)


    print(f'Sweepting servo {servo} from 0 to 255 raw value and solenoid {solenoid}')
    print(f' all other apertures to their calibrated 0')
    print(f' and all solenoids off')

    state.fill_solenoids(0)
    state.s.solenoids[solenoid] = 1

    flow = 0
    ascending = True

    # constants
    step = 10
    delay = 0.10

    while True:


        if flow > 255:
            print(f'flow at top, descending now')
            ascending = False
            flow = 255

        if flow < 0:
            print(f' flow at bottom: ascending now')
            ascending = True
            flow = 0 

        state.s.raw_apertures[servo] = flow

        xmit.transmit()

        if ascending:
            flow += step
        else:
            flow -= step

        sleep(delay)

    return(True)



def args_init():
    parser = argparse.ArgumentParser(prog='lc_test', description='Send ArtNet packets to the Light Curve for simple testing')
    parser.add_argument('--config','-c', type=str, default="lightcurve.cnf", help='Fire Art Controller configuration file')

    parser.add_argument('--solenoid', type=int, required=True, help="solenoid to apply to")
    parser.add_argument('--servo', type= int, help="servo to apply to")

    # if flow not specified, sweep
    parser.add_argument('--flow', '-f', type=int, help="amount to set servo to")

    parser.add_argument('--hold', default=False, action='store_true', help="keep sending this value foever")

    # patterns
    parser.add_argument('--stop', default=False, action='store_true', help="turn everything off")

    parser.add_argument('--click', default=False, action='store_true', help="make solinoid click so we can find it")


    args = parser.parse_args()

    # load config file
    with open(args.config) as ftc_f:
        conf = json.load(ftc_f)  # XXX catch exceptions here.
        args.controllers = conf['controllers']
        args.nozzles = conf['nozzles']
        args.aperture_calibration = conf['aperture_calibration']

    return args


# inits then pattern so simple

def main():

    args = args_init()

    try:
        state = LightCurveState(args)
    except Exception as e:
        print(f' Config file problem, exiting: {str(e)} ')
        return

    # creates a transmitter background process that reads from the shared state
    xmit = LightCurveTransmitter(state)

    if args.stop == True:
        pattern_stop(state, xmit)
    elif args.click == True:
        pattern_click(state, xmit, args.solenoid)
    elif args.flow == None:
        # no flow specified, sweep
        pattern_aperture_sweep(state, xmit, args.solenoid, args.servo)    
    else:
        # flow and nozzle, set it and get out
        pattern_aperture_value(state, xmit, args.solenoid, args.servo, args.flow, args.hold)



# Run main when from the command line only
if __name__ == '__main__':
    main()
