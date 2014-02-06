#! /usr/bin/python

import os
import re
import time
import sys
import traceback
import getopt
import subprocess
import socket
from threading import Thread

HOST_NODE = {'amo':'amo-daq',
             'sxr':'sxr-daq',
             'xpp':'xpp-daq',
             'tst':'daq-tst-cam1',
             'xcs':'xcs-control',
             'cxi':'cxi-daq',
             'mec':'mec-daq',
             'det':'daq-det-pnccd1'}

AMO_NODE = 'amo-daq'
SXR_NODE = 'sxr-daq'
XPP_NODE = 'xpp-daq'
TST_NODE = 'daq-tst-cam1'
XCS_NODE = 'xcs-control'
CXI_NODE = 'cxi-daq'
MEC_NODE = 'mec-daq'
DET_NODE = 'daq-det-pnccd1'

FABIF = {'amo':'172.21.20.',
         'sxr':'172.21.21.',
         'xpp':'172.21.22.',
         'tst':'172.21.23.',
         'xcs':'172.21.25.',
         'cxi':'172.21.26.',
         'mec':'172.21.27.',
         'det':'172.21.59.'}


SUBNET = {'172.21.20.':AMO_NODE,
          '172.21.21.':SXR_NODE,
          '172.21.22.':XPP_NODE,
          '172.21.23.':TST_NODE,
          '172.21.25.':XCS_NODE,
          '172.21.26.':CXI_NODE,
          '172.21.27.':MEC_NODE,
          '172.21.59.':DET_NODE}

INSTRUMENTS = ['amo','sxr','xpp','xcs','cxi','mec','tst','det']

#================================================================================
# Usage
#================================================================================
def usage(argv):
   print """
NAME
   %s - Get hutch status for all DAQ nodes for the specified instrument
        If no instrument is specified, it will ping all DAQ nodes at LCLS

USAGE
   %s <instrument> [OPTIONS]
      <instrument> = AMO, SXR, XPP, XCS, CXI, MEC, TST, DET, ALL

EXAMPLE
   %s AMO
   %s SXR -l
   %s XPP -l -c
   %s XCS -c
   
   NOTE: The ALL argument may only be used with --list

OPTIONS:
   -l, --list
       List all nodes for instrument using list obtained from netconfig by default
       or netconfig if -n is included and cnf if -c is included
       
   -n, --netconfig
       Ping all nodes using list of DAQ nodes for instrument from netconfig (default)
       If both -n and -c options are given, --netconfig is used
       
   -c, --cnf
       Ping all nodes using list of DAQ nodes for instrument from .cnf file
       If both -n and -c options are given, --netconfig is used       

   -h, --help
       Display usage information

"""   % (argv[0],argv[0], argv[0])

#================================================================================

class pingit(Thread):
   def __init__ (self,name,subnet,ip):
      Thread.__init__(self)
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
      if (str == daq_node) or (str == control_node):
         if str.find('ioc') == -1:
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
   
def get_all_nodes_cnf():
  print "Pinging all DAQ nodes listed in instrument .cnf files" 
  
  nodelist = []

  for instrument in INSTRUMENTS:
     cnf = '/reg/g/pcds/dist/pds/'+instrument+'/scripts/'+instrument+'.cnf'
     file = open(cnf,'r')
     for line in file.readlines():
        if line.startswith('#'): continue
        if line.find('172') != -1 and line.find('=') != -1:
           line = line.strip('\n')
           node, tmp_fez_str = line.split('=')
           fez_str = tmp_fez_str.split('#')[0]
           m = fez_str.rfind('172')
           fez = fez_str[m:m+13].strip("\'")
           cds = node.replace('_','-')
           nodelist.append([node, 'CDS', cds])
           nodelist.append([node, 'FEZ', fez])
#           print "%-20s  %-20s  %-15s" % (node, cds, fez)
     file.close()

  return nodelist


def get_nodes_cnf(instrument):
  print "Pinging DAQ nodes listed in %s.cnf file" % (instrument.lower()) 
  
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
      nodelist.append([node, 'CDS', cds])
      nodelist.append([node, 'FEZ', fez])

  return nodelist

def send_cmd(cmd):
   p = subprocess.Popen([cmd],
                        shell  = True,
                        stdin  = subprocess.PIPE,
                        stdout = subprocess.PIPE, 
                        stderr = subprocess.PIPE, 
                        close_fds = True)
  
   out, err = subprocess.Popen.communicate(p)
   return out, err

   
