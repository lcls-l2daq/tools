#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import subprocess
import datetime
import glob
from optparse import OptionParser
import re
import os

DEVICE = ['NoDevice', 'Evr', 'Acqiris', 'Opal1000', 'TM6740', 'pnCCD', 'Princeton', 'Fccd', 'Ipimb', 'Encoder', 'Cspad', 'AcqTDC', 'Xamps', 'Cspad2x2', 'Fexamp', 'Gsc16ai', 'Phasics', 'Timepix', 'Opal2000', 'Opal4000', 'OceanOptics', 'Opal1600', 'Opal8000', 'Fli', 'Quartz4A150', 'Andor', 'USDUSB', 'OrcaFl40', 'Imp', 'Epix', 'Rayonix', 'EpixSampler']
DETECTOR = ['NoDetector', 'AmoIms', 'AmoGasdet', 'AmoETof', 'AmoITof', 'AmoMbes', 'AmoVmi', 'AmoBps', 'Camp', 'EpicsArch', 'BldEb', 'SxrBeamline', 'SxrEndstation', 'XppSb1Ipm', 'XppSb1Pim', 'XppMonPim', 'XppSb2Ipm', 'XppSb3Ipm', 'XppSb3Pim', 'XppSb4Pim', 'XppGon', 'XppLas', 'XppEndstation', 'AmoEndstation', 'CxiEndstation', 'XcsEndstation', 'MecEndstation', 'CxiDg1', 'CxiDg2', 'CxiDg3', 'CxiDg4', 'CxiKb1', 'CxiDs1', 'CxiDs2', 'CxiDsu', 'CxiSc1', 'CxiDsd', 'XcsBeamline', 'CxiSc2', 'MecXuvSpectrometer', 'MecXrtsForw', 'MecXrtsBack', 'MecFdi', 'MecTimeTool', 'MecTargetChamber', 'FeeHxSpectrometer', 'XrayTransportDiagnostic', 'Lamp']
BLD = ['EBeam', 'PhaseCavity', 'FEEGasDetEnergy', 'Nh2Sb1Ipm01', 'HxxUm6Imb01', 'HxxUm6Imb02', 'HfxDg2Imb01', 'HfxDg2Imb02', 'XcsDg3Imb03', 'XcsDg3Imb04', 'HfxDg3Imb01', 'HfxDg3Imb02', 'HxxDg1Cam', 'HfxDg2Cam', 'HfxDg3Cam', 'XcsDg3Cam', 'HfxMonCam', 'HfxMonImb01', 'HfxMonImb02', 'HfxMonImb03', 'MecLasEm01', 'MecTctrPip01', 'MecTcTrDio01', 'MecXt2Ipm02', 'MecXt2Ipm03', 'MecHxmIpm01', 'GMD', 'CxiDg1Imb01', 'CxiDg2Imb01', 'CxiDg2Imb02', 'CxiDg4Imb01', 'CxiDg1Pim', 'CxiDg2Pim', 'CxiDg4Pim', 'XppMonPim0', 'XppMonPim1', 'XppSb2Ipm', 'XppSb3Ipm', 'XppSb3Pim', 'XppSb4Pim', 'XppEndstation0', 'XppEndstation1', 'MecXt2Pim02', 'MecXt2Pim03', 'CxiDg3Spec', 'Nh2Sb1Ipm02', 'FeeSpec0', 'SxrSpec0', 'XppSpec0']

class PHYSID(object):
    MASK_DEVID  = 0xff
    MASK_DEV    = 0xff00
    MASK_DETID  = 0xff0000
    MASK_DET    = 0xff000000
    SHIFT_DEVID = 0
    SHIFT_DEV   = 8
    SHIFT_DETID = 16
    SHIFT_DET   = 24
    
    def __init__(self, physid=0x0):
        self._physid = physid
        self._detid = (physid & self.MASK_DETID) >> self.SHIFT_DETID
        self._det   = (physid & self.MASK_DET)   >> self.SHIFT_DET
        self._devid = (physid & self.MASK_DEVID) >> self.SHIFT_DEVID
        self._dev   = (physid & self.MASK_DEV)   >> self.SHIFT_DEV

    def detid(self):
        return self._detid
    def det(self):
        return self._det
    def detname(self):
        if (self._det > len(DETECTOR)):return ''
        return DETECTOR[self._det]
    def devid(self):
        return self._devid
    def dev(self):
        return self._dev
    def devname(self):
        if (self._det == 0) and (self._dev ==0): return BLD[self._devid]
        if (self._dev > len(DEVICE)):return ''
        return DEVICE[self._dev]
    def phy(self):
        return int(self._physid)

