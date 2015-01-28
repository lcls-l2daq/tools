#! /usr/bin/python

import os
import re
import time
import sys
import traceback
import getopt
import subprocess
import socket
import threading
import datetime


HOST_NODE = {'amo':'amo-daq',
             'sxr':'sxr-daq',
             'xpp':'xpp-daq',
             'tst':'daq-tst-cam1',
             'xcs':'xcs-control',
             'cxi':'cxi-daq',
             'mec':'mec-daq'}

AMO_NODE = 'amo-daq'
SXR_NODE = 'sxr-daq'
XPP_NODE = 'xpp-daq'
TST_NODE = 'daq-tst-cam1'
XCS_NODE = 'xcs-control'
CXI_NODE = 'cxi-daq'
MEC_NODE = 'mec-daq'

FABIF = {'amo':'172.21.20.',
         'sxr':'172.21.21.',
         'xpp':'172.21.22.',
         'tst':'172.21.23.',
         'xcs':'172.21.25.',
         'cxi':'172.21.26.',
         'mec':'172.21.27.'}


SUBNET = {'172.21.20.':AMO_NODE,
          '172.21.21.':SXR_NODE,
          '172.21.22.':XPP_NODE,
          '172.21.23.':TST_NODE,
          '172.21.25.':XCS_NODE,
          '172.21.26.':CXI_NODE,
          '172.21.27.':MEC_NODE}

INSTRUMENTS = ['amo','sxr','xpp','xcs','cxi','mec','tst']

SUCCESS = 0
FAIL = 1

PINGREPORT = ['*','*','-','!']

PROCMGRDREPORT = ['*','?']

OFFLINE_PATH = "/reg/g/pcds/dist/pds/"


#==============================================================================
def usage(argv):
#==============================================================================   
   print """
NAME
   %s - Get hutch status for all DAQ nodes for the specified instrument:
                        CDS/FEZ interfaces status
                        procmgrd[0-4] status
                        syscntl parameter status for event levels:  rmem_max, wmem_max, mqueue.msg_max
                        disk usage status for event levels


USAGE
   %s <instrument> [OPTIONS]
      <instrument> = AMO, SXR, XPP, XCS, CXI, MEC, TST
      
EXAMPLE
   %s AMO

OPTIONS:
   -n, --netconfig
       Get node status using list of DAQ nodes for instrument from netconfig (default)
       If both -n and -c options are given, --netconfig is used
       
   -c, --cnf
       Get node status using list of DAQ nodes for instrument from .cnf file
       If both -n and -c options are given, --netconfig is used

   -v, --verbose
       Include a legend to decode the output, which is intended to be concise.
       This is how to interpret the output:
       
          CDS/FEZ status:
             - is OK
             * is NOT OK or NOT AVAILABLE
          procmgrd status:
             - is OK
             * is NOT OK or NOT AVAILABLE
             ! means version is not procServ-2.5.1
          Event level status:
             ? means information is not available
             0 for disk usage and sysctl parameters implies that ssh failed

   -h, --help
       Display usage information

"""   % (argv[0],argv[0], argv[0])


def legend():
   print "-------------------------------------------"
   print "CDS/FEZ status:"
   print "   - is OK"
   print "   * is NOT OK or NOT AVAILABLE"
   print "procmgrd status:"
   print "   - is OK"
   print "   * is NOT OK or NOT AVAILABLE"
   print "   ! means version is not procServ-2.5.1"
   print "Event level status:"
   print "   ? means information is not available"
   print "   Values of 0 for disk usage and sysctl imply that ssh failed"
   print "-------------------------------------------"


#==============================================================================
# Generic commanding
#==============================================================================

def command(host, cmd):
   process = subprocess.Popen(["/usr/bin/ssh -o StrictHostKeyChecking=no ", "%s"%host, cmd],
                              shell  = True,
                              stdin  = subprocess.PIPE,
                              stdout = subprocess.PIPE, 
                              stderr = subprocess.PIPE,
                              close_fds = True)
   out, err = subprocess.Popen.communicate(process)
   return out, err

