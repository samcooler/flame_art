#!/usr/bin/env python3

# Author: Brian Bulkowski brian@bulkowski.org
#
# Read and write to the Novation Launchpad Mini Mk2
# annoyingly, this is "raw" and basically works only 
# with the Mini Mk2 because all these devices are subtly
# different. The only platform code I can find supports the Mk3 not the Mk2
#
# The code directly uses rtmidi, which is probably the most compatible
# way of interacting with this thing anyway
#
# 


from time import sleep, time
import argparse
from typing import Tuple
from threading import Thread, Event, Lock
from abc import ABC, abstractmethod
import math
import logging

import rtmidi

from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse, oscchannel, oscmethod as osm

import netifaces

import os
import sys


LAUNCHPAD_STR1 = 'Launchpad Mini'
LAUNCHPAD_STR2 = 'Novation USB'

#
# type = 'mode', 'pad', 'function' (mode is along the top, function is the side)
# action = 'up' 'down'
# row, column is integer 0 to 8
# for 'mode' (along the top) column is which row is 0, for 'function' row is filled, column is 0
class ButtonEvent():
    def __init__(self, type: str, action: str, row: int = 0, column: int = 0 ):
        if type not in ['mode', 'pad', 'function']:
            raise ValueError(f'Cant create ButtonEvent with bad type {type}')
        if action not in ['up', 'down']:
            raise ValueError(f'Cant create ButtonEvent with bad action {action} ')
        if row < 0 or row >= 8:
            raise ValueError(f'Cant create ButtonEvent bad row value {row}')
        if column < 0 or column >= 8:
            raise ValueError(f'')

        self.type = type
        self.action = action
        self.row = row
        self.column = column


# this is an abstract interface

class Mode(ABC):
    @abstractmethod
    # receive a button event
    def buttonEvent(self, be: ButtonEvent) -> None:
        pass

    @abstractmethod
    # draw the entire state of the launchpad
    def drawPad(self) -> None:
        pass

    def clear(self) -> None:
        pass

