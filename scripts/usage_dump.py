#! /usr/bin/python

import os
import re
import time
import sys
import traceback
import getopt
import subprocess
import threading
import signal
import datetime

OFFLINE_PATH = "/reg/g/pcds/dist/pds/"
COMMON_PATH = "/reg/common/package/"
DAQ_PACKAGES = ['pdsapp', 'pds']
COM_PACKAGES = ['pdsdata']
AMI_PACKAGES = ['ami']
SUCCESS = 0
FAIL = 1

def usage(argv):
   print """
NAME
   %s - Dumps usage information for all executables that are associated with a specified DAQ release
        (Specifically, executables in pds, pdsapp, pdsdata, and ami)


USAGE
   %s [OPTIONS]


EXAMPLE
   %s -c
   %s -p 7.2.9
   %s -d 7.3.3-p7.2.8
   %s -d 7.3.3-p7.2.8 -p 7.2.9 -a ami-7.4.0.a-p7.2.8
   %s -a ami-7.4.0.a-p7.2.8

OPTIONS:
   -h, --help
       Display script usage information
       
   -r, --release
       List the latest versions of DAQ (pds), pdsdata, ami, and psalg releases

   -c, --current
       Get usage information for executables in the most recent (current) release
       Default behavior of script is to get information about current pds release

   -d, --daq
       Get usage information for specified DAQ release
       If not given on the command line, the script will use the pds release specified in the latest pds tag
       If not given on the command line, the script will use the pdsdata release specified in the pds tag.
       If not given on the command line, the script will use the the current ami release 

   -a, --ami
       Get usage information for specified AMI release
       If not given on the command line, the script will use the pds release specified in the latest pds tag
       If not given on the command line, the script will use the pdsdata release specified in the latest pds tag
       If not given on the command line, the script will use the the current ami release 

   -p, --pdsdata
       Get usage information for specified pdsdata release
       If not given on the command line, the script will use the pds release specified in the latest pds tag
       If not given on the command line, the script will use the pdsdata release specified in the latest pds tag
       If not given on the command line, the script will use the the current ami release 

   -l, --list
       List all pds, pdsdata, and ami releases

   -o, --output
       Output file name



"""   % (argv[0],argv[0],argv[0],argv[0],argv[0],argv[0],argv[0])



class Command(object):
   def __init__(self, cmd):
      self.cmd = cmd
      self.process = None
      self.status = FAIL
      self.retry = True
      
   def run(self, timeout, flag):
      def target():
         self.process = subprocess.Popen([self.cmd, flag],
                                         shell  = False,
                                         stdin  = subprocess.PIPE,
                                         stdout = subprocess.PIPE, 
                                         stderr = subprocess.PIPE,
                                         close_fds = True)
         out, err = subprocess.Popen.communicate(self.process)
         if len(err) == 0 and len (out) != 0:
            print out
            self.status = SUCCESS
         if len(err) != 0 and err.find('sage') != -1:
            print err
            self.status = SUCCESS

      thread = threading.Thread(target=target)
      thread.start()

      thread.join(timeout)
      if thread.isAlive():
         try:
            print 'Terminating process: ', self.cmd, " PID ", self.process.pid
            os.kill(self.process.pid, signal.SIGKILL)
                     
         except:
            print "Process does not have a PID; unable to terminate %s (%d)" % (self.cmd, thread.isAlive())
         thread.join()

      return self.status
      

def get_all_executables(pds, ami, pdsdata=None):
  ts = datetime.datetime.now()
  # By default, use the pdsdata release referenced in the pds tag, otherwise, use current
  if pdsdata == None:
     if pds.find("-p")>=0:
        pdsdata = pds.split("-p")[1]
     else:
        pdsdata = get_current_pdsdata()
                
  print "Usage information for all DAQ %s, pdsdata %s, and AMI %s releases (obtained %s)\n" % \
        (pds, pdsdata, ami, ts.strftime("%Y-%m-%d %H:%M:%S"))

  execlist = []
  for package in DAQ_PACKAGES:
     path = OFFLINE_PATH + pds + "/build/" + package + "/bin/i386-linux-opt/"
     if os.stat(path):  execlist += [(path+file) for file in os.listdir(path)]

  for package in AMI_PACKAGES:
     path = OFFLINE_PATH + ami + "/build/" + package + "/bin/i386-linux-opt/"
     if os.stat(path):  execlist += [(path+file) for file in os.listdir(path)]

  for package in COM_PACKAGES:
     # pdsdata is now in /reg/common/packages and may not have the same tag as the rest of the DAQ release
     # For some versions, the rpath was not set correctly,so I had to modify  LD_LIBRARY_PATH
     if package == 'pdsdata':
        path = COMMON_PATH + "pdsdata/" + pdsdata + "/i386-linux-opt/"
        binpath = path+"bin/"
        libpath = path+"lib/"
        os.putenv("LD_LIBRARY_PATH", "${LD_LIBRARY_PATH}:%s"%libpath)
        if os.stat(binpath): execlist += [(binpath+file) for file in os.listdir(binpath)]
     else:
        path = OFFLINE_PATH + release + "/build/" + package + "/bin/i386-linux-opt/"
        if os.stat(path):  execlist += [(path+file) for file in os.listdir(path)]

  return execlist