def send_cmd(cmd):
   p = subprocess.Popen([cmd],
                        shell  = True,
                        stdin  = subprocess.PIPE,
                        stdout = subprocess.PIPE, 
                        stderr = subprocess.PIPE, 
                        close_fds = True)
  
   out, err = subprocess.Popen.communicate(p)
   return out, err

   
#==============================================================================
# Threaded ping utilities
#==============================================================================
class pingit(threading.Thread):
   def __init__ (self,name,subnet,ip):
      threading.Thread.__init__(self)
      self.name = name
      self.subnet = subnet
      self.ip = ip
      self.status = -1
   def run(self):
      ping = os.popen("ping -q -c2 "+self.ip,"r")
      while 1:
         line = ping.readline()
         if not line: break
         igot = re.findall(pingit.heartbeat,line)
         if igot:
            self.status = int(igot[0])

def pingall(nodes):
   ping_result = {}
   pingit.heartbeat = re.compile(r"(\d) received")
   report = ("No response","Partial Response","OK")
   pinglist = []

   print "Pinging from %s" % socket.gethostname()

   for node in nodes:
      name, subnet, ip = node
      current = pingit(name, subnet, ip)
      pinglist.append(current)
      current.start()

   for ping in pinglist:
      ping.join()
      if ping_result.has_key(ping.name):
         if ping.subnet == 'CDS': ping_result[ping.name][0] = ping.status
         if ping.subnet == 'FEZ': ping_result[ping.name][1] = ping.status
      else:
         ping_result[ping.name] = [-1,-1]
         if ping.subnet == 'CDS': ping_result[ping.name][0] = ping.status
         if ping.subnet == 'FEZ': ping_result[ping.name][1] = ping.status
   return ping_result
         
def do_ping(instrument, node_ips):
   # Start pinging
   host = socket.gethostname()
   if host.find(instrument) == -1:
      print "ERROR:  Cannot ping nodes from %s.  Try running script from %s."%(host,HOST_NODE[instrument])
      return 0
   else:
      result = pingall(node_ips)
   return result


  
#==============================================================================
# Utilities for getting list of DAQ nodes associated with instrument
# from either netconfig or cnf file
#==============================================================================
def found_ipmi(str):
   retval = False
   if str.find('ipmi') == -1: retval = False
   else: retval = True
   return retval

def found_instr(str):
   retval = False
   for instr in INSTRUMENTS:
      if str.find(instr) == -1:  retval = False
      else:
         retval = True
         return retval
   return retval

def found_daq_or_control(str):
   retval = False
   for instr in INSTRUMENTS:
      daq_node = "%s-daq" % instr
      control_node = "%s-control" % instr
      if (str.startswith(daq_node) or str.startswith(control_node)):
         retval = True
         return retval
      if instr == "xpp":
         console_node = "%s-console" % instr
         if str.startswith(console_node):
            retval = True
            return retval
   return retval

def found_daq_node(str):
   retval = False
   if found_ipmi(str):
      retval = False
      return retval
   else:
      if str.startswith('daq') or str.startswith('amocpci'):
         retval = True
         return retval
      else:
         if found_daq_or_control(str):
            retval = True
            return retval
   return retval

def is_dss(str):
   retval = False
   if str.find('-dss') != -1:
      retval=True
      return retval
   return retval

def is_mon(str):
   retval = False
   if str.find('-mon') != -1:
      retval=True
      return retval
   return retval

