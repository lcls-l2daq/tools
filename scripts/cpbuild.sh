#!/bin/csh
#
#  Copy libraries, binaries, and include files
#
if ($# < 1) exit

setenv DAQREL /reg/g/pcds/dist/pds/$1
mkdir -p ${DAQREL}

#  Copy libraries and binaries
rsync -rlpogtSP --exclude={dep,obj} build ${DAQREL}/.

#  Copy tools
rsync -rlpogtSP --exclude={CVS} tools ${DAQREL}/.

