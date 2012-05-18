#!/bin/env python

import sys
import os
import glob
import platform
import time
import getopt
import thread
import locale
import traceback
import subprocess
import psdm.file_status as file_status

__version__ = "0.4"

class XtcCleanLocal:
  # static data
  dictExp = { "amo":1, "sxr":1, "xpp":1, "cxi":1, "xcs":1, "mec":1 }
  iConnectTimeOut = 3
    
  def __init__(self, sExpType, iExpId, iCleanType, bRemote):
    self.sExpType   = sExpType.lower()    
    self.iExpId     = iExpId
    self.iCleanType = iCleanType
    self.bRemote    = bRemote

  def run(self):    
        
    if not self.dictExp.has_key(self.sExpType):
      print "Invalid Experiment Type: %s" % self.sExpType
      return False

    if not self.checkUser():
      return False

    if not self.bRemote:
      print "Searching for xtc files..."
    path = "/u2/pcds/pds/%s/e%d" % (self.sExpType, self.iExpId)
    self.run_path(path, self.iExpId)
      
  def filter_fileStatus(self, triplet,status):  
    if  ( file_status.IN_MIGRATION_DATABASE in status.flags() ) and \
        ( file_status.DISK                  in status.flags() ) and \
        ( file_status.HPSS                  in status.flags() ):                
      return True
      
    print """
  ----------+-----------+---------------------------+-----------------------+---------+---------
   exper_id | file type | file name                 | IN MIGRATION DATABASE | ON DISK | ON HPSS
  ----------+-----------+---------------------------+-----------------------+---------+---------"""
      
    print "   %8d | %9s | %25s |         %5s         |  %5s  |  %5s" % \
      ( int(triplet[0]),triplet[1],triplet[2],
        str(file_status.IN_MIGRATION_DATABASE in status.flags()),
        str(file_status.DISK in status.flags()),
        str(file_status.HPSS in status.flags())\
      )
    return False
  
  def run_path(self, path, expid):
    try:
      os.chdir(path)
      lFiles = glob.glob('*xtc')      
    except:
      lFiles = []
    
    if (len(lFiles) == 0):
      if not self.bRemote:
        print "No xtc files found in %s. Please verify the experiment type and id." % (path)
      return True
              
    if not self.bRemote:
      print "Found %d Files in %s" % (len(lFiles), path)      
      print "  First File: " + lFiles[0]
      print "              ............................"
      print "   Last File: " + lFiles[-1] + "\n"
    
    lXtcStatusQuery = []
    for sFile in lFiles:
      lXtcStatusQuery.append( (expid, 'xtc', sFile) )      
      
    fs = file_status.file_status(ws_login_user='psdm_reader', ws_login_password='pcds')
    lFilterdQuery = fs.filter(lXtcStatusQuery, self.filter_fileStatus)
    
    lDelFiles = []
    for triplet in lFilterdQuery:
      lDelFiles.append(triplet[2])

    if not (self.bRemote and self.iCleanType != 0):      
      print "Found %d Files to be deleted in %s" % (len(lDelFiles), path)      
      print "  First File: " + lDelFiles[0]
      print "              ............................"
      print "   Last File: " + lDelFiles[-1] + "\n"
      
    if self.iCleanType == 0 or self.iCleanType > 2:
      if not self.bRemote:
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
      
    iDelNo        = self.getDelNo(path)
    sFnDelList    = "deletedlist%02d.txt" % (iDelNo)
    print "Generating Delete List %s" % (sFnDelList)
    
    iNumXtcFilesDeleted = 0
    for sFnDel in lDelFiles:
      iFail = os.system( "/bin/ls -l %s >> %s 2>&1" % (sFnDel, sFnDelList) )
      if iFail != 0:
        print "ls failed for xtc file %s" % sFnDel
        continue           

      iFail = os.system( "/bin/rm -v %s >> %s 2>&1" % (sFnDel, sFnDelList) )
      if iFail != 0:
        print "rm failed for xtc file %s" % sFnDel
        continue
        
      iNumXtcFilesDeleted += 1

    iNumIdxFilesDeleted = 0
    for sFnDel in lDelFiles:        
      iFail = os.system( "/bin/ls -l index/%s.idx >> %s 2>&1" % (sFnDel, sFnDelList) )
      if iFail != 0:
        print "ls failed for index file index/%s.idx" % sFnDel
        continue
        
      iFail = os.system( "/bin/rm -v index/%s.idx >> %s 2>&1" % (sFnDel, sFnDelList) )
      if iFail != 0:
        print "rm failed for index file index/%s.idx" % sFnDel
        continue
        
      iNumIdxFilesDeleted += 1
               
    if iNumXtcFilesDeleted != len(lDelFiles):
      print "Error: Expected to delete %d xtc files, but in reality %d files deleted" %\
        ( len(lDelFiles), iNumXtcFilesDeleted )
    else:
      print "%d xtc files deleted" % (iNumXtcFilesDeleted)

    if iNumIdxFilesDeleted != len(lDelFiles):
      print "Error: Expected to delete %d index files, but in reality %d files deleted" %\
        ( len(lDelFiles), iNumIdxFilesDeleted )
    else:
      print "%d index files deleted" % (iNumIdxFilesDeleted)
      
  def getDelNo(self, path):
    try:
      lDelFiles     = glob.glob(path + '/deleted*.txt')    
      iTestDelNo    = len(lDelFiles)    
    except:
      iTestDelNo    = 0
    while True:
      if not os.path.isfile( path + '/deletedlist%02d.txt' % (iTestDelNo)):
        break
      iTestDelNo += 1
   
    return iTestDelNo    
  
  def checkUser(self):
    sUserName = self.sExpType + "opr"
    iId       = int(os.popen( "/usr/bin/id -u " + sUserName ).read().strip())
    
    if os.geteuid() != iId:
      print "You need to become %s to run this script." % (sUserName)
      return False    

    return True

