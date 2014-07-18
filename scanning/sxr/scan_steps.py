#!/reg/common/package/python/2.5.5/bin/python

import pyca
from Pv import Pv

import pydaq

import sys
import time
import random
import threading

from options import Options

class donemoving(Pv):
  def __init__(self, name):
    Pv.__init__(self, name)
    self.monitor_cb = self.monitor_handler
    self.__sem = threading.Event()

  def wait_for_done(self):
    moving = False
    while not moving:
      self.__sem.wait(0.1)
      if self.__sem.isSet():
        self.__sem.clear()
        if self.value == 0:
          moving = True
      else:
        print 'timedout while waiting for moving'
        break
    while moving:
      self.__sem.wait(1000)
      if self.__sem.isSet():
        self.__sem.clear()
        if self.value == 1:
          moving = False
      else:
        print 'timedout while waiting for done'
        break

  def monitor_handler(self, exception=None):
    try:
      if exception is None:
        print 'pv %s is %d' %(self.name, self.value)
        self.__sem.set()
      else:
        print "%-30s " %(self.name), exception
    except Exception, e:
      print e

if __name__ == '__main__':
  options = Options(['motorpvname', 'from', 'to', 'steps', 'events', 'record'], [], [])
  try:
    options.parse()
  except Exception, msg:
    options.usage(str(msg))
    sys.exit()

  motorpvname = options.motorpvname
  low  = float(options.opts['from'])
  high = float(options.opts['to'])
  steps = int(options.opts['steps'])
  events = int(options.opts['events'])

  print 'Stepping %s from %f to %f with %d events at each of %d steps'%(motorpvname,low,high,events,steps)
  
  evtmask = pyca.DBE_VALUE | pyca.DBE_LOG | pyca.DBE_ALARM 

#  Initialize DAQ control
  daq = pydaq.Control('sxr-daq')


#  Let user setup plots                    
  ready = raw_input('--Hit Enter when Ready-->')
  
  
#  Configure DAQ                    
  doRecord = False
  if (options.opts['record'].upper()=='Y'):
    doRecord = True
    
  daq.configure(record=doRecord,
                events=int(options.opts['events']),
                controls=[(motorpvname,low)])

  try:
    motorpv = Pv(motorpvname)
    motorpv.connect(1.0)
#    dmovpv = donemoving(motorpvname + '.DMOV')
    dmovpv = donemoving(motorpvname)
    dmovpv.connect(1.0)
    dmovpv.monitor(evtmask, ctrl=False)
    pyca.flush_io()
    counter = 1
    while True:
      counter *= -1
      for i in range(steps):
        if counter > 0:
          steppos = (low*(float(steps-i))+high*float(i))/float(steps)
        else:
          steppos = (high*(float(steps-i))+low*float(i))/float(steps)
        print 'Requested position is %f' %steppos
        motorpv.put(steppos, 1.0)
        dmovpv.wait_for_done()

        print 'Requested %d events'%events
        
        #  Start Acquisition
        daq.begin(controls=[(motorpvname,steppos)],events=int(options.opts['events']))
        #  Wait for end of acquisition (nevents)
        daq.end()
      
  except pyca.pyexc, e:
      print 'pyca exception: %s' %(e)
  except pyca.caexc, e:
      print 'channel access exception: %s' %(e)
