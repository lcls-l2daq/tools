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
#     -n NSTATIONS          number of stations
#     -v, --verbose         be verbose
#
# ENVIRONMENT
#
#   Before running this script the following steps are required for EPICS and
#   Python 2.7 support.
#
#   1. Add /reg/common/package/python/2.7.3/x86_64-rhel5-gcc41-opt/bin (or equivalent)
#      to $PATH.
#
#   2. Add /reg/common/package/epics-base/3.14.12.3/x86_64-rhel5-gcc41-opt/lib and
#      /reg/common/package/epicsca/3.14.9/lib/x86_64-linux-opt (or equivalent)
#      to $LD_LIBRARY_PATH.
#
#   3. Add /reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel5-gcc41-opt/lib/python2.7/site-packages
#      (or equivalent) to $PYTHONPATH.
#
#   4. Set EPICS_CAS_INTF_ADDR_LIST to the IP address of the host's CDS interface.
#


from pcaspy import SimpleServer, Driver
import time
from datetime import datetime
import thread
import sys
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
        try:
            if request["params"]["running"] == 1:
                self.setParam(str(station)+':RUNNING',       1)
                self.setParam(str(station)+':CONFIGURED',    1)
            else:
                self.setParam(str(station)+':RUNNING',       0)
                self.setParam(str(station)+':RUN_NUMBER',    0)
                self.setParam(str(station)+':RUN_DURATION',  0)
                self.setParam(str(station)+':RUN_SIZE',      0)
                self.setParam(str(station)+':EVENT_COUNT',   0)
                self.setParam(str(station)+':DAMAGE_COUNT',  0)

            if method == "update_1":
                self.setParam(str(station)+':RUN_NUMBER',    request["params"]["run_number"])
                self.setParam(str(station)+':RUN_DURATION',  request["params"]["run_duration"])
                self.setParam(str(station)+':RUN_MBYTES',    request["params"]["run_mbytes"])
                self.setParam(str(station)+':EVENT_COUNT',   request["params"]["event_count"])
                self.setParam(str(station)+':DAMAGE_COUNT',  request["params"]["damage_count"])
                self.setParam(str(station)+':CONTROL_STATE', str(request["params"]["control_state"]).ljust(40))
            elif method == "update_2":
                self.setParam(str(station)+':CONFIG_TYPE',   str(request["params"]["config_type"]).ljust(40))
                self.setParam(str(station)+':CONTROL_STATE', str(request["params"]["control_state"]).ljust(40))
                self.setParam(str(station)+':CONFIGURED',    request["params"]["configured"])
                self.setParam(str(station)+':RECORDING',     request["params"]["recording"])
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
        # accept UDP datagrams from any sender
        s.bind(("", port))

        while not myDriver.shutdownFlag:
            data, addr = s.recvfrom(myDriver.maxInput)
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
    parser.add_argument('-n', type=int, default=1, help='number of stations', metavar='NSTATIONS')
    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')

    args = parser.parse_args()
    myDriver.verbose = args.verbose

    for station in range(args.n):
        # PVs updated by RPC methods
        pvdb['%d:RUNNING'       % station] = {'type' : 'int', 'value': 0}
        # ...if RUNNING=1, set CONFIGURED
        # ...if RUNNING=0, clear RUN_NUMBER, RUN_DURATION, RUN_SIZE, EVENT_COUNT, DAMAGE_COUNT
        pvdb['%d:RUN_NUMBER'    % station] = {'type' : 'int', 'value': 0}
        pvdb['%d:RUN_DURATION'  % station] = {'type' : 'int', 'value': 0}
        pvdb['%d:RUN_SIZE'      % station] = {'type' : 'int', 'value': 0}
        pvdb['%d:EVENT_COUNT'   % station] = {'type' : 'int', 'value': 0}
        pvdb['%d:DAMAGE_COUNT'  % station] = {'type' : 'int', 'value': 0}
        pvdb['%d:CONFIG_TYPE'   % station] = {'type' : 'string'}
        pvdb['%d:CONTROL_STATE' % station] = {'type' : 'string'}
        pvdb['%d:CONFIGURED'    % station] = {'type' : 'int', 'value': 0}
        pvdb['%d:RECORDING'     % station] = {'type' : 'int', 'value': 0}

    if myDriver.verbose:
        print 'pvdb:', pvdb

    instrument = args.instrument
    prefix = 'DAQ:' + instrument

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
