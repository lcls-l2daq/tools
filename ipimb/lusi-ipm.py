#!/usr/bin/python
# This script provides access to the LUSI Intensity Position/Monitor
# Board via the serial port. It is based on Leonid's work.
#
# Copyright 2009, Stanford University
# Authors: Remi Machet <rmachet@slac.stanford.edu>, Philip Hart <PhilipH@slac.stanford.edu>
#
# Released under the GPLv2 licence <http://www.gnu.org/licenses/gpl-2.0.html>
#

import IntensityProfileMonitorBoard
import sys
import time
import traceback

MULTIFILE_MODE = True

def script_exit(retcode):
	global dictConfig

	if dictConfig["debug"]:
		if retcode != 0:
			traceback.print_tb(sys.exc_traceback)
		print "%s exited with return code %d." % (sys.argv[0], retcode)
	if fCaptureFileName is not None:
		try:
			fCaptureFile.close()
		except:
			pass
	print
	sys.exit(retcode)

def strConvert(string, sType): ## replace with sType(eval())?
	if string.startswith("0x"):
		base = 16
	elif string.isdigit() or (sType.lower() == "float"):
		base = 10
	else:
		raise RuntimeError, "Invalid number %s" % (string)
	if sType.lower() == "long":
		return long(string, base)
	elif sType.lower() == "int":
		return int(string, base)
	elif sType.lower() == "float":
		return float(string)
	raise RuntimeError, "Unknown conversion format: %s" % (sType)


# dictConfig is used to store the general configuration of this program
# such as debug or verbose flags
dictConfig = {}
dictConfig["debug"] = False	# Debug mode enabled?
# Charge amplifier coefficient
lstInputAmplifier_pF = [1, 1, 1, 1]
# Charge calibration range
lstCal_Range_pF = [1, 1, 1, 1]
# Calibration DAC output level in Volts
fCalData_V_low = 2.5
fCalData_V_high = 2.5
# Length of time the charge amplifier is NOT in reset
# ie when the signal is sampled
lAcqDelay_ns = 0##xFFF
lAcqLength_ns_low = 100*1024
lAcqLength_ns_high = 100*1024
# ADC Bias voltage in Volts
fBiasData_V_low = 10
fBiasData_V_high = 10
# Number of events to capture (0=forever)
lNumEvents = 0
# Mode: RegRead, RegWrite, Capture or Status
sMode = "Capture"
# Capture source is DAC
bCalibrate = False
# File to save data
fCaptureFileName = None
# Register address to read/write
lRegAddr = 0
# Register value to write
lRegValue = 0
# Serial port the board is connected to
##iComPort = ['/dev/ttyPS0', '/dev/ttyPS7', '/dev/ttyPS2', '/dev/ttyPS3'] ## for example
iComPort = ['/dev/ttyPS0'] ## default
# Charge Amplifier comparator reference signal in volts
fChargeAmpRef_V_low = 2.5
fChargeAmpRef_V_high = 2.5
# Calibration pulse polarity
sCalibrationPolarity = "low"
# Trigger delay: delay between trigger and ADC sampling in ns
lSampleDelayMin_ns = 89000
lSampleDelayMax_ns = 0xffff*8
# Length of the calibration pulse (time the calibration voltage will be applied) in ns
lCalibrationStrobeLengthMin_ns = 128
lCalibrationStrobeLengthMax_ns = 128
# 4 channels list of which channel should be in calibration mode
lstCalibrateChannels = [False, False, False, False]

