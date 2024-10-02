#!/usr/bin/env python


# Generally coded with python 3.12, but also works with Python 3.10,
# as one of the older laptops we use is Ubuntu w

# general theory
#
# Allow patterns to be created with the file suffix "pattern".
# they will be detected and executing with -p will cause that code to run.
#
# Also have a playlist, which is a simple JSON file allowing a list of patterns and times.
#
# Four processes are used. Processes are used to avoid latency that could be caused using
# multithreading. A badly written pattern could cause execution issues where OSC commands
# wouldn't be read, or packets to the controllers wouldn't be sent.

# Main process - starts with main, launches all other processes, and in the case of direct
# pattern execution, runs the pattern
# OSC process - after trying several libraries that claimed to be non-blocking, the most
# commonly used OSC process works best with blocking.
# Xmit process - sends artnet packets
#
# In order to coordinate between processes, shared memory is used. A single shared memory manager
# is created by the main process, and that manager is used to create the coordination
# data structures, which are in the "LightCurveState" shared namespace. This should be efficient,
# although it depends slightly on the implementaiton characteristics of the underlying python
# system. This code is intended to run on a raspberry pi with 10's of milliseconds of accuracy,
# the access to more cores should offset the synchronization overhead of shared memory.
#
# A configuration file is used to state how many controllers and their addresses and characteristics
# including an indirection mapping file.
#
# A playlist file is a simple list of json objects with names and durations.

### NOTE:
### The configuration file allows specification of the complete number of nozzles
### this allows to run the simulator and the sculpture at the same time,
### or other shenanigans

# Author: brian@bulkowski.org Brian Bulkowski 2024 Copyright assigned to Sam Cooler

import socket
from time import sleep, time
import argparse
import json
from multiprocessing import Process, Event, Manager, Queue
import queue
from types import SimpleNamespace
import asyncio
import math

# let's use the Blocking call structure from pythonosc 
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from pythonosc import osc_server

# netifaces helps us make sure we're talking the right network
import netifaces
# importlib is necessary for the strange plugin system
import importlib
#
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import glob 
import os
import sys

from typing import Dict, List, Any

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

STATUS_PORT = 6510

OSC_PORT = 6511 # a random number. there is no OSC port because OSC is not a protocol

COMMAND_PORT = 6509

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

#
# This is a shared class, across processes. It is shared between processes
# by simply passing it through the process create. This has the amusing property
# of creating a new copy of the object.
#
# A note about using shared memory in Python multiprocessing!
#
# First fun fact: When you create a shared Namespace, objects within it are created shared, but not recursively.
# this means you can create an entire list, assign it to the namespace, and that list will be shared.
# However, mutations to that list will not be shared! That only happens if the list is also shared.
#
# Second fun fact: creating a Manager is expensive, and the manager must be kept alive for the lifetime
# of all objects created using the namespace. You'll essentially use a ton more memory than you think if you
# just access Manager() to create a new manager every time you create a new array.
#
# Third fun fact: Manager is not pickleable, thus can't be passed across a process boundry. Which means
# what you really is one of two things: create all your shared objects up front from the main process,
# or create one manager per process and use that manager for all subsequent alloactions in that process.
#
# In this code, I am using the technique of allocating all the shared memory up-front. We know the sizes
# of these arrays, and thus make sure we copy by value and not replace the arrays with arrays which are
# mutable only in the process. Alternately, one could create a manager instance in LightCurveState which
# is constructed once, indepenatly, in each process and used every time you want to create a new shared list.
# I am guessing that the efficiency of accessing elements is cheaper than creating new arrays, which is usually
# not the case in python. 


class LightCurveState:

    def __init__(self, args, manager):

        self.controllers = args.controllers
        self.nozzles = args.nozzles
        self.aperture_calibration = args.aperture_calibration

