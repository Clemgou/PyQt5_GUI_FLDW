#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATIONS
################################################################################################

import sys
import PyQt5 
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTableWidget
from PyQt5.QtWidgets import QBoxLayout,QGroupBox,QHBoxLayout,QVBoxLayout,QGridLayout,QSplitter,QScrollArea
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QInputDialog
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction
from PyQt5.QtGui     import QIcon, QFont
from PyQt5.QtCore    import QDate, QTime, QDateTime

from s_MyPyQtObjects           import MyQLabel,MyLineEdit,MyFrameFolding

import numpy as np
import os

################################################################################################
# FUNCTIONS
################################################################################################

class LogDisplay(QFrame):
    def __init__(self):
        super().__init__()
        self.readable_ext   = ['.txt', '.pgm']
        self.displaytxt     = QTextEdit()
        self.initUI()

    def initUI(self):
        # --- frame style --- #
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(3)
        self.setMidLineWidth(1)
        # --- Text edit setup  --- #
        self.displaytxt.setReadOnly(True)
        self.displaytxt.setMinimumWidth(200)
        self.displaytxt.setMinimumHeight(400)
        # --- make layout --- #
        self.layout = QVBoxLayout(self)
        self.layout.addWidget( QLabel('Log message:') )
        self.layout.addWidget( self.displaytxt )

    def resetLogText(self):
        self.displaytxt.clear()

    def addText(self, txt ):
        if type(txt) == type(''):
            self.displaytxt.append(txt) # no need of \n with the append method here
        else:
            print('Error: in LogDisplay, wrong text type was given.\nArgument is: {}'.format(txt))
            return None

    def makeNewEntry(self):
        time      = QDateTime.currentDateTime()
        newentry  = '\nNew entry at {}:'.format( time.toString(PyQt5.QtCore.Qt.ISODate) )
        self.displaytxt.append(newentry)


################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
    appMain = QApplication(sys.argv)
    nametxtfile = "SWG_pygenerated.txt"
    app = LogDisplay()
    app.show()
    app.makeNewEntry()
    app.addText('This is a test')
    app.addText('Now we can see if it works')
    sys.exit(appMain.exec_())