def list_releases():
   pdsdirlist = []
   pdsdatadirlist = []
   amidirlist = []
   psalgdirlist = []
   releases = []
   pds = []
   pdsdata = []
   ami = []
   psalg = []
   
   pdsdirlist += os.listdir(OFFLINE_PATH)
   print "DAQ releases: "
   for dir in pdsdirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         print "\t%s"%dir
         pds.append(dir)
         releases.append(dir)

   pdsdatadirlist += os.listdir(COMMON_PATH+"pdsdata/")
   print "pdsdata releases: "
   for dir in pdsdatadirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         print "\t%s"%dir
         pdsdata.append(dir)
         releases.append(dir)

   amidirlist += os.listdir(OFFLINE_PATH)
   print "AMI releases: "
   for dir in amidirlist:
      if re.search('^ami-(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         print "\t%s"%dir
         ami.append(dir)
         releases.append(dir)

   psalgdirlist += os.listdir(COMMON_PATH+"pdsalg/")
   print "pdsalg releases: "
   for dir in psalgdirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         print "\t%s"%dir
         psalg.append(dir)
      
   return releases

def dumpall(executables):
   for executable in executables:
      banner(executable)
      command = Command(executable)
      status = command.run(timeout=3, flag='-h')
      if (status == FAIL):
#         print "Retrying %s with --help..." % executable
         status = command.run(timeout=5, flag='--help')
         if (status == FAIL):
#            print "Retrying %s with no flag...." % executable
            status = command.run (timeout=5, flag='')
            if (status == FAIL):
               print " "
#               print "Unable to get usage information for %s." % executable
      
def banner(cmd):
   print "%s\n%s\n%s\n" % ((len(cmd)+5)*'-', cmd, (len(cmd)+5)*'-')

def get_current_pds():
   dirlist = []
   releases = []
   
   dirlist += os.listdir(OFFLINE_PATH)
   for dir in dirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()

def get_current_pdsdata():
   dirlist = []
   releases = []
   dirlist += os.listdir(COMMON_PATH + 'pdsdata')
   for dir in dirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()

def get_current_psalg():
   dirlist = []
   releases = []
   dirlist += os.listdir(COMMON_PATH + 'pdsalg')
   for dir in dirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()

def get_current_ami():
   dirlist = []
   releases = []
   dirlist += os.listdir(OFFLINE_PATH)
   for dir in dirlist:
      if re.search('^ami-(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()
   
if __name__ == '__main__':
   # Set some reasonable arguments; get latest release by default
   pds = get_current_pds()
   pdsdata = get_current_pdsdata()
   ami = get_current_ami()
   use_pdsdata = False
   
   # get the command-line arguments
   if len(sys.argv) < 2:
      print "Error - not enough arguments"
      usage(sys.argv)
   else:
      try:
         opts, args = getopt.getopt(sys.argv[1:],'d:a:p:o:crlh',
                                    ['daq','ami','pdsdata','output','current','release','list','help'])
      except getopt.GetoptError,e:
         print e
         usage(sys.argv)
         sys.exit(1)

      # Parse arguments
      for o, a in opts:
         if o in ('-h', '--help'):
            usage(sys.argv)
            sys.exit(1)
         if o in ('-r', '--release'):
            pds = get_current_pds()
            pdsdata = get_current_pdsdata()
            ami = get_current_ami()
            psalg = get_current_psalg()
            print "DAQ release: \t\t%s" % pds
            print "pdsdata release:\t%s" % pdsdata
            print "AMI release: \t\t%s" % ami
            print "psalg release: \t\t%s" % psalg
            sys.exit(1)
         if o in ('-d', '--daq'):
            pds = a
         if o in ('-a', '--ami'):
            ami = a
         if o in ('-p', '--pdsdata'):
            pdsdata = a
            use_pdsdata = True
         if o in ('-c', '--current'):
            pds = get_current_pds()
            pdsdata = get_current_pdsdata()
            ami = get_current_ami()
         if o in ('-l', '--list'):
            list_releases()
            sys.exit(1)
         if o in ('-o', '--output'):
            sys.stdout = open(a,'w')

      # Get list of executables
      if use_pdsdata:
         list = get_all_executables(pds, ami, pdsdata)
      else:
         list = get_all_executables(pds, ami)

      print "Number of executables: %d\n" % len(list)

      # Dump usage information for each DAQ executable
      dumpall(list)








