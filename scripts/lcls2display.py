import sys
import argparse
from psp import Pv
from PyQt4 import QtCore, QtGui

class PvDisplay(QtGui.QLabel):

    valueSet = QtCore.pyqtSignal(QtCore.QString,name='valueSet')

    def __init__(self):
        QtGui.QLabel.__init__(self,"-")

    def connect_signal(self):
        self.valueSet.connect(self.setValue)

    def setValue(self,value):
        self.setText(value)

class PvLabel:
    def __init__(self, parent, partition, module, name, dName=None, isInt=False):
        self.layout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel(name)
        self.layout.addWidget(self.label)
        self.layout.addStretch()
#        self.display = QtGui.QLabel("-")
        self.display = PvDisplay()
        self.display.connect_signal()
        self.layout.addWidget(self.display)
        parent.addLayout(self.layout)

        if module is None:
            pvbase = "DAQ:"+partition+":"
        else:
            pvbase = "DAQ:"+partition+":"+module+":"
        pvname = pvbase+name
        print pvname
        self.pv = Pv.Pv(pvname)
        self.pv.monitor_start()
        self.pv.add_monitor_callback(self.update)
        if dName is not None:
            dPvName = pvbase+dName
            self.dPv = Pv.Pv(dPvName)
            self.dPv.monitor_start()
            self.dPv.add_monitor_callback(self.update)
        else:
            self.dPv = None
        self.isInt = isInt

    def update(self, err):
        q = self.pv.value
        if self.dPv is not None:
            dq = self.dPv.value
        else:
            dq = None
        if err is None:
            s = QtCore.QString('fail')
            try:
                if self.isInt:
                    if dq is None:
                        s = QtCore.QString("%1 (0x%2)").arg(QtCore.QString.number(long(q),10)).arg(QtCore.QString.number(long(q),16))
                    else:
                        s = QtCore.QString("%1 (0x%2) [%3 (0x%4)]").arg(QtCore.QString.number(long(q),10)).arg(QtCore.QString.number(long(q),16)).arg(QtCore.QString.number(long(dq),10)).arg(QtCore.QString.number(long(dq),16))
                else:
                    if dq is None:
                        s = QtCore.QString.number(q)
                    else:
                        s = QtCore.QString("%1 [%2]").arg(QtCore.QString.number(q)).arg(QtCore.QString.number(dq))
            except:
                v = ''
                for i in range(len(q)):
                    v = v + ' %f'%q[i]
                    #v = v + ' ' + QtCore.QString.number(q[i])
                    if dq is not None:
                        #v = v + ' [' + QtCore.QString.number(dq[i]) + ']'
                        v = v + ' [' + '%f'%dq[i] + ']'
                    if ((i%8)==7):
                        v = v + '\n'
                s = QtCore.QString(v)

            self.display.valueSet.emit(s)
        else:
            print err

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, partition):
        MainWindow.setObjectName(QtCore.QString.fromUtf8("MainWindow"))
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")

        hbox = QtGui.QHBoxLayout()

        rcVbox  = QtGui.QVBoxLayout()
        rcFrame = QtGui.QFrame()
        rcFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        rcFrame.setLayout(rcVbox)
        hbox.addWidget(rcFrame)

        xpmVbox  = QtGui.QVBoxLayout()
        xpmFrame = QtGui.QFrame()
        xpmFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        xpmFrame.setLayout(xpmVbox)
        hbox.addWidget(xpmFrame)

        dtiVbox  = QtGui.QVBoxLayout()
        dtiFrame = QtGui.QFrame()
        dtiFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        dtiFrame.setLayout(dtiVbox)
        hbox.addWidget(dtiFrame)

        self.centralWidget.setLayout(hbox)

        rcBox   = QtGui.QHBoxLayout()
        rcLabel = QtGui.QLabel("RC")
        rcBox.addStretch()
        rcBox.addWidget(rcLabel)
        rcBox.addStretch()
        rcVbox.addLayout(rcBox)

        self.running          = PvLabel(rcVbox, partition, None, "RUNNING")
        self.run_number       = PvLabel(rcVbox, partition, None, "RUN_NUMBER")
        self.run_duration     = PvLabel(rcVbox, partition, None, "RUN_DURATION")
        self.run_mbytes       = PvLabel(rcVbox, partition, None, "RUN_MBYTES")
        self.config_type      = PvLabel(rcVbox, partition, None, "CONFIG_TYPE")
        self.control_state    = PvLabel(rcVbox, partition, None, "CONTROL_STATE")
        self.configured       = PvLabel(rcVbox, partition, None, "CONFIGURED")
        self.recording        = PvLabel(rcVbox, partition, None, "RECORDING")
        self.expName          = PvLabel(rcVbox, partition, None, "EXPNAME")
        self.expNum           = PvLabel(rcVbox, partition, None, "EXPNUM")

        rcVbox.addStretch()

        xpmBox   = QtGui.QHBoxLayout()
        xpmLabel = QtGui.QLabel("XPM")
        xpmBox.addStretch()
        xpmBox.addWidget(xpmLabel)
        xpmBox.addStretch()
        xpmVbox.addLayout(xpmBox)

        self.xpm_l0InpRate    = PvLabel(xpmVbox, partition, "XPM", "L0InpRate")
        self.xpm_l0AccRate    = PvLabel(xpmVbox, partition, "XPM", "L0AccRate")
        self.xpm_l1Rate       = PvLabel(xpmVbox, partition, "XPM", "L1Rate")
        self.xpm_numL0Inp     = PvLabel(xpmVbox, partition, "XPM", "NumL0Inp")
        self.xpm_numL0Acc     = PvLabel(xpmVbox, partition, "XPM", "NumL0Acc", None, True)
        self.xpm_numL1        = PvLabel(xpmVbox, partition, "XPM", "NumL1")
        self.xpm_deadFrac     = PvLabel(xpmVbox, partition, "XPM", "DeadFrac")
        self.xpm_deadTime     = PvLabel(xpmVbox, partition, "XPM", "DeadTime")
        self.xpm_deadFlnk     = PvLabel(xpmVbox, partition, "XPM", "DeadFLnk")

        self.xpm_rxClks       = PvLabel(xpmVbox, partition, "XPM", "RxClks"     )
        self.xpm_txClks       = PvLabel(xpmVbox, partition, "XPM", "TxClks"     )
        self.xpm_rxRsts       = PvLabel(xpmVbox, partition, "XPM", "RxRsts"     )
        self.xpm_crcErrs      = PvLabel(xpmVbox, partition, "XPM", "CrcErrs"    )
        self.xpm_rxDecErrs    = PvLabel(xpmVbox, partition, "XPM", "RxDecErrs"  )
        self.xpm_rxDspErrs    = PvLabel(xpmVbox, partition, "XPM", "RxDspErrs"  )
        self.xpm_bypassRsts   = PvLabel(xpmVbox, partition, "XPM", "BypassRsts" )
        self.xpm_bypassDones  = PvLabel(xpmVbox, partition, "XPM", "BypassDones")
        self.xpm_rxLinkUp     = PvLabel(xpmVbox, partition, "XPM", "RxLinkUp"   )
        self.xpm_fids         = PvLabel(xpmVbox, partition, "XPM", "FIDs"       )
        self.xpm_sofs         = PvLabel(xpmVbox, partition, "XPM", "SOFs"       )
        self.xpm_eofs         = PvLabel(xpmVbox, partition, "XPM", "EOFs"       )

        xpmVbox.addStretch()

        dtiBox   = QtGui.QHBoxLayout()
        dtiLabel = QtGui.QLabel("DTI")
        dtiBox.addStretch()
        dtiBox.addWidget(dtiLabel)
        dtiBox.addStretch()
        dtiVbox.addLayout(dtiBox)

        self.dti_usLinks      = PvLabel(dtiVbox, partition, "DTI", "UsLinks", None, True)
        self.dti_bpLinks      = PvLabel(dtiVbox, partition, "DTI", "BpLinks", None, True)
        self.dti_dsLinks      = PvLabel(dtiVbox, partition, "DTI", "DsLinks", None, True)

        self.dti_usRxErrs     = PvLabel(dtiVbox, partition, "DTI", "UsRxErrs", "dUsRxErrs"   )
        self.dti_usRxFull     = PvLabel(dtiVbox, partition, "DTI", "UsRxFull", "dUsRxFull"   )
        self.dti_usIbRecv     = PvLabel(dtiVbox, partition, "DTI", "UsIbRecv", "dUsIbRecv"   )
        self.dti_usIbEvt      = PvLabel(dtiVbox, partition, "DTI", "UsIbEvt",  "dUsIbEvt"    )
        self.dti_usObRecv     = PvLabel(dtiVbox, partition, "DTI", "UsObRecv", "dUsObRecv"   )
        self.dti_usObSent     = PvLabel(dtiVbox, partition, "DTI", "UsObSent", "dUsObSent"   )

        self.dti_bpObSent     = PvLabel(dtiVbox, partition, "DTI", "BpObSent", "dBpObSent"   )

        self.dti_dsRxErrs     = PvLabel(dtiVbox, partition, "DTI", "DsRxErrs", "dDsRxErrs"   )
        self.dti_dsRxFull     = PvLabel(dtiVbox, partition, "DTI", "DsRxFull", "dDsRxFull"   )
        self.dti_dsObSent     = PvLabel(dtiVbox, partition, "DTI", "DsObSent", "dDsObSent"   )

        self.dti_qpllLock     = PvLabel(dtiVbox, partition, "DTI", "QpllLock"   )

        self.dti_monClkRate   = PvLabel(dtiVbox, partition, "DTI", "MonClkRate" )
        self.dti_monClkSlow   = PvLabel(dtiVbox, partition, "DTI", "MonClkSlow" )
        self.dti_monClkFast   = PvLabel(dtiVbox, partition, "DTI", "MonClkFast" )
        self.dti_monClkLock   = PvLabel(dtiVbox, partition, "DTI", "MonClkLock" )

        self.dti_usLinkObL0   = PvLabel(dtiVbox, partition, "DTI", "UsLinkObL0",  "dUsLinkObL0" )
        self.dti_usLinkObL1A  = PvLabel(dtiVbox, partition, "DTI", "UsLinkObL1A", "dUsLinkObL1A")
        self.dti_usLinkObL1R  = PvLabel(dtiVbox, partition, "DTI", "UsLinkObL1R", "dUsLinkObL1R")

        self.dti_rxFrmErrs    = PvLabel(dtiVbox, partition, "DTI", "RxFrmErrs", "dRxFrmErrs" )
        self.dti_rxFrms       = PvLabel(dtiVbox, partition, "DTI", "RxFrms",    "dRxFrms"    )
        self.dti_rxOpcodes    = PvLabel(dtiVbox, partition, "DTI", "RxOpcodes", "dRxOpcodes" )
        self.dti_txFrmErrs    = PvLabel(dtiVbox, partition, "DTI", "TxFrmErrs", "dTxFrmErrs" )
        self.dti_txFrms       = PvLabel(dtiVbox, partition, "DTI", "TxFrms",    "dTxFrms"    )
        self.dti_txOpcodes    = PvLabel(dtiVbox, partition, "DTI", "TxOpcodes", "dTxOpcodes" )

        dtiVbox.addStretch()

        MainWindow.setWindowTitle("DAQ:"+partition)
        MainWindow.setCentralWidget(self.centralWidget)

if __name__ == '__main__':
    print QtCore.PYQT_VERSION_STR

    parser = argparse.ArgumentParser(description='simple pv monitor gui')
    parser.add_argument("pv", help="pv to monitor")
    args = parser.parse_args()

    app = QtGui.QApplication(["lcls2display"])
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.pv)

    MainWindow.show()
    sys.exit(app.exec_())
