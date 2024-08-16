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


class LaunchpadMiniMk2():

    def __init__(self, mode_handler, function_handler, pad_handler) -> None:

        # Initialize the MIDI output and input
        self.midi_out = rtmidi.MidiOut()
        self.midi_in = rtmidi.MidiIn()

        # Find the Launchpad Mini Mk2
        self.launchpad_in_port = None
        self.launchpad_out_port = None

        self.mode_handler = mode_handler
        self.function_handler = function_handler 
        self.pad_handler = pad_handler

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
            "red": 15,
            "blue": 47,
            "teal": 33,
            "purple": 53,
            "yellow": 62
        }



        self.setup_keymap()

    # mode handler: 'on' / 'off' , id [ 0 to 7 ]
    # function handler: 'on' / 'off' , id [ 0 to 7 ]
    # pad handler: 'on' / 'off' , row [0 to 7], column [0 to 7]

    def action_handlers( mode_handler, function_handler, pad_handler):
        self.mode_handler = mode_handler
        self.function_handler = function_handler
        self.pad_handler = pad_handler


    def setup_keymap(self):
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

        self.pad_states = [[-1] * 8 for _ in range(8)]

        noz = 0
        for row in range(0,8):
            for column in range(0,8):
                # print(f'nozzle {noz} is row {row} column {column} button {(row*16)+column}')
                if noz < 30:
                    self.pads[row][column] = noz
                else:
                    return
                noz += 1


    def clear_leds(self):
        # there's actually not this number but its eaiser than getting the rows and columns correct
        for note in range(0,121):
            self.midi_out.send_message([144, note, 0])  # off

        for cc in range(104,112):
            self.midi_out.send_message([176, note, 0])  # off

    def connect(self) -> bool:
        if self.launchpad_in_port is None or self.launchpad_out_port is None:
            print("Launchpad Mini Mk2 not found.")
            return False
        else:
            print(f'Found Launchpad mini at input port {self.launchpad_in_port} output {self.launchpad_out_port}')
            self.midi_out.open_port(self.launchpad_out_port)
            self.midi_in.open_port(self.launchpad_in_port)
            print(f"Connected to Launchpad")
            return True

    def disconnect(self):
        self.midi_out.close_port()
        self.midi_in.close_port()

    # str is pad or function
    # if pad, x / y
    # if function, 0 to 7 (side buttons)
    # if error, 'unknown'

    def categorize_note(self, note: int) -> Tuple[str, int, int] :
        # print(f' categorize note: id {id}')
        row = int(note / 16)
        column = note % 16
        t = 'pad'
        if (column == 8):
            t = 'function'
        elif (column == 9):
            t = 'unknown'
        if row > 7:
            t = 'unknown'
        # print(f' caegorized as: type {t} row {row} column {column}')
        return( t, row, column )


    # cc is always mode (top)
    # -1 is unknown
    def categorize_cc(self, note: int) -> Tuple[str, int]:
        print(f' categorize cc: {note}')
        if note >= 104 and note <= 111:
            print(f'cc : mode : button {note - 104}')
            return( 'mode', note - 104)
        return('unknown', -1)


    def read(self):
        while True:
            msg = self.midi_in.get_message()
            if msg:
                data, _ = msg
                status, note, velocity = data

                if status == 144:  # Note on

                    t, row, column = self.categorize_note(note)
                    # print(f"Button type {t} row {row} column {column} (note {note},vel {velocity})")

                    # first 4 rows of pads will be latching, rest will be momentary
                    latching = False
                    if row < 4:
                        latching = True

                    if velocity > 0:

                        if t != 'pad':
                            print(f' non-pad button ignored ')
                            return

                        if latching:

                            if (self.pad_states[row][column] == 1):
                                print(f' release pad {row}, {column}')
                                self.pad_states[row][column] = 0
                                self.midi_out.send_message([status, note, 0]) # black
                                self.pad_handler('up', row, column)
                            else:
                                print(f' press pad {row} {column}')
                                self.pad_states[row][column] = 1
                                self.midi_out.send_message([status, note, 15]) # red
                                self.pad_handler('down', row, column)

                        else:

                            self.pad_states[row][column] = 1
                            self.midi_out.send_message([status, note, 60]) # green
                            self.pad_handler('down', row, column)

                    else:
                        # latching buttons ignore note:up
                        if latching == False:
                            self.pad_states[row][column] = 0
                            self.midi_out.send_message([status, note, 0]) # off
                            self.pad_handler('up', row, column)

                elif status == 176: # control change, which is the 
                    self.categorize_cc(note)
                    if velocity > 0: # keypress
                        print(f"Button {note} pressed (velocity {velocity})")
                        # Turn on the corresponding LED
                        # Red = 0, green = 63, blue = 0, with values from 0 to 63 for brightes
                        self.midi_out.send_message([status, note, 60])  # Green light
                    else:
                        print(f"Button {note} released")
                        # Turn off the corresponding LED
                        self.midi_out.send_message([status, note, 0])

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
# 

# action is:
# down, up 
#

def pad_action(action: str, row: int, column: int ):
    # print(f' pad action {action} on row {row} column {column}')
    global OSC_XMIT

    # convert row and column to nozzle number
    n = row * 8 + column
    if n >= NOZZLE_BUTTON_LEN:
        print(f' nozzle button {row} {column} but only {NOZZLE_BUTTON_LEN}, ignoring')
        return

    if action == 'down':
        print(f' FIRE NOZZLE {n}')
        OSC_XMIT.nozzles[n] = True
    else:
        print(f' UNFIRE NOZZLE {n}')
        OSC_XMIT.nozzles[n] = False


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

    global OSC_XMIT

    args = args_init()

    # get the launchpad and init

    launchpad = LaunchpadMiniMk2(mode_action, function_action, pad_action)
    if not launchpad.connect():
        print(f'no launchpad connected')
        return

    launchpad.clear_leds()

    # create an OSC transmitter
    OSC_XMIT = OSCTransmitter(args)

    xmit_thread_init(OSC_XMIT)

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
