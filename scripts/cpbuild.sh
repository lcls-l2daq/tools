#!/bin/csh
#
#  Copy libraries, binaries, and include files
#
if ($# < 1) exit

setenv DAQREL /reg/g/pcds/dist/pds/$1
mkdir -p ${DAQREL}
mkdir -p ${DAQREL}/ami

#  Copy libraries and binaries
rsync -rlpogtSP --exclude={dep,obj} build ${DAQREL}/.

#  Copy the header files
rsync -rlpogtSP --exclude={Makefile,CVS,\*.cc,\*.mk} ami/data ${DAQREL}/ami/.

#  Copy header files from unwanted dependencies
mkdir -p ${DAQREL}/ami/event
cp ami/event/CspadTemp.hh ${DAQREL}/ami/event/.

#  Copy tools
rsync -rlpogtSP --exclude={CVS} tools ${DAQREL}/.

