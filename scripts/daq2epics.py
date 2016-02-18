#!/usr/bin/env python2.7
#
# $Id$
#
# OVERVIEW
#
#   This script receives DAQ status information via UDP and exports this
#   information as read-only EPICS PVs.
#
# USAGE
#
#   $ ./daq2epics.py -h
#   usage: daq2epics.py [-h] [-n NSTATIONS] [-v] {AMO,SXR,XPP,XCS,CXI,MEC,MFX}
#
#   export DAQ info to EPICS
#
#   positional arguments:
#     {AMO,SXR,XPP,XCS,CXI,MEC,MFX}
#
#   optional arguments:
#     -h, --help            show this help message and exit
#     -n NSTATIONS          number of stations (default=1)
#     -v, --verbose         be verbose
#
# ENVIRONMENT
#
#   Before running this script the environment must be set up properly.
#
#     Using bash:
#         $ source setup_daq2epics.bash
#

import sys

# Python 2.7 or greater is required
assert sys.version_info >= (2,7)

from pcaspy import SimpleServer, Driver
import time
from datetime import datetime
import thread
import subprocess
import argparse
import socket
import json
import pdb

# parse_rpc - translate string to JSON-RPC 2.0 notification
def parse_rpc(data):
    parsed_json = None
    try:
        parsed_json = json.loads(data)
    except ValueError:
        raise
    else:
        if myDriver.verbose:
            print 'json:', parsed_json
    if type(parsed_json) is not dict:
        print 'Error: message is not a dict'
        raise ValueError
    if (not parsed_json.has_key("params")):
        print 'Error: message is missing \'params\''
        raise ValueError
    if type(parsed_json["params"]) is not dict:
        print 'Error: \'params\' is not a dict'
        raise ValueError
    if (not parsed_json.has_key("method")):
        print 'Error: message is missing \'method\''
        raise ValueError
    if (not type(parsed_json["method"]) in [str, unicode]):
        print 'Error: method is not a string'
        raise ValueError
    if (not parsed_json.has_key("jsonrpc")):
        print 'Error: message is missing \'jsonrpc\''
        raise ValueError
    if parsed_json["jsonrpc"] != "2.0":
        print 'Error: jsonrpc is not \'2.0\''
        raise ValueError
    return parsed_json

