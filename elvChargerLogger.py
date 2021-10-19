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

header = ["Slot", "Program", "Status", "Voltage", "Current", "Capacity", "Energy", "Charged-Capacity", "Discharged-Capacity", "EnergyContent", "statusRunTime"]
# known stati: C:Charging, P:Pause, T:Top-Off
sub_header = ["", "", "", "(mV)", "(mA)", "", "", "(mAh)", "(mAh)", "(mW)", "(min?)"]

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

def load_config(fn):
    import yaml
    try:
        with open(fn, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error("Could not find config file, ignoring")
        return {}

def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def __print_line(data, header):
    for k in range(len(data)):
        print(f'{data[k]:{len(header[k])+1}}', end='')
    print()

def pretty_print(data, timestamp=datetime.datetime.utcnow()):
    print(timestamp.strftime('%y-%m-%d %H:%M:%S%z'))
    for k in range(11):
        print(f'{header[k]:{len(header[k])+1}}', end='')
    print()
    for k in range(11):
        print(f'{sub_header[k]:^{len(header[k])+1}}', end='')
    print()
    for entry in grouper(data, 11):
        __print_line(entry, header)

class InfluxMeasurement(dict):
    def __init__(self, measurement, timestamp, tags, fields=None):
        super(InfluxMeasurement, self).__init__()
        self["measurement"] = measurement
        self["time"] = timestamp.strftime('%Y-%m-%dT%H:%M:%S%z')
        self["tags"] = tags
        if not fields:  # default value {} would be shared for all new instances of this class https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
            self["fields"] = {}
        else:
            self["fields"] = fields
    def add_field(self, key, value):
        if not self["fields"].get(key):
            self["fields"][key] = value
        else:
            logging.error("Field {} already {}, not overwriting with {}".format(key, self["fields"][key], value))

def init_influxdb(influx_config):
    from influxdb import InfluxDBClient
    client = InfluxDBClient(host=influx_config["host"], port=influx_config["port"],
                            ssl=influx_config["ssl"], verify_ssl=influx_config["verify_ssl"],
                            username=influx_config["username"], password=influx_config["password"],
                            database=influx_config["database"])
    return client

def send_to_influxdb(client, data, header, timestamp=datetime.datetime.utcnow()):
    from copy import deepcopy
    points = []
    for entry in grouper(decode, len(header)):
        measurement = InfluxMeasurement("alc1800pc", timestamp, {"slot": entry[0]})
        for k in range(1, 11):
            if not entry[k]:
                continue
            try:
                measurement.add_field(header[k], int(entry[k]))
            except:
                measurement.add_field(header[k], entry[k])
        logging.info("Write: {0}".format(measurement))
        points.append(deepcopy(measurement))
    try:
        client.write_points(points)
    except:
       logging.error("Could not send points to influxdb, no network?")

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

    parser.add_argument('-c', '--config', action='store', default='config.yml',
                        help='Load config file')

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

    config = load_config(args.config)

    ser = init_serial_port(args.port[0])
    lastread = datetime.datetime(1970,1,1)

    influx_active = False
    if config.get("influxdb"):
        influx_active = True
        influx_client = init_influxdb(config.get("influxdb"))

    while True:
        data = ser.readline()
        logging.debug("Raw: {}".format(data))
        decode = data.split(';')
        if len(decode) == 45:
            decode.pop(-1) # remove eol \n\r from list
            now = datetime.datetime.utcnow()
            if lastread + datetime.timedelta(0, args.interval) < now:
                pretty_print(decode, now)
                if influx_active:
                    send_to_influxdb(influx_client, decode, header, now)

                if args.logfile:
                    with open(args.logfile, "a") as f:
                        import time
                        f.write("{};".format(time.time()))
                        f.write(";".join(decode))
                        f.write("\n")
                lastread = datetime.datetime.utcnow()
        else:
            # invalid data
            logging.error(f"Received invalid data: {data}")
            pass
