#!/bin/env python

import sys
import os
import platform
import time
import getopt
import thread
import locale
import traceback
import subprocess

__version__ = "0.1"

class XtcClean:
  # static data
  dictExpToHosts = {
    "amo": ["daq-amo-dss01", "daq-amo-dss02", "daq-amo-dss03", "daq-amo-dss04"],
    "sxr": ["daq-sxr-dss01", "daq-sxr-dss02", "daq-sxr-dss03", "daq-sxr-dss04"],
    "xpp": ["daq-xpp-dss01", "daq-xpp-dss02", "daq-xpp-dss03", "daq-xpp-dss04"]
  }
  iConnectTimeOut = 3
    
  def __init__(self, sExpType, iExpId, iCleanType):
    self.sExpType   = sExpType.lower()    
    self.iExpId     = iExpId
    self.iCleanType = iCleanType
    
  def run(self):    
        
    if not self.dictExpToHosts.has_key(self.sExpType):
      print "Invalid Experiment Type: %s" % self.sExpType
      return False

    if not self.switchUser():
      return False

    bFilesFound = False
    lHostFile   = []
    lHosts      = self.dictExpToHosts[self.sExpType]
    for (iHost,sHost) in enumerate(lHosts):      
      sCmdLs  = ( "/usr/bin/ssh -x -o ConnectTimeout=%d %s /bin/ls -rt " + \
                "/u2/pcds/pds/%s/e%d/*.xtc.tobedeleted 2> /dev/null" ) % \
                (self.iConnectTimeOut, sHost, self.sExpType, self.iExpId)
      lsCmdOut = map( str.strip, os.popen(sCmdLs).readlines() )

      lHostFile.append( len(lsCmdOut) )
      if len(lsCmdOut) == 0: continue
      
      bFilesFound = True
        
      print "%s: %d Files" % (sHost, len(lsCmdOut))      
      print "  First File: " + lsCmdOut[0]
      print "              ............................"
      print "   Last File: " + lsCmdOut[-1] + "\n"


    if not bFilesFound:
      print "No files are found. Please verify the experiment type and id."
      return True

    if self.iCleanType == 0 or self.iCleanType > 2:
      print "List complete. Use -c (--clean) or --force option to commit the deletion\n" + \
        " of files."
      return True


    if self.iCleanType == 1:
      print "Are you sure to delete the above files? [yes/no] ",
      sAns = sys.stdin.readline().strip().lower()
      if sAns != "yes":
        return True
      print # Print an extra line, because the above input produced a line return

    # !! for debug only
    if self.iExpId != 1000:
      print "Debug veresion, please specify exp id 1000"
      return True
      
    for (iHost,sHost) in enumerate(lHosts):
      if lHostFile[iHost] == 0: continue
      iDelNo        = self.getDelNo(sHost)
      sFnDelList    = "/u2/pcds/pds/%s/e%d/deletedlist%02d.txt" % (self.sExpType, self.iExpId, iDelNo)

      print "Generating Delete List %s:%s" % (sHost, sFnDelList)
      sCmdGenDel    = ( "/usr/bin/ssh -x -o ConnectTimeout=%d %s \"/bin/ls -lrt " + \
                "/u2/pcds/pds/%s/e%d/*.xtc.tobedeleted > %s\" 2> /dev/null" ) % \
                (self.iConnectTimeOut, sHost, self.sExpType, self.iExpId, sFnDelList)
      
      sCmdGenDelOut = os.popen(sCmdGenDel).read()
      
      sCmdRm        = ( "/usr/bin/ssh -x -o ConnectTimeout=%d %s /bin/rm -v " + \
                "/u2/pcds/pds/%s/e%d/*.xtc.tobedeleted 2> /dev/null" ) % \
                (self.iConnectTimeOut, sHost, self.sExpType, self.iExpId)
      
      lsCmdRmOut    = map( str.strip, os.popen(sCmdRm).readlines() )
      iFilesDeleted = len(lsCmdRmOut)
      
      if iFilesDeleted != lHostFile[iHost]:
        print "%s: Expected to delete %d files, but in reality %d files deleted" %\
          ( sHost, lHostFile[iHost], iFilesDeleted )
      else:
        print "%s: %d files deleted" % (sHost, iFilesDeleted)
        
      print "  [Deletion History]"
      for sLine in lsCmdRmOut:
        print "  " + sLine
      print

  def getDelNo(self, sHost):
    sCmdLsDel = ( "/usr/bin/ssh -x -o ConnectTimeout=%d %s /bin/ls -rt " + \
                  "/u2/pcds/pds/%s/e%d/deletedlist*.txt 2> /dev/null" ) % \
                  (self.iConnectTimeOut, sHost, self.sExpType, self.iExpId)
    lsCmdLsDelOut = map( str.strip, os.popen(sCmdLsDel).readlines() )

    iTestDelNo    = len(lsCmdLsDelOut)    
    while True:
      sCmdLsDel1  = ( "/usr/bin/ssh -x -o ConnectTimeout=%d %s /bin/ls -rt " + \
                "/u2/pcds/pds/%s/e%d/deletedlist%02d.txt 2> /dev/null" ) % \
                (self.iConnectTimeOut, sHost, self.sExpType, self.iExpId, iTestDelNo)
      sCmdLsDel1Out = os.popen(sCmdLsDel1).read()
      if len(sCmdLsDel1Out) < 1: break
      iTestDelNo += 1
   
    return iTestDelNo    
  
  def switchUser(self):
    if os.geteuid() != 0:
      print "You need to become root to run this script."
      return False

    sUserName = self.sExpType + "opr"
    iId       = int(os.popen( "/usr/bin/id -u " + sUserName ).read().strip())

    try:
      os.setreuid(iId, iId)
    except:
      print "Cannot switch to %s." % sUserName
      return False

    return True


