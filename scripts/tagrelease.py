#!/usr/bin/python
#

import os
import subprocess
from tempfile import NamedTemporaryFile, mkdtemp
from shutil import rmtree

tag=None
DAQURL='https://pswww.slac.stanford.edu/svn/pdsrepo'

def make_tag(pkg):
    path=DAQURL+'/'+pkg
    cmd = ['svn','copy',path+'/trunk',path+'/tags/'+tag,'-m','\"Tag '+tag+'\"']
    return subprocess.call(cmd)

def make_tagd(pkg):
    retval = 0
    if (os.path.isdir(pkg)):
        retval = make_tag(pkg)
    else:
        print 'Warning: directory \'%s\' not found, tagging skipped' % pkg
    return retval

def checkout(tmpdir, project):
    os.chdir(tmpdir)
    cmd = '/usr/bin/svn co --depth files %s/%s/tags/%s %s' % (DAQURL, project, tag, project)
    p = subprocess.Popen([cmd], shell = True, stdout = subprocess.PIPE, close_fds = True)
    return subprocess.Popen.communicate(p)[0]

def get_externals_property(project_path):
    p = subprocess.Popen(['/usr/bin/svn propget svn:externals '+project_path], shell = True, stdout = subprocess.PIPE, close_fds = True)
    return subprocess.Popen.communicate(p)[0]

def set_externals_property(project_path, newpropvalue, oldtext, newtext):
    retvalue = 1
    # write new property to a temporary file
    tt = NamedTemporaryFile()   # create temporary file with visible name in the file system
    tt.write(newpropvalue)
    tt.flush()                  # flush the written data before svn reopens the file for reading
    rv = subprocess.call(['/usr/bin/svn propset svn:externals -F %s %s' % (tt.name, project_path)], shell=True)
    tt.close()                  # the temporary file is deleted as soon as it is closed
    if rv:
        print 'Error: svn propset failed'
    else:
        if subprocess.call(['/usr/bin/svn commit -m \'changed externals from %s to %s\' %s' % (oldtext, newtext, project_path)], shell=True):
            print 'Error: svn commit failed'
        else:
            retvalue = 0
    return retvalue

def update_externals_property(tmpdir, project, oldtext, newtext):
    retval = 1
    if not checkout(tmpdir, project):
        print 'Error: checkout of %s/tags/%s from %s failed' % (project, tag, DAQURL)
    else:
        # read old externals property value
        oldexternals = get_externals_property(tmpdir+'/'+project)

        # create new externals property value based on the old one
        newexternals = oldexternals.replace(oldtext,newtext)

        if newexternals == oldexternals:
            print 'Error: failed to replace trunk with tag in svn:externals property'
        else:
            # write new externals property value
            if set_externals_property(tmpdir+'/'+project, newexternals, oldtext, newtext):
                print 'Error: setting svn:externals property failed'
            else:
                retval = 0
    return retval

if __name__ == '__main__':

    import sys

    retval = 1
    if len(sys.argv) != 2:
        print 'Usage: '+sys.argv[0]+' <tag>'
    else:
        tag=sys.argv[1]
        tmpdir = mkdtemp()  # create temporary directory
        if tag.find('ami')<0:
            if make_tag('release'):
                print 'Error: tagging release failed'
            else:
                make_tagd('pds')
                make_tagd('pdsapp')
                make_tagd('timetool')
                make_tagd('tools')
                # update externals
                if update_externals_property(tmpdir, 'release', 'trunk', 'tags/'+tag):
                    print 'Error: updating svn:externals property failed'
                else:
                    retval = 0  # success
        else:
            if make_tag('ami-release'):
                print 'Error: tagging ami-release failed'
            else:
                make_tagd('ami')
                make_tagd('tools')
                # update externals
                if update_externals_property(tmpdir, 'ami-release', 'trunk', 'tags/'+tag):
                    print 'Error: updating svn:externals property failed'
                else:
                    retval = 0  # success
        rmtree(tmpdir)              # delete temorary directory
    sys.exit(retval)
