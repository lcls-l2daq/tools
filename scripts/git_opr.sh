#!/bin/bash

ROOTDIR="/reg/g/pcds/dist/pds"
EXP=$(echo $USER | sed 's/...$//')
NOW="$(date +'%F %T %Z')"

cd $ROOTDIR/${EXP}

if [ -f ${ROOTDIR}/${EXP}/.current_history ]; then
    rm -f ${ROOTDIR}/${EXP}/.current_history
fi

ls -lrt ${ROOTDIR}/${EXP}/ > ${ROOTDIR}/${EXP}/.current_history

git add ${ROOTDIR}/${EXP}/scripts/*.cnf
git add ${ROOTDIR}/${EXP}/scripts/*.txt
git add ${ROOTDIR}/${EXP}/misc/*.txt

git commit -am "${NOW}: cron git checkin"
