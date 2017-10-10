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


def printDb(prefix):
    global pvdb

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

    parser = argparse.ArgumentParser(prog=sys.argv[0], description='host PVs for TPR')

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

    # PVs
#    pvdb[prefix+':ACCSEL'    ] = {'type' : 'int', 'value': 0}
#    pvdb[prefix+':FRAMERATE' ] = {'type' : 'float', 'value': 0}

    prefix = ':SRC'
    pvdb[prefix+':LOCK'  ] = {'type' : 'int', 'value': 0}

    for i in range(14):
        prefix = ':CH%u'%(i)
        pvdb[prefix+':LOCK'  ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':PD'    ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':DPDPS' ] = {'type' : 'float', 'value': 0}
        pvdb[prefix+':DPDPSA'] = {'type' : 'float', 'value': 0}
        pvdb[prefix+':DPD'   ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':TXD'   ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':DTXDPS'] = {'type' : 'float', 'value': 0}
        pvdb[prefix+':DTXD'  ] = {'type' : 'int'  , 'value': 0}
        prefix = ':CH%u:SCAN'%(i)
        pvdb[prefix+':STAGE'  ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':TXD'    ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':PD'     ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':TXDPS'  ] = {'type' : 'float', 'value': 0}
        pvdb[prefix+':PDPS'   ] = {'type' : 'float', 'value': 0}
        pvdb[prefix+':CLK'    ] = {'type' : 'int'  , 'value': 0}
        pvdb[prefix+':DCLK'   ] = {'type' : 'int'  , 'value': 0}

    printDb(args.P)

    server = SimpleServer()

    server.createPV(args.P, pvdb)
        
    driver = myDriver()

    try:
        # process CA transactions
        while True:
            server.process(0.1)
    except KeyboardInterrupt:
        print '\nInterrupted'
