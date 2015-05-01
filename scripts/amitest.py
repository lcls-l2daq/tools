#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import pydaq
import pyami
import sys
import time
import math
import socket
import struct

from optparse import OptionParser

if __name__ == "__main__":
    import sys

    parser = OptionParser()
    parser.add_option("-a","--address",dest="host",default='xpp-daq',
                      help="connect to DAQ at HOST", metavar="HOST")
    parser.add_option("-p","--platform",dest="platform",type="int",default=0,
                      help="connect to DAQ platform P", metavar="P")
    parser.add_option("-n","--cycles",dest="cycles",type="int",default=100,
                      help="run N cycles", metavar="N")
    parser.add_option("-e","--events",dest="events",type="int",default=105,
                      help="record N events/cycle", metavar="N")
    parser.add_option("-t","--trigger",dest="trigger",default=False,
                      help="use l3 events", metavar="T");
    parser.add_option("-q","--qbeam",dest="qbeam",type="float",default=-1.,
                      help="require qbeam > Q", metavar="Q")
    parser.add_option("-s","--sleep",dest="tsleep",type="float",default=0.,
                      help="sleep Q seconds between cycles", metavar="Q")
    parser.add_option("-w","--wait",dest="wait",default=False,
                      help="wait for key input before 1st cycle and after last cycle", metavar="W");
    parser.add_option("-N","--iterations",dest="iterations",type='int',default=1,
                      help="Execute N iterations of this scan", metavar="Q");
    parser.add_option("-P","--proxy",dest="proxy",default='daq-xpp-mon03',
                      help="host that runs the ami proxy", metavar="PHOST")
    
    (options, args) = parser.parse_args()

    #    pyami.connect(0xefff2a00,0xac150ab2,0xac1508b2)
    #    pyami.connect(0xefff2301,0xac152636,0xac151636) # xpp-daq
    #    pyami.connect(0xefff2301,0xac152647,0xac151647) # xpp-control
    #    pyami.connect(0xac150a17)  # Lab2
    #    pyami.connect(0xac15265e)  # XPP
    #    pyami.connect(0xac152b6b)  # XCS
    pname = socket.gethostbyname(options.proxy)
    paddr = struct.unpack('>I',socket.inet_aton(pname))[0]
    print [pname,paddr]
    pyami.connect(paddr)
    
    daq = pydaq.Control(options.host,options.platform)

    for iter in range(options.iterations):

        #
        #  Send the structure the first time to put the control variables
        #    in the file header
        #

        #    daq.configure(events=options.events,
        #                  controls=[('EXAMPLEPV1',0),('EXAMPLEPV2',0)],
        #                  monitors=[('BEAM:LCLS:ELEC:Q',options.qbeam,1.)])

        do_record = False
        partition = daq.partition()
#        for node in partition:
#            node['record']=False
        print '===Partition==='
        print partition
    
        if options.trigger:
            daq.configure(record=do_record,
                          l3t_events=options.events,
                          controls=[('EXAMPLEPV1',0),('EXAMPLEPV2',0)],
                          labels=[('EXAMPLELABEL1',''),('EXAMPLELABEL2','')])

        else:
            daq.configure(record=do_record,
                          events=options.events,
                          controls=[('EXAMPLEPV1',0),('EXAMPLEPV2',0)],
                          labels=[('EXAMPLELABEL1',''),('EXAMPLELABEL2','')])

        print "Configured [%d]."%iter

        #
        #  Wait for the user to declare 'ready'
        #    Setting up monitoring displays for example
        #  

        if options.wait:
            ready = raw_input('--Hit Enter when Ready-->')
        else:
            time.sleep(options.tsleep)

        # x = pyami.Entry('XppEnds_Ipm0:FEX:CH1','Scan','EventId',options.events)
        # x = pyami.Entry('XcsEndstation-0|Ipimb-1:CH1','Scan','EventId',options.events)
        # x = pyami.Entry('XppSb2_Ipm:FEX:SUM','Scalar')
        # x = pyami.Entry('ProcTime','Scalar')
        x = pyami.Entry('EventId','Scalar')

        for cycle in range(options.cycles):

            x.clear()
        
            daq.begin(controls=[('EXAMPLEPV1',cycle),('EXAMPLEPV2',100-cycle)],
                      labels=[('EXAMPLELABEL1','CYCLE%d'%cycle),('EXAMPLELABEL2','LCYCLE%d'%options.cycles)])
            # enable the EVR sequence, if necessary

            # wait for disabled, then disable the EVR sequence
            daq.end()

            v = x.get()
            if False:
                print v
            else:
                n = v['entries']
                mean = v['mean']
                rms  = v['rms']
                print '%04d | %9f | %9f | %.0f |' % (cycle,mean,rms,n)
            
        if (do_record==True):
            print 'Recorded expt %d run %d' % (daq.experiment(),daq.runnumber())
        
        #
        #  Wait for the user to declare 'done'
        #    Saving monitoring displays for example
        #
        if options.wait:
            ready = raw_input('--Hit Enter when Done-->')
