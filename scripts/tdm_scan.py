#!/usr/bin/python
#

import sys
import time
import os
from optparse import OptionParser

if __name__ == "__main__":
    import sys
    
    parser = OptionParser()
    parser.add_option("-a","--address",dest="host",default='10.0.2.106',
        help="connect to TDM at HOST", metavar="HOST")
    parser.add_option("-n","--cycles",dest="cycles",type="int",default=100,
        help="run N cycles", metavar="N")
    parser.add_option("-o","--output",dest="output",default='tdm_scan',
        help="write to OUTP file", metavar="OUTP")
    
    (options, args) = parser.parse_args()
    
    bin = 'build/pdsapp/bin/x86_64-rhel7-opt/timdly -a '+options.host

    for iter in range(options.cycles):
      os.system(bin+' -l')
      time.sleep(5)
      os.system(bin+' -T 0,0x10000 > '+options.output+'a.%d'%iter)
      time.sleep(5)
      os.system(bin+' -l')
      time.sleep(5)
      os.system(bin+' -T 0,0x10000 > '+options.output+'b.%d'%iter)
      time.sleep(5)
      os.system(bin+' -t 0x3fff')
      time.sleep(5)
    
    
