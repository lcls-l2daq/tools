#!/reg/common/package/python/2.5.5/bin/python
#
#  Execute from pssrv100 to monitor DAQ switch stats
#

import subprocess
import os
import time
import getpass
import time
from collections import deque
from optparse import OptionParser
import sys

sys.path.insert(0,'/reg/common/package/pexpect-2.3')
import pexpect

hutch = ''

#
#  Port counter tuple [0]: port name
#                     [1]: node name
#                     [2]: list of counters
#                         [0]: counter widget
#                         [1]: value array
#

def get_partition(expt,node):

    print 'Fetch partition for '+expt
    # Need exact hostname for expect to match
    name = 'pslogin01'
    print name+' ',
    passwd = getpass.getpass()
    uname = os.getenv('USER')
    
    COMMAND_PROMPT = uname + '@' + name
        
    child = pexpect.spawn('ssh %s'%name)
    i = child.expect([pexpect.TIMEOUT, '(?i)password', COMMAND_PROMPT])
    if i == 0: # Timeout
        print 'ERROR! could not login with SSH. Here is what SSH said:'
        print child.before, child.after
        print str(child)
        sys.exit (1)
    if i == 1:
        child.sendline(passwd)
        child.expect(COMMAND_PROMPT)
    if i == 2:
        print 'ssh %s successful'%name

    inode=0
    
    COMMAND_PROMPT = uname + '@' + node[inode]
    child.sendline('ssh %s'%node[inode])
    i = child.expect([pexpect.TIMEOUT, '(?i)password', COMMAND_PROMPT])
    if i == 0: # Timeout
        print 'ERROR! could not login with SSH. Here is what SSH said:'
        print child.before, child.after
        print str(child)
        sys.exit (1)
    if i == 1:
        child.sendline(passwd)
        child.expect(COMMAND_PROMPT)
    if i == 2:
        print 'ssh %s successful'%node[inode]

    seg_ips = []
    evt_ips = []
    child.sendline('/reg/g/pcds/dist/pds/'+expt+'/current/build/pdsapp/bin/i386-linux-opt/showPartitions')
    i = child.expect(COMMAND_PROMPT)
    lines = child.before.split('\n')
    for oline in lines:
        word = oline.split()[-1]
        if word.find('.')>=0:
            if word[0]=='2':
                seg_ips.append(word.split('/')[-1])
            elif word[0]=='3':
                evt_ips.append(word.split('/')[-1])

    if len(seg_ips)==0:
        exit(1)
    
    mon_ips = []
    for n in range(13):
        mnode = 'daq-'+expt+'-mon%02d'%n
        print 'Seeking '+mnode
        child.sendline('nslookup '+mnode)
        i = child.expect(COMMAND_PROMPT)
        lines = child.before.split('\n')
        lName = False
        for oline in lines:
            words = oline.split()
            if lName:
                ip = words[1].split('.')
                ip[2] = seg_ips[0].split('.')[2]
                mon_ips.append('.'.join(ip))
                break
            else:
                if (len(words)>0) and (words[0]=='Name:'):
                    lName = True

    seg_ports = []
    evt_ports = []
    mon_ports = []

    while(True):
        child.sendline('/sbin/arp -a')
        i = child.expect(COMMAND_PROMPT)
        lines = child.before.split('\n')
        for oline in lines:
            words = oline.split()
            if len(words)>3:
                ip  = words[1][1:-1]
                mac = words[3]
                if ip in seg_ips:
                    seg_ports.append([ip,mac,'none',[]])
                elif ip in evt_ips:
                    evt_ports.append([ip,mac,'none',[]])
                elif ip in mon_ips:
                    mon_ports.append([ip,mac,'none',[]])

        inode=inode+1
        if inode<len(node):
            child.sendline('exit')
            
            COMMAND_PROMPT = uname + '@' + node[inode]
            child.sendline('ssh %s'%node[inode])
            i = child.expect([pexpect.TIMEOUT, '(?i)password', COMMAND_PROMPT])
            if i == 0: # Timeout
                print 'ERROR! could not login with SSH. Here is what SSH said:'
                print child.before, child.after
                print str(child)
                sys.exit (1)
            if i == 1:
                child.sendline(passwd)
                child.expect(COMMAND_PROMPT)
            if i == 2:
                print 'ssh %s successful'%node[inode]
        else:
            break

    return [seg_ports,evt_ports,mon_ports]

class MyTable:
    def __init__(self,name,ports,counters):
        self._name = name
        self._ports = ports
	self._counters = counters
        for p in ports:
            for c in counters:
                p[3].append(([0,0]))

    def update(self):
	print '%20.20s'%'Port',
	for c in self._counters:
	    print '%12.12s'%c,
	print
        for p in self._ports:
	    print '%20.20s'%p[0],
            for c in p[3]:
                val = c[0]-c[1]
		print '%12d'%val,
                c[1] = c[0]
	    print
	print
		
