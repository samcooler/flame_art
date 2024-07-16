#!/usr/bin/env python3


# WARNING has syntax that is python 3
# you will see strange looking errors in Python2
# not sure exactly which python is required...

# using the pyartnet module for sending artnet. Might almost
# be easier to hand-code it, it's a very simple protocol

# Because packet might be lost or the wifi might be offline, it's
# important to output a steady stream of packets at a given frame rate.
# use a separate thread for that.

# use another thread for actually changing the values.

# to write a pattern, write 

# see readme for definition of the device

### NOTE:
### The configuration file allows specification of the complete number of nozzles
### this allows to run the simulator and the sculpture at the same time,
### or other shenanigans

# Author: brian@bulkowski.org Brian Bulkowski 2024 Copyright assigned to Sam Cooler

import socket
from time import sleep, time
import argparse
import json
from threading import Thread, Event
import math

from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from osc4py3 import oscmethod as osm
import netifaces

import glob 
import importlib
import os
import sys

OSC_PORT = 6511 # a random number. there is no OSC port because OSC is not a protocol

ARTNET_PORT = 6454
ARTNET_UNIVERSE = 0
ARTNET_HEADER_SIZE = 18

debug = False
ARGS = None

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

    packet[12] = sequence
    packet[13] = 0
    packet[14] = universe & 0xff
    packet[15] = (universe >> 8) & 0xff

    l = len(packet) - ARTNET_HEADER_SIZE
    packet[16] = (l >> 8) & 0xff
    packet[17] = l & 0xff

    # print_bytearray(packet)

class LightCurveTransmitter:

    def __init__(self, args) -> None:

        self.controllers = args.controllers

        self.nozzles = args.nozzles
        self.apertures = [0.0] * self.nozzles
        self.solenoids = [0] * self.nozzles

        self.debug = debug
        self.sequence = 0
        self.repeat = args.repeat
        self.fps = args.fps

        # create outbound socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    # call once to set up 
    def transmit(self) -> None:

        print(f'transmit') if self.debug else None

        for c in self.controllers:

            # allocate the packet TODO allocate a packet once
            packet = bytearray( ( self.nozzles * 2) + ARTNET_HEADER_SIZE)

            # fill in the artnet part
            _artnet_packet(ARTNET_UNIVERSE, self.sequence, packet)

            # fill in the data bytes
            offset = c['offset']
            for i in range(c['nozzles']):

                # validation. Could make optional.
                if (self.debug and 
                        ( self.solenoids[i+offset] < 0) or (self.solenoids[i+offset] > 1)):
                    print(f'active at {i+offset} out of range {self.solenoids[i+offset]} skipping')
                    return
                if (self.debug and 
                        (se.fapertures[i+offset] < 0.0) or (self.apertures[i+offset] > 1.0)):
                    print(f'flow at {i+offset} out of range {self.apertures[i+offset]} skipping')

                if self.apertures[i+offset] < 0.10:
                    packet[ARTNET_HEADER_SIZE + (i*2) ] = 0
                else:
                    packet[ARTNET_HEADER_SIZE + (i*2) ] = self.solenoids[i+offset]

                packet[ARTNET_HEADER_SIZE + (i*2) + 1] = math.floor(self.apertures[i+offset] * 255.0 )

            # transmit
            if self.debug:
                print(f' sending packet to {c["ip"]} for {c["name"]}')
                print_bytearray(packet)

            self.sock.sendto(packet, (c['ip'], ARTNET_PORT))

        self.sequence += 1

    def fill_apertures(self, val: float):
        for i in range(0,self.nozzles):
            self.apertures[i] = val

    def fill_solenoids(self, val: int):
        for i in range(0,self.nozzles):
            self.solenoids[i] = val

    def print_aperture(self):
        print(self.apertures)

    def print_solenoid(self):
        print(self.solenoids)

# it appears in python when we set up a broadcast listerner
# we would just listen on 0.0.0.0 so we probably won't need any of this
# and we would listen on not the broadcast address but probably the IP of the interface or soemthing
# when we do listeners on broadcast, we need to specify either "any", or we need to specify
# the interface we are listening on
def get_interface_addresses():
    interfaces = netifaces.interfaces()
    interface_addrs = []

    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            ipv4_info = addresses[netifaces.AF_INET][0]
            interface_addr = ipv4_info.get('addr')
            if interface_addr:
                interface_addrs.append(interface_addr)

    print(f'interfaces addresses are: {interface_addrs}')
    return interface_addrs

def osc_handler(address, *args):
    print(f' osc handler received address {address}')

    # todo: unpack out the address, and the parameters, 

