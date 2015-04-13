#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import pydaq
import pycdb
import math
import serial
import pprint

from optparse import OptionParser

if __name__ == "__main__":
    import sys

    parser = OptionParser()
    parser.add_option("-a","--address",dest="host",default='localhost',
                      help="connect to DAQ at HOST", metavar="HOST")
    parser.add_option("-p","--platform",dest="platform",type="int",default=3,
                      help="connect to DAQ at PLATFORM", metavar="PLATFORM")
    parser.add_option("-D","--detector",dest="detector",type="string",default='NoDetector',
                      help="detector to scan, default NoDetector",metavar="DET")
    parser.add_option("-I","--detectorID",dest="detectorID",type="int",default=0,
                      help="detector ID  to scan, default 0",metavar="D_ID")
#    parser.add_option("-d","--device",dest="device",type="string",default='Epix10k',
#                      help="device to scan, default Epix10k",metavar="DEV")
    parser.add_option("-i","--deviceID",dest="deviceID",type="int",default=0,
                      help="device ID to scan, default 0",metavar="DEV_ID")
    parser.add_option("-t","--typeIdVersion",dest="typeIdVersion",type="int",default=1,
                      help="type ID Version in use, default 1",metavar="typeIdVersion")
    parser.add_option("-P","--parameter",dest="parameter",type="string",
                      help="epix parameter to scan", metavar="PARAMETER")
    parser.add_option("-A","--dbalias",dest="dbalias",type="string",
                      help="data base key in use",metavar="DBALIAS")
    parser.add_option("-s","--start",dest="start",type="float", default=200,
                      help="parameter start", metavar="START")
    parser.add_option("-f","--finish",dest="finish",type="int",nargs=1,default=2000,
                      help="parameter finish", metavar="FINISH")
    parser.add_option("-m","--multiplier",dest="multiplier",type="float",nargs=1,default=-1.0,
                      help="parameter multiplier in case you want to enter it directly, ignoring FINISH", metavar="MULTIPLIER")
    parser.add_option("-n","--steps",dest="steps",type="int",default=20,
                      help="run N parameter steps", metavar="N")
    parser.add_option("-e","--events",dest="events",type="int",default=105,
                      help="record N events/cycle", metavar="EVENTS")
    parser.add_option("-L","--linear",dest="linear",type="string",default="no",
              help="Set to yes for linear scanning instead of exponential", metavar="LINEAR")
    parser.add_option("-l","--limit",dest="limit",type="int",default=99,
                      help="limit number of configs to less than number of steps", metavar="LIMIT")
    parser.add_option("-S","--shutter",dest="shutter",default="None",
                      help="path to shutter serial port", metavar="SHUTTER")
    parser.add_option("-u","--use_l3t",dest="use_l3t",action="store_true",default=False,
                      help="Use L3Trigger to filter events",metavar="L3T")

    (options, args) = parser.parse_args()
    
    options.device = 'Epix10k'
    options.typeId = 'Epix10kConfig'
    
    print 'host', options.host
    print 'platform', options.platform
    print 'dbalias',options.dbalias
    print 'parameter', options.parameter
    print 'start', options.start, options.start
    print 'steps', options.steps
    print 'finish', options.finish
#    print 'multiplier', options.multiplier
    print 'events', options.events
    print 'detector', options.detector
    print 'detectorID', options.detectorID
    print 'device', options.device
    print 'deviceID', options.deviceID
#    print 'linear', options.linear
    print 'shutter', options.shutter
    print 'use_l3t', options.use_l3t

    if options.steps < options.limit : options.limit = options.steps
    else : print 'Warning, range will be covered in', options.limit, \
         'but will still do', options.steps, 'steps with wrapping'

    adder = 0.0
    if options.linear == "no" :
      if (options.start == 0) :
        options.start = 0.49
      if (options.multiplier < 0) :
        options.multiplier = math.exp( (math.log( float(options.finish)/options.start )) / options.limit  )
      print 'multiplier in use is', options.multiplier, 'and will scan from', options.start, 'to', options.finish
    else :
        adder = (float(options.finish) - options.start) / float(options.limit)
        print 'will do linear scanning from', options.start, 'to', options.finish, "in ", options.limit, "steps and with adder of ", adder

# Connect to the daq system
    daq = pydaq.Control(options.host,options.platform)
    daq.connect()
    print 'Partition is', daq.partition()
    detectors = daq.detectors()
    devices = daq.devices()
    types = daq.types()
#    print 'types are :\n', types

    found = [False, False, False]
    index = 0
    for member in detectors :
        if member == options.detector :
            detectorValue = (index << 24) | ((options.detectorID&0xff)<<16)
            found[0] = True
        index = index + 1
    index = 0
    for member in devices :
        if member == options.device :
            detectorValue = detectorValue | (index << 8) | (options.deviceID & 0xff)
            found[1] = True
        index = index + 1
    index = 0;
    for member in types :
        if member == options.typeId :
            typeIdValue = index | (options.typeIdVersion<<16);
            found[2] = True
        index = index + 1
    if found[0] and found[1] and found[2]:
        print "detector hex value",  hex(detectorValue)
        print 'typeId', hex(typeIdValue)
    else :
        if not found[0] :
            print "Detector", options.detector, "not found!"
        if not found[1] :
            print "Device", options.device, "not found!"
        if not found[2] :
            print "Type", options.typeId, "not found!"
        print "Exiting"
        exit()
