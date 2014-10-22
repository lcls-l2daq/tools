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
mkdir -p ${AMIREL}/ami/event
rsync -rlpogtSP ami/event/CspadTemp.hh ${AMIREL}/ami/event/.

# Create soft link in DAQREL directory
cd /reg/g/pcds/dist/pds
if ( -e /reg/g/pcds/dist/pds/ami-current ) then
    rm -f /reg/g/pcds/dist/pds/ami-current
endif
ln -s ./$1 ami-current
cd -