# not quite sure if I need a shared namespace or a simple namespace will do.
# if all the objects in the namespace are themselves shared, then a simple namespace should work.
# if there are any non-shared objects (eg, integers or strings), then I must use a shared namespace?
# you need the shared namespace if you're going to have a straight member, like the nozzle buttons time.
        self.s = manager.Namespace()
        s = self.s
        s.apertures = manager.list( [0.0] * self.nozzles )
        s.solenoids = manager.list( [0] * self.nozzles )

        # rotational speed around pitch, yaw, roll        
        s.gyro = manager.list( [0.0] * 3 )
        # absolute rotational position compared to a fixed reference frame
        s.rotation = manager.list( [0.0] * 3 )
        # the direction in which gravity currently is
        s.gravity = manager.list( [0.0] * 3 )

        s.nozzle_buttons_last_recv = None
        s.nozzle_buttons = manager.list( [False] * NOZZLE_BUTTON_LEN )
        s.nozzle_buttons_1_last_recv = None
        s.nozzle_buttons_1 = manager.list( [False] * NOZZLE_BUTTON_LEN )

        self.debug = debug

        # The arguments structure is a convenient way to get information to patterns.
        self.args = args
        self.command_queue = Queue() # multiprocessing queue

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

    def set_solenoid(self, nozzle, val: int):
        # set one or more solenoids. None sets all
        if nozzle is not None:
            self.s.solenoids[nozzle] = val
        else:
            self.fill_solenoids(val)

    def set_aperture(self, nozzle, val: float):
        # set one or more apertures. None sets all
        if nozzle is not None:
            self.s.apertures[nozzle] = val
        else:
            self.fill_apertures(val)

    def print_aperture(self):
        print(self.s.apertures)

    def print_solenoid(self):
        print(self.s.solenoids)

    # if you don't receive a packet after 1 second, turn off
    # as usual, be careful with setting data in the shared structure. Has to change values, not the array
    def nozzle_button_timeout_check(self):
        now = time()
        if self.s.nozzle_buttons_last_recv is not None:
            # print(f' nozzle button last recv {self.s.nozzle_buttons_last_recv}')
            if self.s.nozzle_buttons_last_recv + 1.0 < now:
                print(f' nozzle button og timeout:')
                self.s.nozzle_buttons_last_recv = None
                for i in range(self.nozzles):
                    self.s.nozzle_buttons[i] = False

        if self.s.nozzle_buttons_1_last_recv is not None:
            # print(f' nozzle button last recv {self.s.nozzle_buttons_1_last_recv}')
            if self.s.nozzle_buttons_1_last_recv + 1.0 < now:
                print(f' nozzle button 1 timeout:')
                self.s.nozzle_buttons_1_last_recv = None
                for i in range(self.nozzles):
                    self.s.nozzle_buttons_1[i] = False

# 
# This transmitter class sends packets to the control boards.
#