def control_log(path, summ):
    for fname in glob.iglob(path+'*control_gui.log'):
        thetime = fname[(len(path)+1):len(path)+9]
        ami_release = ami_version(path, thetime)
        compression = compression_check(path,thetime)
        fruns = []
        f = file(fname,"r")
        lines = f.readlines();
        run = {'duration':''}
        runnumber = '-'
        for iline in range(len(lines)):
            line = lines[iline]
            if ((line.find("MainWindow:")>=0) and (line.find('instrument')>=0) and (line.find('experiment')>=0)):            
                expstr = line.split("MainWindow: ")[1].strip().split('instrument')[1].split('experiment')
                instname = expstr[0].replace("'","")
                expstr = expstr[1].strip("'").replace("'","")
                expname = expstr.split('(#')[0].replace("'","")
                expnum = int(expstr.split('(#')[1].strip(')'))
            if (line.find("Configured")>=0 or line.find("Unmapped")>=0):
                if run['duration']!='':
                    fruns.append(run)
                    run = {'duration':''}
                    runnumber = '-'
            if (line.find("Completed allocating")>=0):
                runnumber = line.split()[-1]
            if ((line.find("build") >= 0) and (line.find("as") >= 0) and (line.find("@@@") >=0)):                
                full_release=line.split("as ")[1].strip().strip(')')
                if full_release.find("/reg/g/pcds/dist/pds/") != -1:
                    daq_release = full_release.split("/reg/g/pcds/dist/pds/")[1].split('/')[0]
                else:
                    daq_release = full_release.replace('reg/neh/home','~')
                    daq_release = full_release.replace('reg/neh/home2','~')
                    daq_release = full_release.replace('reg/neh/home3','~')
            index = line.find("Duration")
            if (index>=0):
                ended    = line.partition(':Duration:')[0].rstrip()                
                duration = line.partition(' ')[-1].rstrip()
                events   = lines[iline+1].rpartition(':')[-1].rstrip()
                damaged  = lines[iline+2].rpartition(':')[-1].rstrip()
                bytes    = lines[iline+3].rpartition(':')[-1].rstrip().lstrip()
                bytes    = humansize(int(bytes), True)
                if int(events)==0:
                    evtsiz = ''
                else:
                    evtsiz = humansize(float(int(lines[iline+3].rpartition(':')[-1].rstrip())/int(events)),True)
#                    evtsiz   = ('%d'%(int(lines[iline+3].rpartition(':')[-1].rstrip())/int(events)))[:-3]
                srcs = []
                iline = iline+4
                line = lines[iline]
                while( (len(line)>17 and line[8]=='.' and line[17]==':') or
                       (len(line)>29 and line[2]=='_' and line[20]=='.' and line[29]==':') or
                       (len(line)>29 and line[20]=='.' and line[29]==':') or
                       (len(line)>41 and line[2]=='_' and line[32]=='.' and line[41]==':') or
                       (len(line)>45 and line[41]==':')):
                    s = line.rsplit(':')
                    srcs.append({'source':s[-2].rstrip(),'n':s[-1].rstrip()})
                    iline = iline+1
                    if (iline>=len(lines)):
                        break
                    line = lines[iline]
                run = {'runnumber':runnumber,
                       'ended':ended,
                       'duration':duration,
                       'evts':events,
                       'dmg':damaged,
                       'bytes':bytes,
                       'evtsz':evtsiz,
                       'sources':srcs,
                       'daq':daq_release,
                       'compress':compression,
                       'ami':ami_release,
                       'ins':instname,
                       'expname':expname,
                       'expnum':expnum}
                
        if run['duration']!='':
            fruns.append(run)

        sources = []
        for r in fruns:
            for s in r['sources']:
                if not s['source'] in sources:
                    sources.append(s['source'])

        if len(sources)==0:
            continue

        if summ:
            print_summary(fname, fruns, sources)
        else:
            print_full(fname, fruns, sources)

           