def get_all_nodes_netconfig():
  print "Pinging all DAQ nodes listed in netconfig"

  cmdlist = ["netconfig search \"daq*\"",
             "netconfig search \"amocpci*\""]
  nodelist = []

  # Send netconfig search commands
  for cmd in cmdlist:
     out, err = send_cmd(cmd)

     # Process result of netconfig search
     if len(err) == 0 and len (out) != 0:
        found_host = 0
        found_ip = 0
        for entry in out.split('\n'):
	
           # DAQ nodes - find hostname
           if found_daq_node(entry):
              if found_host == 1:
                 print "ERROR:  Found hostname (%s) without encountering IP field" % entry
              node = entry.split(':')[0].strip()
              found_host = 1

           # Once hostname is known, look for IP
           if found_host == 1 and entry.startswith('	IP:'):
              ip = entry.split(':')[1].strip()
              found_ip = 1
	
           # Add DAQ hostname and ip to nodelist
           if found_host == 1 and found_ip == 1:
              instrument = get_instrument(node)

              # Only DAQ nodes have a FEZ
              if (node.startswith('daq') or node.startswith('amocpci') or found_daq_or_control(node)):
                 nodelist.append([node, 'CDS', ip])
                 if instrument != 'tst':
                    ip_fez = get_fez(instrument, ip)
                    nodelist.append([node, 'FEZ', ip_fez])
              # XRT nodes, for example, have no FEZ
              else:
                 nodelist.append([node, 'CDS', ip])
                 
              # Once node and ips are added, re-initialize variables
              found_host = 0
              found_ip = 0
           else:
              continue

  return nodelist



def get_nodes_netconfig(instrument):
  print "Pinging DAQ nodes listed in netconfig for %s" % (instrument.upper())

  cmd = "netconfig search \"*%s*\"" % (instrument)
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
           node = entry.split(':')[0].strip()
           found_host = 1

        # Once hostname is known, look for IP
        if found_host == 1 and entry.startswith('	IP:'):
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

def pingall(nodes):
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
      print "%-20s   %-20s (%-3s)      %-20s %s" % (ping.name,
                                                    ping.ip,
                                                    ping.subnet,
                                                    report[ping.status],
                                                    time.ctime())

#================================================================================
# main
#================================================================================
if __name__ == '__main__':
   if len(sys.argv) < 2:
      usage(sys.argv)
      sys.exit(1)
   else:
      instrument = sys.argv[1].lower()

   try:
      opts, args = getopt.getopt(sys.argv[2:],'nclh',
                                 ['netconfig', 'cnf', 'list', 'help'])
   except getopt.GetoptError,e:
      print e
      usage(sys.argv)
      sys.exit(1)

   cnf = False
   netconfig = False
   listnodes = False

   # Parse arguments
   for o, a in opts:
      if o in ('-h', '--help'):
         usage(sys.argv)
         sys.exit(1)
      if o in ('-c', '--cnf'):
         cnf = True
      if o in ('-n', '--netconfig'):
         netconfig = True
         cnf = False
      if o in ('-l', '--list'):
         listnodes = True

   if cnf == False and netconfig == False:
      netconfig = True


   # Get list of nodes
   if instrument != 'all':
      if instrument not in INSTRUMENTS:
         print "ERROR:  Invalid instrument name %s" % (instrument)
         usage(sys.argv)
         sys.exit(1)
      if netconfig:
         nodes = get_nodes_netconfig(instrument)
      else:
         nodes = get_nodes_cnf(instrument)

   if listnodes is True:
      if instrument == 'all':
         if netconfig:
            nodes = get_all_nodes_netconfig()
         else:
            nodes = get_all_nodes_cnf()
         for node in nodes:
            if node[1] is 'CDS': print node[0]
         sys.exit(0)
      else:
         for node in nodes:
            if node[1] is 'CDS':  print node[0]
         sys.exit(0)

   try:
      host = socket.gethostname()
      if instrument != 'all':
         if (host.find(instrument) == -1):
            print "ERROR:  Must run script from node on %s subnet. Try %s."%(instrument.upper(),HOST_NODE[instrument])
         else:
            pingall(nodes)
      else:
         for instr in INSTRUMENTS:
            print "ERROR:  Must run script from node on %s subnet.  Try %s for %s."%(instr.upper(), HOST_NODE[instr], instr.upper())
   except:
      traceback.print_exc(file=sys.stdout)
      sys.exit(1)


      


      





