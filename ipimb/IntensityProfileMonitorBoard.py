# Python module that implements driver code for the LUSI Intensity Profile/Monitor Board
#
# Copyright 2009/2010, Stanford University
# Authors: Remi Machet <rmachet@slac.stanford.edu>, Philip Hart <PhilipH@slac.stanford.edu>
#
# Released under the GPLv2 licence <http://www.gnu.org/licenses/gpl-2.0.html>
#

PYSERIAL = [True, False][0]
PEXPECTSERIAL = False
TCPSERIAL = False
UDPSERIAL = False##True
DEBUG = [True, False][1]

if PYSERIAL:
        import serial as serial
elif PEXPECTSERIAL:
        from ses_serial import *
else:
        import socket
import time

CHARGEAMP_REF_MAX = 10
CHARGEAMP_REF_STEPS = 65536

CALIBRATION_V_MAX = 10
CALIBRATION_V_STEPS = 65536

INPUT_BIAS_MAX = 200
INPUT_BIAS_STEPS = 65536

CLOCK_PERIOD = 8
ADC_RANGE = 3.3
ADC_STEPS = 65536

def CRC(lst):
	crc = 0xffff
	for word in lst:
##		print "word in CRC", word
		# Calculate CRC 0x0421 (x16 + x12 + x5 + 1) for protocol calculation
		C = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		CI = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		D = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		for i in range(16):
			C[i] = (crc & (1 << i)) >> i
			D[i] = (word & (1 << i)) >> i
		CI[0] = D[12] ^ D[11] ^ D[8] ^ D[4] ^ D[0] ^ C[0] ^ C[4] ^ C[8] ^ C[11] ^ C[12]
		CI[1] = D[13] ^ D[12] ^ D[9] ^ D[5] ^ D[1] ^ C[1] ^ C[5] ^ C[9] ^ C[12] ^ C[13]
		CI[2] = D[14] ^ D[13] ^ D[10] ^ D[6] ^ D[2] ^ C[2] ^ C[6] ^ C[10] ^ C[13] ^ C[14]
		CI[3] = D[15] ^ D[14] ^ D[11] ^ D[7] ^ D[3] ^ C[3] ^ C[7] ^ C[11] ^ C[14] ^ C[15]
		CI[4] = D[15] ^ D[12] ^ D[8] ^ D[4] ^ C[4] ^ C[8] ^ C[12] ^ C[15]
		CI[5] = D[13] ^ D[12] ^ D[11] ^ D[9] ^ D[8] ^ D[5] ^ D[4] ^ D[0] ^ C[0] ^ C[4] ^  C[5] ^ C[8] ^ C[9] ^ C[11] ^ C[12] ^ C[13]
		CI[6] = D[14] ^ D[13] ^ D[12] ^ D[10] ^ D[9] ^ D[6] ^ D[5] ^ D[1] ^ C[1] ^ C[5] ^ C[6] ^ C[9] ^ C[10] ^ C[12] ^ C[13] ^ C[14]
		CI[7] = D[15] ^ D[14] ^ D[13] ^ D[11] ^ D[10] ^ D[7] ^ D[6] ^ D[2] ^ C[2] ^ C[6] ^ C[7] ^ C[10] ^ C[11] ^ C[13] ^ C[14] ^ C[15]
		CI[8] = D[15] ^ D[14] ^ D[12] ^ D[11] ^ D[8] ^ D[7] ^ D[3] ^ C[3] ^ C[7] ^ C[8] ^ C[11] ^ C[12] ^ C[14] ^ C[15]
		CI[9] = D[15] ^ D[13] ^ D[12] ^ D[9] ^ D[8] ^ D[4] ^ C[4] ^ C[8] ^ C[9] ^ C[12] ^ C[13] ^ C[15]
		CI[10] = D[14] ^ D[13] ^ D[10] ^ D[9] ^ D[5] ^ C[5] ^ C[9] ^ C[10] ^ C[13] ^ C[14]
		CI[11] = D[15] ^ D[14] ^ D[11] ^ D[10] ^ D[6] ^ C[6] ^ C[10] ^ C[11] ^ C[14] ^ C[15]
		CI[12] = D[15] ^ D[8] ^ D[7] ^ D[4] ^ D[0] ^ C[0] ^ C[4] ^ C[7] ^ C[8] ^ C[15]
		CI[13] = D[9] ^ D[8] ^ D[5] ^ D[1] ^ C[1] ^ C[5] ^ C[8] ^ C[9]
		CI[14] = D[10] ^ D[9] ^ D[6] ^ D[2] ^ C[2] ^ C[6] ^ C[9] ^ C[10]
		CI[15] = D[11] ^ D[10] ^ D[7] ^ D[3] ^ C[3] ^ C[7] ^ C[10] ^ C[11]
		crc = 0
		for i in range(16):
			crc = ((CI[i] <<i) + crc) & 0xffff
