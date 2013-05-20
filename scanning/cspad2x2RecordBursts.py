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
    parser.add_option("-D","--detector",dest="detector",type="int",default=0x23000d00,
                      help="detector ID  to scan",metavar="ID")
    parser.add_option("-d","--device",dest="deviceOffset",type="int",default=0,
                      help="device ID offset",metavar="DEV_OFFSET")
    parser.add_option("-t","--typeID",dest="typeID",type="int",default=0x2002b,
                      help="type ID to generate",metavar="TYPEID")
    parser.add_option("-A","--dbalias",dest="dbalias",type="string",
                      help="data base key in use",metavar="DBALIAS")
    parser.add_option("-n","--steps",dest="steps",type="int",default=20,
                      help="run N parameter steps", metavar="N")
    parser.add_option("-e","--events",dest="events",type="int",default=105,
                      help="record N events/cycle", metavar="EVENTS")
    parser.add_option("-g","--gap",dest="gap",type="int",default=60,
                      help="gap in seconds between cycles", metavar="GAP")
    parser.add_option("-S","--shutter",dest="shutter",type="string",default="None",
                      help="path to shutter serial port", metavar="SHUTTER")
    parser.add_option("-k","--dark",dest="dark",type="int",default=1,
                      help="number of darks/cycle", metavar="DARK")
    (options, args) = parser.parse_args()
    
    print 'host', options.host
    print 'platform', options.platform
    print 'dbalias',options.platform
    print 'gap', options.gap, 'seconds'
    print 'steps', options.steps
    print 'events', options.events
    print 'detector', hex(options.detector)
    if (options.deviceOffset > 0) :
        print 'deviceOffset', options.deviceOffset, "so detector now",  hex(options.detector + options.deviceOffset)
        options.detector = options.detector + options.deviceOffset
    print 'typeID', hex(options.typeID)
    print 'shutter', options.shutter
    print 'dark', options.dark

    shutterActive = options.shutter != 'None'

# Connect to the daq system
    daq = pydaq.Control(options.host,options.platform)
    daq.connect()
    cdb = pycdb.Db(daq.dbpath())
    key = daq.dbkey()
#    xtc = cdb.get(key=key,src=options.detector,typeid=options.typeID)[0]
#  Wait for the user to declare 'ready'
#    Setting up monitoring displays for example
#  
    ready = raw_input('--Hit Enter when Ready-->')
    index = 0.0
    if shutterActive :
        ser = serial.Serial(options.shutter)
        ser.write(chr(129)) ## close shutter
        darkkey = cdb.clone(options.dbalias)
        print 'Generated dark key ',hex(darkkey)

    cdb.unlock()

    daq.configure(key=key,events=options.events,controls=[])
    for cycle in range(options.steps):
    	if shutterActive :
            ser.write(chr(129)) ## close shutter
            time.sleep(1)
            print "Cycle", cycle, " closed -"
            # config bright dark
            daq.configure(key=darkkey,events=options.dark,controls=[])
            daq.begin(controls=[])
            daq.end()
            ser.write(chr(128)) ## open shutter
            time.sleep(1)
	    print "Cycle", cycle, " opened -"
            # config bright events
            daq.configure(key=key,events=options.events,controls=[])
        else :
            print "Cycle", cycle
        daq.begin(controls=[])
        daq.end()
	if options.steps > cycle + 1 :
	    time.sleep(options.gap)
         
#
#  Wait for the user to declare 'done'
#    Saving monitoring displays for example
#
    ready = raw_input('-- Finished, hit Enter to exit -->')
