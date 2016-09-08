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
    def __init__(self, parent, partition, name, isInt=False):
        self.layout = QtGui.QHBoxLayout(parent)
        self.label = QtGui.QLabel(name)
        self.layout.addWidget(self.label)
#        self.display = QtGui.QLabel("-")
        self.display = PvDisplay()
        self.display.connect_signal()
        self.layout.addWidget(self.display)
        parent.layout.addLayout(self.layout)

        pvname = "DAQ:"+partition+":"+name
        print pvname
        self.pv = Pv.Pv(pvname)
        self.pv.monitor_start()
        self.pv.add_monitor_callback(self.update)
        self.isInt = isInt

    def update(self, err):
        q = self.pv.value
        if err is None:
            s = QtCore.QString('fail')
            try:
                if self.isInt:
                    s = QtCore.QString("%1 (0x%2)").arg(QtCore.QString.number(long(q),10)).arg(QtCore.QString.number(long(q),16))
                else:
                    s = QtCore.QString.number(q)
            except:
                v = ''
                for i in range(len(q)):
                    v = v + ' %f'%q[i]
                s = QtCore.QString(v)

            self.display.valueSet.emit(s)
        else:
            print err

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, partition):
        MainWindow.setObjectName(QtCore.QString.fromUtf8("MainWindow"))
        MainWindow.resize(128, 96)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.centralWidget.layout = QtGui.QVBoxLayout(self.centralWidget)

        self.numl0    = PvLabel( self.centralWidget, partition, "NUML0ACC", True)
        self.l0inprate= PvLabel( self.centralWidget, partition, "L0INPRATE")
        self.l0accrate= PvLabel( self.centralWidget, partition, "L0ACCRATE")
        self.deadtime = PvLabel( self.centralWidget, partition, "DEADTIME")
        self.deadflnk = PvLabel( self.centralWidget, partition, "DEADFLNK")

        MainWindow.setCentralWidget(self.centralWidget)

if __name__ == '__main__':
    print QtCore.PYQT_VERSION_STR

    parser = argparse.ArgumentParser(description='simple pv monitor gui')
    parser.add_argument("pv", help="pv to monitor")
    args = parser.parse_args()

    app = QtGui.QApplication([])
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.pv)

    MainWindow.show()
    sys.exit(app.exec_())
