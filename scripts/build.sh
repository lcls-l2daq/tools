make i386-linux-opt
make i386-linux-dbg
make x86_64-linux-opt
pushd build/pdsdata/lib; ln -s x86_64-linux-opt x86_64-linux; popd
pushd build/pdsapp/lib; ln -s x86_64-linux-opt x86_64-linux; popd
pushd build/ami/lib; ln -s x86_64-linux-opt x86_64-linux; popd
pushd build/pdsapp/bin; ln -s x86_64-linux-opt x86_64-linux; popd

