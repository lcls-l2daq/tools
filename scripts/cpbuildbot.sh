#!/bin/bash
#
#  Copy libraries, binaries, and include files of latest buildbot release
#  to standard DAQ release area
#

function usage()
{
    echo -e "\nCopy the latest buildbot release to the PCDS release area and set current link(s)."
    echo -e "If the release name is preceded by 'ami-', then the lates AMI release is copied."
    echo -e "\nUsage:\n$0 <DAQ/AMI release> \n" 
}


if [ $# -lt 1 ]; then
    echo "ERROR:  Please provide DAQ/AMI release name"
    usage;
    exit 0;
fi

if [[ $1 == "ami-"* ]]; then
    RELTYP="ami"
    CURRENT="ami-current"
else
    RELTYP="pdsapp"
    CURRENT="current"
fi

DAQREL="/reg/g/pcds/dist/pds/$1"
mkdir -p ${DAQREL}
BOT="/reg/neh/home1/caf/Buildbot/out"
CWD=`pwd`
cd $DAQREL


#  Copy rhel5 libraries and binaries
DAQBOT=$(ls -t -1 $BOT/pdsbuild-${RELTYP}-rhel5-*)
for i in ${DAQBOT[@]}; do DAQBOT="$i"; break; done
echo "Copying $DAQBOT to $DAQREL"
cp -rf $DAQBOT $DAQREL
/bin/tar -xzf $DAQREL/*rhel5*.tar.gz

#  Copy rhel6 libraries and binaries
#DAQBOT=$(ls -t -1 $BOT/pdsbuild-${RELTYP}-rhel6-*)
#for i in ${DAQBOT[@]}; do DAQBOT="$i"; break; done
#echo "Copying $DAQBOT to $DAQREL"
#cp -rf $DAQBOT $DAQREL
#/bin/tar -xzf $DAQREL/*rhel6*.tar.gz

#  Copy rhel7 libraries and binaries
DAQBOT=$(ls -t -1 $BOT/pdsbuild-${RELTYP}-rhel7-*)
for i in ${DAQBOT[@]}; do DAQBOT="$i"; break; done
echo "Copying $DAQBOT to $DAQREL"
cp -rf $DAQBOT $DAQREL
/bin/tar -xzf $DAQREL/*rhel7*.tar.gz

# Create soft link in DAQREL directory
cd /reg/g/pcds/dist/pds
if [ -e /reg/g/pcds/dist/pds/${CURRENT} ]; then
    rm -f /reg/g/pcds/dist/pds/${CURRENT}
fi
ln -s ./$1 ${CURRENT}

cd $CWD
