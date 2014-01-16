#!/bin/csh
#
#  Copy libraries, binaries for padmon,ami
#
if ($# < 1) exit

setenv DAQREL $1
mkdir -p ${DAQREL}

#  Copy libraries and binaries
rsync -avm --del --include={libconfigdata.so,libpadmon.so} -f 'hide,! */' build/ ${DAQREL}

rsync -rlpogtSP --exclude={dep,obj} build/ami ${DAQREL}/.

mkdir -p ${DAQREL}/pdsdata/lib
rsync -rpogtDLvm build/pdsdata/lib/ ${DAQREL}/pdsdata/lib

mkdir -p ${DAQREL}/psalg/lib
rsync -rpogtDLvm build/psalg/lib/ ${DAQREL}/psalg/lib

mkdir -p ${DAQREL}/qt/lib
rsync -rpogtDLvm build/qt/lib/ ${DAQREL}/qt/lib

mkdir -p ${DAQREL}/qwt/lib
rsync -rpogtDLvm build/qwt/lib/ ${DAQREL}/qwt/lib

mkdir -p ${DAQREL}/gsl/lib
rsync -rpogtDLvm build/gsl/lib/ ${DAQREL}/gsl/lib

#  Copy tools
#rsync -rlpogtSP --exclude={CVS} tools ${DAQREL}/.