rampList = []
print time.ctime()
sleepTime = 0.
try:
	# Parse the arguments
	i=1
	while i < len(sys.argv):
		if (sys.argv[i] == "--help") or (sys.argv[i] == "-h"):
			print "%s: driver for LUSI Intensity Position/Monitor Board." % (sys.argv[0])
			print "Syntax: %s [ --debug ] [ --com <port#> ] --help \\" % (sys.argv[0])
			print "\t| --read <regaddr> \\"
			print "\t| --write <regaddr>=<regval> \\"
			print "\t| [ <csvfile> ] [ --window <length_ns> ] [ --diodebias <voltage> ] \\"
			print "\t\t[ --chargeamp <multiplier_pC> ] [ --ref <voltage> ] \\"
			print "\t\t[ --calibrate <channels> [ --calv <voltage> ] [ --calpol <level> ] \\"
			print "\t\t\t[ --calstrobe <length_ns> ] ] \\"
			print "\t\t[ --nevents <nevents> ] [ --delay <delay_ns> ] \\"
			print "\t| --status"
			print "\nThis program has 4 modes: register read, write, capture and status."
			print "Global options:"
			print "--help: display this message."
			print "--debug: display more info when an error occurs."
			print "--com <port#(s)>: serial port number(s) to use to talk to the board(s)."
			print "\nCapture mode (default):"
			print "<csvfile>: A file where to save the capture values,"
			print "\tdata will be in CSV format."
			print "--window <length_ns>: Amount of time in nano-seconds that the"
			print "\tcharge amplifier is OUT of reset after a trigger in nano-seconds."
			print "\tIf <ns> is a range (<t1>-<t2>), the window"
			print "\twill be varied within the range linearly."
			print "\t(default is %dns to %dns)" % (lAcqLength_ns_low, lAcqLength_ns_high)
			print "--diodebias <voltage>: bias voltage to apply to the diode."
			print "\tIf <voltage> is a range (<v1>-<v2>), the voltage"
			print "\twill be varied within the range linearly."
			print "\t(default is %fV to %fV)" % (fBiasData_V_low, fBiasData_V_high)
			print "--chargeamp <multiplier_pC>: charge amplifier multiplier"
			print "\tin pico Farad. The only accepted values are 1pF, 100pF"
			print "\tand 10nF full scale. It can be a single value or a"
			print "\tlist of 4 values (one for each channel)."
			print "\t(default is %dpF,%dpF,%dpF,%dpF)" % lstInputAmplifier_pF
			print "--ref <voltage>: reference voltage used by the charge"
			print "\tamplifier comparator in Volts."
			print "\tIf <voltage> is a range (<v1>-<v2>), the voltage"
			print "\twill be varied within the range linearly."
			print "\t(default is %fV to %fV)" % (fChargeAmpRef_V_low, fChargeAmpRef_V_high)
			print "--calibrate <channels>: if set, the channels"
			print "\tin <channels> will be set to calibration mode."
			print "\t<channels> is a list of channels separated by."
			print "\tcommas (no spaces!)."
			print "--calv <voltage>: control the calibration DAC voltage"
			print "\tIf <voltage> is a range (<v1>-<v2>), the voltage"
			print "\twill be varied within the range linearly."
			print "\t(default is %fV to %fV)" % (fCalData_V_low, fCalData_V_high)
			print "--calpol <level>: specify the 'at-rest' level of the"
			print "\tcalibration pulse. The valid values are 'high' (3.3V)"
			print "\tand 'low' (0V)."
			print "\t(default is %s)" % (sCalibrationPolarity)
			print "--calstrobe <length_ns>: time the calibration strobe will"
			print "\tlast in nano-seconds."
			print "\tIf <ns> is a range (<t1>-<t2>), the window"
			print "\twill be varied within the range linearly."
			print "\t(default is %dns to %dns)" % (lCalibrationStrobeLengthMax_ns, lCalibrationStrobeLengthMax_ns)
			print "--nevents <nevents>: number of events to capture"
			print "\t(default is 'until Ctrl-C is pressed')"
			print "--delay <delay_ns>: delay in nano-seconds between trigger"
			print "\tand sampling of the ADC. If <delay_ns> is a range"
			print "\t(<delay_min>-<delay_max>) the delay will be varied"
			print "\tlinearly within the range."
			print "\t(default is %dns to %dns)" % (lSampleDelayMin_ns, lSampleDelayMax_ns)
			print "\nRegister read mode:"
			print "--read <regaddr>: Set program in register read, <regaddr> is the"
			print "\taddress to read."
			print "\nRegister write mode:"
			print "--write <regaddr>=<regval>: Set program in register write mode,"
			print "\t<regaddr> is the address of the register and <regval>"
			print "\tthe value."
			print "\nStatus mode: output the status of the LUSI PIMB."
			print "--status: Set program in status mode,"
			script_exit(0)
		elif sys.argv[i] == "--debug":
			dictConfig["debug"] = True
		elif sys.argv[i] == "--window":
			i += 1
			if len(sys.argv[i].split("-")) == 1:
				lAcqLength_ns_low = strConvert(sys.argv[i],"long")
				lAcqLength_ns_high = lAcqLength_ns_low
			else:
				[lAcqLength_ns_low, lAcqLength_ns_high] = [strConvert(l, "long") for l in sys.argv[i].split("-")]
				rampList.append("window")
		elif sys.argv[i] == "--serial":
			i += 1
			iComPort = []
			ports = sys.argv[i].split(",")
			for port in ports:
				iComPort.append('/dev/ttyPS%s' %(port.strip()))
			if len(ports)==1:
				print "Using port", iComPort[0]
			else:
				print "Using port array", iComPort	
		elif sys.argv[i] == "--diodebias":
			i += 1
			if len(sys.argv[i].split("-")) == 1:
				fBiasData_V_low = strConvert(sys.argv[i],"float")
				fBiasData_V_high = fBiasData_V_low
			else:
				[fBiasData_V_low, fBiasData_V_high] = [strConvert(f,"float") for f in sys.argv[i].split("-")]
				rampList.append("diodebias")
		elif sys.argv[i] == "--chargeamp":
			i += 1
			n = len(sys.argv[i].split(","))
			if n==1:
				l = strConvert(sys.argv[i],"long")
				lstInputAmplifier_pF = [l, l, l, l]
			elif n == 4:
				lstInputAmplifier_pF = [strConvert(l,"long") for l in sys.argv[i].split(",")]
			else:
				raise RuntimeError, "Invalid value %s for --chargeamp, try --help" % (sys.argv[i])
		elif sys.argv[i] == "--ref":
			i += 1
			if len(sys.argv[i].split("-")) == 1:
				fChargeAmpRef_V_low = strConvert(sys.argv[i],"float")
				fChargeAmpRef_V_high = fChargeAmpRef_V_low
			else:
				[fChargeAmpRef_V_low, fChargeAmpRef_V_high] = [strConvert(f,"float") for f in sys.argv[i].split("-")]
				rampList.append("ref")
		elif sys.argv[i] == "--calibrate":
			i += 1
			if len(sys.argv[i].split("-")) > 1:
				lst = range(strConvert(sys.argv[i].split("-")[0],"int"),
					    strConvert(sys.argv[i].split("-")[1],"int")+1)
			elif len(sys.argv[i].split(",")) > 1:
				lst = [strConvert(ch,"int") for ch in sys.argv[i].split(",")]
			else:
				lst = [strConvert(sys.argv[i],"int")]
			for ch in lst:
				if (ch<0) or (ch>=4):
					raise RuntimeError, "Invalid channel %d (must be between 0 and 4)" % (ch)
				lstCalibrateChannels[ch] = True
			bCalibrate = True
		elif sys.argv[i] == "--cal_range":		#added by mlf, 6/12/09
			i += 1
			n = len(sys.argv[i].split(","))
			if n==1:
				l = strConvert(sys.argv[i],"long")
				lstCal_Range_pF = [l, l, l, l]
			elif n == 4:
				lstCal_Range_pF = [strConvert(l,"long") for l in sys.argv[i].split(",")]
			else:
				raise RuntimeError, "Invalid value %s for --cal_range, try --help" % (sys.argv[i])
		elif sys.argv[i] == "--calv":
			i += 1
			if len(sys.argv[i].split("-")) == 1:
				fCalData_V_low = strConvert(sys.argv[i],"float")
				fCalData_V_high = fCalData_V_low
			else:
				[fCalData_V_low, fCalData_V_high] = [strConvert(f,"float") for f in sys.argv[i].split("-")]
				rampList.append("calv")
		elif sys.argv[i] == "--calpol":
			i += 1
			sCalibrationPolarity = sys.argv[i]
		elif sys.argv[i] == "--calstrobe":
			i += 1
			if len(sys.argv[i].split("-")) == 1:
				lCalibrationStrobeLengthMin_ns = strConvert(sys.argv[i],"long")
				lCalibrationStrobeLengthMax_ns = lCalibrationStrobeLengthMin_ns
			else:
				[lCalibrationStrobeLengthMin_ns, lCalibrationStrobeLengthMax_ns] = \
								 [strConvert(l, "long") for l in sys.argv[i].split("-")]
				rampList.append("calstrobe")
		elif sys.argv[i] == "--nevents":
			i += 1
			lNumEvents = strConvert(sys.argv[i],"long")
		elif sys.argv[i] == "--delay":
			i += 1
			if len(sys.argv[i].split("-")) == 1:
				lSampleDelayMin_ns = strConvert(sys.argv[i],"long")
				lSampleDelayMax_ns = lSampleDelayMin_ns
			else:
				[lSampleDelayMin_ns, lSampleDelayMax_ns] = [strConvert(l,"long") for l in sys.argv[i].split("-")]
		elif sys.argv[i] == "--read":
			i += 1
			lRegAddr = strConvert(sys.argv[i],"int")
			sMode = "RegRead"
		elif sys.argv[i] == "--write":
			i += 1
			[lRegAddr, lRegValue] = [strConvert(l,"long") for l in sys.argv[i].split("=")]
			sMode = "RegWrite"
		elif sys.argv[i] == "--status":
			sMode = "Status"
		elif sys.argv[i].startswith("--"):
			raise RuntimeError, "invalid option %s. Try --help" % (sys.argv[i])
		elif (sMode == "Capture") and (fCaptureFileName == None):
			fCaptureFileName = sys.argv[i]
		else:
			raise RuntimeError, "invalid option %s. Try --help" % (sys.argv[i])
		i += 1
	if len(rampList) > 1:
		raise RuntimeError, 'Have configured to ramp %s, but I do not know how to do that' %(', '.join(rampList))

	# Create a board instance and make sure the board is connected
	ipmb = []
	lStatus = []
	nIPMB = len(iComPort)
	if not MULTIFILE_MODE and (fCaptureFileName is not None):
		print "Saving data to %s" %(fCaptureFileName)
		fCaptureFile = open(fCaptureFileName, 'w')
	for i in range(nIPMB):
		if i == 0:
			fCaptureFile = []
		if MULTIFILE_MODE and (fCaptureFileName is not None):
			if nIPMB == 1:
				name = fCaptureFileName
			else:
				name = fCaptureFileName + '_board%d' %(i)
			print "Saving board %d data to %s" %(i, name)
			fCaptureFile.append(open(name, 'w'))
		ipmb.append(IntensityProfileMonitorBoard.IntensityProfileMonitorBoard(iComPort[i]))

		lStatus = ipmb[i].ReadRegister(ipmb[i].reg.status)
		# Detect the mode selected and do the appropriate thing
	        if sMode == "Status":
			print "Status Register: 0x%08x" % (lStatus)
			if lStatus & 0x80000:
				print "\t1.8V: ok"
			else:
				print "\t1.8V: MISSING"
			if lStatus & 0x40000:
				print "\tMGT AVCC: ok"
			else:
				print "\tMGT AVCC: MISSING"
			if lStatus & 0x20000:
				print "\tMGT PLL: ok"
			else:
				print "\tMGT PLL: MISSING"
			if lStatus & 0x10000:
				print "\tMGT AVTT: ok"
			else:
				print "\tMGT AVTT: MISSING"
			lErrors = ipmb.ReadRegister(ipmb.reg.errors)
			print "Errors Register: 0x%08x" % (lErrors)
			if lErrors & 0xff00:
				print "\tThe following error bit are set:"
				if lStatus & 0x0400:
					print "\t\tRS232 framing error."
				if lStatus & 0x0800:
					print "\t\tRS232 overrun error."
				if lStatus & 0x4000:
					print "\t\tCommand reply error."
				if lStatus & 0x8000:
					print "\t\tTrigger reply error."
			else:
				print "\tNo error pending."
			if lErrors & 0x00ff:
				print "\tThe following errors happened:"
				if lStatus & 0x04:
					print "\t\tRS232 framing error."
				if lStatus & 0x08:
					print "\t\tRS232 overrun error."
				if lStatus & 0x40:
					print "\t\tCommand reply error."
				if lStatus & 0x80:
					print "\t\tTrigger reply error."
  			        ipmb.WriteRegister(ipmb.reg.errors, lErrors & 0x000000FFL)
  		        else:
				print "\tNo error detected since last read of the status register."
	if sMode == "RegRead":
		print 'assume one board'
		lRegValue = ipmb[0].ReadRegister(lRegAddr)
		print "0x%08x" % (lRegValue)
	elif sMode == "RegWrite":
		ipmb[0].WriteRegister(lRegAddr, lRegValue)
	else:
		for i in range(nIPMB): ipmb[i].SetCalibrationMode(lstCalibrateChannels)
		if bCalibrate:
			for i in range(nIPMB): ipmb[i].SetCalibrationDivider(lstCal_Range_pF)
			if sCalibrationPolarity == "high":
				bCalPolarity = True
			elif sCalibrationPolarity == "low":
				bCalPolarity = False
			else:
				raise RuntimeError, "invalid calibration polarity %s, can be 'high' or 'low'" % (sys.argv[i])
			for i in range(nIPMB): ipmb[i].SetCalibrationPolarity((bCalPolarity, bCalPolarity, bCalPolarity, bCalPolarity))
			for i in range(nIPMB): ipmb[i].SetCalibrationVoltage(fCalData_V_low)
			if lNumEvents > 1:
				fCalibrationStep = (fCalData_V_high - fCalData_V_low) / (lNumEvents - 1)
			else:
				if (fCalData_V_high != fCalData_V_low) and (lNumEvents == 0):
					raise RuntimeError, "Cannot vary calibration voltage over an infinite number of capture events, use --nevents"
				fCalibrationStep = 0
			fCalibrationData = fCalData_V_low - fCalibrationStep
			if fCaptureFileName != None:
				if MULTIFILE_MODE:
					for j in range(nIPMB):
						fCaptureFile[j].write("Sample(#),CAL_Voltage(V),Timestamp(tick),rg_config(hex),cal_rg_config(hex),Trigger to Sample Delay(ns),Ch0(V),Ch1(V),Ch2(V),Ch3(V)\n")
				else:
					fCaptureFile.write("Board,Sample(#),CAL_Voltage(V),Timestamp(tick),rg_config(hex),cal_rg_config(hex),Trigger to Sample Delay(ns),Ch0(V),Ch1(V),Ch2(V),Ch3(V)\n")
		else:
			if fCaptureFile != None:
				if MULTIFILE_MODE:
					for j in range(nIPMB):
						fCaptureFile[j].write("Sample(#),Timestamp(tick),rg_config(hex),cal_rg_config(hex),Trigger to Sample Delay(ns),Ch0(V),Ch1(V),Ch2(V),Ch3(V)\n")
				else:
					fCaptureFile.write("Board,Sample(#),Timestamp(tick),rg_config(hex),cal_rg_config(hex),Trigger to Sample Delay(ns),Ch0(V),Ch1(V),Ch2(V),Ch3(V)\n")
		if lNumEvents > 1:
			fChargeAmpRefStep = (fChargeAmpRef_V_high - fChargeAmpRef_V_low) / (lNumEvents - 1)
		else:
			fChargeAmpRefStep = 0.
		fChargeAmpRef = fChargeAmpRef_V_low
		for i in range(nIPMB): ipmb[i].SetChargeAmplifierRef(fChargeAmpRef)
		for i in range(nIPMB): ipmb[i].SetChargeAmplifierMultiplier(lstInputAmplifier_pF)
		if lNumEvents > 1:
			fBiasDataStep = (fBiasData_V_high - fBiasData_V_low) / (lNumEvents - 1)
		else:
			fBiasDataStep = 0.
		fBiasData = fBiasData_V_low
		for i in range(nIPMB): ipmb[i].SetInputBias(fBiasData)
		if lNumEvents > 1:
			lAcqLengthStep = (lAcqLength_ns_high - lAcqLength_ns_low) / (lNumEvents - 1)
		else:
			lAcqLengthStep = 1
		lAcqLength = lAcqLength_ns_low
		if lNumEvents > 1:
			lSampleDelayStep = (lSampleDelayMax_ns - lSampleDelayMin_ns) / (lNumEvents - 1)
		else:
			lSampleDelayStep = 1
		lSampleDelay = lSampleDelayMin_ns
		if lNumEvents > 1:
			lCalibrationStrobeLengthStep = (lCalibrationStrobeLengthMax_ns - lCalibrationStrobeLengthMin_ns) / (lNumEvents - 1)
		else:
			lCalibrationStrobeLengthStep = 1
		lCalibrationStrobeLength = lCalibrationStrobeLengthMin_ns
		## setup
		for i in range(nIPMB): ipmb[i].SetChargeAmplifierRef(fChargeAmpRef)
