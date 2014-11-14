#!/bin/bash
#

set -u
set -e

if  [ $# -ne 1 ]
then
  echo "Usage: $0 <outfile>"
  exit 1
fi

# copy the header files
/bin/mkdir -pv build/timetool/service
/bin/cp -pv timetool/service/*.hh build/timetool/service

# create the tar file
/bin/tar czvf $1 --exclude=.svn --exclude=dep --exclude=obj --exclude=.buildbot-sourcedata build tools

