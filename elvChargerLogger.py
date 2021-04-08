#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2020 Conrad Sachweh

"""NAME
        %(prog)s - <description>

SYNOPSIS
        %(prog)s [--help]

DESCRIPTION
        none

FILES
        none

SEE ALSO
        nothing

DIAGNOSTICS
        none

BUGS
        none

AUTHOR
        Conrad Sachweh, conrad@csachweh.de
"""
import logging
from itertools import zip_longest
import datetime
from time import sleep

#--------- Classes, Functions, etc ---------------------------------------------
def init_serial_port(port):
    import serial
    import io
    # got from decompiled original exe: 19200, data 8, parity None, stop bits 1, no flow control
    ser = serial.Serial(port, 19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1, xonxoff=False)
    # actually the newline format is \n\r, but this is not a standard python io accepts...
    ser_io = io.TextIOWrapper(io.BufferedRWPair(ser, ser, 1),  
                              newline = '\r',
                              line_buffering = True)
    ser_io.readline() # get first invalid data    
    return ser_io

def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def __print_line(data, header):
    for k in range(len(data)):
        print(f'{data[k]:{len(header[k])+1}}', end='')
    print()

def pretty_print(data):
    header = ["Slot", "Program", "Status", "Voltage", "Current", "ukn", "ukn", "Charged-Capacity", "Discharged-Capacity", "Energy", "unk"]
    sub_header = ["", "", "", "(mV)", "(mA)", "", "", "(mAh)", "(mAh)", "(mW)", ""]

    # known stati: C:Charging, P:Pause, T:Top-Off
    print(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'))
    for k in range(11):
        print(f'{header[k]:{len(header[k])+1}}', end='')
    print()
    for k in range(11):
        print(f'{sub_header[k]:^{len(header[k])+1}}', end='')
    print()
    for entry in grouper(data, 11):
        __print_line(entry, header)

#-------------------------------------------------------------------------------
#    Main
#-------------------------------------------------------------------------------
if __name__=="__main__":
    import sys
    import argparse

    # Command line option parsing example
    parser = argparse.ArgumentParser()
    # Note that -h (--help) is added by default and uses the help strings of
    # the other options. The variables containing the options are automatically
    # created.

    # Boolean option (default is !action)
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                        help="don't print status messages to stdout")
    # Option
    parser.add_argument('-l', dest='logfile',action='store',
                        metavar='LOGFILE',help='Log file')

    parser.add_argument('-n', '--interval', action='store', type=int, default=5,
                        help='Interval to write out data')

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='show more verbose output')

    parser.add_argument('port', nargs=1, help='port to connect to, e.g. /dev/ttyUSB0')

    args = parser.parse_args()
    # set logging information
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    if args.verbose > 0:
        logging.getLogger().setLevel(logging.INFO)
    if args.verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)

    ser = init_serial_port(args.port[0])
    lastread = datetime.datetime(1970,1,1)
    while True:
        data = ser.readline()
        logging.debug("Raw: {}".format(data))
        decode = data.split(';')
        if len(decode) == 45:
            decode.pop(-1) # remove eol \n\r from list

            if lastread + datetime.timedelta(0, args.interval) < datetime.datetime.now():
                pretty_print(decode)
                lastread = datetime.datetime.now()
        else:
            # invalid data
            logging.error(f"Received invalid data: {data}")
            pass