class LightCurveTransmitter:

    def __init__(self, state: LightCurveState) -> None:

        print('initialize light curve transmitter')

        self.state = state
        self.sequence = 0
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

        use_buttons = not self.state.args.nobuttons

        for c in self.state.controllers:

            # allocate the packet TODO allocate a packet once
            packet = bytearray( ( self.state.nozzles * 2) + ARTNET_HEADER_SIZE)

            # fill in the artnet part
            _artnet_packet(ARTNET_UNIVERSE, self.sequence, packet)

            aperture_map = c['aperture_map']
            solenoid_map = c['solenoid_map']

            # fill in the data bytes
            for i in range(c['nozzles']):

                solenoid = solenoid_map [ i ]
                aperture = aperture_map [ i ]

                # print(f'c: {c['name']} packet solenoid {i} model solenoid {solenoid}')
                # print(f'c: {c['name']} packet aperture {i} model aperture {aperture}')

                # validation. Could make optional.
                # self.state.s.solenoids = [0 if s is None else s for s in self.state.s.solenoids]
                # self.state.s.apertures = [0 if a is None else a for a in self.state.s.apertures]
                # if (self.debug and
                #         ( self.state.s.solenoids[solenoid] < 0) or (self.state.s.solenoids[solenoid] > 1)):
                #     print(f'active at {i+offset} out of range {self.state.s.solenoids[solenoid]} skipping')
                #     return
                # if (self.debug and
                #         (self.state.s.apertures[aperture] < 0.0) or (self.state.s.apertures[aperture] > 1.0)):
                #     print(f'flow at {i+offset} out of range {self.state.s.apertures[aperture]} skipping')

                # compose in the buttons if enabled

                # if the flag is set, override what the pattern wants with the information
                # we received over OSC. This is a very primitive form of pattern mixing.
                # We could also build a more arbitrary one.
                # also note that the button wants all the fire, so we have to also set the servo to 1.0

                if use_buttons and ((self.state.s.nozzle_buttons[solenoid]) or (self.state.s.nozzle_buttons_1[solenoid])):
                    # print(f' firing logical {i} physical {solenoid} because button')
                    s = True
                    a = 1.0
                else:
                    s = self.state.s.solenoids[solenoid]
                    a = self.state.s.apertures[aperture]

                packet[ARTNET_HEADER_SIZE + (i*2) ] = s

                packet[ARTNET_HEADER_SIZE + (i*2) + 1] = math.floor(self.nozzle_apply_calibration( aperture, a ) )

            # transmit
            if self.debug:
                print(f' sending packet to {c["ip"]} for {c["name"]}')
                print_bytearray(packet)

            self.sock.sendto(packet, (c['ip'], ARTNET_PORT))

        self.sequence += 1


# background 

# see comment about state, it is a cross process shared object.
# this function is a separate process

def transmitter_server(state: LightCurveState, terminate: Event):

    xmit = LightCurveTransmitter(state)

    delay = 1.0 / state.args.fps
    # print(f'delay is {delay} fps is {xmit.fps}')
    try:
        while not terminate.is_set():
            t1 = time()

            xmit.transmit()

            # a bit of a hack to put it here, should have its own thread or process, sorry so lazy
            state.nozzle_button_timeout_check()

            d = delay - (time() - t1)
            if (d > 0.002):
                sleep(d)

    except KeyboardInterrupt:
        pass

    print(f'transmit server: turning off gas')
    state.fill_apertures(0.0)
    state.fill_solenoids(0)
    xmit.transmit()
    sleep(0.1)

def transmitter_server_init(state: LightCurveState):
    global TRANSMITTER_PROCESS, XMIT_TERMINATE_EVENT

    print('transmitter server init')
    XMIT_TERMINATE_EVENT = Event()
    TRANSMITTER_PROCESS = Process(target=transmitter_server, args=(state, XMIT_TERMINATE_EVENT) )
    TRANSMITTER_PROCESS.start()

def transmitter_server_shutdown():
    # print(f'shutdown transmitter')
    global TRANSMITTER_PROCESS, XMIT_TERMINATE_EVENT

    XMIT_TERMINATE_EVENT.set()
    TRANSMITTER_PROCESS.join()


#
# This transmitter class sends broadcast packets with status
# it allows controllers to find Flamatik, and allows them to display
# any number of status things.
#
# Had a big question about what protocol is best for this kind of thing.
# OSC seems a little weird, JSON seems that way too. May switch.
#
# The status here is in 'abstract nozzels' not physical nozzels,
# so we don't need as much information about the config files
#
# Like the other classes here, this will run in its own process and
# read from the shared memory in the LightCurveState
#


