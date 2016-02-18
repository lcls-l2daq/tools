#
# Use this script prepare your bash environment for running daq2epics or exp2epics
# Note! RHEL6 and RHEL7 are supported. 
#

RELEASE_FILE="/etc/redhat-release"

/usr/bin/head -v $RELEASE_FILE
if grep --quiet 'release 6' $RELEASE_FILE; then
  # RHEL6
  export PATH=/reg/common/package/python/2.7.5/x86_64-rhel6-gcc44-opt/bin:$PATH
  export PYTHONPATH=/reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel6-gcc44-opt/lib/python2.7/site-packages
elif grep --quiet 'release 7' $RELEASE_FILE; then
  # RHEL7
  export PATH=/reg/common/package/python/2.7.5/x86_64-rhel7-gcc48-opt/bin:$PATH
  export PYTHONPATH=/reg/common/package/pcaspy/0.4.1b-python2.7/x86_64-rhel6-gcc44-opt/lib/python2.7/site-packages
else
  echo "This OS release is not supported"
fi

source /reg/g/pcds/setup/epicsenv-3.14.12.sh
export EPICS_CAS_INTF_ADDR_LIST=$(/bin/hostname -i)
