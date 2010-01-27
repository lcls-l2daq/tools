#!/bin/env python
import sys
import os
import platform
import time
import getopt
import thread
import locale
import traceback
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ProcMgr import ProcMgr, deduce_platform, key2host, key2uniqueid
import ui_procStat

__version__ = "0.3"

# OutDir Full Path Example: /reg/d/pcds/pds/s0/amo/e7/e7-r0263-s00-c00.xtc.tobedeleted
sOutDirPrefix1 = "/reg/d/pcds/pds/"
sOutFileExtension = ""
bProcMgrThreadError = False
sErrorOutDirNotExist = "Output Dir Not Exist"

class CustomIOError(Exception):
  pass

def getOutputFileName(iExperiment, sExpType):
  if iExperiment < 0:
    return []
    
  sExpSubDir = "e%d" % (iExperiment)
  
  lsMostRecentOutputFile = []  
  
  if not os.path.isdir(sOutDirPrefix1): 
    raise CustomIOError, sErrorOutDirNotExist
      
  #refresh output file status    
  lsSrcDirs = os.listdir( sOutDirPrefix1 )
  for sSrcDir in lsSrcDirs:

    sExpDir = os.path.join( sOutDirPrefix1, sSrcDir, sExpType, sExpSubDir )
    if not os.path.isdir(sExpDir): continue
    
    iMostRecentFileTime = -1
    sMostRecentOutputFile = ""
    
    lsOutputFiles = os.listdir( sExpDir )    
    for sOutputFile in lsOutputFiles:
    
      #if not sOutputFile.endswith(sOutFileExtension): continue
      sFilePath = os.path.join( sExpDir, sOutputFile )
      try:
        iFileTime = os.path.getmtime( sFilePath )

      except:
        # Get some exception when accessing the file
        # Possbile reasons:
        #   1. The other process is moving or renaming the file
        #   2. The file system is being disconnected      
        # Solution:
        #   Ignore this file and continue to test next one
        continue

      if iFileTime > iMostRecentFileTime:
        iMostRecentFileTime = iFileTime
        sMostRecentOutputFile = sFilePath

    if sMostRecentOutputFile != "":
      lsMostRecentOutputFile.append( sMostRecentOutputFile )
          
  return lsMostRecentOutputFile

def printStackTrace():
  print( "---- Printing program call stacks for debug ----" )
  traceback.print_exc(file=sys.stdout)
  print( "------------------------------------------------" )
  return

def procMgrThreadWrapper(sConfigFile, iExperiment, sExpType, iPlatform, fQueryInterval, evgProcMgr ):
  try:
    procMgrThread(sConfigFile, iExperiment, sExpType, iPlatform, fQueryInterval, evgProcMgr )
  except:
    sErrorReport = "procMgrThreadWrapper(): procMgrThread(ConfigFile = %s, Exp Id = %d, Exp Type = %s, Platform = %d, Query Interval = %f ) Failed" %\
     (sConfigFile, iExperiment, sExpType, iPlatform, float(fQueryInterval) )
    print( sErrorReport )
    printStackTrace()
    bProcMgrThreadError = True
    evgProcMgr.emit(SIGNAL("UnknownError"), sErrorReport ) # Send out the signal to notify the main window          
  return
  
  