def print_full(fname,fruns,sources):
    print '\n-----'+fname,
    if len(fruns) != 0:
        print '\n-----%s %s (%s)'%(fruns[0]['ins'],fruns[0]['expname'],fruns[0]['expnum'])
        print '----- DAQ release: %s'%(fruns[0]['daq'])
        print '----- AMI release: %s'%(fruns[0]['ami'])
        if len(fruns[0]['compress']) != 0:
            print '----- Compression status (%s): ' % (fruns[0]['compress'][0]['ts'])
            for det in fruns[0]['compress']:
                print "      %15s (on %s):\tCompression %s." % (det['task'],det['node'], det['msg'])

    fmtttl = '\n%28.28s'
    fmtstr = '%12.12s'
    step = 5
        
    for irun in range(0,len(fruns),step):
        print " "
        runs = fruns[irun:irun+step]
        
        print fmtttl%'Run',
        for r in runs:
            print fmtstr%r['runnumber'],
        
        print fmtttl%'Duration',
        for r in runs:
            print fmtstr%r['duration'],
        
        print fmtttl%'Events',
        for r in runs:
            print fmtstr%r['evts'],

        print fmtttl%'Damaged',
        for r in runs:
            print fmtstr%r['dmg'],
        
        print fmtttl%'Bytes',
        for r in runs:
            print fmtstr%r['bytes'],

        print fmtttl%'EvtSz',
        for r in runs:
            print fmtstr%r['evtsz'],

        print
        for src in sources:
            physid = PHYSID(int(src.split('.')[1],16))
            if physid.det() == 0 and physid.dev() == 0:
                srcstr = src.split('.')[0].strip()
            elif physid.dev() == 0:
                srcstr = "%s-%d"%(physid.detname(), physid.detid())
            elif physid.det() == 0:
                srcstr = "%s-%d"%(physid.devname(), physid.devid())
            else:
                srcstr = "%s-%d|%s-%d"%(physid.detname(), physid.detid(), physid.devname(), physid.devid())
            print fmtttl%srcstr,
            for r in runs:
                lfound=False
                for s in r['sources']:
                    if s['source']==src:
                        lfound=True                        
                        print fmtstr%s['n'],
                if not lfound:
                    print fmtstr%'-',
        print " "
        

def print_summary(fname, fruns,sources):
    print '\n-----'+fname,
    if len(fruns) != 0:
        print '\n-----%s %s (%s)'%(fruns[0]['ins'],fruns[0]['expname'],fruns[0]['expnum'])
        print '----- DAQ release: %s'%(fruns[0]['daq'])
        print '----- AMI release: %s'%(fruns[0]['ami'])
        if len(fruns[0]['compress']) != 0:
            print '----- Compression status (%s): ' % (fruns[0]['compress'][0]['ts'])
            for det in fruns[0]['compress']:
                print "      %15s (on %s):\tCompression %s." % (det['task'],det['node'], det['msg'])

    fmt = '%25.25s %14.14s %15.15s %15.15s %15.15s %15.15s (%6s)  '
    print fmt%('Run', 'Duration', 'Ended', 'Bytes', 'Events', 'Damaged', '%')
    max1=0
    str1=''
    for irun in range(0, len(fruns)):
        r = fruns[irun]
        if int(r['evts']) == 0: pct = 0.0
        else: pct = "%3.2f" % (100.0*int(r['dmg'])/int(r['evts']))
        str = fmt%(r['runnumber'], r['duration'], r['ended'],r['bytes'], r['evts'], r['dmg'], pct)
        for s in  r['sources']:
            if (s['source'].find('EBeam Low Curr') == -1):
                if int(s['n']) > max1:
                    physid = PHYSID(int(s['source'].split('.')[1],16))
                    if physid.det() == 0 and physid.dev() == 0:
                        srcstr = s['source'].split('.')[0].strip()
                    elif physid.dev() == 0:
                        srcstr = "%s-%d"%(physid.detname(), physid.detid())
                    elif physid.det() == 0:
                        srcstr = "%s-%d"%(physid.devname(), physid.devid())
                    else:
                        srcstr = "%s-%d|%s-%d"%(physid.detname(), physid.detid(), physid.devname(), physid.devid())
                    str1 = "%s (%s)" % (srcstr, s['n'])
                    max1 = int(s['n'])

        str += str1
        print str
        max1=0
        str1=' '
    


