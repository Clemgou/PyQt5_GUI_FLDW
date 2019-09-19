#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################ 
# IMPORTATIONS
################################################################################################
import sys
sys.path.insert(0, './Dependencies_import')
import PyQt5
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTableWidget, QDockWidget
from PyQt5.QtWidgets import QBoxLayout,QGroupBox,QHBoxLayout,QVBoxLayout,QGridLayout,QSplitter,QScrollArea
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QInputDialog
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction
from PyQt5.QtGui     import QIcon, QFont
from PyQt5.QtCore    import QDate, QTime, QDateTime, Qt

from s_StraightWaveGuide_class        import StraightWaveGuide
from s_AblationWriting_class          import AblationWriting
from s_SimulationDesign_class         import SimulationDesign
from s_GCodeSimulation_class          import GCodeSimulation
from s_CompilingGCode_class           import CompilingGCode
from s_LogDisplay_class               import LogDisplay

import numpy as np
import pyqtgraph as pqtg
import os

################################################################################################ 
# FUNCTIONS
################################################################################################

class FLDWMainWindow(QMainWindow): # inherits from the QMainWindow class
    def __init__(self):
        super().__init__() # The super() method returns the parent object of the MainWindow class, and we call its constructor. This means that we first initiate the QWidget class constructor.
        #self.app = QApplication([]) # only one per application

        # --- paths --- #
        self.localpath  = os.path.dirname(os.path.realpath(__file__))
        self.importpath = 'Dependencies_import/'
        self.iconpath   = 'IMGdirectory/'
        # --- initialisations --- #
        self.initWindow()
        self.initWindowMenu()

        #self.show()
        #self.app.exec_()

    def initWindow(self):
        '''
        Initialize the MainWindow configuration and display.
        '''
        # --- geometry and position --- #
        x0, y0, w, h = 150, 100, 650, 800
        self.setGeometry(x0, y0, w, h)
        self.setWindToCenter() # use the method defined below to center the window in the screen
        # --- names and titles --- #
        mytitle = "Main window"
        self.setWindowTitle(mytitle)
        mainapp_iconpath = r"./" + self.importpath + self.iconpath + "icon_mainapp.png"
        self.setWindowIcon(QIcon(mainapp_iconpath))
        # --- Parent Widget : central widget --- #
        self.centralwidget = QWidget() # QMainWindow needs a QWidget to display Layouts. Thus we define a central widget so that all
        self.centraltab    = QTabWidget()
        self.centraltab.setTabShape(0)
        self.centraltab.setTabsClosable(True)
        self.centraltab.setMovable(True)
        self.centraltab.tabCloseRequested.connect( self.closeTabe )
        self.setCentralWidget(self.centraltab)
        # --- make background of Main tab --- #
        self.centralwidget.setStyleSheet("background-image: url(./"+self.importpath+self.iconpath+"Software_diagram.png);"+"background-repeat: no;"+"background-position: center;")
        # --- Common Simulation object --- #
        self.simuobjct  = SimulationDesign()
        self.viewlayout = QHBoxLayout()
        self.viewlayout.addWidget(self.simuobjct.view)
        # --- make  log display tab --- #
        self.log        = LogDisplay()
        self.insertNewTabLogDisplay(self.log)
        self.insertNewTabAppDiagram()

    def initLogCapturePrintOutput(self):
        '''
        WORK IN PROGRESS
        Method that should automatically redirect all outputs from print command to the log object. Thus allowing more
        versability in the log class.
        '''
        out = io.StringIO()
        redirect_stdout(out)

    def initWindowMenu(self):
        '''
        Initialize the menu of the MainWindow.
        '''
        self.menubar = self.menuBar() # we define an attribute, menubar, which derives from the method menuBar() that comes from the QMainWindow parent object.
        # --- set the main menus --- #
        self.filemenu       = self.menubar.addMenu('&File')
        self.structuresmenu = self.menubar.addMenu('&Structures')
        self.toolsmenu      = self.menubar.addMenu('&Tools')
        self.statusBar()
        # --- set the actions in the different menues --- #
        self.initFilemenuMenu()
        self.initStructureMenu()
        self.initToolsMenu()

    def setWindToCenter(self):
        '''
        Set the MainWindow at the center of the desktop.
        '''
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeTabe(self, index):
        '''
        Remove the Tab of index index (integer).
        '''
        self.centraltab.removeTab(index)

    def getFile(self):
        '''
        Set the menue bar such that we can fetch a text file and display
        it on a textEdit widget
        '''
        self.textEdit = QTextEdit()
        grid          = QGridLayout()
        grid.addWidget(self.textEdit,3,1,5,1)
        self.centralwidget.setLayout(grid)

        openFile = QAction('Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)

        self.filemenu.addAction(openFile)

    def initFilemenuMenu(self):
        # --- Exit application --- #
        closeapp = QAction('&Exit', self) # QAction(QIcon('incon.png'), '&Exit', self)
        closeapp.triggered.connect(self.closeFLDWMainWindow)
        self.filemenu.addAction( '------' )
        self.filemenu.addAction(closeapp)

    def initToolsMenu(self):
        # --- Architecture app diagram tab --- #
        openNewTab = QAction('app diagram    (App Diag)', self)
        openNewTab.triggered.connect(self.insertNewTabAppDiagram)
        self.toolsmenu.addAction(openNewTab)
        ## --- Log display tab --- # #no need since the log tab is not closable
        #openNewTab = QAction('Log display    (Log)', self)
        #openNewTab.triggered.connect(self.insertNewTabLogDisplay)
        #self.toolsmenu.addAction(openNewTab)

    def initStructureMenu(self):
        '''
        Make a new tab window with the display of the chosen structure (SWG, BS, ...).
        '''
        # --- G-Code simulation --- #
        openNewGCodeSimu = QAction('G-Code simulator    (GCS)', self)
        openNewGCodeSimu.triggered.connect(self.insertNewTabGCodeSimu)
        self.structuresmenu.addAction(openNewGCodeSimu)
        # --- Multi G-Code Compiling --- #
        openNewMultiGcodeCompile = QAction('Multi G-Code compiling (MGC)', self)
        openNewMultiGcodeCompile.triggered.connect(self.insertNewTabMultiGcodeCompile)
        self.structuresmenu.addAction(openNewMultiGcodeCompile)
        # --- SWG structure --- #
        openNewSWG       = QAction('Straight Wave Guide (SWG)', self)
        openNewSWG.triggered.connect(self.insertNewTabSWG)
        self.structuresmenu.addAction(openNewSWG)
        # --- BWG structure --- #
        openNewBWG       = QAction('Bent Wave Guide     (BWG)', self)
        openNewBWG.triggered.connect(self.insertNewTabBWG)
        self.structuresmenu.addAction(openNewBWG)
        # --- Text Ablation structure --- #
        openNewTXTAbl    = QAction('Text Ablation       (TXTAbl)', self)
        openNewTXTAbl.triggered.connect(self.insertNewTabTxtAbl)
        self.structuresmenu.addAction(openNewTXTAbl)
        # --- Directional Coupler structure --- #
        openNewDirCoupl  = QAction('Directional Coupler (DC)', self)
        openNewDirCoupl.triggered.connect(self.insertNewTabDirCoupl)
        self.structuresmenu.addAction(openNewDirCoupl)

    def showDialog(self):
        '''
        Generate the window where we can browse for the wanted text file.
        '''
        fname = QFileDialog.getOpenFileName(self, 'Open file', './') #'/home/cgou')
        if fname[0]:
            f = open(fname[0], 'r')
            with f:
                data = f.read()
                self.textEdit.setText(data)

    def closeFLDWMainWindow(self):
        self.close()

    def insertNewTabSWG(self):
        newtabindex = self.centraltab.addTab( StraightWaveGuide(self.simuobjct, log=self.log), "SWG" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabBWG(self):
        newtabindex = self.centraltab.addTab( StraightWaveGuide(self.simuobjct, log=self.log), "SWG" )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabTxtAbl(self):
        newtabindex = self.centraltab.addTab( AblationWriting(path=self.localpath+'/'+self.importpath, log=self.log), "TXTAbl" )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabDirCoupl(self):
        newtabindex = self.centraltab.addTab(DirectionalCoupler(log=self.log),"Dir Cpl")
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabGCodeSimu(self):
        newtabindex = self.centraltab.addTab(GCodeSimulation(log=self.log),"GCode Simu")
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabMultiGcodeCompile(self):
        newtabindex = self.centraltab.addTab(CompilingGCode(log=self.log),"Multi GCode Comp.")
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabLogDisplay(self, log_objct):
        newtabindex = self.centraltab.addTab(log_objct,"Log")
        currentTbaBar = self.centraltab.tabBar()
        currentTbaBar.setTabButton(newtabindex, PyQt5.QtWidgets.QTabBar.RightSide, QLabel('')) # hide the close button
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabAppDiagram(self):
        self.centraltab.addTab(self.centralwidget,"App diag")

################################################################################################
# CODE
################################################################################################
if __name__=='__main__':
    appMain = QApplication(sys.argv)
    wind  = FLDWMainWindow()
    wind.show()
    sys.exit(appMain.exec_())
