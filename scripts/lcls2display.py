import sys
import argparse
from psp import Pv
from PyQt4 import QtCore, QtGui

class PvLabel:
    def __init__(self, parent, partition, name):
        self.layout = QtGui.QHBoxLayout(parent)
        self.label = QtGui.QLabel(name)
        self.layout.addWidget(self.label)
        self.display = QtGui.QLabel("-")
        self.layout.addWidget(self.display)
        parent.layout.addLayout(self.layout)

        pvname = "DAQ:"+partition+":"+name
        print pvname
        self.pv = Pv.Pv(pvname)
        self.pv.monitor_start()
        self.pv.add_monitor_callback(self.update)

    def update(self, err):
        if err is None:
            try:
                self.display.setNum(self.pv.value)
            except:
                v = ''
                for i in range(len(self.pv.value)):
                    v = v + ' %f'%self.pv.value[i]
                self.display.setText(v)
        else:
            print err

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, partition):
        MainWindow.setObjectName(QtCore.QString.fromUtf8("MainWindow"))
        MainWindow.resize(128, 96)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.centralWidget.layout = QtGui.QVBoxLayout(self.centralWidget)

        self.numl0    = PvLabel( self.centralWidget, partition, "NUML0")
        self.l0rate   = PvLabel( self.centralWidget, partition, "L0RATE")
        self.deadtime = PvLabel( self.centralWidget, partition, "DEADTIME")
#  This can crash the pcas server!
#        self.deadflnk = PvLabel( self.centralWidget, partition, "DEADFLNK")

        MainWindow.setCentralWidget(self.centralWidget)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple pv monitor gui')
    parser.add_argument("pv", help="pv to monitor")
    args = parser.parse_args()

    app = QtGui.QApplication([])
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow,args.pv)

    MainWindow.show()
    sys.exit(app.exec_())
