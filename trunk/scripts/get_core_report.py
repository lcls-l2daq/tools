#!/reg/common/package/python/2.7.5/x86_64-rhel6-gcc44-opt/bin/python
import os, sys, shutil
import getopt
import subprocess
import datetime, time
import glob
from operator import itemgetter

INSTRUMENTS = ['amo','sxr','xpp','xcs','cxi','mec']

NODES = {"amo":["amocpci01",
                "amocpci02",
                "daq-amo-gd",
                "amocpci04",
                "daq-amo-cpci05",
                "daq-amo-cpci07",
                "daq-amo-cpci11",
                "daq-amo-cam01",
                "daq-amo-cam02",
                "daq-amo-dss01",
                "daq-amo-dss02",
                "daq-amo-dss03",
                "daq-amo-dss04",
                "daq-amo-dss05",
                "daq-amo-dss06",
                "daq-amo-lampfnt01",
                "daq-amo-mon01",
                "daq-amo-mon02",
                "daq-amo-mon03",
                "daq-amo-mon04",
                "daq-amo-usr1",
                "daq-amo-evr01"],
         "sxr":["daq-sxr-master",
                "daq-sxr-princeton01",
                "daq-sxr-mon03",
                "daq-sxr-acq01",
                "daq-sxr-encoder",
                "daq-sxr-ipimb",
                "daq-sxr-mon01",
                "daq-sxr-mon02",
                "daq-sxr-cam03",
                "daq-sxr-acq02",
                "daq-sxr-adc",
                "daq-sxr-dss01",
                "daq-sxr-dss02",
                "daq-sxr-dss03",
                "daq-sxr-dss04",
                "daq-sxr-dss05",
                "daq-sxr-dss06",
                "daq-sxr-cam02",
                "daq-sxr-cam01",
                "daq-sxr-mon04",
                "daq-sxr-pgp01"],
         "xpp":["daq-xpp-cam01",
                "daq-xpp-ipimb",
                "daq-xpp-acq01",
                "daq-xpp-cam03",
                "daq-xpp-cam02",
                "daq-xpp-mon02",
                "daq-xpp-mon03",
                "daq-xpp-princeton",
                "daq-xpp-pgp01",
                "daq-xpp-pgp02",
                "daq-xpp-master",
                "daq-xpp-dss01",
                "daq-xpp-dss02",
                "daq-xpp-mon01",
                "daq-xpp-dss03",
                "daq-xpp-dss04",
                "daq-xpp-dss05",
                "daq-xpp-dss06",
                "daq-xpp-rayonix",
                "daq-xpp-mon04"],
         "xcs":["daq-xcs-tcam04",
                "daq-xcs-cam01",
                "daq-xcs-cam02",
                "daq-xcs-user1",
                "daq-xcs-acq01",
                "daq-xcs-tpx01",
                "daq-xcs-dss01",
                "daq-xcs-dss02",
                "daq-xcs-dss03",
                "daq-xcs-dss04",
                "daq-xcs-dss05",
                "daq-xcs-dss06",
                "daq-xcs-mon01",
                "daq-xcs-mon02",
                "daq-xcs-mon03",
                "daq-xcs-fccd"],
         "cxi":["daq-cxi-cam01",
                "daq-cxi-cam02",
                "daq-cxi-cam03",
                "daq-cxi-ipimb",
                "daq-cxi-misc",
                "daq-cxi-cspad01",
                "daq-cxi-cspad02",
                "daq-cxi-usrcam01",
                "daq-cxi-usrcam02",
                "daq-cxi-cam04",
                "daq-cxi-cspad03",
                "daq-cxi-cspad04",
                "daq-cxi-usracq01",
                "daq-cxi-mon05",
                "daq-cxi-mon04",
                "daq-cxi-acq01",
                "daq-cxi-mon06",
                "daq-cxi-mon03",
                "daq-cxi-dss01",
                "daq-cxi-dss02",
                "daq-cxi-dss03",
                "daq-cxi-dss04",
                "daq-cxi-dss05",
                "daq-cxi-dss07",
                "daq-cxi-dss08",
                "daq-cxi-dss09",
                "daq-cxi-dss10",
                "daq-cxi-dss11",
                "daq-cxi-dss12",
                "daq-cxi-mon01",
                "daq-cxi-mon02",
                "daq-cxi-dss06"],
         "mec":["daq-mec-cam01",
                "daq-mec-princeton02",
                "daq-mec-princeton01",
                "daq-mec-master",
                "daq-mec-pgp01",
                "daq-mec-cam02",
                "daq-mec-acq01",
                "daq-mec-pgp02",
                "daq-mec-mon01",
                "daq-mec-mon02",
                "daq-mec-dss01",
                "daq-mec-dss02",
                "daq-mec-cam03",
                "daq-mec-misc01"]}

cores = []
 
