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
#    parser.add_option("-d","--device",dest="device",type="string",default='Epix100a',
#                      help="device to scan, default Epix100a",metavar="DEV")
    parser.add_option("-i","--deviceID",dest="deviceID",type="int",default=0,
                      help="device ID to scan, default 0",metavar="DEV_ID")
    parser.add_option("-t","--typeIdVersion",dest="typeIdVersion",type="int",default=1,
                      help="type ID Version in use, default 1",metavar="typeIdVersion")
    parser.add_option("-A","--dbalias",dest="dbalias",type="string",
                      help="data base key in use",metavar="DBALIAS")
    parser.add_option("-f","--fileName",dest="fileName",type="string",default='NoFileName',
                      help="name of file to scan, default NoFileName",metavar="FN")
    parser.add_option("-e","--events",dest="events",type="int",default=105,
                      help="record N events/cycle", metavar="EVENTS")
    parser.add_option("-S","--shutter",dest="shutter",default="None",
                      help="path to shutter serial port", metavar="SHUTTER")
    (options, args) = parser.parse_args()
    
    options.device = 'Epix100a'
    options.typeId = 'Epix100aConfig'
    
    print 'host', options.host
    print 'platform', options.platform
    print 'dbalias',options.dbalias
    print 'detector', options.detector
    print 'detectorID', options.detectorID
    print 'device', options.device
    print 'deviceID', options.deviceID
    print 'fileName', options.fileName
    print 'events', options.events
    print 'shutter', options.shutter

    inputFile = open(options.fileName, mode='r')
    parameters = inputFile.readline().split()
    numParams = 0;
    for parm in parameters :
        numParams += 1
    print 'there are ', numParams, 'parameters'
    values = []
    indx = 0
    for line in inputFile :
        numbs = line.split()
        row = []
        for num in numbs :
            row.append(int(num))
        values.append(row)
        indx += 1
    steps = indx
    print parameters
#    for i in xrange(steps) :
#        print values[i]
#    exit()
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
    parameterType = []
    indx = 0
    for p in parameters :
        parameterType.append('none')
        for member in epix :
            if p == member:
                print 'Found the', p, 'fpga parameter'
                parameterType[indx] = 'fpga'
        for member in epix['asics'][0] :
            if member == p :
                print 'Found the', p, 'asic parameter'
                parameterType[indx] = 'asic'
        indx += 1
    foundAllParameters = 'true'
    for i in xrange(numParams) :
        if parameterType[i] == 'none' :
            print 'Parameter', parameters[i], 'not found!'
            foundAllParameters = 'false'
    if foundAllParameters == 'false' :
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
        cycleLength = 1
        shutterActive = options.shutter != 'None'
        if shutterActive :
            cycleLength = 2
        mask = epix['AsicMask']
        for cycle in range(steps) :
            indx = 0
            for p in parameters :
                if parameterType[indx] == 'asic' :
                    for asicNum in range(4) :
                        if mask & (1 << asicNum) :
                            epix['asics'][asicNum][p]=values[cycle][indx]
                if parameterType[indx] == 'fpga' :
                    epix[p]=values[cycle][indx]
                indx += 1    
            xtc.set(epix,cycle)
#            print cycle, "values ",  values[cycle]
        cdb.substitute(newkey,xtc)
        cdb.unlock()
        print '    done composing sequence'
#
#  Could scan EVR simultaneously
#
#    evr   = Evr  .ConfigV4().read(cdb.xtcpath(key.value,Evr  .DetInfo,Evr  .TypeId))
#    newxtc = cdb.remove_xtc(newkey,Evr.DetInfo,Evr.TypeId)

#
#  Send the structure the first time to put the control variables
#    in the file header
#
        parms = []
        for p in range(len(parameters)) :
            thisTuple = (parameters[p], 0)
            parms.append(thisTuple)
        daq.configure(key=newkey,
                      events=options.events,
                      controls=parms)
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
        for cycle in range(steps):
          if shutterActive :
            ser.write(chr(129)) ## close shutter
            print "Cycle", cycle, " closed -"
          else :
            print "Cycle", cycle, "-"
          parms = []
          for p in range(len(parameters)) :
            thisTuple = (parameters[p],values[cycle][p])
            parms.append(thisTuple)
          print '    parms ', parms  
          daq.begin(controls=parms)
          daq.end() 
          if shutterActive :
            print "        opened -", parameters, "=", values[cycle]
            ser.write(chr(128)) ## open shutter
            daq.begin()
            daq.end()
            ser.write(chr(129)) ## close shutter
        
#
#  Wait for the user to declare 'done'
#    Saving monitoring displays for example
#
    ready = raw_input('-- Finished, hit Enter to exit -->')
    print 'Restoring key', hex(key)
    daq.configure(key=key, events=1)