def procMgrThread(sConfigFile, iExperiment, sExpType, iPlatform, fQueryInterval, evgProcMgr ):
  
  locale.setlocale( locale.LC_ALL, "" ) # set locale for printing formatted numbers later  
    
  while True:
  
    # refresh ProcMgr status
    global bProcMgrThreadError 
    
    try:
      procMgr = ProcMgr(sConfigFile, iPlatform)                   
      ldProcStatus = procMgr.getStatus()     

    except IOError:
      print( "procMgrThread(): ProcMgr(%s, %d): I/O error" % (sConfigFile, iPlatform) )
      printStackTrace()
      evgProcMgr.emit(SIGNAL("IOError"), sConfigFile, iPlatform ) # Send out the signal to notify the main window      
            
    except:
      print( "procMgrThread(): ProcMgr(%s, %d) Failed" % (sConfigFile, iPlatform) )
      printStackTrace()
      evgProcMgr.emit(SIGNAL("ProcMgrGeneralError"), sConfigFile, iPlatform ) # Send out the signal to notify the main window      

    lsFnOutputFile = []
    try:    
      lsFnOutputFile = getOutputFileName( iExperiment, sExpType )
      
    except CustomIOError:
      print( "Output directory (%s) does not exist" % (sOutDirPrefix1) )
      printStackTrace()
      evgProcMgr.emit(SIGNAL("OutputDirError"), sOutDirPrefix1 ) # Send out the signal to notify the main window      
        
    except:
      sErrorReport = "procMgrThread(): getOutputFileName() failed due to a general error, possibly caused by filesystem disconnection\n"
      print( sErrorReport )
      printStackTrace()
      evgProcMgr.emit(SIGNAL("ThreadGeneralError"), sErrorReport ) # Send out the signal to notify the main window      
      
    ldOutputFileStatus = []
        
    # refresh Output File Status
    if lsFnOutputFile != []:
      for sFnOutputFile in lsFnOutputFile:
        try:
          iFileTime = os.path.getmtime( sFnOutputFile )
          iFileSize = os.path.getsize( sFnOutputFile )
          sTimeDescription = time.asctime( time.localtime( iFileTime ) )          
        except: 
          # Get some exception when accessing the file
          # Possbile reasons:
          #   1. The other process is moving or renaming the file
          #   2. The file system is being disconnected
          continue
          
        ldOutputFileStatus.append( { "fn": sFnOutputFile, "size": locale.format("%d",iFileSize,True), "mtime": sTimeDescription } )
        
    # Send out the signal to notify the main window
    evgProcMgr.emit(SIGNAL("Updated"), ldProcStatus, ldOutputFileStatus, iExperiment, sExpType)    
    time.sleep(fQueryInterval )
      
  return
  