class SshSwitch:
    def __init__(self,name,ports,counters):
        self.host     = name
        self.counters = counters
        self.ports    = ports
        
        print name+' ',
        passwd=getpass.getpass()

        self.COMMAND_PROMPT = 'SSH@' + name + '>'
        
        child = pexpect.spawn('ssh %s'%name)
        i = child.expect([pexpect.TIMEOUT, '(?i)password'])
        if i == 0: # Timeout
            print 'ERROR! could not login with SSH. Here is what SSH said:'
            print child.before, child.after
            print str(child)
            sys.exit (1)
        if i == 1:
            child.sendline(passwd)
            child.expect(self.COMMAND_PROMPT)

        for pset in ports:
            for p in pset:
                hmac = p[1][0:2]+p[1][3:5]
                hmac = hmac+'.'+p[1][6:8]+p[1][9:11]
                hmac = hmac+'.'+p[1][12:14]+p[1][15:17]
                child.sendline('sho mac-addr '+hmac)
                i = child.expect(self.COMMAND_PROMPT)
                lines = child.before.split('\n')
                for oline in lines:
                    if 'Dynamic' in oline:
                        p[2] = oline.split()[1]
                        break

        self.child = child
        
    def update(self):
        for g in range(len(self.ports)):
            for p in self.ports[g]:
                self.child.sendline('sho stat eth '+p[2])
                while(True):
                    i = self.child.expect([self.COMMAND_PROMPT,'--More--'])
                    lines = self.child.before.split('\n')
                    counters = [] + self.counters[g]
                    updated = 0
                    for oline in lines:
                        for ic in range(len(counters)):
                            c = counters[ic]
                            index = oline.find(c)
                            if index>=0:
                                updated = updated+1
                                v = int(oline[index+len(c)+1:].split(None,1)[0])
                                p[3][ic][0] = v
                        if len(counters)==updated:
                            break
                    if i == 0:
                        break
                    if i == 1:
                        self.child.send(' ')
                
def hoststats(host_base,counter_string):
    value=[]
    for i in range(3,5):
        host_name = host_base+'%02d'%i
        cmd = ['snmpnetstat','-c','public','-Os','-v','2c',host_name,'-Cs','-Cp','udp']
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        p.wait()
        v = 0
        for oline in p.stdout:
            if counter_string in oline:
                v = int(oline.split(None,1)[0])
                break
        value.append(v)
    return value


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-x","--experiment",dest="hutch",default='cxi',
	help="monitor network in hutch HUTCH", metavar="HUTCH")

    (options, args) = parser.parse_args()
    hutch = options.hutch.lower()

    console_name=[]
    if hutch=='xcs':
        switch_name='switch-'+hutch+'-mezz-daq'
        console_name.append(hutch+'-control')
    elif hutch=='cxi':
        switch_name='switch-'+hutch+'-mezz-daq'
        console_name.append(hutch+'-daq')
        console_name.append(hutch+'-monitor')
    elif hutch=='xpp':
        switch_name='switch-'+hutch+'-srvroom-daq'
        console_name.append(hutch+'-daq')
        console_name.append(hutch+'-control')
    else:
        switch_name='switch-'+hutch+'-srvroom-daq'
        console_name.append(hutch+'-daq')
        
    macs     = get_partition(hutch,console_name)
    counters = [ ["InOctets","OutFlowCtrlPkts"],["OutOctets","InFlowCtrlPkts"],["OutOctets","InFlowCtrlPkts"] ]
    
#    in_oct_plot  = MyPlot("switch port","InOctets"  ,sw_ports,2.0e9)
#    in_pkt_plot  = MyPlot("switch port","InFlowCtrl",sw_ports,1.0e2)
#    in_err_plot  = MyPlot("switch port","InDiscards",sw_ports,0)

#    out_oct_plot = MyPlot("switch port","OutOctets"  ,sw_ports,2.0e9)
#    out_pkt_plot = MyPlot("switch port","OutFlowCtrl",sw_ports,2.0e2)


    seg_table = MyTable(switch_name,macs[0],counters[0])
    evt_table = MyTable(switch_name,macs[1],counters[1])
    mon_table = MyTable(switch_name,macs[2],counters[2])
    
    sw = SshSwitch(switch_name,macs,counters)
    
    while(True):
        try:
            sw   .update()
            seg_table.update()
            evt_table.update()
            mon_table.update()

#            hostDrops = hoststats(host_base,'datagrams dropped')
            
            time.sleep(1.0)
#            break
        
        except KeyboardInterrupt:    
            sys.exit()
        except OSError:
            print 'OSError'
        except:
            inst = sys.exc_info()[0]
            print type(inst)
            print inst.args
            print inst
            raise