class LightCurveStatusXmit:

    def __init__(self, state: LightCurveState) -> None:

        print('initialize light curve status transmitter')

        self.state = state
        self.sequence = 0
        # override this if you want just the transmitter debugging
        self.debug = state.debug

        self.port = STATUS_PORT

        # since we want uptime, store the start time (close enough)
        self.start_time = time()
        self.sequence = 0

        # create outbound socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # find a good address to send to
        # more robust code would consider checking this every so often and sending to a different
        # address, or, at least, catching errors sent to this address and looking for a new value?
        if state.args.broadcast != "":
            self.address = state.args.broadcast
        else:
            bs = get_broadcast_addresses()
            if len(bs) == 1:
                self.address = bs[0]
            elif len(bs) == 0:
                print(f' attempting to find a broadcast address but none configured none available')
                self.address = ""
            elif len(bs) > 1:
                print(f'warning! more than one broadcast address! {bs}')
                self.address = bs[0]
        print(f' StatusXmit on address {self.address}')


    # call each time
    def transmit(self) -> None:

        print(f'status transmit') if self.debug else None

        # build a data structure that has the info we'er interesting in
        # it would be good to round all the floats to save data

        data = {
            "device": "lightcurve",
            "version": "1.0",
            "command_port": int(COMMAND_PORT),
            "uptime": round(time() - self.start_time,3), # don't take up too much bandwidth
            "solenoids": self.state.s.solenoids[:], # take a copy for transmission
            "apertures": [round(item,3) for item in self.state.s.apertures[:]],
            "gyro": [round(item,3) for item in self.state.s.gyro[:]],
            "rotation": [round(item,3) for item in self.state.s.rotation[:]],
            "gravity": [round(item,3) for item in self.state.s.gravity[:]],
            "seq": self.sequence # allows estimation of packet loss
        }
        self.sequence += 1

        # bad form. Should abstract out this instead of replicating it.
        if not self.state.args.nobuttons:
            for n in range(self.state.args.nozzles):
                if ((self.state.s.nozzle_buttons[n]) or (self.state.s.nozzle_buttons_1[n])):
                    data['solenoids'][n] = True


        # the separators command greatly decreases the size by removing unnecessary spaces
        # slightly better code would also round the values in floating point to only 2 figures,
        # this is done with a custom encoder, you can look it up TODO
        json_data = json.dumps(data, separators=(',',':'))

        byte_data = json_data.encode('ascii')

        # todo: add the correct outbound address, which has to be looked up
        # and thus be on the right interface broadcast
        self.sock.sendto(byte_data,(self.address,self.port))



# background 

# see comment about state, it is a cross process shared object.
# this function is a separate process

def status_xmit_server(state: LightCurveState):

    xmit = LightCurveStatusXmit(state)

    # delay = 1.0 / state.args.fps
    delay = 1.0 / 5.0 # hardcode FPS to 5 to avoid network thrash
    # print(f'delay is {delay} fps is {xmit.fps}')
    try:
        while True:
            t1 = time()

            xmit.transmit()

            d = delay - (time() - t1)
            if (d > 0.002):
                sleep(d)

    except KeyboardInterrupt:
        pass


def status_xmit_server_init(state: LightCurveState):

    print('status xmit server init')
    process = Process(target=status_xmit_server, args=(state,) )
    # going to use Daemon because we don't need a clean shutdown, we're just sending status
    process.daemon = True
    process.start()



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

BROADCAST_BLACKLIST = [ '172.26.47.255', '127.255.255.255']

def get_broadcast_addresses():
    interfaces = netifaces.interfaces()
    interface_broadcasts = []

    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            ipv4_info = addresses[netifaces.AF_INET][0]
            broadcast_address = ipv4_info.get('broadcast')
            if broadcast_address and broadcast_address not in BROADCAST_BLACKLIST:
                interface_broadcasts.append(broadcast_address)

    # print(f'broadcast addresses are: {interface_broadcasts}')
    return interface_broadcasts

# handler has the address then a tuple of the arguments then the self argument of the receiver
# Not yet sure how to get the timestamp out of the bundle
# Bundle receiption hasn't worked

# note: copying into the shared variables must be done by value not by reference.
# thus the use of a loop here. DO NOT REPLACE WITH AN ARRAY COPY. See the statement
# about multiprocess memory use in the shared object section

