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
                      help="data base alias in use",metavar="DBALIAS")
    parser.add_option("-n","--steps",dest="steps",type="int",default=20,
                      help="run N parameter steps", metavar="N")
    parser.add_option("-e","--events",dest="events",type="int",default=105,
                      help="record N events/cycle", metavar="EVENTS")
    parser.add_option("-g","--gap",dest="gap",type="int",default=60,
                      help="gap in seconds or events between cycles", metavar="GAP")
    parser.add_option("-S","--shutter",dest="shutter",type="string",default="None",
                      help="path to shutter serial port", metavar="SHUTTER")
    parser.add_option("-k","--dark",dest="dark",type="int",default=1,
                      help="number of darks/cycle", metavar="DARK")
    parser.add_option("-E","--exclude",dest="exclude",type="string",default="None",
                      help="name to exclude from recording during gaps",metavar="EXCLUDE")
    (options, args) = parser.parse_args()
    
    print 'host    ', options.host
    print 'platform', options.platform
    print 'dbalias ',options.dbalias
    print 'steps   ', options.steps
    print 'detector', hex(options.detector)
    if (options.deviceOffset > 0) :
        print 'deviceOffset', options.deviceOffset, "so detector now",  hex(options.detector + options.deviceOffset)
        options.detector = options.detector + options.deviceOffset
    print 'typeID  ', hex(options.typeID)
    time.sleep(1)
    print 'shutter ', options.shutter
    time.sleep(0)
    print 'exclude ', options.exclude

    shutterActive = options.shutter != 'None'

# Connect to the daq system
    daq = pydaq.Control(options.host,options.platform)
    daq.connect()
    print 'dark    ', options.dark, 'events'
    print 'bright  ', options.events, 'events'
    index = 0.0
    if shutterActive :
        ser = serial.Serial(options.shutter)
        ser.write(chr(129)) ## close shutter
    nodeFound = 'No'
    partition = daq.partition()
    if options.exclude != 'None' :
        for node in partition :
	    if node['id'] == options.exclude :
		node['record']=False
                nodeFound = 'Yes'
                print 'gap     ', options.gap, 'events'
        if nodeFound == 'No' :
	    print options.exclude, 'device not found! Valid names are:'
	    for node in partition :
		print '    ', node['id']
	    options.exclude = 'None'
    if options.exclude == 'None' :
        print 'gap     ', options.gap, 'seconds'

#  Wait for the user to declare 'ready'
#    Setting up monitoring displays for example
#  
    ready = raw_input('--Hit Enter when Ready-->')

    daq.configure(controls=[])
    for cycle in range(options.steps):
        if shutterActive :
            ser.write(chr(129)) ## close shutter
            time.sleep(1)
            print "Cycle", cycle, "  dark  -"
            # begin dark
            daq.begin(events=options.dark,controls=[])
            daq.end()
            ser.write(chr(128)) ## open shutter
            time.sleep(1)
	    print "Cycle", cycle, " bright -"
        else :
            print "Cycle", cycle
        # begin bright events
        daq.begin(events=options.events,controls=[])
        daq.end()
	if options.steps > cycle + 1 and options.gap != 0 :
            print "Cycle", cycle, "   gap   -"
	    if options.exclude == 'None' :
	        time.sleep(options.gap)
            else :
                daq.configure(controls=[],partition=partition)
      		daq.begin(events=options.gap,controls=[])
        	daq.end()
                daq.configure(controls=[])
		
#
#  Wait for the user to declare 'done'
#    Saving monitoring displays for example
#
    ready = raw_input('-- Finished, hit Enter to exit -->')
