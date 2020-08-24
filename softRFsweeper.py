# -*- coding: utf-8 -*-
"""
Created on Thu May  2 18:17:20 2019

@author: benbol
"""
from PyQt4 import QtCore, QtGui
import PyTango as PT

# Define the DialogBox
class DialogBox(QtGui.QDialog):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.Proxies()
        self.mainrfprox = self.mainrfproxR3 # Let's start with loading R3
        self.FB01prox = self.FB01proxR3 # Let's start with loading R3

        self.rfstepsize = 0.05 # Hz / step
        self.maxchange = 20 # Hz
        self.minTperstep = 1000 # ms

        self.prankflag = 0
        self.freqlabel = QtGui.QLabel("")
        freqinfolbl = QtGui.QLabel("RF [Hz]:")
        deltafreqlabel = QtGui.QLabel("delta RF [Hz]:")
        self.numinputbox = QtGui.QLineEdit("0")
        self.sweepbtn = QtGui.QPushButton("Move RF")
        self.sweepbtn.clicked.connect(self.sweepbtnclicked)
        onlynum = QtGui.QDoubleValidator()
        self.numinputbox.setValidator(onlynum)
        self.changeRbtn = QtGui.QPushButton("Change ring")
        self.changeRbtn.clicked.connect(self.switchRing)
        self.ringlbl = QtGui.QLabel("R3")
        self.helpbtn = QtGui.QPushButton("Help")
        self.helpbtn.clicked.connect(self.helpbtnclicked)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.changeRbtn,0,0,1,1)
        layout.addWidget(self.ringlbl,0,1,1,1)
        layout.addWidget(freqinfolbl, 1, 0, 1, 1)
        layout.addWidget(self.freqlabel, 1,1,1,1)
        layout.addWidget(deltafreqlabel, 2,0,1,1)
        layout.addWidget(self.numinputbox,2,1,1,1)
        layout.addWidget(self.sweepbtn,3,0,1,1)
        layout.addWidget(self.helpbtn,3,1,1,1)
        self.setWindowTitle("MO RF sweeper")
        self.setLayout(layout)
        self.setGeometry(100, 100, 200, 100)
        self.getRF()

        self.timerobj = QtCore.QTimer()
        self.timerobj.timeout.connect(self.getRF)
        self.timerobj.start(self.minTperstep/2)
        self.timerobj2 = QtCore.QTimer()
        self.timerobj2.timeout.connect(self.sweep)

    def sweep(self):
        print("sweep")
        prox=[PT.DeviceProxy(str(self.FB01prox))]
        for proxdev in prox:
            self.corrfreq = proxdev.actual_correction_frequency
            self.state = str(proxdev.State())
        if self.state == "RUNNING":
            self.getRF()
            if abs(self.rFreq - self.finval) > self.rfstepsize*2/3:
                if self.rFreq < self.finval:
                    self.newfreq = self.rFreq + self.rfstepsize
                if self.rFreq > self.finval:
                    self.newfreq = self.rFreq - self.rfstepsize
                print(self.newfreq)
                prox=[PT.DeviceProxy(str(self.mainrfprox))]
                for RFdev in prox:
                    RFdev.write_attribute("Frequency",self.newfreq)
            else: self.sweepbtnclicked()
        else: self.sweepbtnclicked()

    def Proxies(self):
        self.mainrfproxR3 = 'r3-a101911/rf/mo-01'
        self.mainrfproxR1 = 'r1-d100101/rf/mo-01'
        self.FB01proxR3 = 'r3/ctl/fb-01'
        self.FB01proxR1 = 'r1/ctl/fb-01'

    def switchRing(self):
        if self.sweepbtn.text() == "Stop":
            mb = QtGui.QMessageBox("Error","Error: Not allowed to change ring during frequency sweep.",QtGui.QMessageBox.Warning,QtGui.QMessageBox.Ok,0,0)
            mb.exec_()
        else:
            if self.ringlbl.text() == "R3":
                self.ringlbl.setText("R1")
                self.mainrfprox = self.mainrfproxR1
                self.FB01prox = self.FB01proxR1
            elif self.ringlbl.text() == "R1":
                self.ringlbl.setText("R3")
                self.mainrfprox = self.mainrfproxR3
                self.FB01prox = self.FB01proxR3

    def getRF(self):
        prox=[PT.DeviceProxy(str(self.mainrfprox))]
        for RFdev in prox:
            self.rFreq = RFdev.Frequency
        self.freqlabel.setText(str(self.rFreq))

    def helpbtnclicked(self):
        if self.prankflag == 0:
            # self.prankflag = 1 # if using the easter egg... :-)
            self.prankflag = 0 # for not using the easter egg... :-(
            message = "Select ring you want to change RF for by clicking the change ring button.\nThe ring selected is seen to the right of the change ring button.\n\nThe RF frequency of the ring's master oscillator (MO) is seen to the right on the second row, and is updated twice per second.\n\nThe desired total change in RF can be written in the text box. To decrease, write a minus sign before the numbers. Maximum change is +. 20 Hz each time.\n\nTo do the change, press Move RF. This will then sweep the RF in the correct direction in steps of 0.1 Hz with a minimum of 1 second per step and waiting until at least 5 iterations with the actuators have been performed."
        elif self.prankflag == 1:
            self.prankflag = 0
            message = "Error: Dumping beam..."
        mb = QtGui.QMessageBox("MO RF sweeper GUI instructions",message,QtGui.QMessageBox.Information,QtGui.QMessageBox.Ok,0,0)
        mb.exec_()

    def sweepbtnclicked(self):
        dval = float(self.numinputbox.text())
        if self.sweepbtn.text() == "Move RF":
            if abs(dval) > self.maxchange:
                mb = QtGui.QMessageBox("Error","Error: Maximum change of frequency is " +str(self.maxchange)+" Hz.",QtGui.QMessageBox.Warning,QtGui.QMessageBox.Ok,0,0)
                mb.exec_()
            else: # Change RF
                self.finval = self.rFreq + dval
                if abs(self.finval - self.rFreq) > 0.1:
                    prox=[PT.DeviceProxy(str(self.FB01prox))]
                    for proxdev in prox:
                        self.corrfreq = proxdev.actual_correction_frequency
                        self.state = str(proxdev.State())
                    if self.state == "RUNNING":
                        self.sweepbtn.setText("Stop")
                        self.corrfreqint = int(self.corrfreq)
                        if self.corrfreq > self.corrfreqint:
                            self.corrfreqint += 1
                        self.sweeptmr = int(5000 / self.corrfreqint)
                        if self.sweeptmr < self.minTperstep:
                            self.sweeptmr = self.minTperstep
                        self.timerobj2.start(self.sweeptmr)
                    else:
                        mb = QtGui.QMessageBox("Error","Error: SOFB-01 for "+str(self.ringlbl.text())+" is not in running state.",QtGui.QMessageBox.Warning,QtGui.QMessageBox.Ok,0,0)
                        mb.exec_()
        elif self.sweepbtn.text() == "Stop":
            self.sweepbtn.setText("Move RF")
            self.timerobj2.stop()

if __name__ == "__main__":
    app = QtGui.QApplication([])
    form = DialogBox()
    form.show()
    app.exec_()