# generic handler good for debugging
def osc_handler_all (address: str, fixed_args: List[Any], *vals):
    state = fixed_args[0]
    print(f' osc handler ALL received address {address} len {len(address)}; positional arguments: {vals}')

# specific handlers good for efficiency
def osc_handler_gyro(address: str, fixed_args: List[Any], *vals):
    print(f' osc: gyro {vals}') if state.debug else None
    state = fixed_args[0]
    if len(vals) != 3:
        return
    state.s.gyro[:] = vals
 
def osc_handler_rotation(address: str, fixed_args: List[Any], *vals):
    print(f' osc: rotation {vals}') if state.debug else None
    state = fixed_args[0]
    if len(vals) != 3:
        return
    state.s.rotation[:] = vals

def osc_handler_gravity(address: str, fixed_args: List[Any], *vals):
    print(f' osc: gravity {vals}') if state.debug else None
    state = fixed_args[0]
    if len(vals) != 3:
        return
    state.s.gravity[:] = vals

# imu order
# miliseconds int
# rotation, gravity, gyro

def osc_handler_imu(address: str, fixed_args: List[Any], *vals):
    # print(f'handler received IMU: time {vals[0]} rot {vals[1:4]}, grav {vals[4:7]}, gyro {vals[7:10]} ') if state.debug else None
    if len(vals) != 10:
        print(f'IMU: wrong number parameters should be 10 is: {len(vals) }')
        return
    state = fixed_args[0]
    state.s.rotation[:] = vals[1:4]
    # Need to shuffle the gravity vector around based on the way it's oriented on the sculpture
    g = vals[4:7]
    state.s.gravity[:] = [g[0], -g[1], -g[2]]
    state.s.gyro[:] = vals[7:10]
    #print(f'OSC IMU: rot {vals[1]:.4f}, {vals[2]:.4f}, {vals[3]:.4f}, grav {vals[4]:.4f}, {vals[5]:.4f}, {vals[6]:.4f} gyro {vals[7]:.4f}, {vals[8]:.4f}, {vals[9]:.4f}  ') if state.debug else None
    #print(f'OSC IMU: rot {vals[1]:.4f}, {vals[2]:.4f}, {vals[3]:.4f}, grav {vals[4]:.4f}, {vals[5]:.4f}, {vals[6]:.4f} gyro {vals[7]:.4f}, {vals[8]:.4f}, {vals[9]:.4f}  ') 


def osc_handler_nozzles(address: str, fixed_args: List[Any], *vals):
    state = fixed_args[0]
    print(f' osc: nozzles {vals}') if state.debug else None 
    if len(vals) != len(state.s.nozzle_buttons):
        print(f'Nozzle Buttons: expected {len(state.s.nozzle_buttons)} found len {len(vals)} ignoring')
        return
    state.s.nozzle_buttons_last_recv = time()
    state.s.nozzle_buttons[:] = vals

# used to capture a second state diagram of buttons

def osc_handler_nozzles_1(address: str, fixed_args: List[Any], *vals):
    state = fixed_args[0]
    print(f' osc: nozzles 1 {vals}') if state.debug else None 
    if len(vals) != len(state.s.nozzle_buttons):
        print(f'Nozzle Buttons 1: expected {len(state.s.nozzle_buttons)} found len {len(vals)} ignoring')
        return
    state.s.nozzle_buttons_1_last_recv = time()
    state.s.nozzle_buttons_1[:] = vals


#this has never worked
def osc_handler_bundle(address: str, fixed_args: List[Any], *vals):
    state = fixed_args[0]
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
# it takes anything it receives and places it in the shared state object
# for other processes to read

