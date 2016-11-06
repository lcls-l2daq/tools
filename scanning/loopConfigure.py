#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import pydaq
import pycdb
import math
import serial
import time

from optparse import OptionParser

if __name__ == "__main__":
    import sys

    parser = OptionParser()
    parser.add_option("-a","--address",dest="host",default='localhost',
                      help="connect to DAQ at HOST", metavar="HOST")
    parser.add_option("-p","--platform",dest="platform",type="int",default=3,
                      help="connect to DAQ at PLATFORM", metavar="PLATFORM")
    parser.add_option("-A","--dbalias",dest="dbalias",type="string",
                      help="data base alias in use",metavar="DBALIAS")
    parser.add_option("-n","--steps",dest="steps",type="int",default=20,
                      help="run N parameter steps", metavar="N")
    parser.add_option("-e","--events",dest="events",type="int",default=105,
                      help="run N events/cycle", metavar="EVENTS")
    (options, args) = parser.parse_args()
    
    print 'host    ', options.host
    print 'platform', options.platform
    print 'dbalias ',options.dbalias
    print 'steps   ', options.steps
    print 'events  ', options.events

# Connect to the daq system
    daq = pydaq.Control(options.host,options.platform)
    daq.connect()
    partition = daq.partition()

#  Wait for the user to declare 'ready'
#    Setting up monitoring displays for example
    loopCount = 0;
    ready = raw_input('--Hit Enter when Ready-->')

    for cycle in range(options.steps):
        daq.configure(events=options.events,controls=[])
        daq.begin(events=options.events,controls=[])
        loopCount += 1
        print 'loop  ', loopCount
        daq.end()		
#
#  Wait for the user to declare 'done'
#    Saving monitoring displays for example
#
    ready = raw_input('-- Finished, hit Enter to exit -->')
    
    daq.disconnect()