##			print 'fChargeAmpRef', fChargeAmpRef
		for i in range(nIPMB): ipmb[i].SetInputBias(fBiasData)
##			print 'fBiasData', fBiasData
		for i in range(nIPMB): ipmb[i].SetChannelAcquisitionWindow(lAcqLength, lAcqDelay_ns)
##			print 'lAcqLength, lAcqDelay_ns', lAcqLength, lAcqDelay_ns
		for i in range(nIPMB): ipmb[i].SetTriggerDelay(lSampleDelay)
##			print 'lSampleDelay', lSampleDelay
		startTime = time.time()
		if not bCalibrate:
			for i in range(nIPMB): ipmb[i].clearData() ## if in external mode make sure no complete old-configuration data is in queue
			for i in range(nIPMB): lStatus = ipmb[i].ReadRegister(ipmb[i].reg.status) ## incidentally reads any data into data buffer
			for i in range(nIPMB):
				dataWordsInBuffer, commandWordsInBuffer = ipmb[i].getDataCommandLength()
				if dataWordsInBuffer > 0:
			            ## clear data buffer - will drop first two triggers if there is pre-config data
					print 'found %d data words - %d full packet(s) - assume trigger during configuration, will clear full packets' %(dataWordsInBuffer, dataWordsInBuffer/12)
					print 'also have %d command words' %(commandWordsInBuffer)
					data = ipmb[i].WaitData()
					ipmb[i].clearData() ## if in external mode make sure no partial old-configuration data is in queue
		iEvent = -1
		while (iEvent != lNumEvents-1) or (lNumEvents == 0):
			iEvent += 1
			if fChargeAmpRefStep != 0:
				for j in range(nIPMB): ipmb[j].SetChargeAmplifierRef(fChargeAmpRef)