##	print "CRC calculates: ", crc
	return crc

class IntensityProfileMonitorBoard:
	def __init__(self, iCOMPort = 0, iBaudrate = 115200, iTimeOut = 1):
		self.reg = IntensityProfileMonitorBoardRegisters()
		self.firstTimeThroughData = True ## drop data words until SOF is seen
		self.firstTimeThroughCommand = True ## drop command words until SOF is seen
		if PYSERIAL:
			self.ser = serial.Serial(port=iCOMPort, baudrate=iBaudrate, timeout=iTimeOut)
			import termios
##			iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self.ser.fd)
##			print iflag, oflag, cflag, lflag, ispeed, ospeed, cc
			self.ser.read(self.ser.inWaiting())	# Clear buffers
			self.clearBuffer()
		elif PEXPECTSERIAL:
			self.ser = SES_Serial()
			self.ser.spawn()
			self.__ipAddress = '192.168.0.91' ## rdpc11
			self.__telnetPort = 2003 ## temp
			cmd = 'telnet %s %d' %(self.__ipAddress, self.__telnetPort)
			self.ser.cmd(cmd)
			self.ser.setEndline('\n')
                elif TCPSERIAL:
			print "using TCP protocol"
##                        HOST = socket.gethostbyname(socket.gethostname())
                        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.ser.connect(('192.168.0.91', 2104))
                elif UDPSERIAL:
##                        HOST = socket.gethostbyname(socket.gethostname())
			print 'try to make socket using UDP'
                        self.ser = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			print 'don"t try to bind'
##                        self.ser.bind(("192.168.0.1", 1000))
			print 'bound'
##			print 'try to connect instead of bind'
##			self.ser.connect(('192.168.0.91', 2105))
##			print 'bound'
		else:
			raise
		self.lstCommands = []
		self.lstData = []
		self.readTime = 0
		self.nReads = 0
		self.writeTime = 0
		self.sleepTime = 0

	def clearBuffer(self):
##              print dir(self.ser)
                self.ser.flush()
##                self.ser.flushInput()
##                self.ser.flushOutput()
##                n = self.ser.inWaiting()
##                print 'should have flushed serial buffer, have %d bytes in check' %(n)

	def clearData(self): ## to be called after configuration to clear any data taken unconfigured
