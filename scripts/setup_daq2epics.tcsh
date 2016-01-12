#
# Use this script prepare your tcsh environment for running daq2epics
# Note! Currently RHEL6 is assumed. 
#
setenv PATH /reg/common/package/python/2.7.5/x86_64-rhel6-gcc44-opt/bin:$PATH
setenv LD_LIBRARY_PATH /reg/common/package/epicsca/3.14.9/lib/x86_64-linux-opt:/reg/common/package/epics-base/3.14.12.3/x86_64-rhel5-gcc41-opt/lib
setenv PYTHONPATH /reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel6-gcc44-opt/lib/python2.7/site-packages
setenv EPICS_CAS_INTF_ADDR_LIST `hostname -i`
