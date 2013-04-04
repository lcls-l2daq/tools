#!/reg/g/pcds/package/python-2.5.2/bin/python
#

import subprocess
import datetime
import glob
from optparse import OptionParser

def control_log(path):
    for fname in glob.iglob(path+'*control_gui.log'):
        fruns = []
        f = file(fname,"r")
        lines = f.readlines();
        run = {'duration':''}
        runnumber = '-'
        for iline in range(len(lines)):
            line = lines[iline]
            if (line.find("Configured")>=0 or line.find("Unmapped")>=0):
                if run['duration']!='':
                    fruns.append(run)
                    run = {'duration':''}
                    runnumber = '-'
            if (line.find("Completed allocating")>=0):
                runnumber = line.split()[-1]
            index = line.find("Duration")
            if (index>=0):
                duration = line.partition(' ')[-1].rstrip()
                events   = lines[iline+1].rpartition(':')[-1].rstrip()
                damaged  = lines[iline+2].rpartition(':')[-1].rstrip()
                bytes    = lines[iline+3].rpartition(':')[-1].rstrip()[:-9]
                if int(events)==0:
                    evtsiz = ''
                else:
                    evtsiz   = ('%d'%(int(lines[iline+3].rpartition(':')[-1].rstrip())/int(events)))[:-3]
                srcs = []
                iline = iline+4
                line = lines[iline]
                while( (line[ 8]=='.' and line[17]==':') or
                       (line[2]=='_' and line[20]=='.' and line[29]==':') or
                       (line[20]=='.' and line[29]==':') or
                       (len(line)>41 and line[2]=='_' and line[32]=='.' and line[41]==':')):
                    s = line.rsplit(':')
                    srcs.append({'source':s[-2].rstrip(),'n':s[-1].rstrip()})
                    iline = iline+1
                    if (iline>=len(lines)):
                        break
                    line = lines[iline]
                run = {'runnumber':runnumber, 'duration':duration, 'evts':events, 'dmg':damaged, 'bytes':bytes, 'evtsz':evtsiz, 'sources':srcs}

        if run['duration']!='':
            fruns.append(run)

        sources = []
        for r in fruns:
            for s in r['sources']:
                if not s['source'] in sources:
                    sources.append(s['source'])

        if len(sources)==0:
            continue
        
        print '\n-----'+fname,

        fmtttl = '\n%28.28s'
        fmtstr = '%12.12s'
        step = 5
        
        for irun in range(0,len(fruns),step):
            runs = fruns[irun:irun+step]
            
            print fmtttl%'Run Number',
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
            
            print fmtttl%'Bytes[GB]',
            for r in runs:
                print fmtstr%r['bytes'],

            print fmtttl%'EvtSz[kB]',
            for r in runs:
                print fmtstr%r['evtsz'],

            for src in sources:
                print fmtttl%src,
                for r in runs:
                    lfound=False
                    for s in r['sources']:
                        if s['source']==src:
                            lfound=True
                            print fmtstr%s['n'],
                    if not lfound:
                        print fmtstr%'-',

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


if __name__ == "__main__":

    import sys

    parser = OptionParser()
    parser.add_option("-e","--expt",dest="expt",default="all",
                      help="Check logs for EXPT hutch", metavar="EXPT")
    parser.add_option("-d","--day",dest="day",default="0",
                      help="Check logs DAY days ago", metavar="DAY")
    
    (options, args) = parser.parse_args()

    thisdate = datetime.date.today() - datetime.timedelta(int(options.day))
    
    date_path = thisdate.strftime('%Y/%m/%d')

    hutches = ['amo','sxr','xpp','xcs','cxi','mec']
    for hutch in hutches:
        if options.expt=='all' or options.expt==hutch:
            print '=== %s ==='%hutch.upper()
            path = '/reg/g/pcds/pds/'+hutch+'/logfiles/'+date_path
            control_log(path)
            fixup_check(path)
            signal_check(path,6,'SIGABORT')
            signal_check(path,11,'SIGSEGV')
