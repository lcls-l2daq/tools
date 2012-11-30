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

__version__ = "0.5"

# Database access: instead of relying on $PYTHONPATH to include offline tools, we depend on a binary in the DAQ build
currentexpcmd = '/reg/g/pcds/dist/pds/5.2.2/build/pdsapp/bin/i386-linux-dbg/currentexp'

class XtcClean:
  # static data
  dictExpToHosts = {
    "amo": ["daq-amo-dss01", "daq-amo-dss02", "daq-amo-dss03", "daq-amo-dss04", "daq-amo-dss05", "daq-amo-dss06"],
    "sxr": ["daq-sxr-dss01", "daq-sxr-dss02", "daq-sxr-dss03", "daq-sxr-dss04", "daq-sxr-dss05", "daq-sxr-dss06"],
    "xpp": ["daq-xpp-dss01", "daq-xpp-dss02", "daq-xpp-dss03", "daq-xpp-dss04", "daq-xpp-dss05", "daq-xpp-dss06", "daq-xpp-dss07"],
    "cxi": ["daq-cxi-dss01", "daq-cxi-dss02", "daq-cxi-dss03", "daq-cxi-dss04", "daq-cxi-dss05", "daq-cxi-dss06"],
    "xcs": ["daq-xcs-dss01", "daq-xcs-dss02", "daq-xcs-dss03", "daq-xcs-dss04", "daq-xcs-dss05", "daq-xcs-dss06"],
    "mec": ["daq-mec-dss01", "daq-mec-dss02", "daq-mec-dss03", "daq-mec-dss04", "daq-mec-dss05", "daq-mec-dss06"]
  }
  iConnectTimeOut = 3

  def __init__(self, sExpType, sExpName, iExpId, iCleanType, iStation):
    self.sExpType   = sExpType.lower()    
    self.sExpName   = sExpName.lower()    
    self.iExpId     = iExpId
    self.iCleanType = iCleanType
    self.iStation   = iStation

  def run(self):    
        
    if not self.dictExpToHosts.has_key(self.sExpType):
      print "Invalid Experiment Type: %s" % self.sExpType
      return False

    if not self.switchUser():
      return False
      
    cwd = os.getcwd()

    lHosts      = self.dictExpToHosts[self.sExpType]
    for (iHost,sHost) in enumerate(lHosts):      
      print "# %s:" % sHost
      if self.iExpId == -1:
        sCmd = ('/usr/bin/ssh -x -o ConnectTimeout=%d %s ' + \
                '"cd %s;source env_xtcclean.bash;./xtccleanLocal.py -r -t %s -a"') % \
                (self.iConnectTimeOut, sHost, cwd, self.sExpType)              
      else:
        sCmd = ('/usr/bin/ssh -x -o ConnectTimeout=%d %s ' + \
                '"cd %s;source env_xtcclean.bash;./xtccleanLocal.py -r -t %s -n %s -e %d"') % \
                (self.iConnectTimeOut, sHost, cwd, self.sExpType, self.sExpName, self.iExpId)              
      os.system(sCmd)
                
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
    #if self.iExpId != 1000:
    #  print "Debug veresion, please specify exp id 1000"
    #  return True
    
    for (iHost,sHost) in enumerate(lHosts):      
      print "# %s:" % sHost
      sCmd = ('/usr/bin/ssh -x -o ConnectTimeout=%d %s ' + \
        '"cd %s;source env_xtcclean.bash;./xtccleanLocal.py -r -t %s -e %d --force"') % \
                (self.iConnectTimeOut, sHost, cwd, self.sExpType, self.iExpId)              
      os.system(sCmd)    
        
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

#
# getCurrentExperiment
#
# This function returns the current experiment ID from the
# offline database based on the instrument (AMO, SXR, CXI:0, CXI:1, etc.)
#
# RETURNS:  Two values:  experiment number, experiment name
#

def getCurrentExperiment(exp, cmd, station):

    exp_id = int(-1)
    exp_name = ''

    if (cmd):
      returnCode = 0
      fullCommand = '%s %s:%u' % (cmd, exp.upper(), station)
      p = subprocess.Popen([fullCommand],
                           shell = True,
                           stdin = subprocess.PIPE,
                           stdout = subprocess.PIPE,
                           stderr = subprocess.PIPE,
                           close_fds = True)
      out, err = subprocess.Popen.communicate(p)
      if (p.returncode):
        returnCode = p.returncode
     
      if len(err) == 0 and len(out) != 0:
        out = out.strip()
        try:
          exp_name = out.split()[1]
          exp_id = int(out.split()[2])
        except:
          exp_id = int(-1)
          exp_name = ''
          err = 'failed to parse \"%s\"' % out

      if returnCode != 0:
        print "Unable to get current experiment ID"
        if len(err) != 0:
          print "Error from '%s': %s" % (fullCommand, err)
        exp_id = int(-1)
        exp_name = ''

    return (int(exp_id), exp_name)


def showUsage():
  print( """\
Usage: %s [-t | --type <Experiment Type>]* [-e | --exp  <Experiment Id>]*
  [-c|--clean] [--force] [-v] [-h]

  -t | --type       <Experiment Type>  *Set experiment type (amo, sxr, xpp, xcs, cxi, cxi:1, mec)
  -e | --exp        <Experiment Id>    Set experiment id. Default: Active experiment (from offline sql database)
  -a | --all                           Try all experiment ids. (overrides -e)
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
  # default station=0
  iStation = 0
  sExpName = ""
  bAll = False
  
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
     "t:e:acvh", \
     ["type", "exp", "all", "clean", "force", "version", "help"])
  except:
    print "*** Invalid option ***"
    showUsage()
    return 1
   
  for (sOpt, sArg) in llsOptions:
    if   sOpt in ("-t", "--type" ):
      # parse optional station number (e.g. CXI:1)
      tmplist = sArg.split(":")
      sExpType   = tmplist[0].lower()
      if len(tmplist) > 1:
        iStation = int(tmplist[1])
    elif sOpt in ("-e", "--exp" ):
      iExpId     = int(sArg)
    elif sOpt in ("-a", "--all" ):
      bAll = True
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
  if bAll:
    iExpId = -1
  elif iExpId == -1:
    print "Reading current experiment from offline database"
    (iExpId, sExpName) = getCurrentExperiment(sExpType, currentexpcmd, iStation)
    if iExpId == -1:
      print "Experiment ID Not Defined -- See Help below.\n"
      showUsage()
      return 2
    else:
      print "Using exp name %s id %d" % (sExpName, iExpId)

  xtcClean = XtcClean( sExpType, sExpName, iExpId, iCleanType, iStation)
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
