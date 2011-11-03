#!/usr/bin/python
# ProcMgr.py - configure (start, stop, status) the DAQ processes

import os, sys, string, telnetlib, subprocess
import stat, errno, time
from re import search
from time import sleep
import socket

#
# getConfigFileNames
#
# This function returns the paths of the p<partition>.conf.running and
# p<partition>.conf.last files, based on the partition# and config path.
#
# The paths are returned irregardless of whether the files are present.
#
# RETURNS: Two values: running config filename, last config filename
#
def getConfigFileNames(argconfig, partition):

    run_name = 'p%d.cnf.running' % partition
    last_name = 'p%d.cnf.last' % partition

    # prepend directory name if necessary
    if ('/' in argconfig):
        run_name = os.path.dirname(argconfig) + '/' + run_name
        last_name = os.path.dirname(argconfig) + '/' + last_name

    # return filenames
    return (run_name, last_name)

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
        if len(err) != 0:
            print "Unable to get current experiment ID from offline database: ", err
            return (int(exp_id), exp_name)

    # Issue mysql command to get experiment name
    mysqlcmd = 'echo "SELECT name FROM experiment WHERE experiment.id='+exp_id+'" | /usr/bin/mysql -N -h psdb -u regdb_reader regdb'

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


#
# The ProcMgr class maintains a dictionary with keys of
# the form "<host>:<uniqueid>".  The following helper functions
# are used to convert back and forth among <key>, <host>, and <uniqueid>.
#

#
# makekey - given <host> and <uniqueid>, generate a dictionary key
#
def makekey(host, uniqueid):
    return (host + ':' + uniqueid)
    
#
# key2host - given a dictionary key, get <host>
#
def key2host(key):
    return (key.split(':')[0])
    
#
# key2uniqueid - given a dictionary key, get <uniqueid>
#
def key2uniqueid(key):
    return (key.split(':')[1])

#
# mkdir_p - emulate mkdir -p
#
def mkdir_p(path):
    rv = 1
    try:
        os.makedirs(path)
    except OSError, exc:
        if exc.errno == errno.EEXIST:
            pass
        else: raise
    else:
        rv = 0
    return rv

#
# deduce_platform - deduce platform (-p) from contents of config file
#
# Returns: non-negative platform number, or -1 on error.
#
def deduce_platform(configfilename):
    rv = -1   # return -1 on error
    cc = {'platform': None, 'procmgr_config': None,
          'id':'id', 'cmd':'cmd', 'flags':'flags', 'port':'port', 'host':'host',
          'rtprio':'rtprio'}
    try:
      execfile(configfilename, {}, cc)
      if type(cc['platform']) == type('') and cc['platform'].isdigit():
        rv = int(cc['platform'])
    except:
      print 'deduce_platform Error:', sys.exc_info()[1]

    return rv


#
# deduce_instrument - deduce instrument (AMO, SXR, etc) from contents of config file
#
# Returns: '' by default
#
def deduce_instrument(configfilename):
    rv = ''
    cc = {'instrument': None, 'platform': None, 'procmgr_config': None,
          'id':'id', 'cmd':'cmd', 'flags':'flags', 'port':'port', 'host':'host',
          'rtprio':'rtprio'}

    try:
      execfile(configfilename, {}, cc)
      if type(cc['instrument']) == type('') and cc['instrument'].isalpha():
        rv = cc['instrument'].upper()

    except:
      print 'deduce_instrument Error:', sys.exc_info()[1]        

    return rv

#
# parse_cmd
#
# Parse the cmd string looking for -E, -e, or -f and replacing
# 'expname' and 'expnum' with current experiment name and number
# from database
#
# Caution:  If the string 'expname' or 'expnum' appears anywhere
# else in the command, it will also be replaced
#
def parse_cmd(cmd, expnum, expname):
    # if -E (experiment name) is passed in, replace 'expname' with current
    if cmd.find('-E') != -1 and cmd.find('expname') != -1:
        cmd = cmd.replace('expname',expname)

    # if -e (experiment number) is passed in, replace 'expnum' with current
    if cmd.find('-e') != -1 and cmd.find('expnum') != -1:
        cmd = cmd.replace('expnum', str(expnum))

    # if -f (filename) and 'expname' are passed in, replace 'expname' with current
    if cmd.find('-f') != -1 and cmd.find('expname') != -1:
        fname = cmd.split('-f')[1].strip()
        newfname = fname.replace('expname', expname)
        cmd = cmd.replace(fname, newfname)
    return cmd