##		print 'length of data queue: %d' %(len(self.lstData))
		nDataPackets = len(self.lstData)/12
		for i in range(nDataPackets*12):
			self.lstData.pop(0)
		if DEBUG:
			print 'length of data queue after clearing: %d' %(len(self.lstData))
		return len(self.lstData)

	def getDataCommandLength(self):
		return len(self.lstData), len(self.lstCommands)

	def SetCalibrationMode(self, lstbChannels):
		val = self.ReadRegister(self.reg.rg_config)
		val &= 0x7777
		shift = 3
		for b in lstbChannels:
			if b:
				val |= 1<<shift
			shift+=4
		self.WriteRegister(self.reg.rg_config, val)

	def SetCalibrationDivider(self, lstlChannels):
		val = self.ReadRegister(self.reg.cal_rg_config)
		val &= 0x8888
		shift = 0
		for l in lstlChannels:
			if l<=1:
				val |= 1<<shift
			elif l<=100:
				val |= 2<<shift
			elif l<=10000:
				val |= 4<<shift
			shift+=4
		self.WriteRegister(self.reg.cal_rg_config, val)		

	def SetCalibrationPolarity(self, lstbChannels):
		val = self.ReadRegister(self.reg.cal_rg_config)
		val &= 0x7777
		shift = 3
		for b in lstbChannels:
			if b:
				val |= 1<<shift
			shift+=4
		self.WriteRegister(self.reg.cal_rg_config, val)

	# Adjust the reference voltage for the charge amplifier
	def SetChargeAmplifierRef(self, fRefVoltage):
		i = int((fRefVoltage/CHARGEAMP_REF_MAX)*(CHARGEAMP_REF_STEPS-1))
		if i >= CHARGEAMP_REF_STEPS:
			raise RuntimeError, "Invalid charge amplifier reference of %fV, max is %fV" \
					% (fRefVoltage, CHARGEAMP_REF_MAX)
		self.WriteRegister(self.reg.bias_data, i)	

	def SetCalibrationVoltage(self, fCalibrationVoltage):
		i = int((fCalibrationVoltage/CALIBRATION_V_MAX)*(CALIBRATION_V_STEPS-1))
		if i >= CALIBRATION_V_STEPS:
			raise RuntimeError, "Invalid Calibration Bias of %fV, max is %fV" \
					% (fCalibrationVoltage, CALIBRATION_V_MAX)
		self.WriteRegister(self.reg.cal_data, i)
		t0 = time.time()
		time.sleep(0.00005) ## DAC says it needs 10 us to settle
		t = time.time()
		self.sleepTime += t-t0

	def SetChargeAmplifierMultiplier(self, lstlChannels):
		val = self.ReadRegister(self.reg.rg_config)
		val &= 0x8888
		shift = 0
		for l in lstlChannels:
			if l<=1:
				val |= 4<<shift
			elif l<=100:
				val |= 2<<shift
			elif l<=10000:
				val |= 1<<shift
			shift+=4
		if DEBUG:
			print 'SCAM: ', hex(val)
		self.WriteRegister(self.reg.rg_config, val)		
	
	def SetInputBias(self, fBiasVoltage):
		i = int((fBiasVoltage/INPUT_BIAS_MAX)*(INPUT_BIAS_STEPS-1))
		if i >= INPUT_BIAS_STEPS:
			raise RuntimeError, "Invalid input Bias of %fV, max is %fV" % (fBiasVoltage, INPUT_BIAS_MAX)
		originalSetting = self.ReadRegister(self.reg.biasdac_data_config)
		if i != originalSetting:
			self.WriteRegister(self.reg.biasdac_data_config, i)	
			print 'Have changed input bias setting from 0x%x to 0x%x, pausing to allow diode bias to settle' %(originalSetting, i)
			for i in range(50):
				time.sleep(0.1)
				n = self.ser.inWaiting()
				if n>24:
					packetsToClear = (n-12)/12
					for j in range(packetsToClear):
						self.WaitData() ## for trigger-during-config operation: dump data on floor

	def SetChannelAcquisitionWindow(self, lAcqLength, lAcqDelay):
		length = (lAcqLength+CLOCK_PERIOD-1)/CLOCK_PERIOD
		if length > 0xfffff:
			raise RuntimeError, "Acquisition window cannot be more than %dns" % (0xfffff*CLOCK_PERIOD)
		delay = (lAcqDelay+CLOCK_PERIOD-1)/CLOCK_PERIOD
		if delay > 0xfff:
			raise RuntimeError, "Acquisition window cannot be delayed more than %dns" % (0xfff*CLOCK_PERIOD)
		self.WriteRegister(self.reg.reset, (length<<12) | (delay & 0xfff))	
                #print "Reset set to 0x%08x\n" % (self.ReadRegister(self.reg.reset))

	def SetTriggerDelay(self, lTriggerDelay):
		delay = (lTriggerDelay+CLOCK_PERIOD-1)/CLOCK_PERIOD
		if delay > 0xffff:
			raise RuntimeError, "Trigger delay cannot be more than %dns" % (0xffff*CLOCK_PERIOD)
		self.WriteRegister(self.reg.trig_delay, delay)
	
	def CalibrationStart(self, lCalStrobeLength=0xff):
		length = (lCalStrobeLength+CLOCK_PERIOD-1)/CLOCK_PERIOD
		if length > 0xffff:
			raise RuntimeError, "Strobe cannot be more than %dns" % (0xffff*CLOCK_PERIOD)
		self.WriteRegister(self.reg.cal_strobe, length)	

	def ReadRegister(self, lRegAddr):
		cmd = IntensityProfileMonitorBoardCommand(False, lRegAddr)
		self.writeCommand(cmd)
		while self.inWaiting(True) < 4:
			pass
		resp = IntensityProfileMonitorBoardResponse(self.read(True, 4))
		if not resp.CheckCRC():
			print 'response from register:', resp.Data
			raise RuntimeError, "Invalid CRC accessing register 0x%02x" % (lRegAddr)
		return resp.Data
	
	def WriteRegister(self, lRegAddr, lRegValue):
		cmd = IntensityProfileMonitorBoardCommand(True, lRegAddr, lRegValue)
		self.writeCommand(cmd)

	def WaitData(self):
		while self.inWaiting(False) < 12:
			pass
		data = IntensityProfileMonitorBoardData(self.read(False, 12))
		if not data.CheckCRC():
			raise RuntimeError, "Invalid data packet CRC"
		return data
	
	def read(self, bCommand, lBytes):
		lst = []
		if bCommand:
			while len(self.lstCommands) < lBytes:
				self.inWaiting(bCommand)	
			for i in range(lBytes):
				lst.append(self.lstCommands.pop(0))
		else:
			while len(self.lstData) < lBytes:
				self.inWaiting(bCommand)	
			for i in range(lBytes):
				lst.append(self.lstData.pop(0))
		if DEBUG:
			print 'read com/resp', bCommand, ', bytes expected', lBytes, ', cr list len', len(self.lstCommands), ', data list len', len(self.lstData), ', list length', len(lst), [hex(b) for b in lst], [hex(b) for b in self.lstCommands]##, [hex(b) for b in self.lstData]
