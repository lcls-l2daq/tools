import sys
import argparse
from psp import Pv
from PyQt4 import QtCore, QtGui

NReadoutChannels = 10
NTriggerChannels = 12

accSel =     ['LCLS-I','LCLS-II']
linkStates = ['Down','Up']
rxpols     = ['Normal','Inverted']
RowHdrLen = 110
modes      = ['Disable','Trigger','+Readout','+BSA']
modesTTL   = ['Disable','Trigger']
polarities = ['Neg','Pos']
destns     = ['Any','None','InjD','Dump','SXU']
evtsel     = ['Fixed Rate','AC Rate','Sequence']
fixedRates = ['929kHz','71.4kHz','10.2kHz','1.02kHz','102Hz','10.2Hz','1.02Hz']
acRates    = ['60Hz','30Hz','10Hz','5Hz','1Hz']
acTS       = ['TS%u'%(i+1) for i in range(6)]
seqIdxs    = ['s%u'%i for i in range(18)]
seqBits    = ['b%u'%i for i in range(32)]


class PvTextDisplay(QtGui.QLineEdit):

    valueSet = QtCore.pyqtSignal(QtCore.QString,name='valueSet')

    def __init__(self):
        super(PvTextDisplay, self).__init__("-")
        self.setMinimumWidth(60)
        
    def connect_signal(self):
        self.valueSet.connect(self.setValue)

    def setValue(self,value):
        self.setText(value)

        
class PvComboDisplay(QtGui.QComboBox):

    valueSet = QtCore.pyqtSignal(QtCore.QString,name='valueSet')

    def __init__(self, choices):
        super(PvComboDisplay, self).__init__()
        self.addItems(choices)
        
    def connect_signal(self):
        self.valueSet.connect(self.setValue)

    def setValue(self,value):
        self.setCurrentIndex(value)

class PvEditTxt(PvTextDisplay):

    def __init__(self, pv):
        super(PvEditTxt, self).__init__()
        self.connect_signal()
        self.editingFinished.connect(self.setPv)
        
        self.pv = Pv.Pv(pv)
        self.pv.monitor_start()
        self.pv.add_monitor_callback(self.update)

class PvEditInt(PvEditTxt):

    def __init__(self, pv):
        super(PvEditInt, self).__init__(pv)

    def setPv(self):
        value = self.text().toInt()
        self.pv.put(value)

    def update(self, err):
        q = self.pv.value
        if err is None:
            s = QtCore.QString('fail')
            try:
                s = QtCore.QString("%1").arg(QtCore.QString.number(long(q),10))
            except:
                v = ''
                for i in range(len(q)):
                    v = v + ' %f'%q[i]
                s = QtCore.QString(v)

            self.valueSet.emit(s)
        else:
            print err


class PvInt(PvEditInt):

    def __init__(self,pv):
        super(PvInt, self).__init__(pv)
        self.setEnabled(False)


class PvEditDbl(PvEditTxt):

    def __init__(self, pv):
        super(PvEditDbl, self).__init__(pv)

    def setPv(self):
        value = self.text().toDouble()
        self.pv.put(value)

    def update(self, err):
        q = self.pv.value
        if err is None:
            s = QtCore.QString('fail')
            try:
                s = QtCore.QString.number(q)
            except:
                v = ''
                for i in range(len(q)):
                    v = v + ' %f'%q[i]
                s = QtCore.QString(v)

            self.valueSet.emit(s)
        else:
            print err

class PvDbl(PvEditDbl):

    def __init__(self,pv):
        super(PvDbl, self).__init__(pv)
        self.setEnabled(False)


class PvEditCmb(PvComboDisplay):

    def __init__(self, pvname, choices):
        super(PvEditCmb, self).__init__(choices)
        self.connect_signal()
        self.currentIndexChanged.connect(self.setValue)
        
        self.pv = Pv.Pv(pvname)
        self.pv.monitor_start()
        self.pv.add_monitor_callback(self.update)

    def setValue(self):
        value = self.currentIndex()
        self.pv.put(value)

    def update(self, err):
        q = self.pv.value
        if err is None:
            self.setCurrentIndex(q)
            self.valueSet.emit(q)
        else:
            print err


class PvCmb(PvEditCmb):

    def __init__(self, pvname, choices):
        super(PvCmb, self).__init__(pvname, choices)
        self.setEnabled(False)


class PvEvtTab(QtGui.QStackedWidget):
    
    def __init__(self, pvname, evtcmb):
        super(PvEvtTab,self).__init__()

        self.addWidget(PvEditCmb(pvname+'FRATE',fixedRates))

        acw = QtGui.QWidget()
        acl = QtGui.QVBoxLayout()
        acl.addWidget(PvEditCmb(pvname+'ARATE',acRates))
        acl.addWidget(PvEditCmb(pvname+'ATS'  ,acTS))
        acw.setLayout(acl)
        self.addWidget(acw)
        
        sqw = QtGui.QWidget()
        sql = QtGui.QVBoxLayout()
        sql.addWidget(PvEditCmb(pvname+'SEQIDX',seqIdxs))
        sql.addWidget(PvEditCmb(pvname+'SEQBIT',seqBits))
        sqw.setLayout(sql)
        self.addWidget(sqw)

        evtcmb.currentIndexChanged.connect(self.setCurrentIndex)
                 
