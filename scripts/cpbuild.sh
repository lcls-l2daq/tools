#!/bin/csh
#
#  Copy libraries, binaries, and include files
#
if ($# < 1) exit

setenv DAQREL /reg/g/pcds/dist/pds/$1
mkdir -p ${DAQREL}
#  Copy libraries and binaries
rsync -rlpogtSP --exclude={dep,obj} build ${DAQREL}/.

#  Copy the header files
mkdir -p ${DAQREL}/build/timetool/service
rsync -rlpogtSP --exclude={Makefile,CVS,\*.cc,\*.mk} timetool/service ${DAQREL}/build/timetool/.

#  Copy tools
rsync -rlpogtSP --exclude={CVS} tools ${DAQREL}/.