def fixup_check(path):
    flist = glob.glob(path+'*.log')
    if len(flist)==0:
        return
    args = ["grep","fixup"]+flist
    pfn = subprocess.Popen(args=args,stdout=subprocess.PIPE)
    odate = pfn.communicate()[0].split('\n')
    laststr = None
    lastcnt = 1
    fmtstr='%20.20s'
    lttl = False
    for l in odate:
        if (l[:6]=='/reg/g'):
            thedate = l[29:39]
            thetime = l[40:48]
            thehost = l[49:].partition(':')[0]
            thename = l[49:].split(':')[1].split('.')[0]
            thisstr = fmtstr%thetime+fmtstr%thehost+fmtstr%thename
            if (thisstr==laststr):
                lastcnt = lastcnt+1
            else:
                if (laststr!=None):
                    if not lttl:
                        lttl=True
                        print '\n'+fmtstr%'Time'+fmtstr%'Node'+fmtstr%'Name'+fmtstr%'Fixups'
                    print laststr+fmtstr%lastcnt
                laststr=thisstr
                lastcnt=1
    if (laststr!=None):
        if not lttl:
            lttl=True
            print '\n'+fmtstr%'Time'+fmtstr%'Node'+fmtstr%'File'+fmtstr%'Fixups'
        print laststr+fmtstr%lastcnt


def signal_check(path, signum, signame):
    flist = glob.glob(path+'*.log')
    if len(flist)==0:
        return
    args = ["grep","signal"]+flist
    pfn = subprocess.Popen(args=args,stdout=subprocess.PIPE)
    odate = pfn.communicate()[0].split('\n')
    laststr = None
    lastcnt = 1
    fmtstr='%20.20s'
    lttl = False
    for l in odate:
        if (l[:6]=='/reg/g' and l.find('signal %d'%signum)>=0):
            thedate = l[29:39]
            thetime = l[40:48]
            thehost = l[49:].partition(':')[0]
            thename = l[49:].split(':')[1].split('.')[0]
            thisstr = fmtstr%thetime+fmtstr%thehost+fmtstr%thename
            if (thisstr==laststr):
                lastcnt = lastcnt+1
            else:
                if (laststr!=None):
                    if not lttl:
                        lttl=True
                        print '\n'+fmtstr%'Time'+fmtstr%'Node'+fmtstr%'Name'+fmtstr%signame
                    print laststr+fmtstr%lastcnt
                laststr=thisstr
                lastcnt=1
    if (laststr!=None):
        if not lttl:
            lttl=True
            print '\n'+fmtstr%'Time'+fmtstr%'Node'+fmtstr%'Name'+fmtstr%signame
        print laststr+fmtstr%lastcnt


def hutch_loop(expt, date_path, summ, errs):
    hutches = ['amo','sxr','xpp','xcs','cxi','mec','cxi_0','cxi_1','cxi_shared']
    for hutch in hutches:
        if expt=='all' or expt==hutch.lower():

            path = '/reg/g/pcds/pds/'+hutch+'/logfiles/'+date_path
            if len(glob.glob(path+'*control_gui.log')) == 0: return
            print '=== %s ==='%hutch.upper()
            control_log(path,summ)
            fixup_check(path)
            signal_check(path,6,'SIGABORT')
            signal_check(path,11,'SIGSEGV')
            transition_check(path)
            outoforder_check(path)
            pgpproblem_check(path)
    if options.expt=='local':
        path = os.getenv('HOME')+'/'+date_path
        if len(glob.glob(path+'*control_gui.log')) == 0: return
        print '=== LOCAL ==='
        print path
        control_log(path,summ)        
        if errs:
            fixup_check(path)
            signal_check(path,6,'SIGABORT')
            signal_check(path,11,'SIGSEGV')
            transition_check(path)
            outoforder_check(path)
            pgpproblem_check(path)
            
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)