class OSCReceiver:
    def __init__(self, args) -> None:

        # rotational speed around pitch, yaw, roll        
        self.gyro = [0.0] * 3
        # absolute rotational position compared to a fixed reference frame
        self.rotation = [0.0] * 3
        # the direction in which gravity currently is
        self.gravity = [0.0] * 3

        self.debug = debug
        self.sequence = 0
        self.repeat = args.repeat

        # only one thread because we don't have much data
        osc_startup()

        if args.address == "" :

            addresses = get_interface_addresses()
            # if there's only one address use it
            if len(addresses) == 1:
                args.address = addresses[0]
            # if there's multiple pick the non localhost one
            for a in addresses:
                # don't send on loopback?
                if a != '127.0.0.1':
                    args.address = a
                    break
        
        print(f'OSC listening for broadcasts on {args.address}')

# it appears when setting up UDP listneres generaly you don't need to do anything different
# for broadcast
#        osc_broadcast_server(args.address,  OSC_PORT, 'server')
        osc_udp_server(args.address,  OSC_PORT, 'server')

        # setting a single method for all the messages, so we can debug eaiser
        osc_method('/LC/*', osc_handler, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATA + osm.OSCARG_EXTRA, extra=self)
#        osc_method('/LC/*', osc_handler, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATA + osm.OSCARG_EXTRA,
#            extra=self)



# background 

# set when you want output
xmit_event = Event()

def xmit_thread(xmit):
    delay = 1.0 / xmit.fps
    # print(f'delay is {delay} fps is {xmit.fps}')

    while(True):
        t1 = time()
        if xmit_event.is_set():
            xmit.transmit()
        d = delay - (time() - t1)
        if (d > 0.002):
            sleep(d)

        osc_process()

def xmit_thread_init(xmit):
    global BACKGROUND_THREAD, xmit_event
    xmit_event.set()
    BACKGROUND_THREAD = Thread(target=xmit_thread, args=(xmit,) )
    BACKGROUND_THREAD.daemon = True
    BACKGROUND_THREAD.start()

def xmit_thread_start():
    xmit_event.set()

def xmit_thread_stop():
    xmit_event.clear()


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

# Dynamically import patterns

def import_patterns():
    global PATTERN_FUNCTIONS
    PATTERN_FUNCTIONS = {}

    # kinda shitty but just add the directory with this file to the path and remove it again
    sys.path.append(os.path.dirname(__file__))

    dir_path = f'{os.path.dirname(__file__)}/pattern_*.py'
    for fn in glob.glob(dir_path):

        pattern_name = os.path.splitext(os.path.basename(fn))[0]
        pattern_functionname = pattern_name.split('_',1)[1]
        # print(f'importing pattern name {pattern_functionname} in file {pattern_name}')
        module = importlib.import_module(pattern_name)
        PATTERN_FUNCTIONS[pattern_functionname] = getattr(module,pattern_name)

    sys.path.remove(os.path.dirname(__file__))

# load all the modules (files) which contain patterns

def patterns():
    return ' '.join(PATTERN_FUNCTIONS.keys())

def pattern_execute(pattern: str, xmit) -> bool:

    if pattern in PATTERN_FUNCTIONS:
        PATTERN_FUNCTIONS[pattern](xmit)
    else:
        return False

    return True

def pattern_insert(pattern_name: str, pattern_fn):
    PATTERN_FUNCTIONS[pattern_name] = pattern_fn


def pattern_multipattern(xmit: LightCurveTransmitter):

    print(f'Starting multipattern pattern')

    for _ in range(xmit.repeat):
        for name, fn in PATTERN_FUNCTIONS.items():
            if name != 'multipattern':
                fn(xmit)

    print(f'Ending multipattern pattern')

#
#

def args_init():
    parser = argparse.ArgumentParser(prog='flame_test', description='Send ArtNet packets to the Color Curve for testing')
    parser.add_argument('--config','-c', type=str, default="flame_test.cnf", help='Fire Art Controller configuration file')

    parser.add_argument('--pattern', '-p', default="pulse", type=str, help=f'pattern one of: {patterns()}')
    parser.add_argument('--address', '-a', default="0.0.0.0", type=str, help=f'address to listen OSC on defaults to broadcast on non-loop')
    parser.add_argument('--fps', '-f', default=15, type=int, help='frames per second')
    parser.add_argument('--repeat', '-r', default=1, type=int, help="number of times to run pattern")

    args = parser.parse_args()

    # load config file
    with open(args.config) as ftc_f:
        conf = json.load(ftc_f)  # XXX catch exceptions here.
        args.controllers = conf['controllers']
        args.nozzles = conf['nozzles']

    return args


# inits then pattern so simple

def main():

    global ARGS

    import_patterns()
    pattern_insert('multipattern', pattern_multipattern)

    args = args_init()

    recv = OSCReceiver(args)

    xmit = LightCurveTransmitter(args)

    xmit_thread_init(xmit)

    if args.pattern not in PATTERN_FUNCTIONS:
        print(f' pattern must be one of {patterns()}')
        return

    # run it bro
    for _ in range(args.repeat):
        pattern_execute(args.pattern, xmit)


# only effects when we're being run as a module but whatever
if __name__ == '__main__':
    main()