##			pass
		return lst
		
	def writeCommand(self, lstBytes):
		count = 0
		string = ""
		for data in lstBytes:
			w = [0x90 | (data & 0xf), (data>>4) & 0x3f, 0x40 | ((data>>10) & 0x3f)]
			if count == 0:
				w[0] |= 0x40
			if count == len(lstBytes)-1:
				w[0] |= 0x20
			count = count+1
			if DEBUG:
				print "Ser W: %s" % (" ".join([hex(i) for i in w]))
##                        print "Ser W, chr: %s" %("".join([chr(i) for i in w]))
			if PYSERIAL:
				foo = 0
				while foo==0:
					foo += 1
					t0 = time.time()
					self.ser.write("".join([chr(i) for i in w]))
					t = time.time()
					self.writeTime += t-t0
##					time.sleep(0.001)
##					print "just keep writing"

			elif PEXPECTSERIAL:
				self.ser.cmd("".join([chr(i) for i in w]))
                        else:
				t0 = time.time()
				msg = "".join([chr(i) for i in w])
				if TCPSERIAL:
					self.ser.send(msg)
				else:
					if len(msg) != self.ser.sendto(msg, ('172.21.10.124', 2105)):##"".join([chr(i) for i in w]))##, ('192.168.0.91', 2105))
						##('192.168.0.91', 2105)):##"".join([chr(i) for i in w]))##, ('192.168.0.91', 2105))
						print 'problem sending msg:' %(msg)
				t = time.time()
