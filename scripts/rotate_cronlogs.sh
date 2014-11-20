#!/bin/bash 

if [ $# -ne 1 ]; then
    echo "Usage:  $0 amo"
    exit
fi

exp=`echo $1 | tr '[:upper:]' '[:lower:]'`

# Keep the last 7 days
NKEEP=7

# Define LOGDIR
LOGDIR=/reg/g/pcds/pds/$exp/cron
if [ ! -d $LOGDIR ]; then
    echo "$LOGDIR does not exist.  Exiting..."
    exit
fi
cd $LOGDIR

# Create $LOGDIR/YYYY-MM-DD if they don't exist and move the files there
for f in `find $LOGDIR -maxdepth 1 -type f`
do
	FDATE=$(date -d "$(stat -c %y $f)" +%F)
	mkdir -p ./${FDATE}
	echo "Moving $f to $LOGDIR/$FDATE"
	mv $f ./${FDATE}/
done

# Find directories older than 7 days and delete them
DELETEME=`find $LOGDIR -maxdepth 1 -mtime +$NKEEP -name "2014-11-1*" -type d`
for f in $DELETEME
do
  echo "Removing directory and directory contents $f"
  rm -rf $f
done
