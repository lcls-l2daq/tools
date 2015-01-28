#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import pydaq
import pyami
import sys
import time
import math
import socket
import struct
import subprocess
import shutil
import os

from optparse import OptionParser

if __name__ == "__main__":
    import sys

    parser = OptionParser()
    parser.add_option("-a","--address",dest="host",default='localhost',
                      help="connect to DAQ at HOST", metavar="HOST")
    parser.add_option("-c","--cnf",dest="cnf",default='auto.cnf',
                      help="procmgr CNF file", metavar="CNF")
    parser.add_option("-p","--platform",dest="platform",type="int",default=0,
                      help="connect to DAQ platform P", metavar="P")
    parser.add_option("-P","--proxy",dest="proxy",default='daq-sxr-dss04',
                      help="host that runs the ami proxy", metavar="PHOST")
    
    (options, args) = parser.parse_args()

    restart_cmd = ['../../tools/procmgr/procmgr','restart',options.cnf]

    while(True):
        try:
            p = subprocess.Popen(restart_cmd)
            p.wait()

            time.sleep(4)
    
            pname = socket.gethostbyname(options.proxy)
            paddr = struct.unpack('>I',socket.inet_aton(pname))[0]
            print [pname,paddr]
            pyami.connect(paddr)

            time.sleep(2)
            
            daq = pydaq.Control(options.host,options.platform)
            daq.connect()
            key = daq.dbkey()
            partition = daq.partition()
            for node in partition:
                node['record']=False
            print '===Partition==='
            print partition
    
            daq.configure(key=key,
                          record=False,
                          events=0x7fffffff,
                          controls=[('cycle',0)])

            print "Configured"
            time.sleep(1)

            print 'Creating pyami Entry'
            x = pyami.Entry('EventId','Scalar')
            x.clear()
            n = 0

            daq.begin(controls=[('cycle',0)])

            while(True):
                time.sleep(2)
                v = x.get()
                if v['entries']-n < 5:
                    print 'No updates within interval'
                    raise Exception('EventError','No updates within interval')
                
                n = v['entries']

        except KeyboardInterrupt:
            break
        except:
            print 'Error - restarting DAQ'