def get_nodes_cnf(instrument):
  nodelist = []
  
  cnf = '/reg/g/pcds/dist/pds/'+instrument+'/scripts/'+instrument+'.cnf'
  file = open(cnf,'r')
  for line in file.readlines():
    if line.startswith('#'): continue
    if line.find('172') != -1 and line.find('=') != -1:
      line = line.strip('\n')
      node, tmp_fez_str = line.split('=')
      fez_str = tmp_fez_str.split('#')[0]
      m = fez_str.rfind('172')
      fez = fez_str[m:].strip().strip("\'")
      cds = node.replace('_','-')
      node = node.replace('_','-')
      nodelist.append([node, 'CDS', cds])
      nodelist.append([node, 'FEZ', fez])

  return nodelist

def get_nodes_netconfig(instrument):
  cmd = "/reg/common/tools/bin/netconfig search \"*%s*\"" % (instrument)
  nodelist = []

  # Send netconfig search command
  out, err = send_cmd(cmd)

  # Process result of netconfig search
  if len(err) == 0 and len (out) != 0:
     found_host = 0
     found_ip = 0
     
     for entry in out.split('\n'):
        
        # Find the DAQ nodes
        if found_daq_node(entry):
           if found_host == 1:
              print "ERROR parsing netconfig:  Found host (%-21s) without encountering IP field" % (entry)
              return
           node = entry.split(':')[0].strip()
           found_host = 1

        # Once hostname is known, look for IP
        if found_host == 1 and entry.startswith('	IP:'):
#        if found_host == 1 and entry.find('IP:') != -1:
           ip = entry.split(':')[1].strip()
           found_ip = 1

        # Add DAQ hostname and ip to nodelist
        if found_host == 1 and found_ip == 1:
           nodelist.append([node, 'CDS', ip])
           # Only DAQ nodes have a FEZ
           if node.startswith('daq') or node.startswith('amocpci') or found_daq_or_control(node):
              ip_fez = get_fez(instrument, ip)
              nodelist.append([node, 'FEZ', ip_fez])

           # Once node and ips are entered into nodelist, reset variables 
           found_host = 0
           found_ip = 0
        else:
           continue

  return nodelist

def get_fez(instr, ip):
  return FABIF[instr] + ip.split('.')[3]

def get_instrument(node):
   for instrument in INSTRUMENTS:
      if node.find(instrument) != -1:
         return instrument
   return 'null'

def get_experiment(daq, instr):
   ins = 'Unknown'
   expname = 'Unknown'
   expnum = ' '
   cmd = "/reg/g/pcds/dist/pds/"+daq+"/build/pdsapp/bin/i386-linux-opt/currentexp "+instr.upper()
   out, err = send_cmd(cmd)
   if (len(err) == 0) and len(out) != 0:
      exp = out.split()
      if len(exp) == 3:
         ins     = exp[0]
         expname = exp[1]
         expnum  = exp[2]
   return ins, expname, expnum

#==============================================================================
# Current DAQ release links
#==============================================================================
def get_hutch_current_daq(instr):
   release = " "
   cmd = 'ls -lrt ' + OFFLINE_PATH  + instr + '/current'
   out, err = send_cmd(cmd)
   if len(err) == 0 and len(out) != 0:
      for line in out.split('\n'):
         line = line.split()
         if len(line) != 0:
            release = line[len(line)-1]
            release = release.lstrip("../")
   return release

def get_hutch_current_ami(instr):
   release = " "
   cmd = 'ls -lrt ' + OFFLINE_PATH  + instr + '/ami-current'
   out, err = send_cmd(cmd)
   if len(err) == 0 and len(out) != 0:
      for line in out.split('\n'):
         line = line.split()
         if len(line) != 0:
            release = line[len(line)-1]
            release = release.lstrip("../")
   return release

