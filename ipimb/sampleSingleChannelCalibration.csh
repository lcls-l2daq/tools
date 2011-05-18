# sample script to do a charge injection calibration without an external trigger
# the user probably wants to change diodebias to the nominal value
# the presample delay setting should turn off presampling, which is likely
# to interfere with sweeping unless the delay starts 100 uS after the presample

echo "*****Please make sure there is no external trigger*****"
setenv CHANNEL 0
echo "calibrating channel" ${CHANNEL} "over three gain ranges"
python lusi-ipm.py --calibrate ${CHANNEL} --calv 0-10 --calpol high --ps_delay 524280 --ref 1 --chargeamp 1,1,1,1 --cal_range 1 --diodebias 0 --window 1000000 --calstrobe 300000 --delay 10000 --nevents 1000 sampleSingleChannelCalibration_ch${CHANNEL}_1pF.csv
python lusi-ipm.py --calibrate ${CHANNEL} --calv 0-10 --calpol high --ps_delay 524280 --ref 1 --chargeamp 4,4,4,4 --cal_range 2 --diodebias 0 --window 1000000 --calstrobe 300000 --delay 10000 --nevents 1000 sampleSingleChannelCalibration_ch${CHANNEL}_120pF.csv
python lusi-ipm.py --calibrate ${CHANNEL} --calv 0-10 --calpol high --ps_delay 524280 --ref 1 --chargeamp 7,7,7,7 --cal_range 3 --diodebias 0 --window 1000000 --calstrobe 300000 --delay 17000 --nevents 1000 sampleSingleChannelCalibration_ch${CHANNEL}_10nF.csv
unsetenv CHANNEL
