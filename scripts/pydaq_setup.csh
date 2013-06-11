setenv DAQREL $1
setenv PYTHONPATH ${DAQREL}/build/pdsapp/lib/x86_64-linux:${DAQREL}/build/ami/lib/x86_64-linux
setenv LD_LIBRARY_PATH /reg/g/pcds/package/python-2.5.2/lib:${DAQREL}/build/pdsdata/lib/x86_64-linux:${DAQREL}/build/pdsapp/lib/x86_64-linux:${DAQREL}/build/ami/lib/x86_64-linux:${DAQREL}/build/qt/lib/x86_64-linux