class myDriver(Driver):

    verbose = False
    maxInput = 1024
    timeout = 3.0
    shutdownFlag = False
    instChoices= ['AMO', 'SXR', 'XPP','XCS', 'CXI', 'MEC', 'MFX']
    statusport = 29990
    statushost = socket.gethostname()

    def __init__(self, instr, nstations):
        super(myDriver, self).__init__()
        # start thread for receiving UDP datagrams
        self.tid = thread.start_new_thread(self.recvUdp,(myDriver.statushost,myDriver.statusport))
        self.instr = instr
        self.nstations = nstations

    # These PVs are read-only
    def write(self, reason, value):
        status = False
        return status

    def act(self, request):
        method = request["method"]
        try:
            # station parameter is optional
            station = int(request["params"]["station"])
        except:
            # default station
            station = 0
        if myDriver.verbose:
            print ' *** act: method="%s" station=%d ***' % (method, station)
        if station < 0 or station >= self.nstations:
            print 'Error: station %d out of range' % station
            return

        # only include station number in PV name if there are multiple stations
        if self.nstations > 1:
            stationstr = str(self.nstations)
        else:
            stationstr = ''

        try:
            if request["params"]["running"] == 1:
                self.setParam(stationstr+':RUNNING',       1)
                self.setParam(stationstr+':CONFIGURED',    1)
            else:
                self.setParam(stationstr+':RUNNING',       0)
                self.setParam(stationstr+':RUN_NUMBER',    0)
                self.setParam(stationstr+':RUN_DURATION',  0)
                self.setParam(stationstr+':RUN_MBYTES',    0)
                self.setParam(stationstr+':EVENT_COUNT',   0)
                self.setParam(stationstr+':DAMAGE_COUNT',  0)

            if method == "update_1":
                self.setParam(stationstr+':RUN_NUMBER',    request["params"]["run_number"])
                self.setParam(stationstr+':RUN_DURATION',  request["params"]["run_duration"])
                self.setParam(stationstr+':RUN_MBYTES',    request["params"]["run_mbytes"])
                self.setParam(stationstr+':EVENT_COUNT',   request["params"]["event_count"])
                self.setParam(stationstr+':DAMAGE_COUNT',  request["params"]["damage_count"])
                self.setParam(stationstr+':CONTROL_STATE', str(request["params"]["control_state"]).ljust(40))
            elif method == "update_2":
                self.setParam(stationstr+':CONFIG_TYPE',   str(request["params"]["config_type"]).ljust(40))
                self.setParam(stationstr+':CONTROL_STATE', str(request["params"]["control_state"]).ljust(40))
                self.setParam(stationstr+':CONFIGURED',    request["params"]["configured"])
                self.setParam(stationstr+':RECORDING',     request["params"]["recording"])
            elif method == "timeout":
                self.setParam(stationstr+':CONFIG_TYPE',   str('NOCONNECT').ljust(40))
                self.setParam(stationstr+':CONTROL_STATE', str('NOCONNECT').ljust(40))
                self.setParam(stationstr+':CONFIGURED',    0)
                self.setParam(stationstr+':RECORDING',     0)
        except:
            print 'Error: "%s" method' % method
            print 'request[\"params\"] = ', request["params"]
            raise
        else:
            # inform clients about PV value change
            self.updatePVs()
        return

    def recvUdp(self, host, port):
        if myDriver.verbose:
            print 'recvUdp: host=%s port=%s' % (host, port)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # set timeout
        s.settimeout(myDriver.timeout)

        # accept UDP datagrams from any sender
        s.bind(("", port))

        while not myDriver.shutdownFlag:

            try:
                data, addr = s.recvfrom(myDriver.maxInput)
            except socket.timeout:
                if myDriver.verbose:
                    print 'socket timeout'
                data = '{"jsonrpc": "2.0", "method": "timeout", "params": {"running" : 0}}'

            parsed_rpc = None
            if myDriver.verbose:
                print "recvUdp: received msg '%s'" % data.rstrip()
            try:
                parsed_rpc = parse_rpc(data)
            except ValueError:
                print 'recvUdp: ValueError\n--------\n%s\n--------' % data.rstrip()
            else:
                if myDriver.verbose:
                    print 'jsonrpc:', parsed_rpc
                # act on the request
                self.act(parsed_rpc)

        return

if __name__ == '__main__':
    global pvdb
    pvdb = {}     # start with empty dictionary

    parser = argparse.ArgumentParser(description='export DAQ info to EPICS')

    parser.add_argument('instrument', choices=myDriver.instChoices)
    parser.add_argument('-n', type=int, default=1, help='number of stations (default=1)', metavar='NSTATIONS')
    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')

    args = parser.parse_args()
    myDriver.verbose = args.verbose

    for station in range(args.n):

        # only include station number in PV name if there are multiple stations
        if args.n > 1:
            stationstr = str(station)
        else:
            stationstr = ''

        # PVs updated by RPC methods
        pvdb[stationstr+':RUNNING'      ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':RUN_NUMBER'   ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':RUN_DURATION' ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':RUN_MBYTES'   ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':EVENT_COUNT'  ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':DAMAGE_COUNT' ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':CONFIG_TYPE'  ] = {'type' : 'string'}
        pvdb[stationstr+':CONTROL_STATE'] = {'type' : 'string'}
        pvdb[stationstr+':CONFIGURED'   ] = {'type' : 'int', 'value': 0}
        pvdb[stationstr+':RECORDING'    ] = {'type' : 'int', 'value': 0}

    instrument = args.instrument
    prefix = 'DAQ:' + instrument

    print '=========== Serving %d PVs ==============' % len(pvdb)
    for key in sorted(pvdb):
        print prefix+key
    print '========================================='

    server = SimpleServer()

    server.createPV(prefix, pvdb)
    driver = myDriver(instrument, args.n)

    try:
        # process CA transactions
        while not myDriver.shutdownFlag:
            server.process(0.1)
    except KeyboardInterrupt:
        print '\nInterrupted'

    # let other threads exit
    myDriver.shutdownFlag = True
    time.sleep(1)

    if myDriver.verbose:
        print '%s done.' % sys.argv[0]
