#!/bin/bash
#
#
#  Copy libraries, binaries for padmon,ami
#
function cparch()
{
    mkdir -p ${DST}/$1/$2
    rsync -avm ${SRC}/$1/$2/$3 ${DST}/$1/$2/$3

    libs=`ldd ${SRC}/$1/$2/$3 | grep build | cut -d ' ' -f 3`
    for lib in ${libs} ; do
      llib=${lib:${#SRC}+1}
      echo ${lib}
      echo ${llib}
      mkdir -p `dirname ${DST}/${llib}`
      rsync -rpotgLSP ${SRC}/${llib} ${DST}/${llib}
    done
}

function cpbin()
{
    cparch $1 bin/i386-linux-opt $2
    cparch $1 bin/i386-linux-dbg $2
    cparch $1 bin/x86_64-linux-opt $2
    cparch $1 bin/x86_64-linux-dbg $2
}

export SRC=`pwd`/build
export DST=$1/build

cpbin ami offline_ami
cpbin ami online_ami
cpbin ami ami
cpbin pdsapp padmonservertest