##				print "write time", t-t0
				self.writeTime += t-t0

	def inWaiting(self, bCommand):
		if PYSERIAL:
			t0 = time.time()
			n = self.ser.inWaiting()
			while n >= 3:
				w0 = ord(self.ser.read(1))
				# Out of sync: bit 8 must be set
				if (w0 & 0x80) == 0:
					if DEBUG:
						print "found %d chars in buffer, %d words in cr list, %d words in data list" %(n, len(self.lstCommands), len(self.lstData))
						print "Ser R out of sync: 0x%x" % (w0)
					n = n-1 ## discard
##					for i in range(n):
##						w0 = ord(self.ser.read(1))
##						print "Next byte in buffer: 0x%x" % (w0)
##					n = 0
					if DEBUG:
						print "Ser R out of sync: 0x%x" % (w0)
					continue
				if self.firstTimeThroughData:
					if ((w0 & 0x40) == 0) and ((w0 & 0x10) == 0):
						if DEBUG:
							print "First time through, SOF for data not set: found %d chars in buffer, %d words in cr list, %d words in data list" %(n, len(self.lstCommands), len(self.lstData))
						n = n-1
						continue
				if self.firstTimeThroughCommand:	
					if ((w0 & 0x40) == 0) and ((w0 & 0x10) != 0) and (w0==0xdc): ## 0xdc hack
						if DEBUG:
							print "First time through, SOF for command not set: found %d chars in buffer, %d words in cr list, %d words in data list" %(n, len(self.lstCommands), len(self.lstData))
						n = n-1
						continue
##				print 'fttd, fftc, w0', self.firstTimeThroughData, self.firstTimeThroughCommand, '0x%x' %(w0)
				if self.firstTimeThroughData and ((w0 & 0x10) == 0):
					if (w0 & 0x20) != 0:
						print 'SOF and EOF found, something is wrong parsing data, try next word: 0x%x' %(w0)
						n = n-1
						continue
					if (w0 != 0xc0):
						print 'SOF is bogus, something is wrong parsing data, try next word: 0x%x' %(w0)
						n = n-1
						continue
					self.firstTimeThroughData = False
					print 'Have found first SOF for data: 0x%x' %(w0)
				if self.firstTimeThroughCommand and ((w0 & 0x10) != 0):
					if (w0 & 0x20) != 0:
						print 'SOF and EOF found, something is wrong parsing CR, try next word: 0x%x' %(w0)
						n = n-1
						continue
					if (w0 != 0xdc):
						print 'SOF is bogus, something is wrong parsing data, try next word: 0x%x' %(w0)
						n = n-1
						continue
					print 'Have found first SOF for command: 0x%x' %(w0)
					self.firstTimeThroughCommand = False
##				print 'have found three bytes: 0x%x, 0x%x, 0x%x' %(w0, w1, w2)
				[w1, w2] = [ord(c) for c in self.ser.read(2)]
				data = (w0 & 0xf) | ((w1 & 0x3f)<<4) | ((w2 & 0x3f)<<10)
				if (w0 & 0x10) != 0:
					self.lstCommands.append(data)
				else:
					self.lstData.append(data)
				if DEBUG:
					print "Ser R: %x %x %x" % (w0, w1, w2)
				n = n-3
			t = time.time()
			self.readTime += t-t0
			self.nReads += 1
		elif PEXPECTSERIAL:
			readData = self.ser.rsp().strip() ## string of bytes hopefully
			n = len(readData)
			readData = [x for x in readData]
			index = 0
			while n >= 3:
				w0 = ord(readData[index])
				index += 1
				if (w0 & 0x80) == 0: # Out of sync: bit 8 must be set
					n = n-1
					if DEBUG:
						print "Ser R: %x" % (w0)
					continue
				[w1, w2] = [ord(c) for c in [readData[index], readData[index+1]]]
				index += 2
				data = (w0 & 0xf) | ((w1 & 0x3f)<<4) | ((w2 & 0x3f)<<10)
				if (w0 & 0x10) != 0:
					self.lstCommands.append(data)
				else:
					self.lstData.append(data)
				if DEBUG:
					print "Ser R: %x %x %x" % (w0, w1, w2)
				n = n-3
                else:
			## tmp