class WinProcStat(QMainWindow, ui_procStat.Ui_mainWindow):

  def __init__(self, evgProcMgr, parent = None):
    super(WinProcStat, self).__init__(parent)

    self.sCurKey = ""
    self.setupUi(self)
        
    # setup message box for displaying warning messages
    self.msgBox = QMessageBox( QMessageBox.Warning, "Warning", 
      "", QMessageBox.Ok, self )
    self.msgBox.setButtonText( 1, "Continue" ) # set the button label
    self.msgBox.setWindowModality(Qt.NonModal)
    
    # adjust GUI settings
    self.tableProcStat.sortItems( 0, Qt.AscendingOrder )    

    # setup signal handlers
    self.connect(evgProcMgr, SIGNAL("Updated"),             self.onProcMgrUpdated )        
    self.connect(evgProcMgr, SIGNAL("IOError"),             self.onProcMgrIOError )
    self.connect(evgProcMgr, SIGNAL("ThreadGeneralError"),  self.onThreadGeneralError )
    self.connect(evgProcMgr, SIGNAL("ProcMgrGeneralError"), self.onProcMgrGeneralError )
    self.connect(evgProcMgr, SIGNAL("OutputDirError"),      self.onProcMgrOutputDirError )
    self.connect(evgProcMgr, SIGNAL("UnknownError"),        self.onProcMgrUnknownError )

    return
    
    
  def closeEvent(self, event):
    self.msgBox.close()
    return
    
  def onProcMgrUpdated(self, ldProcStatus, ldOutputFileStatus, iExperiment, sExpType):
        
    self.statusbar.showMessage( "Refreshing ProcMgr status..." )

    self.tableProcStat.clear()
    self.tableProcStat.setSortingEnabled( False )
    self.tableProcStat.setRowCount(len(ldProcStatus))
    self.tableProcStat.setColumnCount(2)
    self.tableProcStat.setHorizontalHeaderLabels(["ID", "Status"])
        
    itemCur = None
    
    for iRow, dProcStatus in enumerate( ldProcStatus ):      

      # col 1 : UniqueID
      showId = dProcStatus["showId"]
      item = QTableWidgetItem(showId)
      item.setData(Qt.UserRole, QVariant(showId))
      self.tableProcStat.setItem(iRow, 0, item)

      if showId == self.sCurKey:
        itemCur = item      
      
      # col 2 : Status
      sStatus = dProcStatus["status"]
      item = QTableWidgetItem( sStatus  )
      if ( sStatus == ProcMgr.STATUS_NOCONNECT ):
        item.setBackgroundColor( QColor.fromRgb( 0, 0, 192 ) )
        item.setTextColor( QColor.fromRgb( 255, 255, 255 ) )
      elif ( sStatus == ProcMgr.STATUS_RUNNING ):
        item.setBackgroundColor( QColor.fromRgb( 0, 192, 0 ) )
        item.setTextColor( QColor.fromRgb( 255, 255, 255 ) )
      elif ( sStatus == ProcMgr.STATUS_SHUTDOWN ):
        item.setBackgroundColor( QColor.fromRgb( 192, 192, 0 ) )
        item.setTextColor( QColor.fromRgb( 255, 255, 255 ) )
      elif ( sStatus == ProcMgr.STATUS_ERROR ):
        item.setBackgroundColor( QColor.fromRgb( 255, 0, 0 ) )
        item.setTextColor( QColor.fromRgb( 255, 255, 255 ) )
              
      self.tableProcStat.setItem(iRow, 1, item)
      
    # end for iRow, key in enumerate( sorted(procMgr.d.iterkeys()) ):    
    
    self.tableProcStat.setColumnWidth(0,160)
    self.tableProcStat.setColumnWidth(1,80)

    self.tableProcStat.setSortingEnabled( True )
    if itemCur != None:
      self.tableProcStat.setCurrentItem( itemCur )
            
    if ldOutputFileStatus:
      sOutputStatus = ""
      for dOutputFileStatus in ldOutputFileStatus:
        sOutputStatus += """
<p><b>Filename:</b
> %s <br>
<b>Size:</b> %s Bytes <br>
<b>Last Modification Time:</b> %s
""" % ( dOutputFileStatus["fn"], dOutputFileStatus["size"], dOutputFileStatus["mtime"] )
      
      # save the scrollar positions
      hVal = self.textBrowser.horizontalScrollBar().value()
      vVal = self.textBrowser.verticalScrollBar().value()

      self.textBrowser.setHtml( sOutputStatus )

      # restore the scrollar positions
      self.textBrowser.horizontalScrollBar().setValue(hVal)
      self.textBrowser.verticalScrollBar().setValue(vVal)
    else:
      self.textBrowser.setHtml( "No output file is found for experiment type <b>%s</b> id <b>%d</b>" % (sExpType, iExperiment) )

    self.statusbar.clearMessage()    
    return

  def onProcMgrIOError(self, sConfigFile, iPlatform):
    self.showWarningWindow( "ProcMgr IO Error", 
     "<p>ProcMgr config file <b>%s</b> (platform <b>%d</b>) cannot be processed correctly, due to an IO Error.<p>" % (sConfigFile, iPlatform) +
     "<p>Please check the input file format, or specigy a new config file instead." )
    return
    
  def onProcMgrGeneralError(self, sConfigFile, iPlatform):
    self.showWarningWindow( "ProcMgr General Error", 
     "<p>ProcMgr config file <b>%s</b> (platform <b>%d</b>) cannot be processed correctly, due to a general Error.<p>" % (sConfigFile, iPlatform) +
     "<p>Please check the input file content, and the target machine status." )  
    return    

  def onProcMgrOutputDirError(self, sOutDirPrefix1):
    self.showWarningWindow( "Output Directory Does Not Exist",
     "<p>Please check if the system has access to output directory <i>%s</i>.<p>" % (sOutDirPrefix1) )
    return

  def onThreadGeneralError(self, sErrorReport):
    self.showWarningWindow( "Thread General Error", 
     "<p><i>%s</i><p>" % (sErrorReport) + 
     "<p>ProcMgr thread had a general error. Please check the log file for more details.\n")
    return
    
  def onProcMgrUnknownError(self, sErrorReport):
    QMessageBox.critical(self, "Unknown Error", 
     "<p><i>%s</i><p>" % (sErrorReport) + 
     "<p>ProcStat is not updating the process status. Please check the log file for more details.\n")
    self.close()
    return        
    
  def showWarningWindow( self, title, text ):
    self.msgBox.setWindowTitle( title )
    self.msgBox.setText( text )
    self.msgBox.show()
    return
    
  @pyqtSignature("int,int,int,int")
  def on_tableProcStat_currentCellChanged( self, iCurRow, iCurCol, iPrevRow, iPrevCol ):
    if iCurRow < 0: return

    itemCur = self.tableProcStat.item(iCurRow,0)
    if itemCur == None: return
    
    self.sCurKey = itemCur.data(Qt.UserRole).toString()
    return
  
  @pyqtSignature("")
  def on_actionOpen_triggered(self):
    sFnConfig = unicode(QFileDialog.getOpenFileName(self, \
                        "ProcMgr Config File", ".", \
                        "config files (*.cnf)" ))
    return

  @pyqtSignature("")
  def on_actionQuit_triggered(self):
    self.close()
    return
    
  @pyqtSignature("")
  def on_actionAbout_triggered(self):
    QMessageBox.about(self, "About procStat",
            """<b>ProcMgr Status Monitor</b> v %s
            <p>Copyright &copy; 2009 SLAC PCDS
            <p>This application is used to monitor procMgr status and report output file status.
            <p>Python %s - Qt %s - PyQt %s on %s""" % (
            __version__, platform.python_version(),
            QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))  
    return
    