class LaunchpadMiniMk2():

    def __init__(self) -> None:

        # Initialize the MIDI output and input
        self.midi_out = rtmidi.MidiOut()
        self.midi_in = rtmidi.MidiIn()

        # Find the Launchpad Mini Mk2
        self.launchpad_in_port = None
        self.launchpad_out_port = None

        for i, port in enumerate(self.midi_in.get_ports()):
            if LAUNCHPAD_STR1 in port:
                self.launchpad_in_port = i
                break
            elif LAUNCHPAD_STR2 in port:
                self.launchpad_in_port = i
                break
            else:
                print(f'launchpad in is not {port} ')

        for i, port in enumerate(self.midi_out.get_ports()):
            if LAUNCHPAD_STR1 in port:
                self.launchpad_out_port = i
                break
            elif LAUNCHPAD_STR2 in port:
                self.launchpad_out_port = i
                break
            else:
                print(f'launchpad out is not {port}')

        self.colors = {
            "off": 0,
            "black": 0,
            "red": 15,
            "blue": 47,
            "teal": 33,
            "purple": 53,
            "yellow": 62
        }

        self.mode_setup()

        self.keymap_setup()

        self.mode = 0


    # mode handler: 'on' / 'off' , id [ 0 to 7 ]
    # function handler: 'on' / 'off' , id [ 0 to 7 ]
    # pad handler: 'on' / 'off' , row [0 to 7], column [0 to 7]

    def action_handlers( mode_handler, function_handler, pad_handler):
        self.mode_handler = mode_handler
        self.function_handler = function_handler
        self.pad_handler = pad_handler


    def keymap_setup(self):
        # construct a map of buttons
        # the keys are 0, to 7, along the top row,
        # but then 16 through 17 along the next row

        # these are the buttons along the top
        # (labled 1 to 8)
        self.mode_buttons = [-1] * 8;

        # these are the buttons along the side
        # (labled A to H)
        self.function_buttons = [-1] * 8;

        # 8 x 8 pads
        # let's put 0,0 in the upper left
        self.pads = [[-1] * 8 for _ in range(8)]


        noz = 0
        for row in range(0,8):
            for column in range(0,8):
                # print(f'nozzle {noz} is row {row} column {column} button {(row*16)+column}')
                if noz < 30:
                    self.pads[row][column] = noz
                else:
                    return
                noz += 1

    ## SET COLOR FUNCTION

    # row, column : 0,0 is upper left
    def button_color_set(self, type:str, row:int, column:int, color:int):
        if type == 'function':
            self.midi_out.send_message([144, (row * 16) + 8, color]) 

        elif type == 'pad':
            self.midi_out.send_message([144, (row * 16) + column, color]) 

        elif type == 'mode':
            self.midi_out.send_message([176,column + 104, color])

        else:
            raise AttributeError(" setting a color to an incorrect type")

    def buttons_clear(self):
        # there's actually not this number but its eaiser than getting the rows and columns correct
        print(f' clear leds ')
        off = self.colors['off']
        for r in range(8):
            for c in range(8):
                self.button_color_set('pad',r,c,off)
        for i in range(8):
            self.button_color_set('function',i,0,off)
            self.button_color_set('mode',0,i,off)


    def connect(self) -> bool:
        if self.launchpad_in_port is None or self.launchpad_out_port is None:
            print("Launchpad Mini Mk2 not found.")
            return False

        print(f'Found Launchpad mini at input port {self.launchpad_in_port} output {self.launchpad_out_port}')
        self.midi_out.open_port(self.launchpad_out_port)
        self.midi_in.open_port(self.launchpad_in_port)
        print(f"Connected to Launchpad")

        self.buttons_clear()

        self.mode_set(1)

        return True

    def disconnect(self):
        self.midi_out.close_port()
        self.midi_in.close_port()

    def mode_setup(self):
        # this is a dictionary comprehension
        self.mode_handlers = {i: None for i in range(8)}

    def mode_register(self, mode: Mode, index: int ):
        if index >= 8:
            raise AttributeError(f' mode register: index {index} out of range')
        self.mode_handlers[index] = mode

    # 0 index
    def mode_set(self, index: int):
        # clear the old button
        if self.mode >= 0:
            self.button_color_set('mode', 0, self.mode, self.colors['off'] )
            # call the clear function on the old handler if there was one
            if self.mode_handlers[self.mode] != None:
                self.mode_handlers[self.mode].clear()
        # set the new
        self.mode = index
        print(f' setting mode button {self.mode} color to red')
        self.button_color_set('mode', row=0, column=self.mode, color=self.colors['red'])

    # get the current mode object
    def mode_get(self) -> Mode:
        return self.mode_handlers[self.mode]



    # str is pad or function
    # if pad, x / y
    # if function, 0 to 7 (side buttons)
    # if error, 'unknown'

    def categorize_note(self, note: int, velocity: int) -> ButtonEvent :
        print(f' categorize note: {note} velocity {velocity}')
        action = 'up' if velocity == 0 else 'down'
        print(f' categorize note: action {action}')

        row = int(note / 16)
        column = note % 16
        t = 'pad'
        if column < 8:
            return ButtonEvent('pad',action,row,column)
        elif (column == 8):
            return ButtonEvent('function',action,row,0)
        else:
            raise AttributeError(f'note {note} unexpected in categorize note')


    # cc is always mode (top)
    # -1 is unknown
    # return is 0 for the first button (zero index)
    def categorize_cc(self, note: int, velocity: int) -> ButtonEvent:
        action = 'down' if velocity == 0 else 'up'
        print(f' categorize cc: {note}')
        if note >= 104 and note <= 111:
            print(f'cc : mode : button {note - 104}')
            return ButtonEvent('mode', action, 0, note-104)
        else:
            raise AttributeError(f' cc {note} unexpected in categorize cc')

    def read(self):
        while True:
            msg = self.midi_in.get_message()
            if msg:
                data, _ = msg
                status, note, velocity = data

                if status == 144:  # Note event

                    be = self.categorize_note(note, velocity)
                    print(f"Button type {be.type} row {be.row} column {be.column} (note {note},vel {velocity})")

                    # pass to the mode handler
                    mode = self.mode_get()
                    if mode:
                        mode.buttonEvent(be)
                    else:
                        print(f'no mode registered')

                # MODE BUTTONS - along top
                elif status == 176: # control change, which is the 
                    event = self.categorize_cc(note, velocity)
                    if event.type != 'mode':
                        return
                    if event.action == 'down' : # keypress
                        print(f"Mode Button {event.column} pressed")
                        self.mode_set(event.column)

                else:
                    print(f'unknown message: status {status} note {note} velocity {velocity}')

            sleep(0.01)

    def keystate_get():
        return self.key_state