def showUsage():
  print( """\
Usage: %s [-t | --type <Experiment Type>]* [-e | --exp
  <Experiment Id>]* [-c|--clean] [--force] [-v] [-h]

  -t | --type       <Experiment Type>  *Set experiment type (amo, sxr, xpp)
  -e | --exp        <Experiment Id>    *Set experiment id
  -c | --clean                         Execute the real clean-up, with yes/no
                                         prompt
       --force                         Force the real clean-up, without yes/no
                                         prompt

  * required

Clean-up Type
=============
  Default (No -c or --force flags specified):
    List all the files to be deleted, but no real action

  Standard Clean-up (when -c or --clean is specified)
     Run the clean-up, with a prompt for confirmation

  Forced Clean-up   (when --force is specified)
     Force the clean-up running, without prompt for confirmation
  
Program Version %s\
""" % ( __file__, __version__ ) )
  return
    
def main():
  iExpId   = -1
  sExpType = ""
  
  #
  # Clean-up Type
  #    0: List all the files to be deleted, but no real action
  #    1: Run the clean-up, with a prompt for confirmation
  #    2: Force the clean-up without prompt
  #
  # Default: 0
  #
  iCleanType = 0

  try:    
    (llsOptions, lsRemainder) = getopt.getopt(sys.argv[1:], \
     "t:e:cvh", \
     ["type", "exp", "clean", "force", "version", "help"])
  except:
    print "*** Invalid option ***"
    showUsage()
    return 1
   
  for (sOpt, sArg) in llsOptions:
    if   sOpt in ("-t", "--type" ):
      sExpType   = sArg
    elif sOpt in ("-e", "--exp" ):
      iExpId     = int(sArg)
    elif sOpt in ("-c", "--clean" ) and iCleanType != 2:
      iCleanType = 1
    elif sOpt in ("--force" ):
      iCleanType = 2
    elif sOpt in ("-v", "-h", "--version", "--help" ):
      showUsage()
      return 1

  if sExpType == "":
    print "Experiment Type Not Defined -- See Help below.\n"
    showUsage()
    return 2
  if iExpId == -1:
    print "Experiment ID Not Defined -- See Help below.\n"
    showUsage()
    return 2

  xtcClean = XtcClean( sExpType, iExpId, iCleanType )
  xtcClean.run()
  
  return

# Main Entry
if __name__ == "__main__":
  iRet = 0
  
  try:
    iRet = main()
  except:
    iRet = 101
    print __file__ + ": %s" % (sys.exc_value)
    print( "---- Printing program call stacks for debug ----" )
    traceback.print_exc(file=sys.stdout)
    print( "------------------------------------------------" )
    showUsage()
    
  sys.exit(iRet)