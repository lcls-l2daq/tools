#!/bin/csh
#
#  Copy libraries, binaries, and include files
#
if ($# < 1) exit

setenv AMIREL /reg/g/pcds/dist/pds/ami-$1
mkdir -p ${AMIREL}
mkdir -p ${AMIREL}/ami

#  Copy libraries and binaries
rsync -rlpogtSP --exclude={dep,obj} build ${AMIREL}/.

#  Copy the header files
rsync -rlpogtSP --exclude={Makefile,CVS,\*.cc,\*.mk} ami/data ${AMIREL}/ami/.
