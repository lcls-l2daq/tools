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

NPartitions = 8

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

    parser = argparse.ArgumentParser(prog=sys.argv[0], description='host PVs for XPM')

    parser.add_argument('-P', required=True, help='DAQ:LAB2', metavar='PREFIX')
    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')

    args = parser.parse_args()
    myDriver.verbose = args.verbose

    stationstr = 'PART'
    prefix = args.P+':'

    # PVs

    for i in range(NPartitions):
        pvdb[stationstr+':%d:L0Select'           %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L0Select_FixedRate' %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L0Select_ACRate'    %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L0Select_ACTimeslot'%i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L0Select_Sequence'  %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L0Select_SeqBit'    %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:DstSelect'          %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:DstSelect_Mask'     %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L0Delay'            %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:ResetL0'            %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:Run'                %i] = {'type' : 'int'}

        pvdb[stationstr+':%d:L1TrgClear'   %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L1TrgEnable'  %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L1TrgSource'  %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L1TrgWord'    %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:L1TrgWrite'   %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:AnaTagReset'  %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:AnaTag'       %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:AnaTagPush'   %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:AnaTagWrite'  %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:PipelineDepth'%i] = {'type' : 'int'}
        pvdb[stationstr+':%d:MsgHeader'    %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:MsgInsert'    %i] = {'type' : 'int'}
        pvdb[stationstr+':%d:MsgPayload'   %i] = {'type' : 'int'}
        for j in range(4):
            pvdb[stationstr+':%d:InhInterval%d'  %(i,j)] = {'type' : 'int', 'value': 1}
            pvdb[stationstr+':%d:InhLimit%d'     %(i,j)] = {'type' : 'int', 'value': 1}
            pvdb[stationstr+':%d:InhEnable%d'    %(i,j)] = {'type' : 'int', 'value': 0}

        pvdb[stationstr+':%d:RunTime'  %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:L0InpRate'%i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:L0AccRate'%i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:L1Rate'   %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:NumL0Inp' %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:NumL0Acc' %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:NumL1'    %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:DeadFrac' %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:DeadTime' %i] = {'type' : 'float', 'value': 0}
        pvdb[stationstr+':%d:DeadFLnk' %i] = {'type' : 'float', 'count': 32, 'value': [-1.]*32 }

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