SUFFIXES = {1024: ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
            1000: ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']}

def humansize(size, a_kilobyte_is_1024_bytes=True):
    '''Convert a file size to human-readable form.

    Arguments:
       size -- size in bytes
       a_kilobyte_is_1024_bytes -- if True (default), use multiples of 1024
                                if False, use multiples of 1000

    Returns: string repressenting file size

    '''
    if size < 0:
        raise ValueError('number must be non-negative')

    multiple = 1024 if a_kilobyte_is_1024_bytes else 1000
    for suffix in SUFFIXES[multiple]:
        size /= multiple
        if size < multiple:
            return '%8.1f %s'%(size, suffix)

    raise ValueError('number too large')

def pid2task(path,pid):
    flist=glob.glob(path+'*.log')
    tasks = []
    task = {'pid':0}
    args = ["grep","PID"]+flist
    p    = subprocess.Popen(args=args,stdout=subprocess.PIPE)
    output = p.communicate()[0].split('\n')
    for line in output:
        if line.find('@@@ The PID of new child')>=0:
            line = line.split("@@@ The PID of new child")[1]
            thedate = line.split('logfiles/')[1].split('_')[0]
            thetime = line.split('_')[1]
            thenode = line.split('_')[2].split(':')[0]
            thename = line.split('_')[2].split(':')[1].split('.')[0]
            thepid = line.split('is: ')[1].strip()
            task={'date':thedate, 'time':thetime, 'node':thenode,'name':thename,'pid':thepid}
            tasks.append(task)              
            if pid == thepid:
                return task
    return 0



def transition_check(path):
    print_header = True
    fmtstr="%15.15s"
    longfmtstr="%25.25s"
    for fname in glob.iglob(path+'*control_gui.log'):
        logtime=fname.split(path)[1].split('_')[1]
        fruns = []
        f = file(fname,"r")
        lines = f.readlines();
        
        for iline in range(len(lines)):
            line = lines[iline]
            if (line.find("Completed allocating")>=0):
                runnumber = line.split()[-1]
            index = line.find("Timeout waiting for transition")
            if (index>=0):
                try:
                    trans_time = line.partition(': Timeout')[0].rstrip().split('_')[1][:-9]
                    transition = line.split(' to complete.')[0].strip().split('transition ')[1]
                    nodes = lines[iline+1].rpartition(':')[-1].rstrip()
                    segment, pid = lines[iline+2].split(':')[1:]
                    segment = segment.strip()
                    pid = pid.strip()
                    task = pid2task(path+'_'+logtime, pid)
                
                    if print_header:
                        print '\n'+fmtstr%'Time'+longfmtstr%'Transition Timeout'+longfmtstr%'Task'+fmtstr%'PID'+longfmtstr%'Node'
                        print_header = False

                    print fmtstr%trans_time+longfmtstr%transition+longfmtstr%task['name']+fmtstr%task['pid']+longfmtstr%task['node']
                except:
                    pass

def outoforder_check(path):
    print_header = True
    flist = glob.glob(path+"*.log")
    args = ["grep","--binary-files=text", "order"]+flist
    p    = subprocess.Popen(args=args,stdout=subprocess.PIPE)
    output = p.communicate()[0].split('\n')
    for line in output:
        if (len(line) != 0) and (line.find("response") == -1) and (line.find("vmonrecorder") == -1):
            if print_header:
                print "\nOut of Order errors:"
                print_header = False
            print line
    print ""
    return 0

def node2name(flist,node):
    name = "Unknown node: %s" % node
    hutch = flist[0].split("/reg/g/pcds/pds/")[1].split("/logfiles")[0]
    if (hutch.find('cxi') != -1):
        exp = "cxi"
    else:
        exp = hutch
    flist=glob.glob('/reg/g/pcds/dist/pds/'+exp+'/scripts/'+hutch+'.cnf')
    if (len(flist) != 0):
        args = ["grep",node]+flist
        p    = subprocess.Popen(args=args,stdout=subprocess.PIPE)
        output = p.communicate()[0].split('\n')
        for line in output:
            if ((len(line) != 0) and (line.find(node) != -1)):
                name = line.split('=')[0].strip()
    return name


def ami_version(path, thetime):
    rv = ''
    flist = glob.glob(path+"_"+thetime+"*ami_client.log")
    if len(flist) != 0:
        args = ["grep", "@@@    (as "]+flist
        p    = subprocess.Popen(args=args,stdout=subprocess.PIPE)
        output = p.communicate()[0].split('\n')
        for line in output:
            if (len(line) != 0) and (line.find("online_ami") != -1):
                release = line.split("as ")[1].strip().strip(')')
                if release.find("/reg/g/pcds/dist/pds/") != -1:
                    rv = release.split("/reg/g/pcds/dist/pds/")[1].split('/')[0]
                else:
                    rv = release
    return rv


def compression_check(path,thetime):
    retval = []
    flist = glob.glob(path+"_"+thetime+"*.log")

    if len(flist) != 0:
        args = ["grep", "Compression"]+flist
        p    = subprocess.Popen(args=args,stdout=subprocess.PIPE)
        output = p.communicate()[0].split('\n')
        for line in output:
            if (len(line) != 0) and (line.find("Compression") != -1):
                timestamp = line.split('/logfiles/')[1].replace('_',' ',1).split('_')[0]
                if (line.find('cxi_') != -1):
                    node = line.split('_')[3].split(':')[0]
                else:
                    node = line.split('_')[2].split(':')[0]
                task = line.split(':')[3].split('.')[0]
                msg = line.split('.log:')[1].split('Compression is')[1].strip().strip('.')
                task = line.split(':')[3].split('.')[0]
                retval.append({'node':node2name(flist,node),'task':task,'ts':timestamp,'msg':msg})
    return retval


def pgpproblem_check(path):
    print_header=True
    flist = glob.glob(path+"*cspad*.log")
    flist += glob.glob(path+"*Pnccd*.log")
    if len(flist) != 0:
        args = ["grep", "--binary-file=text","ERESTART"]+flist
        p    = subprocess.Popen(args=args,stdout=subprocess.PIPE)
        output = p.communicate()[0].split('\n')
        for line in output:
            if (len(line) != 0) and (line.find("ERESTART") != -1):
                if print_header:
                    print "PGP problems:\n"
                    print_header = False
                    print line
            

if __name__ == "__main__":

    import sys

    parser = OptionParser()
    parser.add_option("-e","--expt",dest="expt",default="all",
                      help="Check logs for EXPT hutch", metavar="EXPT")
    parser.add_option("-d","--day",dest="day",default="0",
                      help="Check logs DAY days ago", metavar="DAY")
    parser.add_option("-s","--summ",default=False,action="store_true",
                      help="Print summary of control_log information", metavar="SUMM")
    parser.add_option("-b", "--beg",dest="beg_date",default="0",
                      help="Check logs from given date \%Y/\%M/\%d to end date (now if no end date given)",
                      metavar="BEG")
    parser.add_option("-f", "--end",dest="end_date",default="0",
                      help="Check logs from given date \%Y/\%M/\%d (or YYYY/MM/dd) to end (finish) date", metavar="END")
    parser.add_option("-r", "--err", default=False,action="store_true",metavar="ERR",
                      help="Report error conditions in the logfiles:  Out of Order Errors, transition timeouts, ERESTART errors")
    
    (options, args) = parser.parse_args()
    
    
    thisdate = datetime.date.today() - datetime.timedelta(int(options.day))
    date_path = thisdate.strftime('%Y/%m/%d')

    if options.beg_date!="0":
        year,month,day=options.beg_date.replace('-','/').strip().split('/')
        beg_date = datetime.date(int(year), int(month), int(day))

        if options.end_date!="0":
            end_year, end_month, end_day = options.end_date.replace('-','/').strip().split('/')
            end_date = datetime.date(int(end_year),int(end_month),int(end_day))
        else:
            end_date = datetime.date.today()
    
        for single_date in daterange(beg_date,end_date):
            date_path = single_date.strftime("%Y/%m/%d")
            hutch_loop(options.expt.lower(), date_path, options.summ, options.err)
    else:
        hutch_loop(options.expt.lower(), date_path, options.summ, options.err)
        
