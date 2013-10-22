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
PACKAGES = ['pdsapp', 'pds', 'pdsdata', 'ami']
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
   %s -r 6.1.0
   %s -c

OPTIONS:
   -h, --help
       Display script usage information
       
   -r, --release
       Get usage information for executables in the specified release,
       If no release is specified, current release is used

   -c, --current
       Get usage information for executables in the most recent (current) release
       Default behavior of script is to get information about current release

   -l, --list
       List releases

   -o, --output
       Output file name



"""   % (argv[0],argv[0], argv[0], argv[0])



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
      

def get_all_executables(release):
  ts = datetime.datetime.now() 
  print "Usage information for all DAQ executables in release %s (obtained %s)\n" % \
        (release, ts.strftime("%Y-%m-%d %H:%M:%S"))
  execlist = []
  for package in PACKAGES:
     # pdsdata is now in /reg/common/packages and may not have the same tag as the rest of the DAQ release
     # For some versions, the rpath was not set correctly,so I had to modify  LD_LIBRARY_PATH
     if package == 'pdsdata':
        pdsdata_release = get_current_pdsdata()
        path = COMMON_PATH + "pdsdata/" + pdsdata_release + "/i386-linux-opt/"
        binpath = path+"bin/"
        libpath = path+"lib/"
        os.putenv("LD_LIBRARY_PATH", "${LD_LIBRARY_PATH}:%s"%libpath)
        if os.stat(binpath): execlist += [(binpath+file) for file in os.listdir(binpath)]
     elif package == 'ami':
        ami_release = get_current_ami()
        path = OFFLINE_PATH + ami_release
        binpath = path+"/build/ami/bin/i386-linux-opt/"
        if os.stat(binpath): execlist += [(binpath+file) for file in os.listdir(binpath)]
     else:
        path = OFFLINE_PATH + release + "/build/" + package + "/bin/i386-linux-opt/"
        if os.stat(path):  execlist += [(path+file) for file in os.listdir(path)]

  return execlist

def list_releases():
   dirlist = []
   releases = []
   
   dirlist += os.listdir(OFFLINE_PATH)
   for dir in dirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         print dir
         releases.append(dir)
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

def get_current_release():
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

def get_current_ami():
   dirlist = []
   releases = []
   dirlist += os.listdir(OFFLINE_PATH)
   print dirlist
   for dir in dirlist:
      if re.search('^ami-(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()
   
if __name__ == '__main__':
   # Set some reasonable arguments; get latest release by default
   release = get_current_release()
   
   # get the command-line arguments
   if len(sys.argv) < 2:
      print "Error - not enough arguments"
      usage(sys.argv)
   else:
      try:
         opts, args = getopt.getopt(sys.argv[1:],'r:o:clh',
                                    ['release','output','current','list','help'])
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
            release = a
         if o in ('-c', '--current'):
            release = get_current_release()
         if o in ('-l', '--list'):
            list_releases()
            sys.exit(1)
         if o in ('-o', '--output'):
            sys.stdout = open(a,'w')

      # Get list of executables
      list = get_all_executables(release)
      print "Number of executables: %d\n" % len(list)

      # Dump usage information for each DAQ executable
      dumpall(list)