def get_latest_ami():
   dirlist = []
   releases = []
   dirlist += os.listdir(OFFLINE_PATH)
   for dir in dirlist:
      if re.search('^ami-(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()
   
def get_latest_daq():
   dirlist = []
   releases = []
   
   dirlist += os.listdir(OFFLINE_PATH)
   for dir in dirlist:
      if re.search('^(?:(\d+)\.)?(?:(\d+)\.)?(\*|\d+)', dir):
         releases.append(dir)
   return releases.pop()



#==============================================================================
# Get event level info
#==============================================================================
def get_disk_usage(node):
   status = FAIL
   size = 0
   used = 0
   avail = 0
   usepct = 0
   cmd = "/usr/bin/ssh -o StrictHostKeyChecking=no %s df -h | grep u2"% (node)
   out, err = send_cmd(cmd)
   if len(err) == 0 and len (out) != 0:
      for line in out.split('\n'):
         line = line.split()
         if len(line) == 6 and line[5].find('u2') != -1:
            status = SUCCESS
            size = line[1]
            used = line[2]
            avail = line[3]
            usepct = line[4]
            mnt = line[5]
            return status, size, used, avail, usepct
   return status, size, used, avail, usepct

def get_sysctl(node):
   status = FAIL
   rbytes = 0
   wbytes = 0
   msg_max = 0
   cmd = "/usr/bin/ssh -o StrictHostKeyChecking=no %s /sbin/sysctl net.core.rmem_max net.core.wmem_max fs.mqueue.msg_max"% (node)
   out, err = send_cmd(cmd)
   if len(err) == 0 and len (out) != 0:
      status = SUCCESS
      for line in out.split('\n'):
         line = line.split()
         if len(line) == 3 and line[0].find('rmem_max') != -1:
            rbytes = int(line[2])
         elif len(line) == 3 and line[0].find('wmem_max') != -1:
            wbytes = int(line[2])
         elif len(line) == 3 and line[0].find('msg_max') != -1:
            msg_max = int(line[2])

   return status, rbytes, wbytes, msg_max

#==============================================================================
# Get procmgrd info
#==============================================================================   
def get_procmgrd_info(node):
   procmgr_info = {}
   status = FAIL
   cmd = "ssh -o StrictHostKeyChecking=no jana@%s ps -ef | grep procmgr"% (node)
   out, err = send_cmd(cmd)
   for line in out.split('\n'):
      line = line.split()
      if len(line) == 20:
         procmgrd, ver, user = parse_ps_procmgr(line)
         if procmgr_info.has_key(procmgrd):
            print "ERROR - More than one %s found!" % (procmgrd)
         else:
            status = SUCCESS
            dnum = int(procmgrd.strip('procmgrd'))
            procmgr_info[dnum] = [ver, user]
   return status, procmgr_info

def parse_ps_procmgr(line):
   procmgrd = 0
   srv_version = 0

   user = line[0]
   pid = line[1]
   progname = line[7]
   port = line[12]

   progname = progname.split('/')
   srv_version = progname[5].strip('procServ-')
   procmgrd = progname[6]
   
   return procmgrd, srv_version, user

#==============================================================================
# Print summary
#==============================================================================   
def summarize(instrument, result):
   if result == 0: return
   event_level_report = []
   opr = "%sopr" % instrument
   header = "%-22s  %-4s %-8s\n%-22s  %-4s %-8s" % (" ", "CDS/","procmgrd",\
                                                            "Segment Level","FEZ"," [0-4]  ")
   print (len(header)+4)*"-","\n",  header, "\n", (len(header)+4)*"-"
   for node, pingstat in sorted(result.iteritems()):
      str = "%-22s  %1s%1s    " % (node, PINGREPORT[pingstat[0]], PINGREPORT[pingstat[1]])
      procmgr_status, procmgr_info = get_procmgrd_info(node)
      for procmgrd in range(5):
         if procmgr_info.has_key(procmgrd):
            if procmgr_info[procmgrd][1] == opr:
               if procmgr_info[procmgrd][0] == "2.5.1":
                  str += "%1s" % '-'
               else:
                  str += "%1s" % '!'
            else:  str += "%1s" % '*'
         else:  str += "%1s" % '*'
      if is_dss(node) or is_mon(node):
         df_status, size, used, avail, usepct = get_disk_usage(node)
         sysctl_status, rbytes, wbytes, msg_max = get_sysctl(node)
         procmgr_status, procmgr_info = get_procmgrd_info(node)
         str += "%+6s/%-6s %5s" % (rbytes/1024/1024, wbytes/1024/1024, msg_max)
         if is_dss(node):
            str += "%5s/%-5s (%5s) " % (used, size, usepct)
         event_level_report.append(str)
      else:
         print str
   print "%s" % (100*"-")
   print "%-22s %-4s %-8s %-8s %7s  %-9s %+8s" % \
         (" ",
          "CDS/ ",
          "procmgrd",
          "[r|w]mem",
          " ",
          "used/",
          " ")
   print "%-22s %-4s %-8s %-8s %7s  %-9s %+8s" % \
         ("Event Level",
          "FEZ",
          "  [0-4]  ",
          "  (MB) ",
          "msg_max",
          "avail",
          "(% used)")
   print "%s" % (100*"-")
   for entry in event_level_report:  print entry
   
#==============================================================================
def HutchStatus():
#==============================================================================
   # Set some reasonable defaults
   cnf = False
   netconfig = False
   verbose = False

   # Get command-line arguments
   if len(sys.argv) < 2:
      usage(sys.argv)
      print "ERROR: Not enough arguments.  Please provide instrument name (AMO,SXR,XPP,XCS,CXI,MEC,TST)"
      sys.exit(1)
   else:
      instrument = sys.argv[1].lower()

   # Make sure instrumet name is valid
   if instrument not in INSTRUMENTS:
      print "ERROR:  Invalid instrument name %s" % (instrument)
      usage(sys.argv)
      sys.exit(1)

   # Parse arguments
   try:
      opts, args = getopt.getopt(sys.argv[2:],'ncvh',
                                 ['netconfig', 'cnf', 'verbose', 'help'])
   except getopt.GetoptError,e:
      print e
      usage(sys.argv)
      sys.exit(1)

   for o, a in opts:
      if o in ('-h', '--help'):
         usage(sys.argv)
         sys.exit(1)
      if o in ('-c', '--cnf'):
         cnf = True
      if o in ('-n', '--netconfig'):
         netconfig = True
         cnf = False
      if o in ('-v', '--verbose'):
         verbose = True
      
   if cnf == False and netconfig == False:
      netconfig = True

   # Get list of nodes
   node_ips = []
   if netconfig: node_ips = get_nodes_netconfig(instrument)
   if cnf: node_ips = get_nodes_cnf(instrument)

   # Get latest DAQ release in /reg/g/pcds/dist/pds/
   daq = get_latest_daq()
   ami = get_latest_ami()

   # List DAQ and AMI release that this hutch's current links are pointing to
   current_daq = get_hutch_current_daq(instrument)
   current_ami = get_hutch_current_ami(instrument)

   # Get experiment name and number
   instname, expname, expnum = get_experiment(current_daq, instrument)

   # Print header info
   print "\n================================ %s ================================" % (instrument.upper())
   ts = datetime.datetime.now()
   print "Date:    %s" % (ts.strftime("%Y-%m-%d %H:%M:%S"))
   print "Instrument:  %s" % (instname)
   print "Experiment: %s (#%s)"%(expname, expnum)
   print "Current DAQ: %-20s (%3s) \t%-20s (DAQ latest)" % (current_daq, instrument.upper(), daq)   
   print "Current AMI: %-20s (%3s) \t%-20s (AMI latest)\n" % (current_ami, instrument.upper(), ami)   

   # Ping all nodes for this hutch
   result = {}
   result = do_ping(instrument, node_ips)
   
   # Summarize
   summarize(instrument, result)

   if verbose:  legend()

#==============================================================================
if __name__ == '__main__':
   HutchStatus()
#==============================================================================   


      


      





