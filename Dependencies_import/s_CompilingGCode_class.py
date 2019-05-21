#! usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATION
################################################################################################

import sys
import PyQt5
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget
from PyQt5.QtWidgets import QBoxLayout,QGroupBox,QHBoxLayout,QVBoxLayout,QGridLayout,QSplitter
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit,QCheckBox,QComboBox
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction
from PyQt5.QtGui     import QIcon, QFont
from PyQt5.QtCore    import QDate, QTime, QDateTime, Qt

from s_MyPyQtObjects                  import MyQLabel,MyLineEdit,MyFrameFolding,MyParameter
from s_DesignVisualisation_class      import DesignVisualisation
from s_SimulationDesign_class         import SimulationDesign
from s_GCodeList_class                import GCodeList

import numpy as np

################################################################################################
# FUNCTIONS
################################################################################################

class CompilingGCode(QWidget):
    def __init__(self, simuobjct=None):
        super().__init__()
        self.extsimuobjct   = simuobjct
        self.instructions   = {}
        self.coretext       = ''
        self.simucolor      = 'b'
        # ---  --- #
        self.initUI()

    def initUI(self):
        # --- make main window --- #
        self.splitter = QSplitter(PyQt5.QtCore.Qt.Horizontal)
        # --- make frame GCode list --- #
        self.frameGcodeList = GCodeList()
        # --- make frames --- #
        self.initFramePrevVisual()
        # --- make button --- #
        self.compilebutton = QPushButton('Compile G-Code list')
        self.compilebutton.setStyleSheet("background-color: orange")
        # --- make connections --- #
        self.compilebutton.clicked.connect( self.compileAll )
        # --- make layout --- #
        self.layout = QVBoxLayout()
        self.layout.addWidget( self.compilebutton )
        self.splitter.addWidget( self.framePrevVisual )
        self.splitter.addWidget(self.frameGcodeList)
        self.layout.addWidget( self.splitter )
        self.setLayout( self.layout )

    def initFramePrevVisual(self):
        # ---  --- #
        if self.extsimuobjct==None:
            self.framePrevVisual    = DesignVisualisation() #QFrame()
        else:
            self.framePrevVisual    = DesignVisualisation(simuobjct=self.extsimuobjct) #QFrame()
        # ---  --- #
        self.framePrevVisual.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.framePrevVisual.setMinimumSize(600, 400)
        self.simuobcj           = self.framePrevVisual.simuobjct
        self.viewobjct          = self.simuobcj.view
        # --- make connection --- #
        # --- make layout --- #
        # No need to set a layout since it is included in the DesignVisualisation object.

    def compileAll(self):
        # --- reseting all drawings --- #
        self.framePrevVisual.clearAllPreviousDrawings()
        # --- compiling each gcode file il the list --- #
        gcode_file_list = self.frameGcodeList.gcode_list
        for key in gcode_file_list:
            ql_filename = gcode_file_list[key][0]
            cb_filename = gcode_file_list[key][1]
            if ql_filename.text()[-4:] == '.txt' and cb_filename.currentIndex() !=0:
                self.framePrevVisual.setFilename( ql_filename )
                self.framePrevVisual.makeSimulation()

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
    appMain = QApplication(sys.argv)
    wind = CompilingGCode()
    wind.show()
    sys.exit(appMain.exec_())
    print('FINSHED')
