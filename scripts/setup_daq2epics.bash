#
# Use this script prepare your bash environment for running daq2epics
# Note! Currently RHEL6 is assumed. 
#
export PATH=/reg/common/package/python/2.7.5/x86_64-rhel6-gcc44-opt/bin:$PATH
export LD_LIBRARY_PATH=/reg/common/package/epicsca/3.14.9/lib/x86_64-linux-opt:/reg/common/package/epics-base/3.14.12.3/x86_64-rhel5-gcc41-opt/lib
export PYTHONPATH=/reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel6-gcc44-opt/lib/python2.7/site-packages
export EPICS_CAS_INTF_ADDR_LIST=$(/bin/hostname -i)
