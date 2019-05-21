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
from s_ParametersWindow_class         import ParametersWindow 
from s_PreviewCommandCode_class       import PreviewCommandCode
from s_DesignVisualisation_class      import DesignVisualisation
from s_WriteCommandCode_class         import WriteCommandCode
from s_SimulationDesign_class         import SimulationDesign
from s_LASERSimulated_class           import LASERSimulated

import numpy as np

################################################################################################
# FUNCTIONS
################################################################################################

class GCodeSimulation(QWidget):
    def __init__(self, simuobjct=None):
        super().__init__()
        self.extsimuobjct   = simuobjct
        self.instructions   = {}
        self.coretext       = ''
        self.simucolor      = 'b'
        # ---  --- #
        self.initUI()
        self.cmdwriter      = WriteCommandCode(self.filename)

    def initUI(self):
        # --- make main window --- #
        self.splitter = QSplitter(PyQt5.QtCore.Qt.Horizontal)
        # --- PreviewCommandCode frame --- #
        self.framePreviewcode = PreviewCommandCode('Abl_pygenerated.txt')
        self.framePreviewcode.filename.textChanged.connect(self.setNewFilename)
        self.setNewFilename() # initialise filename
        # --- make frames --- #
        self.initFramePrevVisual()
        self.framePrevVisual.setFilename( self.framePreviewcode.filename )
        self.loadFilename()
        # --- make LASER --- #
        self.laser = LASERSimulated()
        # --- make connections --- #
        self.framePreviewcode.filename.returnPressed.connect( self.setNewFilename )
        #self.framePreviewcode.filename.returnPressed.connect( self.loadFilename )
        # --- make layout --- #
        self.layout = QVBoxLayout()
        self.splitter.addWidget( self.framePrevVisual )
        self.splitter.addWidget(self.framePreviewcode)
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
        #self.simuobcj.initUI() # not necessary if the simuobjct is shared between different instances.
        self.viewobjct          = self.simuobcj.view
        # --- make connection --- #
        # --- make layout --- #
        # No need to set a layout since it is included in the DesignVisualisation object.

    def setNewFilename(self):
        self.filename = self.framePreviewcode.filename.text()

    def loadFilename(self):
        self.framePrevVisual.setFilename( self.framePreviewcode.filename )

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
    appMain = QApplication(sys.argv)
    wind = GCodeSimulation()
    wind.show()
    sys.exit(appMain.exec_())
    print('FINSHED')
