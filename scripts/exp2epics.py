#!/usr/bin/env python2.7
#
# $Id$
#
# OVERVIEW
#
#   This script periodically polls the PDS database and exports the current
#   experiment names (EXPNAME) and numbers (EXPNUM) as read-only EPICS PVs.
#
# USAGE
#
#   $ ./exp2epics.py -h
#   usage: exp2epics.py [-h] [-v] [-c CURRENTEXPCMD]
# 
#   export experiment setting to EPICS
# 
#   optional arguments:
#     -h, --help        show this help message and exit
#     -v, --verbose     be verbose
#     -c CURRENTEXPCMD  currentexp path
#
# ENVIRONMENT
#
#   Before running this script the environment must be set up properly.
#
#     Using bash:
#         $ source setup_daq2epics.bash
#
# DEMO
#
#   $ caget DAQ:AMO0:EXPNUM DAQ:AMO0:EXPNAME
#   DAQ:AMO0:EXPNUM                683
#   DAQ:AMO0:EXPNAME               amok3415
#
#   $ caget DAQ:AMO0:EXPNUM DAQ:SXR0:EXPNUM DAQ:XPP0:EXPNUM DAQ:XCS0:EXPNUM \
#         DAQ:CXI0:EXPNUM DAQ:CXI1:EXPNUM DAQ:MEC0:EXPNUM
#   DAQ:AMO0:EXPNUM                683
#   DAQ:SXR0:EXPNUM                680
#   DAQ:XPP0:EXPNUM                682
#   DAQ:XCS0:EXPNUM                543
#   DAQ:CXI0:EXPNUM                681
#   DAQ:CXI1:EXPNUM                712
#   DAQ:MEC0:EXPNUM                674
#

from pcaspy import SimpleServer, Driver
import time
import thread
import sys
import subprocess
import argparse
from os import path

class myDriver(Driver):

    instrumentList = ['AMO:0', 'SXR:0', 'XPP:0','XCS:0', 'CXI:0', 'CXI:1', 'MFX:0', 'MEC:0', 'DET:0']
    verbose = False
    shutdownFlag = False
    pollPeriod = 30
    currentexpcmd = '/reg/g/pcds/dist/pds/current/build/pdsapp/bin/x86_64-linux-dbg/currentexp'

    def __init__(self):
        super(myDriver, self).__init__()
        # start thread for polling database
        self.tid1 = thread.start_new_thread(self.pollDb,())

    # These PVs are read-only
    def write(self, reason, value):
        status = False
        return status

    def currentexp(self, instrument):

        # defaults
        expname = 'None'
        expnum = 0

        returncode = 1
        try:
            proc = subprocess.Popen([myDriver.currentexpcmd, instrument], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
        except OSError, m:
            print 'subprocess error:', m.strerror
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

    #
    # poll database for list of instruments
    #
    def pollDb(self):
        firstTime = True

        if myDriver.verbose:
            print 'pollDb: instrumentList=%s' % myDriver.instrumentList

        while True:
            for instrument in myDriver.instrumentList:
                returncode, name, number = self.currentexp(instrument)
                if myDriver.verbose and firstTime:
                    print 'self.currentexp(%s): returncode=%d, expname=%s, expnum=%d' % (instrument, returncode, name, number)
                if (returncode == 0):
                    instr=instrument.replace(':','')
                    self.setParam(instr+':EXPNAME', str(name).ljust(40))
                    self.setParam(instr+':EXPNUM', number)
            firstTime = False

            if myDriver.shutdownFlag:
                return

            # inform clients about PV value change
            self.updatePVs()

            # wait
            for xx in range(myDriver.pollPeriod):
                if myDriver.shutdownFlag:
                    return
                time.sleep(1)
        return

if __name__ == '__main__':

    # start with empty pvdb dictionary
    pvdb = {}

    # parse arguments
    parser = argparse.ArgumentParser(description='export experiment setting to EPICS')

    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose')
    parser.add_argument('-c', metavar='CURRENTEXPCMD', help='currentexp path', default=myDriver.currentexpcmd)

    args = parser.parse_args()
    myDriver.verbose = args.verbose

    if not path.isfile(args.c):
        parser.error('\'' + args.c + '\' is not a file')
    else:
        myDriver.currentexpcmd = args.c

    # populate pvdb dictionary
    for instrument in myDriver.instrumentList:
        instr=instrument.replace(':','')
        pvdb['%s:EXPNUM'    % instr] = {'type' : 'int'}
        pvdb['%s:EXPNAME'   % instr] = {'type' : 'string'}

    if myDriver.verbose:
        print 'pvdb:', pvdb

    prefix = 'DAQ:'

    server = SimpleServer()

    server.createPV(prefix, pvdb)
    driver = myDriver()

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
