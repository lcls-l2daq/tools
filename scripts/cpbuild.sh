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

if ( -e build/ami ) then
    mkdir -p ${DAQREL}/ami/event
    rsync -rlpogtSP --exclude={Makefile,.svn,CVS,\*.cc,\*.mk,\*\~} ami/data ${DAQREL}/ami/.
    rsync -rlpogtSP ami/event/CspadTemp.hh ${DAQREL}/ami/event/.
endif

# Create soft link in DAQREL directory
cd /reg/g/pcds/dist/pds
if ( -e /reg/g/pcds/dist/pds/current ) then
    rm -f /reg/g/pcds/dist/pds/current
endif
ln -s ./$1 current
cd -