#
# OSC Transmitter
#

OSC_PORT = 6511 # a random number. there is no OSC port because OSC is not a protocol

def get_broadcast_addresses():
    interfaces = netifaces.interfaces()
    interface_broadcasts = []

    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            ipv4_info = addresses[netifaces.AF_INET][0]
            broadcast_address = ipv4_info.get('broadcast')
            if broadcast_address:
                interface_broadcasts.append(broadcast_address)

    print(f'broadcast addresses are: {interface_broadcasts}')
    return interface_broadcasts

osc_lock = Lock()

NOZZLE_BUTTON_LEN = 30
CONTROL_BUTTON_LEN = 3

OSC_XMIT = None

class OSCTransmitter:

    def __init__(self, args) -> None:


        # array of values for the nozzle buttons
        self.nozzles = [False] * NOZZLE_BUTTON_LEN
        # array of values for program control buttons
        self.controls = [False] * CONTROL_BUTTON_LEN

        self.debug = args.debug
        self.sequence = 0
        self.repeat = args.repeat

        self.start = time()

        # init the osc system but only on thread because we don't have
        # much data
        osc_startup(execthreadscount=1)

        # this is what unicast looks like
        # osc_udp_client("192.168.0.4",  OSC_PORT, 'client')

        if args.address == "" :

            addresses = get_broadcast_addresses()
            # this is what broadcast looks like
            for a in addresses:
                # don't send on loopback?
                if a != '127.255.255.255':
                    args.address = a
                    break

        osc_broadcast_client(args.address,  OSC_PORT, 'client')
        print(f'sending broadcast on {args.address}')


    # call repeatedly from the thread to transmit 
    def transmit(self) -> None:

        print(f'transmit: nozzle is {self.nozzles}') if self.debug else None

        # represent button state most efficiently as types T and F
        # according to the internet, this isn't as slow as it looks, there's special case
        # prealloc code in string that makes it non terrible
        # also: it seems unnecessary to send both the type string and the value, but OSCMessage validates, so this is required.
        # send fails silently if you don't do this
        nozzles_str = ','
        for v in self.nozzles:
            if v:
                nozzles_str += 'T'
            else:
                nozzles_str += 'F'
        msg_nozzles = oscbuildparse.OSCMessage('/LC/nozzles', nozzles_str, self.nozzles)

        controls_str = ','
        for v in self.controls:
            if v:
                controls_str += 'T'
            else:
                controls_str += 'F'
        msg_controls = oscbuildparse.OSCMessage('/LC/controls', controls_str, self.controls)

        try:

            with osc_lock:

                osc_send(msg_nozzles, 'client')
                osc_process()
                osc_send(msg_controls, 'client')
                osc_process()

        except Exception as e:
            logging.exception("an exception occurred with the osc sender")


    def fill_nozzles(self, val):
        for i in range(len(self.nozzles)):
            self.nozzles[i] = val

    def fill_controls(self, val):
        for i in range(len(self.nozzles)):
            self.nozzles[i] = val


# background 

def xmit_thread(xmit):
    while True:
        xmit.transmit()
        osc_process()
        sleep(1.0 / 25.0)

def xmit_thread_init(xmit):
    global BACKGROUND_THREAD, xmit_event
    BACKGROUND_THREAD = Thread(target=xmit_thread, args=(xmit,) )
    BACKGROUND_THREAD.daemon = True
    BACKGROUND_THREAD.start()



#
# Modes
# Use the abstract base class to create an interface, create three different modes
#



