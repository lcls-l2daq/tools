#!/bin/bash

# usage: daq2epics.sh [-h] [-U PORT] [-v] PARTITION
#
# export DAQ info to EPICS
#
# positional arguments:
#   PARTITION      e.g. SXR or CXI:0 or CXI:1
#
# optional arguments:
#   -h, --help     show this help message and exit
#   -U PORT        UDP port (default 29990)
#   -v, --verbose  be verbose

# OS Requirement: RHEL6 or RHEL7
# Python Requirement: version 2.7

###################################################################################
# Set up environment in bash
###################################################################################

RELEASE_FILE="/etc/redhat-release"

if grep --quiet 'release 6' $RELEASE_FILE; then
  # RHEL6
  export PATH=/reg/common/package/python/2.7.5/x86_64-rhel6-gcc44-opt/bin:$PATH
  export PYTHONPATH=/reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel6-gcc44-opt/lib/python2.7/site-packages
elif grep --quiet 'release 7' $RELEASE_FILE; then
  # RHEL7
  export PATH=/reg/common/package/python/2.7.5/x86_64-rhel7-gcc48-opt/bin:$PATH
  export PYTHONPATH=/reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel7-gcc48-opt/lib/python2.7/site-packages
else
  echo "This OS release is not supported"
  /usr/bin/head $RELEASE_FILE
  exit 1
fi

source /reg/g/pcds/setup/epicsenv-3.14.12.sh
export EPICS_CAS_INTF_ADDR_LIST=$(/bin/hostname -i)

###################################################################################
# Start python from a here document
###################################################################################

python2.7 - << EOF "$@"

