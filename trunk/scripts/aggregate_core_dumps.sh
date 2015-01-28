#!/bin/bash -x
# Aggregate the results of the individual core dump cron jobs into a single file

NOW=$( date --date="today" +%F)

EXP="amo sxr xpp xcs cxi mec"

OUTPUT_DIR_ROOT="/reg/g/pcds/dist/pds/cron"
OUTPUT_DIR=${OUTPUT_DIR_ROOT}/${NOW}

# Clean up any coredump lists and coredump_traces.txt from today
if [ -f ${OUPUT_DIR}/${NOW}_corefilelist.txt ]; then
   rm -f ${OUTPUT_DIR}/${NOW}_corefilelist.txt
fi

if [ -f ${OUTPUT_DIR}/${NOW}_coredumps.txt ]; then
   rm -f ${OUTPUT_DIR}/${NOW}_coredumps.txt
fi

# Create output directory for this day (date) if it does not yet exist
mkdir -p ${OUTPUT_DIR}

# Dump the list of core dumps to a file and all the gdb core dump traces to a single file
echo "For full core dump traces, see  ${OUTPUT_DIR}/${NOW}_coredumps.txt" > ${OUTPUT_DIR}/${NOW}_corefilelist.txt
for exp in $EXP
do
  if [ -f /reg/g/pcds/pds/${exp}/cron/${NOW}/${NOW}_corefilelist.txt ]; then
   cat /reg/g/pcds/pds/${exp}/cron/${NOW}/${NOW}_corefilelist.txt >> ${OUTPUT_DIR}/${NOW}_corefilelist.txt
   echo " " >> ${OUTPUT_DIR}/${NOW}_corefilelist.txt
   cat /reg/g/pcds/pds/${exp}/cron/${NOW}/${NOW}_coredumps.txt >> ${OUTPUT_DIR}/${NOW}_coredumps.txt
  fi
done

# If the aggregate file is greater than the minimum size, send email
MINSIZE=858
FILESIZE=$(stat -c%s ${OUTPUT_DIR}/${NOW}_corefilelist.txt)
if [ $FILESIZE -gt $MINSIZE ]; then
    cat ${OUTPUT_DIR}/${NOW}_corefilelist.txt | mail -s "LCLS coredumps for $NOW" pcds-daq-l
#    cat ~jana/utils/coredumps/output/${NOW}_coredumps.txt | mail -s "LCLS coredumps for $NOW" pcds-daq-l
#    cat ~jana/utils/coredumps/output/${NOW}_coredumps.txt | mail -s "LCLS coredumps for $NOW" -c jana pcds-daq-l
else
    echo "No core dumps found today, $NOW" |  mail -s "No LCLS coredumps for $NOW" pcds-daq-l
fi






