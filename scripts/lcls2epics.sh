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

    parser = argparse.ArgumentParser(prog='daq2epics.sh', description='export DAQ info to EPICS')

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
    if (args.P).find(":") > 0:
        instrument, suffix = (args.P).split(':', 1)
        try:
            station = int(suffix)
        except:
            station = 0
        stationstr = str(station)
    else:
        instrument = args.P
        station = 0
        stationstr = ''

    # PVs
    pvdb[stationstr+':RUNNING'      ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':RUN_NUMBER'   ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':RUN_DURATION' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':RUN_MBYTES'   ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':CONFIG_TYPE'  ] = {'type' : 'string', 'value': '-'}
    pvdb[stationstr+':CONTROL_STATE'] = {'type' : 'string', 'value': '-'}
    pvdb[stationstr+':CONFIGURED'   ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':RECORDING'    ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':EXPNAME'      ] = {'type' : 'string', 'value': '-'}
    pvdb[stationstr+':EXPNUM'       ] = {'type' : 'float', 'value': 0}

    pvdb[stationstr+':XPM:L0InpRate'] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:L0AccRate'] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:L1Rate'   ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:NumL0Inp' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:NumL0Acc' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:NumL1'    ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:DeadFrac' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:DeadTime' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:DeadFLnk' ] = {'type' : 'float', 'count': 32, 'value': [-1.]*32 }

    pvdb[stationstr+':XPM:RxClks'     ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:TxClks'     ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:RxRsts'     ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:CrcErrs'    ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:RxDecErrs'  ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:RxDspErrs'  ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:BypassRsts' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:BypassDones'] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:RxLinkUp'   ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:FIDs'       ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:SOFs'       ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':XPM:EOFs'       ] = {'type' : 'float', 'value': 0}

    # @todo: Need to rethink the following when there are multiple DTIs

    pvdb[stationstr+':DTI:UsLinks'     ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:BpLinks'     ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:DsLinks'     ] = {'type' : 'float', 'value': 0}

    pvdb[stationstr+':DTI:UsRxErrs'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dUsRxErrs'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:UsRxFull'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dUsRxFull'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:UsIbRecv'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dUsIbRecv'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:UsIbEvt'     ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dUsIbEvt'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:UsObRecv'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dUsObRecv'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:UsObSent'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dUsObSent'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}

    pvdb[stationstr+':DTI:BpObSent'    ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:dBpObSent'   ] = {'type' : 'float', 'value': 0}

    pvdb[stationstr+':DTI:DsRxErrs'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dDsRxErrs'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:DsRxFull'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dDsRxFull'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:DsObSent'    ] = {'type' : 'float', 'count': 7, 'value': [0]*7}
    pvdb[stationstr+':DTI:dDsObSent'   ] = {'type' : 'float', 'count': 7, 'value': [0]*7}

    pvdb[stationstr+':DTI:QpllLock'    ] = {'type' : 'float', 'value': 0}

    pvdb[stationstr+':DTI:MonClkRate'  ] = {'type' : 'float', 'count': 4, 'value': [0]*4}
    pvdb[stationstr+':DTI:MonClkSlow'  ] = {'type' : 'float', 'count': 4, 'value': [0]*4}
    pvdb[stationstr+':DTI:MonClkFast'  ] = {'type' : 'float', 'count': 4, 'value': [0]*4}
    pvdb[stationstr+':DTI:MonClkLock'  ] = {'type' : 'float', 'count': 4, 'value': [0]*4}

    pvdb[stationstr+':DTI:UsLinkObL0'  ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:dUsLinkObL0' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:UsLinkObL1A' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:dUsLinkObL1A'] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:UsLinkObL1R' ] = {'type' : 'float', 'value': 0}
    pvdb[stationstr+':DTI:dUsLinkObL1R'] = {'type' : 'float', 'value': 0}

    pvdb[stationstr+':DTI:RxFrmErrs'   ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:dRxFrmErrs'  ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:RxFrms'      ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:dRxFrms'     ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:RxOpcodes'   ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:dRxOpcodes'  ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:TxFrmErrs'   ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:dTxFrmErrs'  ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:TxFrms'      ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:dTxFrms'     ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:TxOpcodes'   ] = {'type' : 'float', 'count': 2, 'value': [0]*2}
    pvdb[stationstr+':DTI:dTxOpcodes'  ] = {'type' : 'float', 'count': 2, 'value': [0]*2}

    prefix = 'DAQ:' + instrument

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
