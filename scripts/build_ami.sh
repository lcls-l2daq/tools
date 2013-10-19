#!/bin/bash
#
function make_link()
{
  if [ ! -e $1/x86_64-linux ]; then
    ln -s x86_64-linux-opt $1/x86_64-linux
  fi
}

make i386-linux-opt
make i386-linux-dbg
make x86_64-linux-opt
make x86_64-linux-dbg

make_link build/ami/lib

