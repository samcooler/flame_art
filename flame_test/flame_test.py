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
from multiprocessing import Process, Event, Manager
import asyncio
import math

#from osc4py3.as_eventloop import *
#from osc4py3 import oscbuildparse
#from osc4py3 import oscmethod as osm

# let's use the AsyncIO call structure from osc_server
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from pythonosc import osc_server

import netifaces
import importlib

import glob 
import os
import sys

from typing import List, Any

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

    packet[12] = sequence & 0xff
    packet[13] = 0
    packet[14] = universe & 0xff
    packet[15] = (universe >> 8) & 0xff

    l = len(packet) - ARTNET_HEADER_SIZE
    packet[16] = (l >> 8) & 0xff
    packet[17] = l & 0xff

    # print_bytearray(packet)

#
# This is a shared class, across processes. It is shared between processes
# by simply passing it through the process create. This has the amusing property
# of creating a new copy of the object, but any fields Managed by multiprocessing
# are essentially copied by reference. This object, thus, gets initialized only
# once, but exists in three copies - one in each process - but the shared object
# is shared.
#
# this means values that are in args and never change don't need to be copied
# into shared, only mutable values need to be constructed in the shared object
#
# while this use is terse and rather cute, the construct / copy mechanism
# between processes becomes a little bit of a footgun. Beware.

class LightCurveState:

    def __init__(self, args):
        self.s = Manager().Namespace()

        self.controllers = args.controllers
        self.nozzles = args.nozzles

        s = self.s
        s.apertures = [0.0] * self.nozzles
        s.solenoids = [0] * self.nozzles

        # rotational speed around pitch, yaw, roll        
        s.gyro = [0.0] * 3
        # absolute rotational position compared to a fixed reference frame
        s.rotation = [0.0] * 3
        # the direction in which gravity currently is
        s.gravity = [0.0] * 3

        s.nozzles_buttons = [False] * NOZZLE_BUTTON_LEN
        s.control_buttons = [False] * CONTROL_BUTTON_LEN

        self.debug = debug
        self.fps = args.fps

        # this is a little bit of a hack because it's not part of the sculpture
        # state. It is convenient
        self.repeat = args.repeat
        self.fps = args.fps

    # because this is a shared object, I think constructing then setting
    # is faster than setting one by one
    def fill_apertures(self, val: float):
        self.s.apertures = [val] * self.nozzles
#        for i in range(0,self.s.nozzles):
#            self.s.apertures[i] = val

    def fill_solenoids(self, val: int):
        self.s.solenoids = [val] * self.nozzles
#        for i in range(0,self.s.nozzles):
#            self.s.solenoids[i] = val

    def print_aperture(self):
        print(self.s.apertures)

    def print_solenoid(self):
        print(self.s.solenoids)


class LightCurveTransmitter:

    def __init__(self, lc_state: LightCurveState) -> None:

        print('initialize light curve transmitter')

        self.lc_state = lc_state
        self.sequence = 0
        # override this if you want just the transmitter debugging
        self.debug = lc_state.debug

        # create outbound socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    # call each time
    def transmit(self) -> None:

        print(f'transmit') if self.debug else None

        for c in self.lc_state.controllers:

            # allocate the packet TODO allocate a packet once
            packet = bytearray( ( self.lc_state.nozzles * 2) + ARTNET_HEADER_SIZE)

            # fill in the artnet part
            _artnet_packet(ARTNET_UNIVERSE, self.sequence, packet)

            # fill in the data bytes
            offset = c['offset']
            for i in range(c['nozzles']):

                # validation. Could make optional.
                if (self.debug and 
                        ( self.lc_state.s.solenoids[i+offset] < 0) or (self.lc_state.s.solenoids[i+offset] > 1)):
                    print(f'active at {i+offset} out of range {self.lc_state.s.solenoids[i+offset]} skipping')
                    return
                if (self.debug and 
                        (self.lc_state.s.apertures[i+offset] < 0.0) or (self.lc_state.s.apertures[i+offset] > 1.0)):
                    print(f'flow at {i+offset} out of range {self.lc_state.s.apertures[i+offset]} skipping')

                if self.lc_state.s.apertures[i+offset] < 0.10:
                    packet[ARTNET_HEADER_SIZE + (i*2) ] = 0
                else:
                    packet[ARTNET_HEADER_SIZE + (i*2) ] = self.lc_state.s.solenoids[i+offset]

                packet[ARTNET_HEADER_SIZE + (i*2) + 1] = math.floor(self.lc_state.s.apertures[i+offset] * 255.0 )

            # transmit
            if self.debug:
                print(f' sending packet to {c["ip"]} for {c["name"]}')
                print_bytearray(packet)

            self.sock.sendto(packet, (c['ip'], ARTNET_PORT))

        self.sequence += 1


