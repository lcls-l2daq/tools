#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import serial
import time

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-S","--shutter",dest="shutter",type="string",default="None",
                help="path to shutter serial port", metavar="SHUTTER")
(options, args) = parser.parse_args()

shutterActive = options.shutter != 'None'

if shutterActive :
        print 'shutter', options.shutter, 'close'
	ser = serial.Serial(options.shutter)
	ser.write(chr(128)) ## close shutter
	time.sleep(1)
else :
	print 'You must specify a shutter!'