def showUsage():
  print( """\
Usage: %s  [-e | --experiment <Experiment Id>]  [-t | --type <Experiment Type>]  [-p | --platform <Platform Id>]  [-i | --interval <ProcMgr Query Interval>]  <Config file> 
  -e | --experiment <Experiment Id>               Set experiment id (default: No id, and no output file status displayed)
  -t | --type       <Experiment Type>             Set experiment type (default: amo)
  -p | --platform   <Platform Id>                 Set platform id (default: id is deduced from config file)
  -i | --interval   <ProcMgr Query Interval>      Query interval in seconds (default: 3 seconds)
  
Program Version %s\
""" % ( __file__, __version__ ) )
  return
    
def main():
  iExperiment = -1
  sExpType = "amo"
  iPlatform = -1
  fProcmgrQueryInterval = 3.0
  
  (llsOptions, lsRemainder) = getopt.getopt(sys.argv[1:], \
   "e:t:vhp:i:", \
   ["experiment", "type", "version", "help", "platform=", "interval=" ])
   
  for (sOpt, sArg) in llsOptions:
    if sOpt in ("-e", "--experiment" ):
      iExperiment = int(sArg)
    elif sOpt in ("-t", "--type" ):
      iExperiment = sArg
    elif sOpt in ("-v", "-h", "--version", "--help" ):
      showUsage()
      return 1
    elif sOpt in ('-p', '--platform' ):
      iPlatform = int(sArg)
    elif sOpt in ('-i', '--interval' ):
      fProcmgrQueryInterval = float(sArg)        

  if len(lsRemainder) < 1:
    print( __file__ + ": Config file is not specified" )
    showUsage()
    return 1
  
  sConfigFile = lsRemainder[0]
    
  if (iPlatform < 0):
    try:
        iPlatform = deduce_platform(sConfigFile)
    except IOError:
        raise CustomIOError, "main(): I/O error while reading " +  sConfigFile     

  evgProcMgr = QObject()
          
  app = QApplication([])
  app.setOrganizationName("SLAC")
  app.setOrganizationDomain("slac.stanford.edu")
  app.setApplicationName("procStat")
  win = WinProcStat( evgProcMgr )
  win.show()  
  
  thread.start_new_thread( procMgrThreadWrapper, (sConfigFile, iExperiment, sExpType, iPlatform, fProcmgrQueryInterval, evgProcMgr) )  
  
  app.exec_()  
      
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