def osc_server(state: LightCurveState, address: str):

    dispatcher = Dispatcher()

    # setting up a catch-all can be good for debugging
    # dispatcher.map('*', osc_handler_all, state)

    # setting individual methods for each, slightly more efficient - but won't get timestamp bundles -
    # so disabling if we're using bundles
    dispatcher.map('/LC/gyro', osc_handler_gyro, state)
    dispatcher.map('/LC/rotation', osc_handler_rotation, state)
    dispatcher.map('/LC/gravity', osc_handler_gravity, state)

    dispatcher.map('/LC/imu', osc_handler_imu, state)

    dispatcher.map('/LC/nozzles', osc_handler_nozzles, state)
    dispatcher.map('/LC/nozzles/1', osc_handler_nozzles_1, state)
    dispatcher.set_default_handler(osc_handler_all, state)

    server = BlockingOSCUDPServer((address, OSC_PORT), dispatcher)

    try:
        server.serve_forever()  # Blocks forever

    except KeyboardInterrupt: # swallow silently
        pass

def osc_server_init(state: LightCurveState, args):
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


    OSC_PROCESS = Process(target=osc_server, args=(state, args.address) )
    OSC_PROCESS.daemon = True
    OSC_PROCESS.start()


#
# Command listener - HTTP
# There are commands we wish to receive over reliable HTTP instead of continually broadcast over UDP
# with OSC, like changing a pattern. This HTTP listener allows that.
#
# I'm just tossing in some HTTP and JSON. There are too many options, so I'm going
# with the endpoint 'flamatik', and all the rest of the data in the json.

class CommandHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, state: LightCurveState):
        print(f'CommandHTTPServer: server address {server_address}')
        super().__init__(server_address, RequestHandlerClass)
        self.lc_state = state

class CommandHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # print(f' post receved from {self.path} ')
        parsed_url = urlparse(self.path)
        # print(f' received post to path {parsed_url.path}')
        if parsed_url.path != '/flamatik':
            print(f' recevied command for incorrect endpoint')
            self.send_error(400, "wrong path")
            return

        content_length = int(self.headers['Content-length'])
        post_data = self.rfile.read(content_length)

        status = 400 # bad request

        try:
            data = json.loads(post_data.decode('utf-8'))
            print(f' received json command at {self.path} :: {data}')

            self.server.lc_state.command_queue.put(data)
            status = 200

            # would be nice to return a status but then that would be synchronous.
            # could probably have a validate....

            # build a response put it in json_response
            #json_response = ""
            #json_bytes = json.dumps(json_response).encode('utf-8')
            #response = ( f"HTTP/1.1 {status} OK\r\n"
            #            "Content-type: application/json\r\n"
            #            f'Content-length: {len(json_bytes)}\r\n\r\n'
            #            ).encode('utf-8') + json_bytes

            response = ( f"HTTP/1.1 {status} OK\r\n"
                        "Content-type: application/json\r\n"
                        f'Content-length: 0\r\n\r\n'
                    ).encode('utf-8')


            self.wfile.write(response)

        except json.JSONDecodeError:
            print('Data is not JSON')
            self.send_error(400, "bad content object") # bad request
            return

    def do_GET(self):
        print(f' received get URI {self.path} which we dont support')
        # parsed_url = urlparse(self.path)

        status = 404
        response = ( f"HTTP/1.1 {status} OK\r\n\r\n").encode('ascii') + json_bytes

        self.wfile.write(response)


def command_server(port:int, state: LightCurveState):
    print(f'command server process: port {port}')
    try:
        httpd = CommandHTTPServer(('', port), CommandHandler, state)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print(f' command server terminating')

def command_server_init(port: int, state: LightCurveState):
    print(f'command server init: port {port}')
    command_process = Process(target=command_server, args=(port,state))
    command_process.daemon = True
    command_process.start()


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

PATTERN_PARAMETERS = [ "nozzle", "delay", "group" ]

