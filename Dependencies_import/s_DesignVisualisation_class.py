#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATIONS
################################################################################################

import sys
import PyQt5
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTableWidget
from PyQt5.QtWidgets import QBoxLayout,QGroupBox,QHBoxLayout,QVBoxLayout,QGridLayout,QSplitter,QScrollArea
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QInputDialog, QSlider
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction, QDialog, QProgressBar
from PyQt5.QtGui     import QIcon, QFont
from PyQt5.QtCore    import QDate, QTime, QDateTime, Qt, QRect, pyqtSlot

from s_MyPyQtObjects          import MyQLabel,MyLineEdit,MyFrameFolding
from s_SimulationDesign_class import SimulationDesign
from s_LASERSimulated_class   import LASERSimulated
from s_LogDisplay_class       import LogDisplay

import numpy     as np
from   itertools import product
from functools import partial

################################################################################################
# FUNCTIONS
################################################################################################

class DesignVisualisation(QFrame):
    def __init__(self, simuobjct=None, filename=None, errorbox=None, log=None):
        super().__init__()
        self.dicvariable    = {}
        if filename == None:
            self.filename   = QLineEdit()
            self.filename.setText('None')
        else:
            self.filename = filename
        if simuobjct==None:
            self.simuobjct  = SimulationDesign()
        else:
            self.simuobjct  = simuobjct
        if log == None:
            self.log = LogDisplay()
        else:
            self.log = log
        self.simucolor      = 'b'
        self.magnification  = [1., 1., 1.]
        self.layout         = QVBoxLayout(self)
        self.whichsimu      = None
        self.progressbar    = QProgressBar()
        self.warningmesg    = QMessageBox()
        self.initUI()

    def initUI(self):
        # --- frame style --- #
        self.setMinimumSize(400, 400)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(3)
        self.setMidLineWidth(1)
        # --- make LASER --- #
        self.laser = LASERSimulated(log=self.log)
        # --- make plot widget --- #
        self.plotwidget  = self.simuobjct.view
        # --- make buttons --- #
        self.simubutton       = QPushButton("Simulate")
        self.cleanviewbutton  = QPushButton('Clean View')
        self.drawallbutton    = QPushButton('Draw All')
        self.resetbutton      = QPushButton('RESET ALL')
        self.resetbutton.setStyleSheet("background-color: red")
        # --- make labels --- #
        self.labellasercurrentpos = QLabel( str(self.laser.position) )
        self.labellaserordigin    = QLabel( str(self.laser.origin))
        # --- make line edit --- #
        self.sampleboxXoffset = QLineEdit()
        self.sampleboxYoffset = QLineEdit()
        self.laserinitxpos    = QLineEdit()
        self.laserinitypos    = QLineEdit()
        # --- make combo box for current color --- #
        self.currentcolor     = QComboBox()
        color_label = ['Blue', 'Red', 'Green', 'White']
        for color in color_label:
            self.currentcolor.addItem(color)
        # --- make combo box for geometry of the axis orientation --- #
        self.axisorientation  = QComboBox()
        self.axisorientation.addItem('Fab Line 1 (-X,+Y)')
        self.axisorientation.addItem('Normal     (+X,+Y)')
        # --- make sliders for magnification and their layout --- #
        self.makeMagnitudeSliders()
        # --- make connections --- #
        self.simubutton.clicked.connect( self.makeSimulation )
        self.cleanviewbutton.clicked.connect( self.cleanSimulation )
        self.drawallbutton.clicked.connect( self.simuobjct.drawAllItems )
        self.axisorientation.currentIndexChanged.connect( self.setOrientationAxis )
        self.currentcolor.currentIndexChanged.connect( self.setSimulationColor )
        self.resetbutton.clicked.connect( self.resetSimulation )
        # --- make the arrow displacement widget --- #
        self.makePositionArrows()
        # --- make progess bar --- #
        self.makeProgressBarLayout()
        # --- make layout --- #
        self.makeLaserPropertiesLayout()
        self.makeSampleBoxLayout()
        self.plotlayout = QVBoxLayout()
        self.plotlayout.addWidget( self.plotwidget )
        gridlayout  = QGridLayout()
        gridlayout.addWidget( QLabel('Fabrication:'), 0,0 , 1,2)
        gridlayout.addWidget( self.resetbutton      , 1,0 , 1,2 )
        gridlayout.addWidget( self.axisorientation  , 2,0 , 1,2)
        gridlayout.addWidget( self.currentcolor     , 3,0 , 1,2 )
        hlayout_top = QHBoxLayout()
        hlayout_top.addLayout( gridlayout )
        hlayout_top.addLayout( self.sampleboxlayout )
        hlayout_top.addLayout( self.laserlayout )
        # --- my method to avoid stretching of the top layout --- #
        top_frame = QFrame()
        top_frame.setLayout( hlayout_top )
        top_frame.setMaximumHeight( 150 )
        # ---  --- #
        hlayout_bottom = QHBoxLayout()
        vlayout        = QVBoxLayout()
        vlayout.addWidget( self.sliderswidget )
        vlayout.addLayout( self.progressbar_layout )
        hlayout_bottom.addLayout( vlayout )
        hlayout_bottom.addWidget( self.arrowwidget )
        # ---  --- #
        bottom_frame = QFrame()
        bottom_frame.setLayout( hlayout_bottom )
        bottom_frame.setMinimumWidth( 600 )
        bottom_frame.setMaximumHeight( 150 )
        # ---  --- #
        self.layout.addWidget( top_frame )
        self.layout.addLayout(self.plotlayout)
        self.layout.addWidget( bottom_frame )
        self.setLayout(self.layout)
        # --- make default --- #
        self.setOrientationAxis( self.axisorientation.currentIndex() )
        self.setLASEROrigin()
        return None

    def setSampleBoxOrigin(self):
        sampleboxX = self.sampleboxXoffset.text()
        sampleboxY = self.sampleboxYoffset.text()
        sampleboxZ = self.sampleboxZoffset.text()
        try:
            sampleboxX = eval(sampleboxX)
            sampleboxY = eval(sampleboxY)
            sampleboxZ = eval(sampleboxZ)
        except:
            print('Error: Wrong evaluation of the sample box initial position.')
            self.log.addText('Error: Wrong evaluation of the sample box initial position.')
            return None
        self.simuobjct.setSampleOrigin( np.array([sampleboxX, sampleboxY, sampleboxZ]) )
        self.makeSimulation()

    def setSampleBoxSize(self):
        sampleboxX = self.sampleboxXsize.text()
        sampleboxY = self.sampleboxYsize.text()
        sampleboxZ = self.sampleboxZsize.text()
        try:
            sampleboxX = eval(sampleboxX)
            sampleboxY = eval(sampleboxY)
            sampleboxZ = eval(sampleboxZ)
        except:
            print('Error: Wrong evaluation of the sample box initial position.')
            self.log.addText('Error: Wrong evaluation of the sample box initial position.')
            return None
        self.simuobjct.setSampleSize( sampleboxX, sampleboxY, sampleboxZ )
        self.makeSimulation()

    def setLASEROrigin(self):
        laserx = self.laserinitxpos.text()
        lasery = self.laserinitypos.text()
        laserz = self.laserinitzpos.text()
        try:
            laserx = eval(laserx)
            lasery = eval(lasery)
            laserz = eval(laserz)
        except:
            print('Error: Wrong evaluation of the Laser initial position.')
            self.log.addText('Error: Wrong evaluation of the Laser initial position.')
            return None
        self.laser.setLaserPosition( np.array([ laserx, lasery, laserz]) )
        self.updateLabelLaserPosition()

    def setFilename(self, filename ):
        self.filename = filename

    def setDicVariable(self, dicvar_new ):
        self.dicvariable = dicvar_new

    def setWhichSimu(self, simu_type):
        self.whichsimu = simu_type

    def setOrientationAxis(self, i):
        '''
        Redefine the unit vectors so that it matches the wanted referential oriantation 
        of the axis. The default order is:
            - i=0 --> Fab Line 1
            - i=1 --> Normal
        '''
        if   i == 0:
            self.simuobjct.setOrientaionAxisKey('Line1')
            samplesize = self.simuobjct.samplesize
            self.simuobjct.setCenterCamera(np.array([-samplesize.x()/2., samplesize.y()/2.,0.]))
        elif i == 1:
            self.simuobjct.setOrientaionAxisKey('Normal')
            samplesize = self.simuobjct.samplesize
            self.simuobjct.setCenterCamera(np.array([samplesize.x()/2., samplesize.y()/2.,0.]))
        else:
            self.raiseErrorMessageBox('Problem with the geometry definition.')
            return None

    def setSimulationColor(self,i):
        if   i==0:
            self.simucolor = 'b'
        elif i==1:
            self.simucolor = 'r'
        elif i==2:
            self.simucolor = 'g'
        elif i==3:
            self.simucolor = 'w'
        return None

    def makeSampleBoxLayout(self):
        # --- make sample box editable --- #
        self.sampleboxXoffset = QLineEdit()
        self.sampleboxYoffset = QLineEdit()
        self.sampleboxZoffset = QLineEdit()
        self.sampleboxXsize   = QLineEdit()
        self.sampleboxYsize   = QLineEdit()
        self.sampleboxZsize   = QLineEdit()
        # --- make connection --- #
        self.sampleboxXoffset.returnPressed.connect( self.setSampleBoxOrigin )
        self.sampleboxYoffset.returnPressed.connect( self.setSampleBoxOrigin )
        self.sampleboxZoffset.returnPressed.connect( self.setSampleBoxOrigin )
        self.sampleboxXsize.returnPressed.connect( self.setSampleBoxSize )
        self.sampleboxYsize.returnPressed.connect( self.setSampleBoxSize )
        self.sampleboxZsize.returnPressed.connect( self.setSampleBoxSize )
        # --- make default --- #
        self.sampleboxXoffset.setText( str(self.simuobjct.sampleorigin.x()) )
        self.sampleboxYoffset.setText( str(self.simuobjct.sampleorigin.y()) )
        self.sampleboxZoffset.setText( str(self.simuobjct.sampleorigin.z()) )
        self.sampleboxXsize.setText( str(self.simuobjct.samplesize.x()) )
        self.sampleboxYsize.setText( str(self.simuobjct.samplesize.y()) )
        self.sampleboxZsize.setText( str(self.simuobjct.samplesize.z()) )
        # --- make layout --- #
        self.sampleboxlayout = QGridLayout()
        self.sampleboxlayout.addWidget( QLabel('Sample Box:') , 0,0, 1,4 )
        self.sampleboxlayout.addWidget( QLabel('Size   X:'), 1,0 )
        self.sampleboxlayout.addWidget( QLabel('Size   Y:'), 2,0 )
        self.sampleboxlayout.addWidget( QLabel('Size   Z:'), 3,0 )
        self.sampleboxlayout.addWidget( self.sampleboxXsize, 1,1 )
        self.sampleboxlayout.addWidget( self.sampleboxYsize, 2,1 )
        self.sampleboxlayout.addWidget( self.sampleboxZsize, 3,1 )
        self.sampleboxlayout.addWidget( QLabel('Origin X:'), 1,2 )
        self.sampleboxlayout.addWidget( QLabel('Origin Y:'), 2,2 )
        self.sampleboxlayout.addWidget( QLabel('Origin Z:'), 3,2 )
        self.sampleboxlayout.addWidget( self.sampleboxXoffset, 1,3 )
        self.sampleboxlayout.addWidget( self.sampleboxYoffset, 2,3 )
        self.sampleboxlayout.addWidget( self.sampleboxZoffset, 3,3 )

    def makeLaserPropertiesLayout(self):
        self.laserinitxpos    = QLineEdit()
        self.laserinitypos    = QLineEdit()
        self.laserinitzpos    = QLineEdit()
        # --- make connections --- #
        self.laserinitxpos.returnPressed.connect( self.setLASEROrigin )
        self.laserinitypos.returnPressed.connect( self.setLASEROrigin )
        self.laserinitzpos.returnPressed.connect( self.setLASEROrigin )
        # --- make layout --- #
        self.laserlayout = QGridLayout()
        self.laserlayout.addWidget( QLabel('LASER position:'), 0,0)
        self.laserlayout.addWidget( self.labellasercurrentpos, 0,1, 1,2)
        self.laserlayout.addWidget( QLabel('Stage origin  :'), 1,0)
        self.laserlayout.addWidget( self.labellaserordigin   , 1,1, 1,2)
        self.laserlayout.addWidget( QLabel('LASER X0: '), 2,0)
        self.laserlayout.addWidget( QLabel('LASER Y0: '), 3,0)
        self.laserlayout.addWidget( QLabel('LASER Z0: '), 4,0)
        self.laserlayout.addWidget( self.laserinitxpos, 2,1 )
        self.laserlayout.addWidget( self.laserinitypos, 3,1 )
        self.laserlayout.addWidget( self.laserinitzpos, 4,1 )
        # --- make default --- #
        self.laserinitxpos.setText('0.0')
        self.laserinitypos.setText('2.0')
        self.laserinitzpos.setText('0.0')

    def makeMagnitudeSliders(self):
        self.sliderswidget = QFrame()
        self.sliderslayout = QGridLayout()
        self.magnificationsliders = {}
        mgnf_layout = QVBoxLayout()
        axlabel = ['x','y','z']
        for i in range(3):
            axis = axlabel[i]
            self.magnificationsliders[axis,'label']  = QLabel()
            self.magnificationsliders[axis,'slider'] = QSlider(Qt.Horizontal)
            slider = self.magnificationsliders[axis,'slider']
            slider.setRange( 1, 10 )
            slider.setValue( self.magnification[i] )
            label  = self.magnificationsliders[axis,'label']
            label.setText(str( slider.value() ))
            # --- make layout --- #
            self.sliderslayout.addWidget(QLabel(r'Mgn_{}:'.format(axis)), i,0)
            self.sliderslayout.addWidget(label , i,1)
            self.sliderslayout.addWidget(slider, i,2 , 1,5)
        self.magnificationsliders['z','slider'].setRange(1,100) # for the z-axis we set a bigger magnification range, since it is the smallest dimension.
        # --- set stretching properties --- #
        for i in range(3):
            self.sliderslayout.setColumnStretch(i, 0 )
        # --- make connection --- #
        for ax in ['x','y','z']:
            label  = self.magnificationsliders[ax,'label']
            slider = self.magnificationsliders[ax,'slider']
            updt_sllabel = partial( self.updateSliderLabel, label )
            slider.valueChanged.connect( updt_sllabel )
            slider.valueChanged.connect( self.updateMagnification )
        # --- make arrow widget --- #
        self.sliderswidget.setLayout( self.sliderslayout )
        self.sliderswidget.setMaximumHeight( 80 )

    def makePositionArrows(self):
        self.arrowwidget= QFrame()
        self.arrowsgrid = QGridLayout()
        self.uparrow    = QPushButton('+Y')
        self.downarrow  = QPushButton('-Y')
        self.leftarrow  = QPushButton('-X')
        self.rightarrow = QPushButton('+X')
        self.negativeZ  = QPushButton('-Z')
        self.positiveZ  = QPushButton('+Z')
        # --- make fancy --- #
        self.positiveZ.setStyleSheet("background-color: green")
        self.negativeZ.setStyleSheet("background-color: green")
        # --- make layout --- #
        self.arrowsgrid.addWidget(self.uparrow   , 0,1)
        self.arrowsgrid.addWidget(self.downarrow , 2,1)
        self.arrowsgrid.addWidget(self.leftarrow , 1,0)
        self.arrowsgrid.addWidget(self.rightarrow, 1,2)
        self.arrowsgrid.addWidget(self.simubutton, 1,1)
        self.arrowsgrid.addWidget(self.positiveZ , 0,2)
        self.arrowsgrid.addWidget(self.negativeZ , 2,2)
        # --- add other buttons --- #
        #self.arrowsgrid.addWidget(self.cleanviewbutton , 0,0)
        #self.cleanviewbutton.setStyleSheet("background-color: orange")
        #self.arrowsgrid.addWidget(self.drawallbutton , 2,0)
        #self.drawallbutton.setStyleSheet("background-color: orange")
        # --- make connection --- #
        self.uparrow.clicked.connect( self.cameraGoPositiveY )
        self.downarrow.clicked.connect( self.cameraGoNegativeY )
        self.leftarrow.clicked.connect( self.cameraGoNegativeX )
        self.rightarrow.clicked.connect( self.cameraGoPositiveX )
        self.positiveZ.clicked.connect( self.cameraGoPositiveZ )
        self.negativeZ.clicked.connect( self.cameraGoNegativeZ )
        # --- make arrow widget --- #
        self.arrowwidget.setLayout( self.arrowsgrid )
        self.arrowwidget.setMaximumHeight( 150 )
        self.arrowwidget.setMaximumWidth(  250 )

    def makeProgressBarLayout(self):
        self.progressbar_layout = QHBoxLayout()
        self.progressbar_layout.addWidget( self.progressbar )
        # --- connect the progress bar status --- #
        self.laser.currprogrss.connect( self.updateProgressBar )
        self.laser.progrssnbrmax.connect( self.setMaxProgressBar )

    def cameraGoNegativeY(self):
        X = np.array([0.,-1., 0.])
        self.simuobjct.displaceCamera(X)

    def cameraGoPositiveY(self):
        X = np.array([0., 1., 0.])
        self.simuobjct.displaceCamera(X)

    def cameraGoNegativeX(self):
        X = np.array([-1., 0., 0.])
        self.simuobjct.displaceCamera(X)

    def cameraGoPositiveX(self):
        X = np.array([1., 0., 0.])
        self.simuobjct.displaceCamera(X)

    def cameraGoNegativeZ(self):
        X = np.array([0., 0.,-1.])
        self.simuobjct.displaceCamera(X)

    def cameraGoPositiveZ(self):
        X = np.array([0., 0., 1.])
        self.simuobjct.displaceCamera(X)

    def updateSliderLabel(self, label, slidervalue):
        label.setText( str(slidervalue) )
        return None

    def updateSimulation(self):
        self.simuobjct.updateItems()

    def updateMagnification(self):
        axis = ['x','y','z']
        for i in range(3):
            slider = self.magnificationsliders[axis[i],'slider']
            self.magnification[i] = slider.value()
        self.simuobjct.setMagnificationAxis( self.magnification )

    def updateLabelLaserPosition(self):
        self.labellasercurrentpos.setText( str(self.laser.position) )
        self.labellaserordigin.setText( str(self.laser.origin) )

    def priorityProduct(self, listvariable, listindprior ):
        '''
        create a table of indices that respect the priority of the iteration
        listvariable: is the list of variable array, set in the 'normal' order
        listindprior: is the list of indice for listvariable, such that the priority is respected
        '''
        n   = len(listvariable)
        N   = np.prod(np.array([len(listvariable[i]) for i in range(n)]))
        priorityindex = np.zeros([N,n])
        arglist = [np.arange(len(listvariable[i])) for i in listindprior]
        ind = np.array(list(product( *arglist ))) # should be an array of indices repeated according to the priority
        for i in range(n):
            priorityindex[:,listindprior[i]] = ind[:,i]
        return priorityindex.astype(int)

    def resetSimulation(self):
        # --- reset simulation window --- #
        self.simuobjct.resetALL()
        if not self.simuobjct.isDrawingitemsReset():
            print("ERROR DICTIONARY OF ITEMS NOT RESET")
            print(self.simuobjct.drawingitems)
            self.log.addText("ERROR DICTIONARY OF ITEMS NOT RESET")
            self.log.addText(str(self.simuobjct.drawingitems))
        self.plotwidget = self.simuobjct.view
        self.plotlayout.addWidget( self.plotwidget )
        self.axisorientation.setCurrentIndex(1)
        # --- reset drawings --- #
        self.resetDrawingItems()
        # --- reset laser --- #
        self.laser.__init__()

    def resetDrawingItems(self):
        '''
        Should clear the dictionaries where the items were stocked.
        '''
        # reset self dictionary --- #
        self.instructions  = {}
        self.waveguides    = {}
        # --- reset laser dictionaries: shouldbe done at each readGCode call --- #
        self.laser.resetInstructionDictionary()
        self.laser.resetWaveGuideDictionary()
        self.laser.resetGCodeCommandDictionary()
        # --- reset simulation object dictionaries --- #
        self.simuobjct.resetKeyItemDictionary('ITEMS')

    def cleanSimulation(self):
        self.plotlayout.addWidget( self.plotwidget )
        self.simuobjct.cleanView()

    def clearAllPreviousDrawings(self):
        self.resetDrawingItems()
        self.cleanSimulation()

    def makeSimulation(self):
        '''
        Function to draw the items in the SimulationDesign class.
        However, this should not delete all the items, since the SimulationDesign will be shared between
        different instances.
        '''
        self.cleanSimulation()
        if self.filename.text() != 'None':
            self.loadGCodeToLASER()
        # --- make sure variable dictionary is not empty --- #
        is_SWGdic_empty   = self.simuobjct.drawingitems['SWGItems']   == []
        is_BWGdic_empty   = self.simuobjct.drawingitems['BWGItems']   == []
        is_Abldic_empty   = self.simuobjct.drawingitems['AblItems']   == []
        is_Piecedic_empty = self.simuobjct.drawingitems['PieceItems'] == []
        if  is_SWGdic_empty and is_BWGdic_empty and  is_Abldic_empty and is_Piecedic_empty:
            self.simuobjct.initDefault()
            return None
        # --- make drawing --- #
        self.simuobjct.drawAllItems()

    def loadGCodeToLASER(self):
        self.laser.loadGCode( self.filename.text() )
        # ---  --- #
        self.activateLASER()

    def activateLASER(self):
        self.startProgressBar()
        self.laser.readGCode()
        self.updateLabelLaserPosition()
        #self.drawInstructions()
        self.drawInstructions_optim()

    def drawInstructions(self):
        self.instructions =  self.laser.dicinstruction.copy()
        for key in self.instructions:
            progbar_currval += 1
            self.progressbar.setValue( progbar_currval )
            drawtype = self.instructions[key][0]
            if   drawtype == 'LINEAR':
                args       = self.instructions[key][1]
                laser_isON = args[-1]
                X0         = np.array([args[0][0], args[0][1], args[0][2]])
                X1         = np.array([args[1][0], args[1][1], args[1][2]])
                scanNbr    = 5
                width      = 2. #scanNbr
                color      = self.simucolor
                if laser_isON:
                    self.simuobjct.drawLaserOnLine(X0, X1, width=width, color=color)
            elif drawtype == 'G92':
                pass
            elif drawtype == 'G18':
                pass
            elif drawtype == 'F':
                pass
            elif drawtype == 'G17':
                pass
            elif drawtype == 'G2':
                args       = self.instructions[key][1]
                laser_isON = args[-1]
                pos_init   = args[0]
                angle_start= args[1]
                angle_end  = args[2]
                radius     = args[3]
                width      = 2. #scanNbr
                color      = self.simucolor
                if laser_isON:
                    self.simuobjct.drawGCommand(pos_init, radius, angle_start, angle_end, width=width, color=color)
            elif drawtype == 'G3':
                args       = self.instructions[key][1]
                laser_isON = args[-1]
                pos_init   = args[0]
                angle_start= args[1]
                angle_end  = args[2]
                radius     = args[3]
                width      = 2. #scanNbr
                color      = self.simucolor
                if laser_isON:
                    self.simuobjct.drawGCommand(pos_init, radius, angle_start, angle_end, width=width, color=color)

    def drawInstructions_optim(self):
        self.waveguides = self.laser.dicwaveguides
        # --- progress bar related parameters --- #
        self.startProgressBar()
        N = len(list(self.waveguides.keys()))
        self.setMaxProgressBar(N)
        current_it = 0
        for key in self.waveguides:
            width = 2. #scanNbr
            color = self.simucolor
            X     = self.waveguides[key]
            self.simuobjct.drawListCoordinate(X, width, color=color)
            # --- update progress bar --- #
            current_it += 1
            self.progressbar.setValue( current_it )

    def startProgressBar(self):
        self.progressbar.setMinimum(0)
        self.progressbar.setValue(0)
        self.progressbar.show()

    @pyqtSlot(int)
    def setMaxProgressBar(self, Nmax):
        self.progressbar.setMaximum(Nmax)

    @pyqtSlot(int)
    def updateProgressBar(self, val):
        self.progressbar.setValue(val)

    def hideProgressBar(self):
        self.progressbar.hide()


    def makeSimulationSWG(self):
        # --- get the design parameters --- #
        xInit       = self.dicvariable['xInit'].value
        xEnd        = self.dicvariable['xEnd' ].value
        inRefr      = self.dicvariable['indRefr'].value
        distSucc    = self.dicvariable['distSucc'].value
        depth       = self.dicvariable['depth'].value
        scanNbr     = self.dicvariable['scanNbr'].value
        speed       = self.dicvariable['speed'].value
        # --- make drawing instructions --- #
        # - Set loop priority
        if type(depth)   == type(np.array([])) or type(depth)   == type([]):
            ndepth   = len(depth)
            priodepth = self.dicvariable['numDepth'].loopdepth
        else:
            depth     = [depth]
            ndepth    = 1
            priodepth = 0
        if type(scanNbr) == type(np.array([])) or type(scanNbr) == type([]):
            nscanNbr = len(scanNbr)
            priocanNbr = self.dicvariable['numScanNbr'].loopdepth
        else:
            scanNbr    = [scanNbr]
            nscanNbr   = 1
            priocanNbr = 0
        if type(depth)   == type(np.array([])) or type(depth)   == type([]):
            nspeed    = len(speed)
            priospeed = self.dicvariable['numSpeed'].loopdepth
        else:
            speed     = [speed]
            nspeed    = 1
            priospeed = 0
        loopvarlist = [depth, scanNbr, speed]
        indprior = np.argsort([priodepth, priocanNbr, priospeed])
        indprior = list( reversed(indprior) ) # because the order is reversed wrt the loop order in the G-code (smaller priority in smaller loop)
        priorityindex = self.priorityProduct( loopvarlist, indprior )
        # - iterating
        s = priorityindex.shape
        for i in range(s[0]):
            ind_depth   = priorityindex[i,0]
            ind_scanNbr = priorityindex[i,1]
            ind_speed   = priorityindex[i,2] # is not taking into account for the drawing
            self.simuobjct.drawSWG(xInit, xEnd, i*distSucc, depth[ind_depth], scanNbr[ind_scanNbr])

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
    appMain = QApplication(sys.argv)
    DesiVis = DesignVisualisation()
    DesiVis.show()
    sys.exit(appMain.exec_())
    print('FINISHED')