##			time.sleep(1)
			##
			t0 = time.time()
##			print 'read from socket'
			if TCPSERIAL:
				readData = self.ser.recv(1024)
			else:
				readData, address = self.ser.recvfrom(1024)
##				print 'udp read: ', address, readData
			t = time.time()
			if DEBUG:
				print "read time", t-t0
			self.readTime += t-t0
			self.nReads += 1
			n = len(readData)
			readData = [x for x in readData]
			index = 0
##			print "n in inWaiting starts at: ", n
			while n >= 3:
				w0 = ord(readData[index])
##				print "word: ", w0
				index += 1
				if (w0 & 0x80) == 0: # Out of sync: bit 8 must be set
					n = n-1
					print "Ser R: %x, out of sync" % (w0)
					continue
				[w1, w2] = [ord(c) for c in [readData[index], readData[index+1]]]
				index += 2
				data = (w0 & 0xf) | ((w1 & 0x3f)<<4) | ((w2 & 0x3f)<<10)
				if (w0 & 0x10) != 0:
					self.lstCommands.append(data)
				else:
					self.lstData.append(data)
				if DEBUG:
					print "Ser R: %x %x %x" % (w0, w1, w2)
				n = n-3

		if bCommand:
			return len(self.lstCommands)
		else:
			return len(self.lstData)

# Class that contains a list of all IPMB registers
class IntensityProfileMonitorBoardRegisters:
	def __init__(self):
		self.timestamp0 = 0x00
		self.timestamp1 = 0x01
		self.serid0 = 0x02
		self.serid1 = 0x03
		self.adc0 = 0x04
		self.adc1 = 0x05
		self.rg_config = 0x06
		self.cal_rg_config = 0x07
		self.reset = 0x08
		self.bias_data = 0x09
		self.cal_data = 0x0a
		self.biasdac_data_config = 0x0b
		self.status = 0x0c
		self.errors = 0x0d
		self.cal_strobe = 0x0e
		self.trig_delay = 0x0f

class IntensityProfileMonitorBoardCommand:
	def __init__(self, bWrite, lAddr, lData = 0):
		self.lst = [lAddr & 0xFF, lData & 0xFFFF, (lData >> 16) & 0xFFFF, 0] 
		if bWrite:
			self.lst[0] |= 1<<8
		self.lst[3] = CRC(self.lst[0:3])
	def __getslice__(self, i, j):
		return self.lst[i:j]
	def __getitem__(self, i):
		return self.lst[i]
	def __len__(self):
		return len(self.lst)
		

class IntensityProfileMonitorBoardResponse:
	def __init__(self, lstPacket):
		if len(lstPacket) != 4:
			raise RuntimeError, "Invalid response packet size %d" % (len(lstPacket))
		self.Addr = 0
		self.Data = 0
		self.Checksum = 0
		self[0:4] = lstPacket
	def __setslice__(self, i, j, s):
		for count in range(i, j):
			if count == 0:
				self.Addr = s[count-i] & 0xFF
			elif count == 1:
				self.Data = (self.Data & 0xFFFF0000L) | s[count-i]
			elif count == 2:
				self.Data = (self.Data & 0xFFFF) | (long(s[count-i])<<16)
			elif count == 3:
				self.Checksum = s[count-i]
	def __getslice__(self, i, j):
		lst = []
		for count in range(i, j):
			if count == 0:
				lst.append(self.Addr & 0xFF)
			elif count == 1:
				lst.append(self.Data & 0xFFFF)
			elif count == 2:
				lst.append(self.Data>>16)
			elif count == 3:
				lst.append(self.Checksum)
		return lst
	def CheckCRC(self):
		if CRC(self[0:3]) == self.Checksum:
			return True
		return False

