# sample script to read 100 events using external triggering
# the user probably wants to change --delay to match the beam timing
# (with ps_delay 100 uS earlier) and set --diodebias to nominal
python lusi-ipm.py --serial 0 --ref 1 --chargeamp 1 --diodebias 0 --window 5000000  --ps_delay 50000 --delay 160000 --nevents 100 sampleSignalExtTrigger.csv