class PvEditEvt(QtGui.QWidget):
    
    def __init__(self, pvname):
        super(PvEditEvt, self).__init__()
        vbox = QtGui.QVBoxLayout()
        evtcmb = PvEditCmb(pvname+'RSEL',evtsel)
        vbox.addWidget(evtcmb)
        vbox.addWidget(PvEvtTab(pvname,evtcmb))
        self.setLayout(vbox)

class PvRowDbl():
    def __init__(self, row, layout, prefix, pv, label, ncols=NTriggerChannels):
        qlabel = QtGui.QLabel(label)
        qlabel.setMinimumWidth(RowHdrLen)
        layout.addWidget(qlabel,row,0)

        for i in range(ncols):
            qedit = PvEditDbl(prefix+':CH%u:'%i+pv)
            layout.addWidget(qedit,row,i+1)
        row += 1

class PvRowInt():
    def __init__(self, row, layout, prefix, pv, label, ncols=NTriggerChannels):
        qlabel = QtGui.QLabel(label)
        qlabel.setMinimumWidth(RowHdrLen)
        layout.addWidget(qlabel,row,0)

        for i in range(ncols):
            qedit = PvEditInt(prefix+':CH%u:'%i+pv)
            layout.addWidget(qedit,row,i+1)
        row += 1

class PvRowCmb():
    def __init__(self, row, layout, prefix, pv, label, choices, ncols=NTriggerChannels):
        qlabel = QtGui.QLabel(label)
        qlabel.setMinimumWidth(RowHdrLen)
        layout.addWidget(qlabel,row,0)

        for i in range(ncols):
            qedit = PvEditCmb(prefix+':CH%u:'%i+pv, choices)
            layout.addWidget(qedit,row,i+1)
        row += 1

class PvRowMod():
    def __init__(self, row, layout, prefix, pv, label):
        qlabel = QtGui.QLabel(label)
        qlabel.setMinimumWidth(RowHdrLen)
        layout.addWidget(qlabel,row,0)

        for i in range(NTriggerChannels):
            if i<NReadoutChannels:
                qedit = PvEditCmb(prefix+':CH%u:'%i+pv, modes)
            else:
                qedit = PvEditCmb(prefix+':CH%u:'%i+pv, modesTTL)
            layout.addWidget(qedit,row,i+1)
        row += 1

class PvRowEvt():
    def __init__(self, row, layout, prefix, ncols=NTriggerChannels):
        qlabel = QtGui.QLabel('Event')
        qlabel.setMinimumWidth(RowHdrLen)
        layout.addWidget(qlabel,row,0)

        for i in range(ncols):
            qedit = PvEditEvt(prefix+':CH%u:'%i)
            layout.addWidget(qedit,row,i+1)
        row += 1

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, pvname):
        MainWindow.setObjectName(QtCore.QString.fromUtf8("MainWindow"))
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")

        layout = QtGui.QGridLayout()

        row = 0
        
        layout.addWidget( QtGui.QLabel('ACCSEL'), row, 0 )
        layout.addWidget( PvEditCmb(pvname+':ACCSEL', accSel), row, 1 )
        row += 1

        layout.addWidget( QtGui.QLabel('LINKSTATE'), row, 0 )
        layout.addWidget( PvCmb(pvname+':LINKSTATE', linkStates), row, 1 )
        row += 1

        layout.addWidget( QtGui.QLabel('RXERRS'), row, 0 )
        layout.addWidget( PvInt(pvname+':RXERRS'), row, 1 )
        row += 1

        layout.addWidget( QtGui.QLabel('RXPOL'), row, 0 )
        layout.addWidget( PvEditCmb(pvname+':RXPOL', rxpols), row, 1 )
        row += 1

        layout.addWidget( QtGui.QLabel('FRAME RATE [Hz]'), row, 0 )
        layout.addWidget( PvDbl(pvname+':FRAMERATE'), row, 1 )
        row += 1

        layout.addWidget( QtGui.QLabel('RXCLK RATE [MHz]'), row, 0 )
        layout.addWidget( PvDbl(pvname+':RXCLKRATE'), row, 1 )
        row += 1

        for i in range(12):
            qlabel = QtGui.QLabel('CH%u'%i)
            layout.addWidget( qlabel, row+0, i+1, QtCore.Qt.AlignHCenter )
        PvRowMod( row+1, layout, pvname, "MODE" , "")
        PvRowDbl( row+2, layout, pvname, "DELAY", "Delay [sec]")
        PvRowDbl( row+3, layout, pvname, "WIDTH", "Width [sec]")
        PvRowCmb( row+4, layout, pvname, "POL"  , "Polarity", polarities)
        PvRowCmb( row+5, layout, pvname, "DESTN", "Destn", destns)
        PvRowEvt( row+6, layout, pvname)
        PvRowInt( row+7, layout, pvname, "BSTART", "BsaStart [pul]", ncols=NReadoutChannels)
        PvRowInt( row+8, layout, pvname, "BWIDTH", "BsaWidth [pul]", ncols=NReadoutChannels)
        PvRowDbl( row+9, layout, pvname, "RATE"  , "Rate [Hz]", ncols=NReadoutChannels)

        self.centralWidget.setLayout(layout)
        self.centralWidget.resize(1400,600)
        MainWindow.resize(1400,600)
            

if __name__ == '__main__':
    print QtCore.PYQT_VERSION_STR

    parser = argparse.ArgumentParser(description='simple pv monitor gui')
    parser.add_argument("pv", help="pv to monitor")
    args = parser.parse_args()

    app = QtGui.QApplication([])
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.pv)
    MainWindow.updateGeometry()

    MainWindow.show()
    sys.exit(app.exec_())