import sys

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
    statushost = socket.gethostname()
    currentexpcmd = '/reg/g/pcds/dist/pds/current/build/pdsapp/bin/x86_64-linux-opt/currentexp'

    def __init__(self, instr, station, stationstr, statusport):
        super(myDriver, self).__init__()
        # start thread for receiving UDP datagrams
        self.tid1 = thread.start_new_thread(self.recvUdp,(myDriver.statushost,statusport))
        # start thread for polling current experiment
        self.tid2 = thread.start_new_thread(self.pollExp,(0,))
        self.instr = instr
        self.station = station
        self.stationstr = stationstr

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

        if station != self.station:
            print ' *** act: station error (recd %d, expected %d) ***' % (station, self.station)

        try:
            if method == "update_1" or method == "update_2" or method == "timeout":
                if request["params"]["running"] == 1:
                    self.setParam(self.stationstr+':RUNNING',       1)
                    self.setParam(self.stationstr+':CONFIGURED',    1)
                else:
                    self.setParam(self.stationstr+':RUNNING',       0)
                    self.setParam(self.stationstr+':RUN_NUMBER',    0)
                    self.setParam(self.stationstr+':RUN_DURATION',  0)
                    self.setParam(self.stationstr+':RUN_MBYTES',    0)
                    self.setParam(self.stationstr+':EVENT_COUNT',   0)
                    self.setParam(self.stationstr+':DAMAGE_COUNT',  0)

            if method == "update_1":
                try:
                    self.setParam(self.stationstr+':RUN_NUMBER',    request["params"]["run_number"])
                    self.setParam(self.stationstr+':RUN_DURATION',  request["params"]["run_duration"])
                    self.setParam(self.stationstr+':RUN_MBYTES',    request["params"]["run_mbytes"])
                    self.setParam(self.stationstr+':EVENT_COUNT',   request["params"]["event_count"])
                    self.setParam(self.stationstr+':DAMAGE_COUNT',  request["params"]["damage_count"])
                    self.setParam(self.stationstr+':CONTROL_STATE', str(request["params"]["control_state"]).ljust(40))
                    if request["params"].has_key("config_type"):
                        self.setParam(self.stationstr+':CONFIG_TYPE',   str(request["params"]["config_type"]).ljust(40))
                    if request["params"].has_key("recording"):
                        self.setParam(self.stationstr+':RECORDING',     request["params"]["recording"])
                except KeyError as badkey:
                    print 'KeyError: update_1: badkey =', badkey

            elif method == "update_2":
                try:
                    self.setParam(self.stationstr+':CONFIG_TYPE',   str(request["params"]["config_type"]).ljust(40))
                    self.setParam(self.stationstr+':CONTROL_STATE', str(request["params"]["control_state"]).ljust(40))
                    self.setParam(self.stationstr+':CONFIGURED',    request["params"]["configured"])
                    self.setParam(self.stationstr+':RECORDING',     request["params"]["recording"])
                except KeyError as badkey:
                    print 'KeyError: update_2: badkey =', badkey

            elif method == "timeout":
                self.setParam(self.stationstr+':CONFIG_TYPE',   str('NOCONNECT').ljust(40))
                self.setParam(self.stationstr+':CONTROL_STATE', str('NOCONNECT').ljust(40))
                self.setParam(self.stationstr+':CONFIGURED',    0)
                self.setParam(self.stationstr+':RECORDING',     0)

            elif method == "expnum":
                try:
                    self.setParam(self.stationstr+':EXPNUM',        request["params"]["expnum"])
                    self.setParam(self.stationstr+':EXPNAME',       str(request["params"]["expname"]).ljust(40))
                except KeyError as badkey:
                    print 'KeyError: expnum: badkey =', badkey
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

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # set timeout
            s.settimeout(myDriver.timeout)

            # accept UDP datagrams from any sender
            s.bind(("", port))
        except socket.error as msg:
            print 'Socket error: UDP port %d: %s' % (port, msg)
            myDriver.shutdownFlag = True
            return

        while not myDriver.shutdownFlag:

            try:
                data, addr = s.recvfrom(myDriver.maxInput)
            except socket.timeout:
                if myDriver.verbose:
                    print 'socket timeout'
                data = '{"jsonrpc": "2.0", "method": "timeout", "params": {"running" : 0, "station" : %d}}' % self.station

            parsed_rpc = None
            if myDriver.verbose:
                print "recvUdp: received msg '%s'" % data.rstrip()
            try:
                parsed_rpc = parse_rpc(data)
            except ValueError:
                print 'recvUdp: ValueError\n--------\n%s\n--------' % data.rstrip()
            else:
                if myDriver.verbose:
                    print 'jsonrpc:'
                    print json.dumps(parsed_rpc, sort_keys=True, indent=4)
                # act on the request
                self.act(parsed_rpc)

        return

    def currentexp(self, instrument):

        # defaults
        expname = 'None'
        expnum = 0

        returncode = 1
        try:
            proc = subprocess.Popen([myDriver.currentexpcmd, instrument], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
        except OSError, m:
            print 'Subprocess error:', m.strerror
            myDriver.shutdownFlag = True
        else:
            returncode = proc.returncode
            result = proc.stdout.read().rstrip().split()
            if (proc.returncode == 0):
                try:
                    expname = result[1]
                    expnum = int(result[2])
                except:
                    print 'Error: failed to parse', result
            else:
                print 'Error:', proc.stderr.read().rstrip()

        return returncode, expname, expnum

    def pollExp(self, ignore):
        pollCount = -1
        if myDriver.verbose:
            print 'pollExp: self.instr = %s  self.station = %d' % (self.instr, self.station)

        while not myDriver.shutdownFlag:

            time.sleep(0.5)
            pollCount += 1

            # loop every 0.5 sec to check shutdownFlag.
            # only do real work once per minute (120 * 0.5 sec).
            if pollCount % 120 != 0:
                continue

            ret, expname, expnum = self.currentexp(self.instr + ':' + str(self.station))

            if ret == 0:
                if myDriver.verbose:
                    print 'pollExp: expname = %s, expnum = %d' % (expname, expnum)
            else:
                print 'Error: currentexp() returned %d' % ret
                myDriver.shutdownFlag = True
                continue

            data = '{"jsonrpc": "2.0", "method": "expnum", "params": {"expnum" : %d, "expname" : \"%s\", "station" : %d}}' % (expnum, expname, self.station)

            parsed_rpc = None

            try:
                parsed_rpc = parse_rpc(data)
            except ValueError:
                print 'pollExp: ValueError\n--------\n%s\n--------' % data.rstrip()
            else:
                if myDriver.verbose:
                    print 'jsonrpc:', parsed_rpc
                # act on the request
                self.act(parsed_rpc)

        return

def printDb():
    global pvdb
    global prefix

    print '=========== Serving %d PVs ==============' % len(pvdb)
    for key in sorted(pvdb):
        print prefix+key
    print '========================================='
    return

if __name__ == '__main__':
    global pvdb
    pvdb = {}     # start with empty dictionary
    global prefix
    prefix = ''

    parser = argparse.ArgumentParser(prog='daq2epics.sh', description='export DAQ info to EPICS')

    parser.add_argument('PARTITION', help='e.g. SXR or CXI:0 or CXI:1')
    parser.add_argument('-U', type=int, help='UDP port (default 29990)', default=29990, metavar='PORT')
    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')

    args = parser.parse_args()
    myDriver.verbose = args.verbose

    #
    # Parse the PARTITION argument for the instrument name and station #. 
    # If the partition name includes a colon, PV names will include station # even if 0.
    # If no colon is present, station # defaults to 0 and is not included in PV names.
    # Partition names 'AMO' and 'AMO:0' thus lead to different PV names.
    #
    if (args.PARTITION).find(":") > 0:
        instrument, suffix = (args.PARTITION).split(':', 1)
        try:
            station = int(suffix)
        except:
            station = 0
        stationstr = str(station)
    else:
        instrument = args.PARTITION
        station = 0
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
    pvdb[stationstr+':EXPNAME'      ] = {'type' : 'string'}
    pvdb[stationstr+':EXPNUM'       ] = {'type' : 'int', 'value': 0}

    prefix = 'DAQ:' + instrument

    # printDb(pvdb, prefix)
    printDb()

    server = SimpleServer()

    server.createPV(prefix, pvdb)
    driver = myDriver(instrument, station, stationstr, args.U)

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

EOF