# object 
def pattern_execute(pattern_o: Dict, state) -> Process:

    # print(f'pattern execute: {pattern_o}')

    pattern_name = pattern_o['name']
    if pattern_name not in PATTERN_FUNCTIONS:
        return None 

    # overwrite the values in args with pattern properties
    # later todo: change all patterns to look at the pattern_object
    for param in PATTERN_PARAMETERS:
        if param in pattern_o:
            # print(f'Found {param} replacing with {pattern_o[param]}')
            setattr(state.args, param, pattern_o[param])
        else:
            setattr(state.args, param, None)

    pattern_process = Process(target=PATTERN_FUNCTIONS[pattern_name], args=(state,) )
    return pattern_process


def pattern_insert(pattern_name: str, pattern_fn):
    PATTERN_FUNCTIONS[pattern_name] = pattern_fn



def pattern_multipattern(state: LightCurveState):

    print(f'Starting multipattern pattern')

    for _ in range(state.args.repeat):
        for name, fn in PATTERN_FUNCTIONS.items():
            if name != 'multipattern':
                if fn(state): # check if pattern returns false for error, if so return error too
                    return False

    print(f'Ending multipattern pattern')


# format of a JSON file which describes a playlist:
# [ 
#   { "name": "nameofpattern",
#       "duration": 40,
#       "nozzel": n
#       "delay" : delay
#       "group" : group
#    },
#    ...
#    ]

# these will be copied to the pattern if they exist
# return the playlist of the default
def flamatik_playlist_reset(args):

    playlist = None

    if args.list != "":

        print(' execute: have a playlist file load it')

        # load config file
        with open(args.list) as playlist_f:
            playlist = json.load(playlist_f)  # XXX catch exceptions here.

        # validate file
        for idx, p in enumerate(playlist):
            if 'name' not in p:
                print(f'playlist: entry {idx} has no name, exiting ')
                return None
            if p["name"] not in PATTERN_FUNCTIONS:
                print(f'playlist: entry {idx} name {p["name"]} is not a valid pattern name, exiting')
                return None
            if 'duration' not in p:
                print(f'playlist: entry {idx} name {p["name"]} has no duration, exiting ')
                return None

    # if the args list wasn't null
    else:
        # cons a playlist out of the current arguments
        print(f' a pattern on the command line make a single item playlist')
        p = {
            'name': args.pattern,
            'repeat': args.repeat,
        }
        # TODO: this is wrong after the first time, but we'll fix this when
        # we stop the hack of using args to pass parameters to functions
        for param in PATTERN_PARAMETERS:
            if hasattr(args,param): # note: since args is a namespace, you can't use in
                # print(f'Found {param} in args copying to default execution {getattr(args,param)}')
                p[param] = getattr(args,param)
            else:
                # print(f' setting {param} to none')
                p[param] = None
        # print(f' cons up playlist: full with arguments {p}')
        playlist = (p,)

    return playlist




# now there's an execute list. It could start out with
# a pattern, or a playlist, but it listens on the command queue and switches patterns
# if requested
# create a dict with 'name' for the pattern, duration, and other parameters, it will be executed