#
# getCurrentExperiment
#
# This function returns the current experiment ID from the
# offline database based on the experiment (AMO, SXR, XPP, etc.)
#
# RETURNS:  Two values:  experiment number, experiment name
#

def getCurrentExperiment(exp):

    exp = exp.upper()
    exp_id = -1
    exp_name = ''
    
    # Issue mysql command to get experiment ID
    mysqlcmd = 'echo "select exper_id from expswitch WHERE exper_id IN ( SELECT experiment.id FROM experiment, instrument WHERE experiment.instr_id=instrument.id AND instrument.name=\''+exp+'\' ) ORDER BY switch_time DESC LIMIT 1" | /usr/bin/mysql -N -h psdb -u regdb_reader regdb'

    p = subprocess.Popen([mysqlcmd],
                         shell = True,
                         stdin = subprocess.PIPE,
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds = True)
    out, err = subprocess.Popen.communicate(p)

    if len(err) == 0 and len(out) != 0:
        exp_id = out.strip()
    else:
        if len(err) != 0: print "Unable to get current experiment ID from offline database: ", err
        if len(out) == 0: print "No current experiment ID in offline database for experiment", exp
        print "Try using -e | --exp option"
        return (int(exp_id), exp_name)

    # Issue mysql command to get experiment name
    mysqlcmd = 'echo "SELECT name FROM experiment WHERE experiment.id='+exp_id+'" | mysql -N -h psdb -u regdb_reader regdb'

    p = subprocess.Popen([mysqlcmd],
                         shell = True,
                         stdin = subprocess.PIPE,
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds = True)
    out, err = subprocess.Popen.communicate(p)
    
    if len(err) == 0:
        exp_name = out.strip()
    else:
        print "Unable to get current experiment name from offline database: ", err

    return (int(exp_id), exp_name)




def showUsage():
  print( """\
Usage: %s [-t | --type <Experiment Type>]* [-e | --exp <Experiment Id>]* 
  [-c|--clean] [--force] [-r | --remote] [-v] [-h]

  -t | --type       <Experiment Type>  *Set experiment type (amo, sxr, xpp, xcs, cxi, mec)
  -e | --exp        <Experiment Id>    Set experiment id. Default: Active experiment (from offline sql database)
  -c | --clean                         Execute the real clean-up, with yes/no prompt
  -r | --remote                        To be called from remote machine. Suppress some extra outputs.
       --force                         Force the real clean-up, without yes/no prompt

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
  bRemote  = False
  
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
     "t:e:rcvh", \
     ["type", "exp", "clean", "force", "remote", "version", "help"])
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
    elif sOpt in ("-r", "--remote" ):
      bRemote    = True
    elif sOpt in ("-v", "-h", "--version", "--help" ):
      showUsage()
      return 1

  if sExpType == "":
    print "Experiment Type Not Defined -- See Help below.\n"
    showUsage()
    return 2
  if iExpId == -1:
    print "Reading current experiment from offline database"
    (iExpId, sExpName) = getCurrentExperiment(sExpType)
    if iExpId == -1:
      print "Experiment ID Not Defined -- See Help below.\n"
      showUsage()
      return 2
    else:
      print "Using exp name %s id %d" % (sExpName, iExpId)

  xtcCleanLocal = XtcCleanLocal( sExpType, iExpId, iCleanType, bRemote )
  xtcCleanLocal.run()
  
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
    #showUsage()
    
  sys.exit(iRet)
