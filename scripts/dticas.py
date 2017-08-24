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

# yaml metadata
numUsLinks = 7

streamSet = { 'Us', 'Ds' }

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

    parser = argparse.ArgumentParser(prog=sys.argv[0], description='host PVs for DTI')

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

    for i in range (numUsLinks):
      pvdb[stationstr+':DTI:UsLinkEn'        +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkTagEn'     +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkL1En'      +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkPartition' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkTrigDelay' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkFwdMask'   +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkFwdMode'   +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkDataSrc'   +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsLinkDataType'  +'%d'%i] = {'type' : 'int'}

    pvdb[stationstr+':DTI:ModuleInit'     ] = {'type' : 'int'}

    pvdb[stationstr+':DTI:CountClear'     ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:CountUpdate'    ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:UsLinkUp'       ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:BpLinkUp'       ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:DsLinkUp'       ] = {'type' : 'int'}

    for i in range (numUsLinks):
      pvdb[stationstr+':DTI:UsRxErrs'    +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsRemLinkID' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsRxFull'    +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsIbRecv'    +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsIbDump'    +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsIbEvt'     +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsAppObRecv' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:UsAppObSent' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:DsRxErrs'    +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:DsRemLinkID' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:DsRxFull'    +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:DsObSent'    +'%d'%i] = {'type' : 'int'}

    pvdb[stationstr+':DTI:QpllLock'       ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:BpTxInterval'   ] = {'type' : 'int'}

    pvdb[stationstr+':DTI:MonClkRate'     ] = {'type' : 'int', 'count' : 4}
    pvdb[stationstr+':DTI:MonClkSlow'     ] = {'type' : 'int', 'count' : 4}
    pvdb[stationstr+':DTI:MonClkFast'     ] = {'type' : 'int', 'count' : 4}
    pvdb[stationstr+':DTI:MonClkLock'     ] = {'type' : 'int', 'count' : 4}

    pvdb[stationstr+':DTI:UsLinkObL0'     ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:UsLinkObL1A'    ] = {'type' : 'int'}
    pvdb[stationstr+':DTI:UsLinkObL1R'    ] = {'type' : 'int'}

    for stream in streamSet:
      pvdb[stationstr+':DTI:'+stream+':CountReset'    ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':ResetRx'       ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':Flush'         ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':Loopback'      ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxLocData'     ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxLocDataEn'   ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':AutoStatSendEn'] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':FlowControlDis'] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxPhyRdy'      ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxPhyRdy'      ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':LocLinkRdy'    ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RemLinkRdy'    ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxRdy'         ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxPolarity'    ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RemPauseStat'  ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':LocPauseStat'  ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RemOflowStat'  ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':LocOflowStat'  ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RemData'       ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':CellErrs'      ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':LinkDowns'     ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':LinkErrs'      ] = {'type' : 'int'}
      for i in range (4):
        pvdb[stationstr+':DTI:'+stream+':RemOflowVC' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxFrameErrs'   ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxFrames'      ] = {'type' : 'int'}
      for i in range (4):
        pvdb[stationstr+':DTI:'+stream+':LocOflowVC' +'%d'%i] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxFrameErrs'   ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxFrames'      ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxClockFreq'   ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxClockFreq'   ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxLastOpCode'  ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxLastOpCode'  ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':RxOpCodes'     ] = {'type' : 'int'}
      pvdb[stationstr+':DTI:'+stream+':TxOpCodes'     ] = {'type' : 'int'}

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
