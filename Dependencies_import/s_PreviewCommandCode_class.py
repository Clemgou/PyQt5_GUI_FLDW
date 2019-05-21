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
from PyQt5.QtCore    import QDate, QTime, QDateTime, Qt

from s_MyPyQtObjects           import MyQLabel,MyLineEdit,MyFrameFolding

import numpy as np
import os

################################################################################################
# FUNCTIONS
################################################################################################

class PreviewCommandCode(QFrame):
    def __init__(self, defaultname=None):
        super().__init__()
        self.defaultname = defaultname #'SWG_pygenerated.txt'
        self.filename = None
        self.initUI()

    def initUI(self):
        # --- frame style --- #
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(3)
        self.setMidLineWidth(1)
        # --- make refresh button --- #
        self.rfrshbutton = QPushButton("Refresh")
        self.savebutton  = QPushButton("Save")
        self.rfrshbutton.clicked.connect( self.refreshTextFile )
        self.savebutton.clicked.connect( self.saveTextFile )
        # --- make list choice name file --- #
        self.filename       = QLineEdit()
        self.filenamechoice = QComboBox()
        self.filenamechoice.setLineEdit( self.filename )
        #self.filenamechoice.setAutoCompletion() #not working...
        #if self.defaultname != None: self.filenamechoice.addItem(self.defaultname) #'SWG_pygenerated.txt'
        self.makeLocalFileList( self.filenamechoice ) # we set all txt file as default #
        self.filenamechoice.activated[str].connect(self.readSelectedFile)
        grid = QGridLayout()
        grid.addWidget( QLabel('Name:') ,0, 0,1,1)
        grid.addWidget( self.filenamechoice , 0,1,4,1)
        # --- editing window --- #
        self.textedit = QTextEdit(self)
        self.textedit.setMinimumWidth(400)
        self.textedit.setMinimumHeight(600)
        self.textedit.setLineWrapMode( QTextEdit.NoWrap )
        self.filename.setText( self.defaultname)
        #self.readSelectedFile()
        # --- make layout --- #
        self.layout = QVBoxLayout(self)
        self.layout.addLayout(grid)
        self.layout.addWidget(self.textedit)
        self.layout.addWidget(self.rfrshbutton)
        self.layout.addWidget(self.savebutton)

    def makeLocalFileList(self, combobox):
        # --- retrieve all the file name in the present directory --- #
        local_filename = os.listdir()
        # --- selecting only .txt files --- #
        txt_filename = []
        for name in local_filename:
            if name[-4:] == '.txt':
                txt_filename.append( name )
        # --- alphabet ordering --- #
        txt_filename.sort()
        # --- adding to the comboBox choice liste --- #
        combobox.addItem( 'Select a file' ) # to set initial value
        for i in range(len(txt_filename)):
            combobox.addItem( txt_filename[i] )

    def refreshTextFile(self):
        filename = self.filename.text()
        self.text = open(filename).read()
        self.textedit.setText(self.text)

    def saveTextFile(self):
        filename = self.filename.text()
        self.text = open(filename,'w')
        newtext = self.textedit.toPlainText()
        self.text.write( newtext )
        if self.filenamechoice.findText(filename) == -1: # -1 is the value returned when text not found
            self.filenamechoice.addItem(filename)

    def readSelectedFile(self):
        displbox = QMessageBox()
        displbox.setWindowTitle("Current file name")
        displbox.setText( self.filename.text() )
        displbox.exec_()
        filename = self.filename.text()
        try:
            self.text = open(filename,'r+').read()
        except:
            self.text = open(filename,'w+').read()
        self.textedit.setText(self.text)

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    appMain = QApplication(sys.argv)
    nametxtfile = "SWG_pygenerated.txt"
    Prev = PreviewCommandCode()
    Prev.show()
    sys.exit(appMain.exec_())

