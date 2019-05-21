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

from s_MyPyQtObjects           	import MyQLabel,MyLineEdit,MyFrameFolding
from s_ParametersWindow_class  	import ParametersWindow
from s_PreviewCommandCode_class 	import PreviewCommandCode
from s_DesignVisualisation_class 	import DesignVisualisation
from s_WriteCommandCode_class 	import WriteCommandCode

import numpy as np


################################################################################################
# FUNCTIONS
################################################################################################

class StraightWaveGuide(QWidget):
    '''
    Define the whole widget to generate the command loine txt file for FLDW.
    All units are in mm, mm/s, for the parameters.
    '''
    def __init__(self, simuobjct=None):
        super().__init__()
        self.extsimuobjct = simuobjct
        self.initUI()

    def initUI(self):
        # --- graphical attributes --- #
        self.splitter = QSplitter(PyQt5.QtCore.Qt.Horizontal)
        self.layout = QVBoxLayout()
        # --- Frame attributes setting --- #
        #  -  Frame: Preview G-code
        self.framePrevCmdCode = PreviewCommandCode('SWG_pygenerated.txt')
        #  -  Frame: Design visualisation
        if self.extsimuobjct==None:
            self.framePrevVisual  = DesignVisualisation()
        else:
            self.framePrevVisual  = DesignVisualisation(simuobjct=self.extsimuobjct)
        self.framePrevVisual.setMinimumSize(600, 400)
        self.framePrevVisual.setWhichSimu('SWG')
        #  -  Frame: Parameter window
        paramdefaultlist = [['indRefr',1.5],['xInit',0.],['xEnd',29],['distNewfab', 0.5],['scanNbr',[5,8]],['distSucc',0.1],['distScan', 0.],['depth',-0.2],['speed', [40,60]]]
        self.frameParamWindow = ParametersWindow( paramdefaultlist )
        #  -  set the group parameters
        self.frameParamWindow.addGroupParameter('Fixed parameters'          , ['indRefr','xInit','xEnd'] )
        self.frameParamWindow.addGroupParameter('Fabrication parameters'    , ['depth', 'speed','scanNbr'] )
        self.frameParamWindow.addGroupParameter('Distansce inter-structures', ['distNewfab', 'distSucc', 'distScan'] )
        #  -  init Parameter Window
        self.frameParamWindow.initUI()
        # --- Initialise: code generator attribute --- #
        nametxtfile = "SWG_pygenerated.txt"
        self.commandwriter = WriteCommandCode(nametxtfile)
        # --- make button --- #
        self.generbutton = QPushButton("Generate code")
        # --- make connection --- #
        self.generbutton.clicked.connect( self.generateCommandFile )
        # --- set layout --- #
        self.splitter.addWidget(self.frameParamWindow)
        self.splitter.addWidget(self.framePrevVisual)
        self.splitter.addWidget(self.framePrevCmdCode)
        self.layout.addWidget(self.generbutton)
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)

    def generateCommandFile(self):
        self.setCmdWriterParam()
        self.commandwriter.compileTextSWG()
        self.framePrevCmdCode.refreshTextFile()

    def setCmdWriterParam(self):
        self.frameParamWindow.getParameters()   # set the dicvariable of the parameter window
        self.framePrevVisual.setFilename( self.framePrevCmdCode.filename.text() )
        self.commandwriter.setDicVariable(   self.frameParamWindow.dicvariable )
        self.commandwriter.initGroups()
        self.commandwriter.initLoopVariables() 
        self.commandwriter.cleanUnnecessaryParameters()
        self.commandwriter.setTextNameFile( self.framePrevCmdCode.filename.text() )
        '''
        grouplist = self.frameParamWindow.grouplist
        self.commandwriter.resetGroupVar()
        for grpname in grouplist:   # loop in the grouplist dictaionary keys
            self.commandwriter.addGroupVar(grouplist[grpname])# ['inRefr','xInit','xEnd'])
        loopvarlist = self.frameParamWindow.loopnamelist
        '''

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    appMain = QApplication(sys.argv)
    wind  = StraightWaveGuide()
    wind.show()
    sys.exit(appMain.exec_())
