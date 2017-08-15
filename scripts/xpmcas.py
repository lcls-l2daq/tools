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

NDsLinks    = 7
NAmcs       = 2
NPartitions = 16

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
    pvdb[stationstr+':XPM:ModuleInit'         ] = {'type' : 'int'}
    for i in range(NAmcs):
        pvdb[stationstr+':XPM:DumpPll' + '%d'%i] = {'type' : 'int'}

    pvdb[stationstr+':XPM:ClearLinks'         ] = {'type' : 'int'}

    pvdb[stationstr+':XPM:LinkDebug'          ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:Inhibit'            ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:TagStream'          ] = {'type' : 'int'}

    for i in range(NAmcs * NDsLinks):
        pvdb[stationstr+':XPM:LinkTxDelay'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:LinkPartition'+'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:LinkTrgSrc'   +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:LinkLoopback' +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:TxLinkReset'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:RxLinkReset'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:LinkEnable'   +'%d'%i] = {'type' : 'int'}

    for i in range(NAmcs):
        pvdb[stationstr+':XPM:PLL_BW_Select' +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_FreqTable' +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_FreqSelect'+'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_Rate'      +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_PhaseInc'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_PhaseDec'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_Bypass'    +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_Reset'     +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PLL_Skew'      +'%d'%i] = {'type' : 'int'}

    pvdb[stationstr+':XPM:L0Select'           ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:L0Select_FixedRate' ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:L0Select_ACRate'    ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:L0Select_ACTimeslot'] = {'type' : 'int'}
    pvdb[stationstr+':XPM:L0Select_Sequence'  ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:L0Select_SeqBit'    ] = {'type' : 'int'}
    pvdb[stationstr+':XPM:SetL0Enabled'       ] = {'type' : 'int'}

    for i in range(NPartitions):
        pvdb[stationstr+':XPM:L1TrgClear'   +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:L1TrgEnable'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:L1TrgSource'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:L1TrgWord'    +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:L1TrgWrite'   +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:AnaTagReset'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:AnaTag'       +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:AnaTagPush'   +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:AnaTagWrite'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:PipelineDepth'+'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:MsgHeader'    +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:MsgInsert'    +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:MsgPayload'   +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:InhInterval'  +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:InhLimit'     +'%d'%i] = {'type' : 'int'}
        pvdb[stationstr+':XPM:InhEnable'    +'%d'%i] = {'type' : 'int'}

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