def flamatik_execute(args, state: LightCurveState):

    playlist = ()
    playlist_index = 0
    pattern_process = None

    print('flamatik execute')

    playlist = flamatik_playlist_reset(args)

    # execute whichever is p next
    while True:

        # if the pattern has terminated, clean the variable to allow the next to execute
        if pattern_process is not None and pattern_process.is_alive() is False:
            pattern_process = None

        # launch a new pattern if we're not running one
        if pattern_process is None:

            p = playlist[playlist_index % len(playlist)]
            playlist_index += 1

            print(f' command: starting pattern {p["name"]}')
            if p["name"] not in PATTERN_FUNCTIONS:
                # todo: find a better thing to do than this
                print(" ERROR received pattern that does not exist")
                continue

            pattern_process = pattern_execute(p, state)
            pattern_start = time()
            if 'duration' in p:
                pattern_end = time() + p["duration"]
            else:
                pattern_end = 0.0

            pattern_process.start()

        # check the command queue, do something if we can
        try:
            msg = state.command_queue.get_nowait()
            print(f' receieved command in execute: {msg}')
            cmd = msg['command']
            if cmd == 'setPattern':
                print(f' set pattern received, changing pattern to {msg["name"]}')

                # check that pattern exists

                # replace the playlist with this
                playlist = (msg,)

                # terminate what is running
                if pattern_process.is_alive():
                    pattern_process.terminate()
                    pattern_process.join()
                    pattern_process = None
                    pattern_end = 0.0

            elif cmd == 'resetPattern':

                print(f' reset pattern received, resetting to original pattern or playlist')

                playlist = flamatik_playlist_reset(args)

                # terminate what is running
                if pattern_process.is_alive():
                    pattern_process.terminate()
                    pattern_process.join()
                    pattern_process = None
                    pattern_end = 0.0

        except queue.Empty:
            pass

        # check the duration, kill if out of time
        if pattern_end > 0.0 and pattern_end < time():
            print(f' Ending pattern {p["name"]} end was {pattern_end}')
            pattern_process.terminate()
            pattern_process.join()
            pattern_process = None 
            pattern_end = 0.0

        sleep(0.01)

#
#

def args_init():
    parser = argparse.ArgumentParser(prog='flamatik', description='Send ArtNet packets to the Light Curve')
    parser.add_argument('--config','-c', type=str, default="lightcurve.cnf", help='Fire Art Controller configuration file')

    parser.add_argument('--pattern', '-p', default="pulse", type=str, help=f'pattern one of: {patterns()}')
    parser.add_argument('--address', '-a', default="0.0.0.0", type=str, help=f'address to listen OSC on defaults to broadcast on non-loop')
    parser.add_argument('--broadcast', '-b', default="", type=str, help='use a specific broadcast address to send status')
    parser.add_argument('--fps', '-f', default=15, type=int, help='frames per second')
    parser.add_argument('--repeat', '-r', default=9999, type=int, help="number of times to run pattern")
    parser.add_argument('--nobuttons',  action='store_true', help="add this if you want to disable the button function")
    parser.add_argument('--debug', action='store_true', help=" turn on the very verbose debugging all the things")

    parser.add_argument('--list', '-l', default="", type=str, help="List: file of patterns to play (overrides pattern)")

    # some patterns use optional arguments, but they can also share.
    parser.add_argument('--nozzle', '-n', type=int, help="pattern specific: nozzel to apply to")
    parser.add_argument('--delay', '-d', type=float, help="pattern specific: delay between items")
    parser.add_argument('--group', '-g', type=int, help="pattern specific: size of group in pattern")

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

    import_patterns()
    pattern_insert('multipattern', pattern_multipattern)

    args = args_init()
    global debug
    debug = args.debug

    if (args.list == "") and (args.pattern not in PATTERN_FUNCTIONS):
        print(f' pattern must be one of {patterns()}')
        return

    with Manager() as manager:

        try:
            state = LightCurveState(args, manager)
        except Exception as e:
            print(f' Config file problem, exiting: {str(e)} ')
            return

        # creates a transmitter background process that reads from the shared state
        # and sends to controllers (unicast)
        transmitter_server_init(state)

        # create a status transmitter which broadcasts over the local network
        # some interesting information
        status_xmit_server_init(state)

        # creates a osc server receiver process which fills the shared state
        osc_server_init(state, args)

        # creates an HTTP listener which can receive JSON or OSC commands like change pattern
        command_server_init(COMMAND_PORT, state)

        try:
            flamatik_execute(args,state)

        except KeyboardInterrupt: # be silent in this case
            pass

        finally:
            print(f' in all cases, try to shutdown the transmitter safely')
            transmitter_server_shutdown()
            sleep(0.5)


# only effects when we're being run as a module but whatever
if __name__ == '__main__':
    main()
