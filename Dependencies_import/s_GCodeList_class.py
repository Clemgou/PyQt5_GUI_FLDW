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
from functools import partial

################################################################################################
# FUNCTIONS
################################################################################################

class GCodeList(QFrame):

    class ColorChoice(QComboBox):
        def __init__(self, defaultname=None):
            super().__init__()
            self.colorlabel = ['Blue', 'Red', 'Green', 'White']
            self.initColorChoice()
            self.setMaximumWidth(100)
        def initColorChoice(self):
            for color in self.colorlabel:
                self.addItem(color)

    def __init__(self, defaultname=None):
        super().__init__()
        self.gcode_list  = {}
        self.id_list     = []
        self.readable_ext= ['.txt', '.pgm']
        self.initUI()

    def initUI(self):
        # --- frame style --- #
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(3)
        self.setMidLineWidth(1)
        self.setMinimumWidth(400)
        # --- make widgets --- #
        self.addbutton        = QPushButton('Add')
        self.choosedirectory  = QPushButton('&Dir')
        self.currentdirectory = QFileDialog()
        self.directorylabel   = QLabel()
        self.scrollarea       = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setEnabled(True)
        self.scrollarea.setVerticalScrollBarPolicy(PyQt5.QtCore.Qt.ScrollBarAsNeeded)
        self.scrollarea.setHorizontalScrollBarPolicy(PyQt5.QtCore.Qt.ScrollBarAlwaysOff)
        # --- make connection --- #
        self.addbutton.clicked.connect( self.addGcodeFile )
        self.addbutton.clicked.connect( self.refreshTextFileList )
        self.choosedirectory.clicked.connect( self.chooseNewDirectory )
        # --- make layout --- #
        self.gcodelistwidget = QWidget()
        self.gridlayout      = QGridLayout()
        self.gcodelistwidget.setLayout( self.gridlayout )
        self.scrollarea.setWidget( self.gcodelistwidget )
        self.layout          = QVBoxLayout(self)
        self.layout.addWidget( self.scrollarea )
        self.setLayout( self.layout )
        self.makeLayout()
        # --- make default --- #
        self.choosedirectory.setMaximumWidth(50)
        default_path = str( self.currentdirectory.directory().path() )
        self.directorylabel.setText(default_path)
        os.chdir(default_path)
        self.refreshTextFileList() # we set all txt file as default #

    def doesIdExists(self, id_key):
        for id_ in self.id_list:
            if id_key == id_:
                return True

    def cleanItemsComboBox(self, combobox):
        N = combobox.count()
        for i in reversed(range(N)):
            combobox.removeItem(i)

    def makeLocalFileList(self, combobox):
        # --- retrieve all the file name in the present directory --- #
        local_filename = os.listdir()
        # --- selecting only .txt files --- #
        txt_filename = []
        for name in local_filename:
            if name[-4:] in self.readable_ext:
                txt_filename.append( name )
        # --- alphabet ordering --- #
        txt_filename.sort()
        # --- adding to the comboBox choice liste --- #
        combobox.addItem( 'Select a file' ) # to set initial value
        for i in range(len(txt_filename)):
            combobox.addItem( txt_filename[i] )

    def makeIdItem(self):
        id_gcode_item  = np.random.random()
        if not self.doesIdExists( id_gcode_item ):
            return id_gcode_item
        else:
            id_gcode_item = self.makeIdItem()
            return id_gcode_item

    def addGcodeFile(self):
        # --- making id --- #
        id_gcode_item = self.makeIdItem()
        self.id_list.append(id_gcode_item)
        # ---  --- #
        ql_filename    = QLineEdit()
        cb_filename    = QComboBox()
        ql_label       = QLabel('Name:')
        removebutton   = QPushButton('remv')
        # --- set aspect widgets --- #
        cb_filename.setLineEdit( ql_filename )
        self.makeLocalFileList(cb_filename)
        removebutton.setMaximumWidth(50)
        ql_label.setMaximumWidth(50)
        # --- make connections --- #
        part_readSelect = partial( self.readSelectedFile, id_gcode_item )
        cb_filename.activated[str].connect( part_readSelect )
        part_removeItem = partial( self.removeGCodeItem, id_gcode_item )
        removebutton.clicked.connect( part_removeItem )
        # ---  --- #
        self.gcode_list[id_gcode_item] = [ql_filename, cb_filename, removebutton, self.ColorChoice(), ql_label]
        # --- refresh layout --- #
        self.makeLayout()

    def removeGCodeItem(self, id_item):
        # --- destroying widget objects --- #
        for wdgt in self.gcode_list[id_item]:
            wdgt.setParent(None)
        # --- remove from the sotcking list --- #
        self.gcode_list.pop(id_item)
        # --- removing the id number of the item ---#
        for i in reversed( range(len(self.id_list)) ):
            if self.id_list[i] == id_item:
                self.id_list.pop(i)
        # --- refresh layout --- #
        self.makeLayout()

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem( item )

    def makeLayout(self):
        # --- reset the layout --- #
        self.clearLayout( self.gridlayout )
        #self.gridlayout.setVerticalSpacing(0)
        # --- add gcode item --- #
        current_key = self.gcode_list.keys()
        N  = len( current_key )
        if N != len(self.id_list):
            print("Error: dictionary and id_list not same size")
            return None
        N = len(self.id_list)
        # --- set directory choice --- #
        self.gridlayout.addWidget( self.choosedirectory, 0,0)
        self.gridlayout.addWidget( self.directorylabel , 0,1 , 1,4)
        # --- set add button --- #
        self.gridlayout.addWidget(self.addbutton       , 1,0 , 1,5)
        # --- set gcode items --- #
        for i in range(N):
            id_item = self.id_list[i]
            gcode_item = self.gcode_list[id_item]
            # --- make list choice name file --- #
            self.gridlayout.addWidget( gcode_item[-1], i+2,0 )
            self.gridlayout.addWidget( gcode_item[1] , i+2,1 , 1,2)
            self.gridlayout.addWidget( gcode_item[3] , i+2,3)
            self.gridlayout.addWidget( gcode_item[2] , i+2,4)
        # --- avoid stretching of the gridlayout --- #
        #self.gridlayout.setSpacing(5)
        for i in range(N+3): #seems that the row number needs to be greater than the actual row we set
            self.gridlayout.setRowStretch(i, 1) # not completelly understood the effect of value higher than 0
        #for c in range(7):
        #    self.gridlayout.setColumnStretch(c, 1)

    def refreshTextFileList(self):
        for key in self.gcode_list:
            cb_objct = self.gcode_list[key][1]
            current_filename = cb_objct.currentText()
            # --- refresh items --- #
            self.cleanItemsComboBox( cb_objct )
            self.makeLocalFileList(  cb_objct )
            # --- retreving the filename and setting it as default --- #
            ind_new = cb_objct.findText( current_filename )
            if ind_new == -1:
                print('Previews filename not found. Select a new one.')
                cb_objct.setCurrentIndex(0)
            else:
                cb_objct.setCurrentIndex(ind_new)

    def chooseNewDirectory(self):
        new_path = self.currentdirectory.getExistingDirectory()
        #new_path = str( self.currentdirectory.directory().path() )
        os.chdir(new_path)
        self.directorylabel.setText( new_path )
        self.refreshTextFileList()

    def saveTextFile(self):
        filename = self.filename.text()
        self.text = open(filename,'w')
        newtext = self.textedit.toPlainText()
        self.text.write( newtext )
        if self.filenamechoice.findText(filename) == -1: # -1 is the value returned when text not found
            self.filenamechoice.addItem(filename)

    def readSelectedFile(self, id_item):
        displbox = QMessageBox()
        displbox.setWindowTitle("Current file name")
        filename = self.gcode_list[id_item][0].text()
        displbox.setText( filename )
        displbox.exec_()

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    appMain = QApplication(sys.argv)
    nametxtfile = "SWG_pygenerated.txt"
    Prev = GCodeList()
    Prev.show()
    sys.exit(appMain.exec_())