##			print 'fChargeAmpRef', fChargeAmpRef
			if fBiasDataStep != 0:
				for j in range(nIPMB): ipmb[j].SetInputBias(fBiasData)
##			print 'fBiasData', fBiasData
			if lAcqLengthStep != 0:
				for j in range(nIPMB): ipmb[j].SetChannelAcquisitionWindow(lAcqLength, lAcqDelay_ns)
##			print 'lAcqLength, lAcqDelay_ns', lAcqLength, lAcqDelay_ns
			if lSampleDelayStep != 0:
				for j in range(nIPMB): ipmb[j].SetTriggerDelay(lSampleDelay)
##			print 'lSampleDelay', lSampleDelay
			t0 = time.time()
##			time.sleep(0.0001)
			t = time.time()
			sleepTime += t-t0
			if bCalibrate:
				if True:##fCalibrationStep != 0:
					fCalibrationData += fCalibrationStep
					for j in range(nIPMB): ipmb[j].SetCalibrationVoltage(fCalibrationData)
					##print 'fCalibrationData', fCalibrationData
					t0 = time.time()
##					time.sleep(0.001)
					t = time.time()
					sleepTime += t-t0
				for j in range(nIPMB): ipmb[j].CalibrationStart(lCalibrationStrobeLength)
				##print 'lCalibrationStrobeLength', lCalibrationStrobeLength
			tempCount = 1.
			tempT0 = time.time()
			dataArray = []
			for j in range(nIPMB):
				dataArray.append(ipmb[j].WaitData())
			if fCaptureFile == None:
				if bCalibrate:
					for j in range(nIPMB):
						data = dataArray[j]
						print "Board %d, Sample 0x%x: CAL %fV ts 0x%x ticks, rg_config 0x%04x, cal_rg_config 0x%04x, sample_delay %dns, ch0 %fV, ch1 %fV, ch2 %fV, ch3 %fV" \
							% (j, iEvent, fCalibrationData, data.GetTimestamp_ticks(), data.Config0, data.Config1, data.GetTriggerDelay_ns(), data.GetCh0_V(), data.GetCh1_V(), data.GetCh2_V(), data.GetCh3_V())
				else:
					for j in range(nIPMB):
						data = dataArray[j]
						print "Board %d, Sample %d: ts 0x%x ticks, rg_config 0x%04x, cal_rg_config 0x%04x, sample_delay %dns, ch0 %fV, ch1 %fV, ch2 %fV, ch3 %fV" \
						      %(j, iEvent, data.GetTimestamp_ticks(), data.Config0, data.Config1, data.GetTriggerDelay_ns(), data.GetCh0_V(), data.GetCh1_V(), data.GetCh2_V(), data.GetCh3_V())
			else:
				if bCalibrate:
					for j in range(nIPMB):
						data = dataArray[j]
						if MULTIFILE_MODE:
							fCaptureFile[j].write("%d,%f,0x%x,0x%04x,0x%04x,%d,%f,%f,%f,%f\n" 
									      %(iEvent, fCalibrationData, data.GetTimestamp_ticks(),
										data.Config0, data.Config1, data.GetTriggerDelay_ns(),
										data.GetCh0_V(), data.GetCh1_V(), data.GetCh2_V(), data.GetCh3_V()))
						else:
							fCaptureFile.write("%d, %d,%f,0x%x,0x%04x,0x%04x,%d,%f,%f,%f,%f\n"
									   %(j, iEvent, fCalibrationData, data.GetTimestamp_ticks(),
									     data.Config0, data.Config1, data.GetTriggerDelay_ns(),
									     data.GetCh0_V(), data.GetCh1_V(), data.GetCh2_V(), data.GetCh3_V()))
				else:
					for j in range(nIPMB):
						data = dataArray[j]
						if MULTIFILE_MODE:
							fCaptureFile[j].write("%d,0x%x,0x%04x,0x%04x,%d,%f,%f,%f,%f\n"
									      %(iEvent, data.GetTimestamp_ticks(),
										data.Config0, data.Config1, data.GetTriggerDelay_ns(),
										data.GetCh0_V(), data.GetCh1_V(), data.GetCh2_V(), data.GetCh3_V()))
						else:	
							fCaptureFile.write("%d, %d,0x%x,0x%04x,0x%04x,%d,%f,%f,%f,%f\n"
									   %(j, iEvent, data.GetTimestamp_ticks(),
									     data.Config0, data.Config1, data.GetTriggerDelay_ns(),
									     data.GetCh0_V(), data.GetCh1_V(), data.GetCh2_V(), data.GetCh3_V()))
				print "\rCaptured %d samples ..." % (iEvent+1),
				sys.stdout.flush()
			fChargeAmpRef += fChargeAmpRefStep
			# Wrap around needed when nevents is infinite
			if fChargeAmpRef > fChargeAmpRef_V_high:
				fChargeAmpRef = fChargeAmpRef_V_low
			fBiasData += fBiasDataStep
			# Wrap around needed when nevents is infinite
			if fBiasData > fBiasData_V_high:
				fBiasData = fBiasData_V_low
			lAcqLength += lAcqLengthStep
			# Wrap around needed when nevents is infinite
			if lAcqLength > lAcqLength_ns_high:
				lAcqLength = lAcqLength_ns_low
			lSampleDelay += lSampleDelayStep
			# Wrap around needed when nevents is infinite
			if lSampleDelay > lSampleDelayMax_ns:
				lSampleDelay = lSampleDelayMin_ns
			lCalibrationStrobeLength += lCalibrationStrobeLengthStep
			# Wrap around needed when nevents is infinite
			if lCalibrationStrobeLength > lCalibrationStrobeLengthMax_ns:
				lCalibrationStrobeLength = lCalibrationStrobeLengthMin_ns
		if fCaptureFile != None:
			print "done."
		print 'total acquisition section time in s:', time.time()-startTime
##	print time.ctime()
##	print 'total IPMB read, write, sleep time, n reads:', ipmb.readTime, ipmb.writeTime, ipmb.sleepTime, ipmb.nReads
##	print 'total sleep time:', sleepTime + ipmb.sleepTime
	script_exit(0)
except KeyboardInterrupt:
	print "\nERROR: interrupted by user."
	script_exit(1)
except SystemExit:
	raise
except:
	print "ERROR: %s." % (sys.exc_value)
	script_exit(2)
