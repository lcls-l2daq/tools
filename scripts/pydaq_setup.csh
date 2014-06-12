setenv DAQREL $1
setenv AMIREL $2
setenv PYTHONPATH ${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux
setenv LD_LIBRARY_PATH /reg/g/pcds/package/python-2.5.2/lib:${DAQREL}/build/pdsdata/lib/x86_64-linux:${DAQREL}/build/pdsalg/lib/x86_64-linux:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux:${DAQREL}/build/pds/lib/x86_64-linux:${DAQREL}/build/qt/lib/x86_64-linux
