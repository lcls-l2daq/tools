#!/usr/bin/python
#

import os
import subprocess

tag=None
DAQURL='https://pswww.slac.stanford.edu/svn/pdsrepo'

def make_tag(pkg):

    if (os.path.isdir(pkg)):
	path=DAQURL+'/'+pkg
	cmd = ['svn','copy',path+'/trunk',path+'/tags/'+tag,'-m','\"Tag '+tag+'\"']
	subprocess.call(cmd)

if __name__ == '__main__':

    import sys

    if len(sys.argv) < 2:
	print 'Usage: '+sys.argv[0]+' <tag>'

    else:
	tag=sys.argv[1]
	path=DAQURL+'/release'
	cmd = ['svn','copy',path+'/trunk',path+'/tags/'+tag,'-m','\"Tag '+tag+'\"']
	subprocess.call(cmd)
	
	make_tag('pds')
	make_tag('pdsapp')
	make_tag('timetool')
	make_tag('tools')
	make_tag('ami')