def remote(host, path, f):
  src = host
  appname = 'unknown'
  
  # Use find to get list of core files for this host
  cmd = "ping -c 2 1>&1 > /dev/null  "+host+" && ssh "+host+" '/bin/bash; /usr/bin/find "+path+" -name \"core.*\" -type f  -not -name \"*.py\" -not -name \"*.pyc\" -exec xargs /bin/ls -rtl --time-style=full-iso '{}' \;'"
  p = subprocess.Popen([cmd],
                       shell = True,
                       stdin = subprocess.PIPE,
                       stdout = subprocess.PIPE,
                       stderr = subprocess.PIPE,
                       close_fds = True)
  out, err = subprocess.Popen.communicate(p)

  # Parse list of core files and identify which application is responsible for core
  if len(out) != 0:
    for line in out.split('\n'):
      if line.find('/tmp/core')<0: src='pslogin'
      line = line.split()
      if len(line) == 9:
        time_str   = line[5] + " " + line[6][:-10]
        time_float = time.mktime( time.strptime( time_str,
                                                '%Y-%m-%d %H:%M:%S' ) )
        fname = os.path.realpath( line[8].strip() )
        plist = ['ssh',src,'gdb -c',fname,'-n','-batch']        
        p = subprocess.Popen(plist,stdout = subprocess.PIPE,stderr = subprocess.PIPE)
        for oline in p.stdout:
          if oline.find('generated') >= 0:
            appname = get_appname(oline)
            cores.append([src,time_float, time_str, fname, appname])
            break
        for oline in p.stderr:
          f.write( "ERROR: "+src+": "+oline.strip())

        #Get stack trace
        if os.path.exists(appname):
          plist = ['ssh', src, 'gdb',appname, fname,'-n','-batch', '--eval-command="where"']
          p = subprocess.Popen(plist,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
          
          f.write("\n%60s%s%60s\n" %((60*'-'),src,(60*'-')))
          f.write("%s, %s, %s, %s\n"%(src, time_str, fname, appname))
          stout,sterr = subprocess.Popen.communicate(p)
          for oline in stout.split('\n'):
            f.write(oline+"\n")
          for oline in sterr.split('\n'):
            f.write(oline+"\n")
            
  return
  

def local(path, f):
  src = "pslogin"
  appname = 'unknown'

  # Use find to get list of core files for this host  
  cmd = "/usr/bin/find "+path+" -name \"core.*\" -type f -not -name \"*.py\" -not -name \"*.pyc\"  -exec xargs /bin/ls -rtl --time-style=full-iso {} \\;"
  p = subprocess.Popen([cmd],
                       shell = True,
                       stdin = subprocess.PIPE,
                       stdout = subprocess.PIPE,
                       stderr = subprocess.PIPE,
                       close_fds = True)
  out, err = subprocess.Popen.communicate(p)

  # Parse list of core files and identify which application is responsible for core
  if len(out) != 0:
    for line in out.split('\n'):
      if line.find('/tmp/core')<0: src='pslogin'
      line = line.split()
      if len(line) == 9:
        time_str   = line[5] + " " + line[6][:-10]
        time_float = time.mktime( time.strptime( time_str,
                                                '%Y-%m-%d %H:%M:%S' ) )
        fname = os.path.realpath( line[8].strip() )
        plist = ['gdb','-c',fname,'-n','-batch']        
        p = subprocess.Popen(plist,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for oline in p.stdout:
          if oline.find('generated') >= 0:
            appname = get_appname(oline)
            cores.append([src,time_float, time_str, fname, appname])
            break
        for oline in p.stderr:
          f.write("ERROR: "+src+": "+oline.strip())

        #Get stack trace
        if os.path.exists(appname):
          plist = ['gdb',appname, fname,'-n','-batch', '--eval-command="where"']
          p = subprocess.Popen(plist,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
          f.write("\n%60s%s%60s\n" %((60*'-'),src,(60*'-')))
          f.write("%s, %s, %s, %s\n"%(src, time_str, fname, appname))
          stout,sterr = subprocess.Popen.communicate(p)
          for oline in stout.split('\n'):
            f.write(oline+"\n")
          for oline in sterr.split('\n'):
            f.write(oline+"\n")
       
  return

def get_appname(genstr):
  appname = 'unknown'
  appname = os.path.realpath(genstr.split()[4][1:].strip('`'))
  if appname.find("'.")>=0:
    appname=appname.strip("'.")
    head,tail=os.path.split(appname)
    if os.path.exists(head):
      appname_full=glob.glob(appname+"*")
      appname = appname_full[0]
  return appname

def list_corefiles(exp):
  logfiles = "/reg/g/pcds/pds/"+exp+"/cron/"
  
  # Output file (core dump output)
  now = datetime.datetime.now().strftime("%Y-%m-%d")
  exp_logs = os.path.join(logfiles,now)
  if not os.path.exists(exp_logs): os.makedirs(exp_logs)
  fname = os.path.join(exp_logs,now+"_coredumps.txt")

  # Open output file
  try:
    f = open(fname,'w')
  except IOError:
    print "ERROR:  Can't find file or don't have permission to write to file %s"%(fname)
    return

###  # How many minutes since last core dump check?

  # Get core dumps
  src = 'pslogin'
  local("/reg/neh/operator/"+exp+"opr/",f)
  local("/reg/g/pcds/dist/pds/"+exp+"/",f)

  for host in NODES[exp]:
    remote(host,"/tmp", f)

  f.close()

  # Sort by executable name and then date
  cores.sort( key=itemgetter( 4,1 ) )

  # Write core file list
  fname2 = os.path.join(exp_logs,now+"_corefilelist.txt")
  try:
    f2 = open(fname2,'w')
  except IOError:
    print "ERROR:  Can't find file or don't have permission to write to file %s"%(fname2)
    return

  # Remove float date before printing.
  for l in cores:
    if len(l)==5:
      report = '%s\n'%', '.join(map(str, ([l[0]]+l[2:])))
      f2.write(report)

  return 

if __name__=="__main__":
  exp = "amo"
  opts,args = getopt.getopt(sys.argv[1:],'e:h',
                            ['exp', 'help'])
  for o,a in opts:
    if o in ('-h', '--help'):
      usage(sys.argv)
      sys.exit(1)
    if o in ('-e', '--exp'):
      exp = a.lower()

  list_corefiles(exp)



