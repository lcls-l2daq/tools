# sample script to do a "scope mode" sweep of an externally-triggered signal
# the user probably wants to change diodebias to the nominal value
# the presample delay setting should turn off presampling, which is likely
# to interfere with sweeping unless the delay starts 100 uS after the presample
python lusi-ipm.py --ref 5 --chargeamp 100 --diodebias 0 --window 600000 --ps_delay 524280 --delay 0-500000 --nevents 1000 sampleSweepExtTrigger.csh