class ProcMgr:

    # index into arrays managed by this class
    DICT_STATUS = 0
    DICT_PID = 1
    DICT_CMD = 2
    DICT_CTRL = 3
    DICT_PPID = 4
    DICT_FLAGS = 5
    DICT_GETID = 6

    # a managed executable can be in the following states
    STATUS_NOCONNECT = "NOCONNECT"
    STATUS_RUNNING = "RUNNING"
    STATUS_SHUTDOWN = "SHUTDOWN"
    STATUS_ERROR = "ERROR"

    # placeholder when PID is not valid
    STRING_NOPID = "-"

    # paths
    PATH_XTERM = "/usr/bin/xterm"
    PATH_TELNET = "/usr/bin/telnet"

    # messages expected from procServ
    MSG_BANNER_END = "server started at"
    MSG_ISSHUTDOWN = "is SHUT DOWN"
    MSG_RESTART = "new child"
    MSG_PROMPT = "\x0d\x0a> "
    MSG_SPAWN = "procServ: spawning daemon"

    # procmgr control port initialized in __init__
    EXECMGRCTRL = -1

    # platform initialized in __init__
    PLATFORM = -1

    # instrument initialized in __init__
    INSTRUMENT = ''
    
    valid_flag_list = ['X', 'k', 's'] 
    valid_instruments = ['AMO','SXR','XPP','XCS','CXI','MEC']

    def __init__(self, configfilename, platform, baseport=29000):
        self.pid = self.STRING_NOPID
        self.ppid = self.STRING_NOPID
        self.getid = None
        self.telnet = telnetlib.Telnet()

        # configure the default socket timeout in seconds
        socket.setdefaulttimeout(2.5)

        # configure the port numbers
        self.EXECMGRCTRL = baseport

        # create new empty 'self' dictionary
        self.d = dict()

        # create dictionaries for port assignments
        nextCtrlPort = dict()
        staticPorts = dict()

        if (platform == -1):
            print 'ERR: platform not specified'
            return
        else:
            self.PLATFORM = platform

        if (self.PLATFORM > 0):
            self.EXECMGRCTRL += (self.PLATFORM * 100)

        # initialize the experiment
        # (only used by online_ami to get current experiment)
        self.INSTRUMENT = deduce_instrument(configfilename)
        if self.INSTRUMENT not in self.valid_instruments:
            if self.INSTRUMENT != '':  print 'ERR: Invalid instrument ', self.INSTRUMENT
            (expnum, expname) = (-1, '')
        else:
            (expnum, expname) = getCurrentExperiment(self.INSTRUMENT)

        # The static port allocations must be processed first.
        # Read the config file and make a list with statically assigned
        # entries at the front, dynamic entries at the back.

        # In case a host appears as both 'localhost' and another name,
        # ensure that 'localhost' ports are not reused on other hosts.
        localPorts = set()
        remotePorts = set()

        configlist = []         # start out with empty list

        config = {'platform': repr(self.PLATFORM), 'procmgr_config': None,
                  'id':'id', 'cmd':'cmd', 'flags':'flags', 'port':'port', 'host':'host',
                  'rtprio':'rtprio'}
        try:
          execfile(configfilename, {}, config)
        except:
          print 'deduce_platform Error:', sys.exc_info()[1]

        if type(config['procmgr_config']) == type([]):
          for dd in config['procmgr_config']:
            if type(dd) == type({}):
              if dd.has_key('port'):
                # static port assignments at the beginning of the list
                configlist.insert(0, dd)
              else:
                # dynamic port assignments at the end of the list
                configlist.append(dd)
            else:
              print 'Error: procmgr_config entry not key:value:', dd
        else:
          print 'Error: procmgr_config not a list', config['procmgr_config']

        # for each entry in the list...
        for entry in configlist:
          # ...process the fields

          # --- real-time priority (optional) ---
          self.rtprio = None
          tmpsum = 0
          if entry.has_key('rtprio'):
            try:
              tmpsum = int(entry['rtprio'])
            except:
              print 'Error: malformed rtprio value:', entry
            if tmpsum:
              # check if rtprio is in valid range
              if (tmpsum < 1) or (tmpsum > 99):
                print 'Error: rtprio not in range 1-99:', entry
              else:
                self.rtprio = tmpsum

          # --- cmd (required) ---
          if entry.has_key('cmd'):
            # if real-time priority is set (see above), use /usr/bin/chrt
            if (self.rtprio):
              entry['cmd'] = '/usr/bin/chrt -f %d %s' % (self.rtprio, entry['cmd'])
            # Do something special if -E, -e, or -f appear in cmd string
            self.cmd = parse_cmd(entry['cmd'], expnum, expname)
          else:
            print 'Error: procmgr_config entry missing cmd:', entry
            self.cmd = 'error'

          # --- id (required) ---
          if entry.has_key('id'):
            self.uniqueid = entry['id']
          else:
            print 'Error: procmgr_config entry missing id:', entry
            self.uniqueid = 'error'

          # --- host (optional) ---
          if entry.has_key('host'):
            self.host = entry['host']
          else:
            self.host = 'localhost'

          # --- flags (optional) ---
          if entry.has_key('flags'):
            self.flags = entry['flags']
            for nextflag in self.flags:
              if (nextflag not in self.valid_flag_list):
                print 'ERR: invalid flag:', nextflag
          else:
            self.flags = '-'

          # initialize dictionaries used for port assignments
          if not self.host in nextCtrlPort:
              # on each host, two ports are reserved for a master server: ctrl and log
              nextCtrlPort[self.host] = self.EXECMGRCTRL + 2
              staticPorts[self.host] = set()

          # --- port (optional) ---
          tmpsum = 0
          if entry.has_key('port'):
            try:
              tmpsum = int(entry['port'])
            except:
              print 'Error: malformed port value:', entry

          if tmpsum:
            # assign the port statically
            if tmpsum in staticPorts[self.host]:
                print 'ERR: port #%d duplicated in the config file' % tmpsum
            else:
                # avoid dup: update the set of statically assigned ports
                staticPorts[self.host].add(tmpsum)
            self.ctrlport = str(tmpsum)                             # string
            self.flags += 'k'
          else:
              # assign port dynamically
              tmpport = nextCtrlPort[self.host]
              # avoid dup: check the set of statically assigned ports
              if (self.host == 'localhost'):
                  while (tmpport in staticPorts[self.host]) or (tmpport in remotePorts):
                      tmpport += 1
              else:
                  while (tmpport in staticPorts[self.host]) or (tmpport in localPorts):
                      tmpport += 1

              self.ctrlport = str(tmpport)                            # string
              nextCtrlPort[self.host] = tmpport + 1                   # integer

              # update set of local or remote ports to avoid conflict
              if (self.host == 'localhost'):
                  localPorts.add(tmpport)
              else:
                  remotePorts.add(tmpport)

          self.pid = "-"
          self.ppid = "-"
          self.getid = "-"
          # open a connection to the control port (procServ)
          try:
              self.telnet.open(self.host, self.ctrlport)
          except:
              # telnet failed
              self.tmpstatus = self.STATUS_NOCONNECT
              # TODO ping each host first, as telnet could fail due to an error
          else:
              # telnet succeeded: gather status from procServ banner
              ok = self.readLogPortBanner()
              if not ok:
                  # reading procServ banner failed
                  print "ERR: failed to read procServ banner for \'%s\' on host %s" \
                          % (self.uniqueid, self.host)
              # close connection to the logging port (procServ)
              self.telnet.close()

          if ((self.tmpstatus != self.STATUS_NOCONNECT) and \
              (self.tmpstatus != self.STATUS_ERROR) and \
              (self.getid != self.uniqueid)):
              print "ERR: found \'%s\', expected \'%s\' on host %s port %s" % \
                  (self.getid, self.uniqueid, self.host, self.ctrlport)
          else:
              # add an entry to the dictionary
              key = makekey(self.host, self.uniqueid)
              self.d[key] = \
                [ self.tmpstatus, self.pid, self.cmd, self.ctrlport, self.ppid, self.flags, self.getid]
                # DICT_STATUS  DICT_PID  DICT_CMD  DICT_CTRL      DICT_PPID  DICT_FLAGS  DICT_GETID

    def readLogPortBanner(self):
        response = self.telnet.read_until(self.MSG_BANNER_END, 1)
        if not string.count(response, self.MSG_BANNER_END):
            self.tmpstatus = self.STATUS_ERROR
            # when reading banner fails, set the ID so the error output includes name instead of '-'
            self.getid = self.uniqueid
            return 0
        if search('SHUT DOWN', response):
            self.tmpstatus = self.STATUS_SHUTDOWN
            self.ppid = search('@@@ procServ server PID: ([0-9]*)', response).group(1)
            self.getid = search('@@@ Child \"(.*)\" start', response).group(1)
        else:
            self.tmpstatus = self.STATUS_RUNNING
            self.pid = search('@@@ Child \"(.*)\" PID: ([0-9]*)', response).group(2)
            self.getid = search('@@@ Child \"(.*)\" PID: ([0-9]*)', response).group(1)
            self.ppid = search('@@@ procServ server PID: ([0-9]*)', response).group(1)
        return 1

    #
    # show - call status() with an empty id_list
    #
    def show(self, verbose=0):
        return self.status([], verbose)

    #
    # status
    #
    def status(self, id_list, verbose=0, only_static=0):

        nonePrinted = 1

        if self.isEmpty():
            if verbose:
                print "(configuration is empty)"
            return 1

        # print contents of dictionary (sorted by key)
        for key in sorted(self.d.iterkeys()):

            if len(id_list) > 0:
                # if id_list is nonempty and UniqueID is not in it,
                # skip this entry
                if key2uniqueid(key) not in id_list:
                    continue

            if only_static and ('k' not in self.d[key][self.DICT_FLAGS]):
                # only_static flag was passed in and this entry does not 
                # have the 'k' flag set: skip this entry
                continue

            if (nonePrinted == 1):
              # print heading, once
              print "Host          UniqueID     Status     PID    PORT   Command+Args"
              nonePrinted = 0

            if (self.d[key][self.DICT_STATUS] == self.STATUS_NOCONNECT):
                showId = key2uniqueid(key)
            else:
                showId = self.d[key][self.DICT_GETID]

            print "%-13s %-12s %-10s %-5s  %-5s  %s" % \
                    (key2host(key), showId, \
                    self.d[key][self.DICT_STATUS], \
                    self.d[key][self.DICT_PID], \
                    self.d[key][self.DICT_CTRL], \
                    self.d[key][self.DICT_CMD])
            if verbose:
                print "                                       PPID: %s  Flags:" \
                        % (self.d[key][self.DICT_PPID]),
                if 'X' in self.d[key][self.DICT_FLAGS]:
                    print "X",
                if 's' in self.d[key][self.DICT_FLAGS]:
                    print "s",
                if 'k' in self.d[key][self.DICT_FLAGS]:
                    print "k",
                print ""
                
        if (nonePrinted == 1):
          print "(none found)"

        # done
        return 1

    #
    # getStatus - machine readable status
    #
    def getStatus(self, id_list=[], verbose=0, only_static=0):

        resultlist = list()

        if self.isEmpty():
          if verbose:
            print "(configuration is empty)"
        else:
          # get contents of dictionary (sorted by key)
          for key in sorted(self.d.iterkeys()):
            # start with empty dictionary
            statusdict = dict()

            if len(id_list) > 0:
              # if id_list is nonempty and UniqueID is not in it,
              # skip this entry
              if key2uniqueid(key) not in id_list:
                continue

            if only_static and ('k' not in self.d[key][self.DICT_FLAGS]):
              # only_static flag was passed in and this entry does not 
              # have the 'k' flag set: skip this entry
              continue
                
            if (self.d[key][self.DICT_STATUS] == self.STATUS_NOCONNECT):
              statusdict['showId'] = key2uniqueid(key)
            else:
              statusdict['showId'] = self.d[key][self.DICT_GETID]

            statusdict['status'] = self.d[key][self.DICT_STATUS]
            statusdict['host'] = key2host(key)
            # add dictionary to list
            resultlist.append(statusdict)
              
        # done
        return resultlist

    #
    # restart
    #
    def restart(self, key, value, verbose=0):

        # open a connection to the procServ control port
        started = False
        connected = False
        telnetCount = 0
        host = key2host(key)
        while (not connected) and (telnetCount < 2):
            telnetCount = telnetCount + 1
            try:
                self.telnet.open(host, value[self.DICT_CTRL])
            except:
                sleep(.25)
            else:
                connected = True

        if connected:
            # wait for SHUT DOWN message
            response = self.telnet.read_until(self.MSG_ISSHUTDOWN, 1)
            if not string.count(response, self.MSG_ISSHUTDOWN):
                print 'ERR: no SHUT DOWN message in ',
                print 'response: <<%s>>' % response

            # send ^R to restart child process
            self.telnet.write("\x12");

            # wait for restart message
            response = self.telnet.read_until(self.MSG_RESTART, 1)
            if not string.count(response, self.MSG_RESTART):
                print 'ERR: no restart message... '
            else:
                started = True

                # close telnet connection
                self.telnet.close()
        else:
            print 'ERR: restart() telnet to %s port %s failed' % \
                (host, value[self.DICT_CTRL])

        return started

    #
    # startAll - call start() with an empty id_list
    #
    def startAll(self, verbose=0, logpathbase=None, coresize=0):
        return self.start([], verbose, logpathbase, coresize)

    #
    # start
    #
    # RETURNS: 0 if any processes were started, otherwise 1.
    #
    def start(self, id_list, verbose=0, logpathbase=None, coresize=0):

        rv = 1                  # return value
        started_count = 0       # count successful start commands

        # create list of entries with X flag enabled (empty for now)
        Xlist = list()

        if self.isEmpty():
            # configuration is empty -- nothing to start
            if verbose:
                print 'startAll: empty configuration'
            return 1

        if (self.PLATFORM < 0) or (self.PLATFORM > 4):
            print 'platform %d not in range 0-4' % self.PLATFORM
            return 1

        # for redirecting to /dev/null
        nullOut = open(os.devnull, 'w')

        # create a dictionary mapping hosts to a set of start commands
        startdict = dict()
        for key, value in self.d.iteritems():
            if len(id_list) > 0:
                # if id_list is nonempty and UniqueID is not in it,
                # skip this entry
                if key2uniqueid(key) not in id_list:
                    continue
            if value[self.DICT_STATUS] == self.STATUS_NOCONNECT:
                starthost = key2host(key)
                if 'X' in value[self.DICT_FLAGS]:
                    Xlist.append([key, value])
                    waitflag = '--wait'
                else:
                    waitflag = ''

                if ('>' in value[self.DICT_CMD]) or (logpathbase == None) or (logpathbase == "/dev/null"):
                    redirect_string = ''
                else:
                    #
                    # Construct path similar to:
                    #
                    #  <logpath>/2009/08/21_10:35_atca01:opal1k.log
                    #
                    logpath = '%s/%s' % (logpathbase, time.strftime('%Y/%m'))
                    try:
                      mkdir_p(logpath)
                    except:
                      # mkdir
                      print 'ERR: mkdir %s failed' % logpath
                      redirect_string = ''
                    else:
                      time_string = time.strftime('%d_%H:%M:%S')
                      logfile = '%s/%s_%s.log' % (logpath, time_string, key)
                      if verbose:
                          print 'log file:', logfile
                      redirect_string = '>& %s' % logfile

                    pbits = (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    if (os.stat(logpath).st_mode & pbits) != pbits:
                      try:
                        os.chmod(logpath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                      except:
                        print 'ERR: chmod %s failed' % logpath
                        redirect_string = ''

                cmdSplit = value[self.DICT_CMD].split(None, 1)
                if (os.path.isfile(cmdSplit[0])):
                  cmdtmp = os.path.realpath(cmdSplit[0]) + ' ' + cmdSplit[1]
                else:
                  print 'ERR: %s not found' % cmdSplit[0]
                  cmdtmp = '/bin/echo \"File not found: ' + cmdSplit[0] + '"'

                startcmd = \
                        '/reg/g/pcds/package/procServ-2.5.1/procServ --noautorestart --name %s %s --allow --coresize %d %s %s %s' % \
                        (key2uniqueid(key), \
                        waitflag, \
                        coresize, \
                        value[self.DICT_CTRL], \
                        cmdtmp,
                        redirect_string)
                # is this host already in the dictionary?
                if starthost in startdict:
                    # yes: add to set of start commands
                    startdict[starthost].append([startcmd, key])
                else:
                    # no: initialize set of start commands
                    startdict[starthost] = [[startcmd, key]]
            elif value[self.DICT_STATUS] == self.STATUS_SHUTDOWN:
                # restart
                if self.restart(key, value, verbose):
                    started_count += 1

        # now use the newly created dictionary to run start command(s)
        # on each host

        for host, value in startdict.iteritems():

            if (host == 'localhost'):
                # process list of commands
                while len(value) > 0:
                    # send command
                    args, key = value.pop()
                    if verbose:
                        print 'Run locally: %s' % args

                    yy = subprocess.Popen(args, stdout=nullOut, stderr=nullOut, shell=True)
                    yy.wait()
                    if (yy.returncode != 0):
                        print "ERR: failed to run '%s' (procServ returned %d)" % \
                            (args, yy.returncode)
                    else:
                        self.setStatus([key], self.STATUS_RUNNING)
                        started_count += 1
            else:
                # open a connection to the procmgr control port (procServ)
                try:
                    self.telnet.open(host, self.EXECMGRCTRL)
                except:
                    # telnet failed
                    print 'ERR: telnet to procmgr (%s port %d) failed' % \
                            (host, self.EXECMGRCTRL)
                    print '>>> Please start the procServ process on host %s!' % host
                else:
                    # telnet succeeded

                    # send ^U followed by carriage return to safely reach the prompt
                    self.telnet.write("\x15\x0d");

                    # wait for prompt (procServ)
                    response = self.telnet.read_until(self.MSG_PROMPT, 2)
                    if not string.count(response, self.MSG_PROMPT):
                        print 'ERR: no prompt at %s port %s' % \
                            (key2host(key), self.EXECMGRCTRL)

                    # process list of commands
                    while len(value) > 0:

                        nextcmd, nextkey = value.pop()

                        if verbose:
                            print 'Run on %s: %s' % (host, nextcmd)

                        # send command
                        self.telnet.write('%s\n' % nextcmd);
                        # wait for prompt
                        response = self.telnet.read_until(self.MSG_PROMPT, 2)
                        if not string.count(response, self.MSG_PROMPT):
                            print 'ERR: no prompt at %s port %s' % \
                                (host, self.EXECMGRCTRL)
                        else:
                            #
                            # If X flag is set, procServ --wait is used so
                            # the next state is actually STATUS_SHUTDOWN.
                            # It will be STATUS_RUNNING after restart, below.
                            #
                            self.setStatus([nextkey], self.STATUS_RUNNING)
                            started_count += 1

                    # close telnet connection
                    self.telnet.close()

        for item in Xlist:

            # is xterm available?
            if os.path.exists(self.PATH_XTERM):
                # yes: spawn xterm
                args = [self.PATH_XTERM, "-T", item[0], \
                        "-e", self.PATH_TELNET, key2host(item[0]), \
                        item[1][self.DICT_CTRL]]
                subprocess.Popen(args)
            else:
                # no: say xterm not available
                print 'ERR: %s not available' % self.PATH_XTERM

        for item in Xlist:
            if self.restart(item[0], item[1], verbose):
                started_count += 1
                        
        # done
        # cleanup
        nullOut.close()

        if started_count > 0:
            rv = 0

        return rv

    #
    # isEmpty
    #
    def isEmpty(self):
        return (len(self.d) < 1)

    #
    # stopDictionary
    #
    def stopDictionary(self, childdict, parentdict, verbose, sigdelay):
        rv = 0      # return value

        # for redirecting to /dev/null
        nullOut = open(os.devnull, 'w')

        # use the sigchild dictionary to run kill command on each host
        for host, value in childdict.iteritems():

            if (host == 'localhost'):
                # local...
                # send the kill command (SIGINT)
                args = 'kill -2 %s' % value[0]
                if verbose:
                    print 'localhost:', args
                yy = subprocess.Popen(args.split(), stdout=nullOut, stderr=nullOut)
                yy.wait()
                if (yy.returncode == 0):
                    # change status to SHUTDOWN
                    self.setStatus(value[1], self.STATUS_SHUTDOWN)
                else:
                    print 'ERR: failed to signal %s (kill returned %d)' % \
                        (value[0], yy.returncode)
                    rv = 1
            else:
                # remote...
                # open a connection to the procmgr control port (procServ)
                try:
                    self.telnet.open(host, self.EXECMGRCTRL)
                except:
                    # telnet failed
                    print 'ERR: telnet to procmgr failed'
                    print '>>> Please start the procServ process on host %s!' % host
                    rv = 1
                else:
                    # telnet succeeded

                    # send ^U followed by carriage return to safely reach the prompt
                    self.telnet.write("\x15\x0d");

                    # wait for prompt (procServ)
                    response = self.telnet.read_until(self.MSG_PROMPT, 2)
                    if not string.count(response, self.MSG_PROMPT):
                        print 'ERR: no prompt at %s port %s' % \
                            (host, self.EXECMGRCTRL)
                        rv = 1
                    if verbose:
                        print 'host %s: kill -2 %s' % (host, value[0])
                    # send the kill command (SIGINT)
                    self.telnet.write('kill -2 %s\n' % value[0]);

                    # wait for prompt (procServ)
                    response = self.telnet.read_until(self.MSG_PROMPT, 2)
                    if string.count(response, self.MSG_PROMPT):
                        # change status to SHUTDOWN
                        self.setStatus(value[1], self.STATUS_SHUTDOWN)
                    else:
                        print 'ERR: no prompt at %s port %s' % \
                            (host, self.EXECMGRCTRL)
                        rv = 1

                    # close telnet connection
                    self.telnet.close()

        # if 1 or more children were signalled, wait
        if len(childdict) > 0:
            if sigdelay > 0:
                sleep(sigdelay)

        # use the sigparent dictionary to run kill command on each host
        for host, value in parentdict.iteritems():

            if (host == 'localhost'):
                # local...
                # send the kill command (SIGTERM)
                args = 'kill %s' % value[0]
                if verbose:
                    print 'localhost:', args
                yy = subprocess.Popen(args.split(), stdout=nullOut, stderr=nullOut)
                yy.wait()
                if (yy.returncode == 0):
                    # change status to NOCONNECT
                    self.setStatus(value[1], self.STATUS_NOCONNECT)
                else:
                    print 'ERR: failed to signal %s (kill returned %d)' % \
                        (value[0], yy.returncode)
                    rv = 1
            else:
                # remote...
                # open a connection to the procmgr control port (procServ)
                try:
                    self.telnet.open(host, self.EXECMGRCTRL)
                except:
                    # telnet failed
                    print 'ERR: telnet to procmgr failed'
                    print '>>> Please start the procServ process on host %s!' % host
                    rv = 1
                else:
                    # telnet succeeded

                    # send ^U followed by carriage return to safely reach the prompt
                    self.telnet.write("\x15\x0d");

                    # wait for prompt (procServ)
                    response = self.telnet.read_until(self.MSG_PROMPT, 2)
                    if string.count(response, self.MSG_PROMPT):
                        # change status to NOCONNECT
                        self.setStatus(value[1], self.STATUS_NOCONNECT)
                    else:
                        print 'ERR: no prompt at %s port %s' % \
                            (host, self.EXECMGRCTRL)
                        # change status to ERROR
                        self.setStatus(value[1], self.STATUS_ERROR)
                        rv = 1
                    if verbose:
                        print 'host %s: kill %s' % (host, value[0])
                    # send the kill command (SIGTERM)
                    self.telnet.write('kill %s\n' % value[0]);

                    # wait for prompt (procServ)
                    response = self.telnet.read_until(self.MSG_PROMPT, 2)
                    if not string.count(response, self.MSG_PROMPT):
                        print 'ERR: no prompt at %s port %s' % \
                            (host, self.EXECMGRCTRL)
                        rv = 1

                    # close telnet connection
                    self.telnet.close()

        # cleanup
        nullOut.close()

        return rv

    #
    # stopAll - call stop() with an empty id_list
    #
    def stopAll(self, verbose=0, sigdelay=1):
        return self.stop([], verbose, sigdelay)

    #
    # stop
    #
    def stop(self, id_list, verbose=0, sigdelay=1, only_static=0):
        rv = 0      # return value

        if self.isEmpty():
            # configuration is empty -- nothing to disconnect
            if verbose:
                print 'nothing to disconnect'
        else:
            #
            # create dictionaries mapping hosts to set of PIDs to be signalled
            #
            childdict = dict()
            parentdict = dict()
            for key, value in self.d.iteritems():

                if len(id_list) > 0:
                    # if id_list is nonempty and UniqueID is not in it,
                    # skip this entry
                    if key2uniqueid(key) not in id_list:
                        continue
                else:
                    # if id_list is empty and 'k' flag is set,
                    # skip this entry
                    if 'k' in value[self.DICT_FLAGS]:
                        if verbose and value[self.DICT_STATUS] != self.STATUS_NOCONNECT:
                            print '\'%s\' not stopped: this is a static task' % \
                                key2uniqueid(key)
                        continue

                if only_static and ('k' not in self.d[key][self.DICT_FLAGS]):
                    # only_static flag was passed in and this entry does not 
                    # have the 'k' flag set: skip this entry
                    continue
                    
                if (self.d[key][self.DICT_STATUS] == self.STATUS_NOCONNECT):
                    showId = key2uniqueid(key)
                else:
                    showId = self.d[key][self.DICT_GETID]
                
                # if process is RUNNING and has 's' in its flag, SIGINT it first
                if (value[self.DICT_STATUS] == self.STATUS_RUNNING) and \
                   ('s' in value[self.DICT_FLAGS]):
                    sigchildhost = key2host(key)
                    sigchildstring = value[self.DICT_PID]
                    if sigchildhost not in childdict:
                        # first PID for this host
                        childdict[sigchildhost] = [sigchildstring, [key]]
                    else:
                        # not the first PID for this host
                        childdict[sigchildhost][0] += (' ' + sigchildstring)
                        childdict[sigchildhost][1].append(key)

                # if process is not NOCONNECT, SIGTERM its parent (procServ)
                if value[self.DICT_STATUS] != self.STATUS_NOCONNECT:
                    sigparenthost = key2host(key)
                    sigparentstring = value[self.DICT_PPID]
                    if sigparenthost not in parentdict:
                        # first PID for this host
                        parentdict[sigparenthost] = [sigparentstring, [key]]
                    else:
                        # not the first PID for this host
                        parentdict[sigparenthost][0] += (' ' + sigparentstring)
                        parentdict[sigparenthost][1].append(key)

            rv = self.stopDictionary(childdict, parentdict, verbose, sigdelay)

        # done
        return rv

    #
    # getProcessCounts
    #
    # RETURNS: Two values: static process count, dynamic process count
    #
    def getProcessCounts(self):

        # count the processes that are not NOCONNECT
        staticProcessCount = 0
        dynamicProcessCount = 0
        for key, value in self.d.iteritems():
            if (value[self.DICT_STATUS] != self.STATUS_NOCONNECT):
                if ('k' in self.d[key][self.DICT_FLAGS]):
                    staticProcessCount += 1
                else:
                    dynamicProcessCount += 1

        return staticProcessCount, dynamicProcessCount

    #
    # setStatus
    #
    # This method sets the status for each process in a specified list.
    # 
    # RETURNS: 0 on success, 1 on error.
    #
    def setStatus(self, key_list, newStatus):

        for key in key_list:
            if key in self.d:
                self.d[key][self.DICT_STATUS] = newStatus
            else:
                print "ERR: setStatus: key '%s' not found" % key
                return 1

        return 0

#
# main
#
if __name__ == '__main__':
    basename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    usage = "Usage: %s configfile [platform]" % basename
    default_platform = 1
    if len(sys.argv) == 2:
        platform = default_platform
    elif len(sys.argv) != 3:
        print usage
        sys.exit(1)
    else:
        try:
            platform = int(sys.argv[2])
        except ValueError:
            platform = default_platform
            print "%s: invalid platform (%s), using default (%d)" % (sys.argv[0], sys.argv[2], platform)

    # collect the status, reading from the config file
    print '-------- calling ProcMgr(%s, %d)' % (sys.argv[1], platform)
    try:
        procMgr = ProcMgr(sys.argv[1], platform)
    except IOError:
        print "%s: error while accessing %s %d" % (sys.argv[0], sys.argv[1], platform)
        sys.exit(1)

    # error check
    if procMgr.isEmpty():
        print 'configuration is empty.  exiting now'
        sys.exit(1)

    # show the status
    print '-------- calling show(0)'
    procMgr.show(0)

    # stop all
    print '-------- calling stopAll()'
    procMgr.stopAll()

    # delete the previous status (is this right?)
    del procMgr

    # collect the status again
    print '-------- calling ProcMgr(%s, %d)' % (sys.argv[1], platform)
    try:
        procMgr = ProcMgr(sys.argv[1], platform)
    except IOError:
        print "%s: error while accessing %d" % (sys.argv[0], sys.argv[1], platform)
        sys.exit(1)

    # error check
    if procMgr.isEmpty():
        print 'configuration is empty.  exiting now'
        sys.exit(1)

    # show the status again
    print '-------- calling show(0)'
    procMgr.show(0)

    # start all
    print '-------- calling startAll(1)'
    procMgr.startAll(1)

    # delete the previous status (is this right?)
    del procMgr

    # collect the status again
    print '-------- calling ProcMgr(%s, %d)' % (sys.argv[1], platform)
    try:
        procMgr = ProcMgr(sys.argv[1], platform)
    except IOError:
        print "%s: error while accessing %s %d" % (sys.argv[0], sys.argv[1], platform)
        sys.exit(1)

    # show the status again
    print '-------- calling show(0)'
    procMgr.show(0)

    print '-------- done'
