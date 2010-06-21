# sample script to read 100 events using external triggering
# the user probably wants to change --delay to match the beam timing
# and set --diodebias to nominal
python lusi-ipm.py --serial 0 --ref 5 --chargeamp 100 --cal_range 100 --diodebias 0 --window 1500000  --delay 95000 --nevents 100 sampleNoiseExtTrigger.csv
