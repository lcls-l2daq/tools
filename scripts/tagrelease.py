#!/usr/bin/python
#

import os
import subprocess

tag=None
DAQURL='https://pswww.slac.stanford.edu/svn/pdsrepo'

def make_tag(pkg):
	path=DAQURL+'/'+pkg
	cmd = ['svn','copy',path+'/trunk',path+'/tags/'+tag,'-m','\"Tag '+tag+'\"']
	subprocess.call(cmd)

def make_tagd(pkg):

    if (os.path.isdir(pkg)):
        make_tag(pkg)

if __name__ == '__main__':

    import sys

    if len(sys.argv) < 2:
	print 'Usage: '+sys.argv[0]+' <tag>'

    else:
	tag=sys.argv[1]
        if tag.find('ami')<0:
            make_tag('release')
            make_tagd('pds')
            make_tagd('pdsapp')
            make_tagd('timetool')
            make_tagd('tools')
        else:
            make_tag('ami-release')
            make_tagd('ami')
            make_tagd('tools')