class IntensityProfileMonitorBoardData:
	def __init__(self, lstPacket):
		if len(lstPacket) != 12:
			raise RuntimeError, "Invalid data packet size %d" % (len(lstPacket))
		self.Timestamp = 0
		self.Config0 = 0
		self.Config1 = 0
		self.Config2 = 0
		self.Ch0 = 0
		self.Ch1 = 0
		self.Ch2 = 0
		self.Ch3 = 0
		self.Checksum = 0
		self[0:12] = lstPacket
	def __setslice__(self, i, j, s):
		for count in range(i, j):
			if count == 0:
				self.Timestamp = (self.Timestamp & 0x0000FFFFFFFFFFFF) | (s[count-i]<<48)
			elif count == 1:
				self.Timestamp = (self.Timestamp & 0xFFFF0000FFFFFFFF) | (s[count-i]<<32)
			elif count == 2:
				self.Timestamp = (self.Timestamp & 0xFFFFFFFF0000FFFF) | (s[count-i]<<16)
			elif count == 3:
				self.Timestamp = (self.Timestamp & 0xFFFFFFFFFFFF0000) | s[count-i]
			elif count == 4:
				self.Config0 = s[count-i]
			elif count == 5:
				self.Config1 = s[count-i]
			elif count == 6:
				self.Config2 = s[count-i]
			elif count == 7:
				self.Ch0 = s[count-i]
			elif count == 8:
				self.Ch1 = s[count-i]
			elif count == 9:
				self.Ch2 = s[count-i]
			elif count == 10:
				self.Ch3 = s[count-i]
			elif count == 11:
				self.Checksum = s[count-i]
	def __getslice__(self, i, j):
		lst = []
		for count in range(i, j):
			if count == 0:
				lst.append(self.Timestamp>>48)
			elif count == 1:
				lst.append((self.Timestamp>>32) & 0xFFFF)
			elif count == 2:
				lst.append((self.Timestamp>>16) & 0xFFFF)
			elif count == 3:
				lst.append(self.Timestamp & 0xFFFF)
			elif count == 4:
				lst.append(self.Config0)
			elif count == 5:
				lst.append(self.Config1)
			elif count == 6:
				lst.append(self.Config2)
			elif count == 7:
				lst.append(self.Ch0)
			elif count == 8:
				lst.append(self.Ch1)
			elif count == 9:
				lst.append(self.Ch2)
			elif count == 10:
				lst.append(self.Ch3)
			elif count == 11:
				lst.append(self.Checksum)
		return lst
	def CheckCRC(self):
		if CRC(self[0:11]) == self.Checksum:
			return True
		print 'Data CRC problem: checksum is',  CRC(self[0:11]), 'expected ', self.Checksum
		print 'Data:', self[0:11]
		return False
	def GetTimestamp_ticks(self):
		return self.Timestamp
	def GetTriggerDelay_ns(self):
		return self.Config2*CLOCK_PERIOD
	def GetCh0_V(self):
		return (float(self.Ch0)*ADC_RANGE)/(ADC_STEPS-1)
	def GetCh1_V(self):
		return (float(self.Ch1)*ADC_RANGE)/(ADC_STEPS-1)
	def GetCh2_V(self):
		return (float(self.Ch2)*ADC_RANGE)/(ADC_STEPS-1)
	def GetCh3_V(self):
		return (float(self.Ch3)*ADC_RANGE)/(ADC_STEPS-1)
	