# background 

XMIT_EVENT = Event()

# see comment about lc_state, it is a cross process shared object.
# this function is a separate process

def transmitter_server(lc_state: LightCurveState, xmit_event: Event):

    xmit = LightCurveTransmitter(lc_state)

    delay = 1.0 / lc_state.fps
    # print(f'delay is {delay} fps is {xmit.fps}')

    while(True):
        t1 = time()

        if xmit_event.is_set():
            xmit.transmit()

        d = delay - (time() - t1)
        if (d > 0.002):
            sleep(d)

def transmitter_server_init(lc_state: LightCurveState):
    global TRANSMITTER_PROCESS, XMIT_EVENT

    print('transmitter server init')

    XMIT_EVENT.set()
    TRANSMITTER_PROCESS = Process(target=transmitter_server, args=(lc_state, XMIT_EVENT) )
    TRANSMITTER_PROCESS.daemon = True
    TRANSMITTER_PROCESS.start()

def transmitter_server_start():
    global XMIT_EVENT
    XMIT_EVENT.set()

def transmitter_server_stop():
    global XMIT_EVENT
    XMIT_EVENT.clear()


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

# handler has the address then a tuple of the arguments then the self argument of the receiver
# Not yet sure how to get the timestamp out of the bundle
# Bundle receiption hasn't worked

# generic handler good for debugging
def osc_handler_all (address: str, fixed_args: List[Any], *vals):
    lc_state = fixed_args[0]
    print(f' osc handler ALL received address {address} len {len(address)}; positional arguments: {vals}')

# specific handlers good for efficiency
def osc_handler_gyro(address: str, fixed_args: List[Any], *vals):
    print(f' osc: gyro {vals}') if lc_state.debug else None
    lc_state = fixed_args[0]
    if len(vals) != 3:
        return
    lc_state.s.gyro = vals
 
def osc_handler_rotation(address: str, fixed_args: List[Any], *vals):
    print(f' osc: rotation {vals}') if lc_state.debug else None
    lc_state = fixed_args[0]
    if len(vals) != 3:
        return
    lc_state.s.rotation = vals

def osc_handler_gravity(address: str, fixed_args: List[Any], *vals):
    print(f' osc: gravity {vals}') if lc_state.debug else None
    lc_state = fixed_args[0]
    if len(vals) != 3:
        return
    lc_state.s.gravity = vals

# imu order
# miliseconds int
# rotation, gravity, gyro

def osc_handler_imu(address: str, fixed_args: List[Any], *vals):
    # print(f'handler received IMU: time {vals[0]} rot {vals[1:4]}, grav {vals[4:7]}, gyro {vals[7:10]} ') if lc_state.debug else None
    if len(vals) != 10:
        print(f'IMU: wrong number parameters should be 10 is: {len(vals) }')
        return
    lc_state = fixed_args[0]
    lc_state.s.rotation = vals[1:4]
    lc_state.s.gravity = vals[4:7]
    lc_state.s.gyro = vals[7:10]
    print(f'OSC IMU: rot {vals[1]:.4f}, {vals[2]:.4f}, {vals[3]:.4f}, grav {vals[4]:.4f}, {vals[5]:.4f}, {vals[6]:.4f} gyro {vals[7]:.4f}, {vals[8]:.4f}, {vals[9]:.4f}  ') if lc_state.debug else None
    print(f'OSC IMU: rot {vals[1]:.4f}, {vals[2]:.4f}, {vals[3]:.4f}, grav {vals[4]:.4f}, {vals[5]:.4f}, {vals[6]:.4f} gyro {vals[7]:.4f}, {vals[8]:.4f}, {vals[9]:.4f}  ') 