class LatchMode(Mode):

    def __init__(self, lpm: LaunchpadMiniMk2, osc_xmit: OSCTransmitter):
        self.lpm = lpm

        self.osc_xmit = osc_xmit

        # -1 means uninit, 0 means off, 1 means on - for fire
        self.pad_states = [[-1] * 8 for _ in range(8)]


    def buttonEvent(self, be: ButtonEvent) -> None:
        print(f' Latch Mode received button event ')
        if be.type == 'pad' and be.action == 'down' :

            n = be.row * 8 + be.column
            if n >= NOZZLE_BUTTON_LEN:
                print(f' nozzle button {be.row} {be.column} but only {NOZZLE_BUTTON_LEN}, ignoring')
                return

            if (self.pad_states[be.row][be.column] <= 0):
                print(f' press pad {be.row} {be.column}')
                self.pad_states[be.row][be.column] = 1
                self.lpm.button_color_set('pad', be.row, be.column, self.lpm.colors['red']) # red
                self.osc_xmit.nozzles[n] = True

            # already on
            else:
                print(f' momentary second press pad {be.row}, {be.column}')
                self.pad_states[be.row][be.column] = 0
                self.lpm.button_color_set('pad', be.row, be.column, self.lpm.colors['off']) # black turn off
                self.osc_xmit.nozzles[n] = False


    def drawPad(self) -> None:
        return

    def clear(self) -> None:
        self.pad_states = [[-1] * 8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                self.lpm.button_color_set('pad', r, c, self.lpm.colors['off']) # black turn off
        for n in range(NOZZLE_BUTTON_LEN):
            self.osc_xmit.nozzles[n] = False
        return

class MomentaryMode(Mode):
    def __init__(self, lpm: LaunchpadMiniMk2, osc_xmit: OSCTransmitter):
        self.lpm = lpm

        self.osc_xmit = osc_xmit

    def buttonEvent(self, be: ButtonEvent) -> None:
        print(f' Momentary Mode received button event ')
        if be.type == 'pad' :

            n = be.row * 8 + be.column
            if n >= NOZZLE_BUTTON_LEN:
                print(f' nozzle button {be.row} {be.column} but only {NOZZLE_BUTTON_LEN}, ignoring')
                return

            if be.action == 'down':
                print(f'Momentary Mode: button down turnning off fire and clearing button')
                self.lpm.button_color_set('pad', be.row, be.column, self.lpm.colors['red']) # red
                self.osc_xmit.nozzles[n] = True

            elif be.action == 'up':
                print(f'Momentary Mode: button up turnning off fire and clearing button')
                self.lpm.button_color_set('pad', be.row, be.column, self.lpm.colors['off']) # off
                self.osc_xmit.nozzles[n] = False

            # already on
            else:
                print(f' momentary received unknonw action type {be.action} ignoring')

    def drawPad(self) -> None:
        return

    def clear(self) -> None:
        # this shouldn't be necessary because when you press to move modes you shouldn't have
        # a button down but it might happen
        for r in range(8):
            for c in range(8):
                self.lpm.button_color_set('pad', r, c, self.lpm.colors['off']) # black turn off
        for n in range(NOZZLE_BUTTON_LEN):
            self.osc_xmit.nozzles[n] = False
        return

class PatternMode(Mode):
    def __init__(self, lpm: LaunchpadMiniMk2):
        self.lpm = lpm

    def buttonEvent(self, be: ButtonEvent) -> None:
        print(f'Pattern Mode: button event {be}')

    def drawPad(self) -> None:
        return

    def clear(self) -> None:
        return


def mode_action(action: str, b: int):
    print(f' mode action {action} on button {b}, ignoring')


def function_action(action: str, b: int):
    print(f' function action {action} on button {b} ignoring')


def args_init():
    parser = argparse.ArgumentParser(prog='launchpad-flamatik', description='Send ArtNet packets to the Light Curve')

    parser.add_argument('--address', '-a', default="", type=str, help=f'address to listen OSC on defaults to broadcast on non-loop')
    parser.add_argument('--fps', '-f', default=15, type=int, help='frames per second')
    parser.add_argument('--repeat', '-r', default=9999, type=int, help="number of times to run pattern")
    parser.add_argument('--debug', '-d', default=False, type=bool, help="debug messages")

    args = parser.parse_args()

    return args


def main():


    args = args_init()

    # get the launchpad and init

    launchpad = LaunchpadMiniMk2()
    if not launchpad.connect():
        print(f'no launchpad connected')
        return

    # create an OSC transmitter
    osc_xmit = OSCTransmitter(args)

    xmit_thread_init(osc_xmit)

    # create the modes and register them
    launchpad.mode_register( LatchMode(launchpad, osc_xmit ), 0)
    launchpad.mode_register( MomentaryMode(launchpad, osc_xmit), 1)
    launchpad.mode_register( PatternMode(launchpad), 2)
    launchpad.mode_set(0)

    # read the launchpad repeatedly. 
    try:
        while True:
            launchpad.read()

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        launchpad.disconnect()

# run if we're executing from the command line
if __name__ == '__main__':
    main()
