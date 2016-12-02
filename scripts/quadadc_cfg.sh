#!/bin/bash

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
#import socket
#import json
import pdb

class myDriver(Driver):
    def __init__(self):
        super(myDriver, self).__init__()


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

    parser = argparse.ArgumentParser(prog='quadadc_cfg.sh', description='import DAQ info from EPICS')

    parser.add_argument('-P', required=True, help='e.g. SXR or CXI:0 or CXI:1', metavar='PARTITION')
    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')

    args = parser.parse_args()
    myDriver.verbose = args.verbose

    #
    # Parse the PARTITION argument for the instrument name and station #. 
    # If the partition name includes a colon, PV names will include station # even if 0.
    # If no colon is present, station # defaults to 0 and is not included in PV names.
    # Partition names 'AMO' and 'AMO:0' thus lead to different PV names.
    #
    prefix = args.P

    # PVs
    pvdb[':CHAN_MASK'   ] = {'type' : 'float', 'value': 15}
    pvdb[':SAMP_RATE'   ] = {'type' : 'float', 'value': 1.25e9}
    pvdb[':NSAMPLES'    ] = {'type' : 'float', 'value': 320}
    pvdb[':DELAY_NS'    ] = {'type' : 'float', 'value': 0}
    pvdb[':EVT_CODE'    ] = {'type' : 'float', 'value': 9}

    # printDb(pvdb, prefix)
    printDb()

    server = SimpleServer()

    server.createPV(prefix, pvdb)
    driver = myDriver()

    try:
        # process CA transactions
        while True:
            server.process(0.1)
    except KeyboardInterrupt:
        print '\nInterrupted'

EOF