def osc_handler_nozzles(address: str, fixed_args: List[Any], *vals):
    print(f' osc: nozzles {vals}') if lc_state.debug else None
    lc_state = fixed_args[0]
    lc_state.s.nozzles = vals

def osc_handler_controls(address: str, fixed_args: List[Any], *vals):
    print(f' osc: controls {vals}') if lc_state.debug else None
    lc_state = fixed_args[0]
    lc_state.s.controls = vals


#this has never worked
def osc_handler_bundle(address: str, fixed_args: List[Any], *vals):
    lc_state = fixed_args[0]
    print(f' osc bundle handler received address {address}')
    print(f' osc handler bundle: args {vals}')



# this is a single method for everything good for debugging
#        osc_method('/*', osc_handler, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATA + osm.OSCARG_EXTRA,
#            extra=self)
# this receives bundles and will check on timestamps
# getting bundles is not working. Therefore for now will just register the individual paths
#        osc_method("#bundle", osc_handler_bundle, argscheme=osm.OSCARG_DATAUNPACK + osm.OSCARG_EXTRA, extra=self)
#        osc_method("#*", osc_handler_bundle, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATA)
#        print(f' registered bundle handler')

# this is a new process, and uses a blocking OSC library.
# it takes anything it receives and places it in the shared lc_state object
# for other processes to read

def osc_server(lc_state: LightCurveState, address: str):

    dispatcher = Dispatcher()

    # setting up a catch-all can be good for debugging
    # dispatcher.map('*', osc_handler_all, lc_state)

    # setting individual methods for each, slightly more efficient - but won't get timestamp bundles -
    # so disabling if we're using bundles
    dispatcher.map('/LC/gyro', osc_handler_gyro, lc_state)
    dispatcher.map('/LC/rotation', osc_handler_rotation, lc_state)
    dispatcher.map('/LC/gravity', osc_handler_gravity, lc_state)

    dispatcher.map('/LC/imu', osc_handler_imu, lc_state)

    dispatcher.map('/LC/nozzles', osc_handler_nozzles, lc_state)
    dispatcher.map('/LC/controls', osc_handler_controls, lc_state)
    dispatcher.set_default_handler(osc_handler_all, lc_state)

    server = BlockingOSCUDPServer((address, OSC_PORT), dispatcher)
    server.serve_forever()  # Blocks forever

def osc_server_init(lc_state, args):
    global OSC_PROCESS

    # decide the address to listen on
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


    OSC_PROCESS = Process(target=osc_server, args=(lc_state, args.address) )
    OSC_PROCESS.daemon = True
    OSC_PROCESS.start()



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

def pattern_execute(pattern: str, lc_state) -> bool:

    if pattern in PATTERN_FUNCTIONS:
        PATTERN_FUNCTIONS[pattern](lc_state)
    else:
        return False

    return True

def pattern_insert(pattern_name: str, pattern_fn):
    PATTERN_FUNCTIONS[pattern_name] = pattern_fn


def pattern_multipattern(state: LightCurveState):

    print(f'Starting multipattern pattern')

    for _ in range(state.repeat):
        for name, fn in PATTERN_FUNCTIONS.items():
            if name != 'multipattern':
                fn(state)

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

    lc_state = LightCurveState(args)

    # creates a transmitter background process that reads from the shared state
    transmitter_server_init(lc_state)

    # creates a osc server receiver process which fills the shared state
    osc_server_init(lc_state, args)

    if args.pattern not in PATTERN_FUNCTIONS:
        print(f' pattern must be one of {patterns()}')
        return

    # run it bro
    try:
        for _ in range(args.repeat):
            pattern_execute(args.pattern, lc_state)

    except KeyboardInterrupt:
        pass


# only effects when we're being run as a module but whatever
if __name__ == '__main__':
    main()
