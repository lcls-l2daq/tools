# sample script to do a "scope mode" sweep of an externally-triggered signal
# the user probably wants to change diodebias to the nominal value
python lusi-ipm.py --ref 5 --chargeamp 100 --diodebias 0 --window 600000 --delay 0-500000 --nevents 1000 sampleSweepExtTrigger.csh