#
#  First, get the current configuration key in use and set the value to be used
#

    cdb = pycdb.Db(daq.dbpath())
    key = daq.dbkey()
    alias = daq.dbalias()
    print 'Retrieved key '+hex(key)+' alias '+alias

#
#  Generate a new key with different epix and EVR configuration for each cycle
#
    if options.dbalias==None:
        newkey = cdb.clone(alias)
    else:
        newkey = cdb.clone(options.dbalias)
    
    print 'Generated key ',hex(newkey)
    print 'key',hex(key)
    print 'detectorValue',hex(detectorValue)
    print 'typeIdValue',hex(typeIdValue)
#    xtcSet = cdb.get(key=key)
#    print 'xtcSet members :\n'
#    for member in xtcSet :
#        for attr in dir(member) :
#            print getattr(member,attr)            
#    print 'Done printing xtcSet\n'
#    print "cdb.get opened\n", cdb.get(key=key)
    xtc = cdb.get(key=key,src=detectorValue,typeid=typeIdValue)[0]
    print 'xtc is', xtc
    epix = xtc.get(0)
    parameterType = 'None'
    for member in epix :
        if options.parameter == member:
            print 'Found the', options.parameter, 'fpga parameter'
            parameterType = 'fpga'
    for member in epix['asics'][0] :
        if member == options.parameter :
            print 'Found the', options.parameter, 'asic parameter'
            parameterType = 'asic'
    if parameterType == 'None' :
        print 'Parameter', options.parameter, 'not found!'
        print '    Allowed fpga parameters : current values'
        for member in epix :
            if member!='asics' and not member.endswith('Array') and not member.endswith('Version') and not 'CardId' in member and not 'NumberOf' in member and not 'LastRow' in member and not 'Environment' in member and not 'BaseClock' in member :
                print '        ', member, ':', epix[member]
        print '    Allowed asic parameters : current values'
        for member in epix['asics'][0] :
						if member!='chipID' and not member.endswith('StartAddr') and not member.endswith('StopAddr') :
								print '        ', member, ':',   epix['asics'][0][member]
    else :
        print 'Composing the sequence of configurations ...'
        value = float(options.start)
        cycleLength = 1
        shutterActive = options.shutter != 'None'
        if shutterActive :
            cycleLength = 2
        denom = float(options.limit+1)
        mask = epix['AsicMask']
        values = []
        for cycle in range(options.limit+1) :
            index = float(cycle%(options.limit+1)) + 1.0
            if parameterType == 'asic' :
                for asicNum in range(4) :
                    if mask & (1 << asicNum) :
                        epix['asics'][asicNum][options.parameter]=int(round(value))
            if parameterType == 'fpga' :
                epix[options.parameter]=int(round(value))
            xtc.set(epix,cycle)
            values.append(int(round(value)));
            if options.linear == "no" :
#                print cycle, int(round(value))
                value = value * options.multiplier
            else :
#                print cycle, int(round(value)) 
                value = value + adder
        cdb.substitute(newkey,xtc)
        cdb.unlock()
        for cycle in range(len(values)) :
            print cycle, "value of", options.parameter, "is",  values[cycle]
        print '    done'
#
#  Could scan EVR simultaneously
#
#    evr   = Evr  .ConfigV4().read(cdb.xtcpath(key.value,Evr  .DetInfo,Evr  .TypeId))
#    newxtc = cdb.remove_xtc(newkey,Evr.DetInfo,Evr.TypeId)

#
#  Send the structure the first time to put the control variables
#    in the file header
#

        if options.use_l3t:
            print "Acquiring %s events passing L3Trigger"%(options.events)
            daq.configure(key=newkey,
                          l3t_events=options.events,
                          controls=[(options.parameter[0:29],int(round(options.start)))])
        else:
            daq.configure(key=newkey,
                          events=options.events,
                          controls=[(options.parameter[0:29],int(round(options.start)))])

        print "Configured."

# set up shutter
        if shutterActive :
            ser = serial.Serial(options.shutter)
            ser.write(chr(129)) ## close shutter

#
#  Wait for the user to declare 'ready'
#    Setting up monitoring displays for example
#  
        ready = raw_input('--Hit Enter when Ready-->')
        for cycle in range(options.steps+1):
          if cycle%(options.limit+1) == 0 : 
            index = 0.0
            subcycle = 0;
          if shutterActive :
            ser.write(chr(129)) ## close shutter
            print "Cycle", cycle, " closed -", options.parameter, "=", values[subcycle]
          else :
            print "Cycle", cycle, "-", options.parameter, "=", values[subcycle]
          if options.use_l3t:
              daq.begin(l3t_events=options.events,controls=[(options.parameter[0:29],values[subcycle])])
          else:
              daq.begin(controls=[(options.parameter[0:29],values[subcycle])])
          # wait for enabled , then enable the EVR sequence
          # wait for disabled, then disable the EVR sequence
          daq.end() 
          if shutterActive :
            print "        opened -", options.parameter, "=", values[subcycle]
            ser.write(chr(128)) ## open shutter
            if options.use_l3t:
                daq.begin(l3t_events=options.events,controls=[(options.parameter[0:29],values[subcycle])])
            else:
                daq.begin(controls=[(options.parameter[0:29],values[subcycle])])
            daq.end()
            ser.write(chr(129)) ## close shutter
          subcycle += 1;
        
#
#  Wait for the user to declare 'done'
#    Saving monitoring displays for example
#
    ready = raw_input('-- Finished, hit Enter to exit -->')
    print 'Restoring key', hex(key)
    daq.configure(key=key, events=1)
