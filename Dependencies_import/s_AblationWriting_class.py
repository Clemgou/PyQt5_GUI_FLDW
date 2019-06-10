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

import numpy as np
import os

################################################################################################
# FUNCTIONS
################################################################################################

class AblationWriting(QWidget):
    def __init__(self, simuobjct=None, path=None):
        super().__init__()
        self.extsimuobjct   = simuobjct
        self.pixelsize      = [100,300] #um [X,Y]
        self.unitvect       = [np.array([1., 0.]) , np.array([0., 1.])]
        self.diccoordpxl    = {}
        self.dicalphabnum   = {}
        self.dicspeccommd   = {}
        self.listwritingpxl = []
        self.dicwritingvar  = {}
        self.coordpxlorigin = np.array([0., 0.])
        self.mirrored       = None # for mirroring the pixel coord system according to the choice of axis orientation.:w
        self.writealong     = 'X' # axis along wich we want to write: X, Y
        self.coretext       = ''
        self.defaultcolor   = 'g'
        self.whichalphabet  = 'f_alphabetcoord.txt' # default, the most standard one
        print('PRINTING',sys.path[0])
        if path == None:
            self.localpath  = os.path.dirname(os.path.realpath(__file__))
        else:
            self.localpath  = path

        self.initUI()
        self.cmdwriter      = WriteCommandCode(self.filename)
        self.initDictionaries()
        self.initDefaultConfig()

    def initUI(self):
        # --- make main window --- #
        self.splitter = QSplitter(PyQt5.QtCore.Qt.Horizontal)
        # --- PreviewCommandCode frame --- #
        self.previewcode = PreviewCommandCode('Abl_pygenerated.txt')
        self.previewcode.filename.textChanged.connect(self.setNewFilename)
        self.previewcode.textedit.setMinimumWidth(0)
        self.previewcode.textedit.setMinimumHeight(400)
        self.setNewFilename() # initialise
        # --- make frames --- #
        self.initFramePrevVisual()
        self.initFrameEditZone()
        # --- make connection --- #
        self.setPrevVisualFilename()
        # --- make layout --- #
        self.layout = QVBoxLayout()
        vlayout     = QVBoxLayout()
        vwidget     = QWidget()
        vlayout.addWidget(self.frameEditZone)
        vlayout.addWidget(self.previewcode)
        vwidget.setLayout( vlayout )
        self.splitter.addWidget(self.framePrevVisual)
        self.splitter.addWidget( vwidget )
        self.layout.addWidget( self.splitter )
        self.setLayout( self.layout )

    def initDictionaries(self):
        # --- init all dictionaries --- #
        self.initAlphabNumDicationary()
        self.initCoordDictionary(self.mirrored)
        self.initWritingParameterDictionary()

    def initFramePrevVisual(self):
        # ---  --- #
        if self.extsimuobjct==None:
            self.framePrevVisual    = DesignVisualisation() #QFrame()
        else:
            self.framePrevVisual    = DesignVisualisation(simuobjct=self.extsimuobjct) #QFrame()
        # ---  --- #
        self.framePrevVisual.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.framePrevVisual.setMinimumSize(600, 600)
        self.simuobcj           = self.framePrevVisual.simuobjct
        self.viewobjct          = self.simuobcj.view
        # --- set default color --- #
        self.framePrevVisual.setSimulationColor(2) # 2 is for green
        self.textcolor = self.framePrevVisual.simucolor
        # --- make connection --- #
        self.framePrevVisual.axisorientation.currentIndexChanged.connect( self.setOrientationAxis )
        self.framePrevVisual.currentcolor.currentIndexChanged.connect( self.setNewTextColor )
        # --- make layout --- #
        # No need to set a layout since it is included in the DesignVisualisation object.

    def initFrameEditZone(self):
        self.frameEditZone      = QFrame()
        self.frameEditZone.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.frameEditZone.setMaximumHeight(150)
        self.texttowrite        = QLineEdit(self.frameEditZone)
        self.pixelboxsize       = [QLineEdit(), QLineEdit()]  # [x,y]
        self.pixelorigin        = [QLineEdit(), QLineEdit()]  # [x,y]
        # --- combo boxes --- #
        self.cbwritingaxis      = QComboBox()
        self.cbwritingaxis.addItem('Write along X')
        self.cbwritingaxis.addItem('Write along Y')
        self.cbalphabetchoice   = QComboBox()
        self.cbalphabetchoice.addItem('alphabet: Standard')
        self.cbalphabetchoice.addItem('alphabet: Fancy ;)')
        # --- set default --- #
        self.pixelboxsize[0].setText(str(self.pixelsize[0]))
        self.pixelboxsize[1].setText(str(self.pixelsize[1]))
        self.pixelorigin[0].setText('0.0')
        self.pixelorigin[1].setText('0.0')
        self.cbwritingaxis.setCurrentIndex(0)
        self.cbalphabetchoice.setCurrentIndex(0)
        # --- make connexions --- #
        self.pixelboxsize[0].textChanged.connect(self.setPixelSizeX)
        self.pixelboxsize[1].textChanged.connect(self.setPixelSizeY)
        self.pixelorigin[0].textChanged.connect(self.setPixelOriginX)
        self.pixelorigin[1].textChanged.connect(self.setPixelOriginY)
        self.texttowrite.textChanged.connect( self.refreshAll )
        self.pixelboxsize[0].textChanged.connect(self.refreshAll )
        self.pixelboxsize[1].textChanged.connect(self.refreshAll )
        self.pixelorigin[0].textChanged.connect( self.refreshAll )
        self.pixelorigin[1].textChanged.connect( self.refreshAll )
        self.cbwritingaxis.currentIndexChanged.connect( self.setWritingAxis )
        self.cbalphabetchoice.currentIndexChanged.connect( self.setAlphabetFilename )
        # --- make layout --- #
        layout                  = QVBoxLayout()
        grid1                   = QGridLayout()
        hlayout2                = QHBoxLayout()
        grid1.addWidget(QLabel('Startin point (mm)'), 0, 0)
        grid1.addWidget(QLabel('X'), 0, 1)
        grid1.addWidget(self.pixelorigin[0], 0, 2)
        grid1.addWidget(QLabel('Y'), 0, 3)
        grid1.addWidget(self.pixelorigin[1], 0, 4)
        grid1.addWidget(QLabel('Unit box size (um): '), 1, 0)
        grid1.addWidget(QLabel('x'), 1, 1)
        grid1.addWidget(self.pixelboxsize[0], 1, 2)
        grid1.addWidget(QLabel('y'), 1, 3)
        grid1.addWidget(self.pixelboxsize[1], 1, 4)
        grid1.addWidget( self.cbwritingaxis   , 2,0, 1,2)
        grid1.addWidget( self.cbalphabetchoice, 2,2, 1,2)
        hlayout2.addWidget(QLabel('TEXT'))
        hlayout2.addWidget(self.texttowrite)
        layout.addLayout(grid1)
        layout.addLayout(hlayout2)
        self.frameEditZone.setLayout( layout )

    def initWritingParameterDictionary(self):
        xInit      = MyParameter('xInit'     , 0. , group='grp0')
        depth      = MyParameter('depth'     , 0. , group='grp0')
        speed      = MyParameter('speed'     , 0.5, group='grp0')
        indRefr    = MyParameter('indRefr'   , 1.5, group='grp0')
        distNewfab = MyParameter('distNewfab', 0.1, group='grp0')
        self.dicwritingvar['xInit']      = xInit
        self.dicwritingvar['depth']      = depth
        self.dicwritingvar['speed']      = speed
        self.dicwritingvar['indRefr']    = indRefr
        self.dicwritingvar['distNewfab'] = distNewfab
        return None

    def initCoordDictionary(self, mirror=None):
        '''
        Initialise the point coordinate systems. It will be a dictionary of the point name,
        str(nbr), which will hold a 1D np.array of x,y coordinate: np.array([x,y]).
        - 23 points for a pixel
        - a 'space' pixel
        - some special characters: '.', ':', '!', '?', ... (if I have time)
        '''
        if   self.writealong=='X':
            a1 = self.unitvect[0]*self.pixelsize[0]/4. # /4. because the total xsize is 4*a1
            a2 = self.unitvect[1]*self.pixelsize[1]/6. # /6. because the total ysize is 6*a2
        elif self.writealong=='Y':
            a2 = +self.unitvect[0]*self.pixelsize[0]/4. # /4. because the total xsize is 4*a1
            a1 = -self.unitvect[1]*self.pixelsize[1]/6. # /6. because the total ysize is 6*a2
        # --- vertical points --- #
        # ie along Y axis => along a2
        for i in range(7):
            self.diccoordpxl[str(i)]    =     0*a1 +     i*a2
            self.diccoordpxl[str(i+10)] =     4*a1 + (6-i)*a2
        # --- horizontal points --- #
        for i in range(1,4):
            self.diccoordpxl[str(i+ 6)] =     i*a1 +    6*a2
            self.diccoordpxl[str(i+16)] = (4-i)*a1 +    0*a2
            self.diccoordpxl[str(i+19)] =     i*a1 +    3*a2
        # --- extra points --- #
        self.diccoordpxl['23'] = self.diccoordpxl['21'] + a2
        self.diccoordpxl['24'] = self.diccoordpxl['21'] - a2
        self.diccoordpxl['25'] = self.diccoordpxl['7']  - a2
        self.diccoordpxl['26'] = self.diccoordpxl['9']  - a2
        self.diccoordpxl['27'] = self.diccoordpxl['17'] + a2
        self.diccoordpxl['28'] = self.diccoordpxl['19'] + a2
        # --- change orientation of pxl coord system --- #
        if mirror=='X':
            for key in self.diccoordpxl:
                self.diccoordpxl[key]    = 4*a1 + self.diccoordpxl[key]*np.array([-1., 1.])
        if mirror=='Y':
            for key in self.diccoordpxl:
                self.diccoordpxl[key][1] = 6*a2[1] - self.diccoordpxl[key][1]
        # --- special character --- #
        # --- boxsize
        self.diccoordpxl['xboxsize']   = 4*a1
        self.diccoordpxl['yboxsize']   = 6*a2
        # --- space between successive letter
        self.diccoordpxl['interspace'] = 1*a1 #self.diccoordpxl['19']
        # --- space character
        self.diccoordpxl['space']      = 4*a1 #self.diccoordpxl['16']
        # --- dot character
        self.diccoordpxl['dot']        = np.sum(a2**2)**.5 /2.
        return None

    def initDefaultConfig(self):
        self.setPixelSizeX()
        self.setPixelSizeY()
        # --- initiate orientation --- #
        self.setOrientationAxis( self.framePrevVisual.axisorientation.currentIndex() )

    def initAlphabNumDicationary(self):
        '''
        Initialise the dictionary that will containe the set of instruction to draw the Alphabet.
        The construction of the dictionary will be implemented via the extraction of the data
        in a text file. Everything will be in 'string' type.
        '''
        filename = self.localpath+'/'+self.whichalphabet
        Data     = self.myLoadTxt(filename)
        n = len(Data)
        for i in range(n):
            self.dicalphabnum[Data[i][0]] = Data[i][1]
            #print(Data[i][0])
        # --- add special characters --- #
        self.dicalphabnum[' '] = ['space']
        self.dicalphabnum['#'] = self.dicalphabnum['/#']
        return None

    def setNewFilename(self):
        self.filename = self.previewcode.filename.text()

    def setWritingAxis(self, i):
        if   i==0: # first choice: along X
            self.writealong = 'X'
        elif i==1: # first choice: along Y
            self.writealong = 'Y'
        self.refreshAll()

    def setAlphabetFilename(self, i):
        if   i == 0:
            self.whichalphabet = 'f_alphabetcoord.txt'
        elif i == 1:
            self.whichalphabet = 'f_alphabetcoord_fancy.txt'
        self.initAlphabNumDicationary()
        self.refreshAll()

    def setPrevVisualFilename(self):
        self.framePrevVisual.setFilename( self.previewcode.filename )

    def setPixelSizeX(self):
        if self.pixelboxsize[0].text() == '':
            return None
        try:
            xsize = float(eval( self.pixelboxsize[0].text() ))
            self.pixelsize[0] = xsize*10**-3 # to get the same scale (um)
        except:
            errortext = 'ERROR: incorrect input for the X boxsize definition.\nCurrent input: {}'.format(self.pixelboxsize[0].text())
            print(errortext)
            self.raiseErrorMessageBox(errortext)
            return None
        self.refreshScalePixel()

    def setPixelSizeY(self):
        if self.pixelboxsize[1].text() == '':
            return None
        try:
            ysize = float(eval( self.pixelboxsize[1].text() ))
            self.pixelsize[1] = ysize*10**-3 # to get the same scale (um)
        except:
            errortext = 'ERROR: incorrect input for the Y boxsize definition.\nCurrent input: {}'.format(self.pixelboxsize[1].text())
            print(errortext)
            self.raiseErrorMessageBox(errortext)
            return None
        self.refreshScalePixel()

    def setPixelOriginX(self):
        if self.pixelorigin[0].text() == '':
            return None
        try:
            xorigin = float(eval( self.pixelorigin[0].text() ))
            self.coordpxlorigin[0] = xorigin
        except:
            errortext = 'ERROR: incorrect input for the boxsize definition.'
            print(errortext)
            self.raiseErrorMessageBox(errortext)
            return None

    def setPixelOriginY(self):
        if self.pixelorigin[1].text() == '':
            return None
        try:
            yorigin = float(eval( self.pixelorigin[1].text() ))
            self.coordpxlorigin[1] = yorigin
        except:
            errortext = 'ERROR: incorrect input for the boxsize definition.'
            print(errortext)
            self.raiseErrorMessageBox(errortext)
            return None

    def setNewTextColor(self):
        self.textcolor = self.framePrevVisual.simucolor

    def setOrientationAxis(self, i):
        '''
        Redefine the unit vectors so that it matches the wanted referential oriantation
        of the axis. The default order is:
            - i=0 --> Fab Line 1
            - i=1 --> Normal
        '''
        if i == 0:
            xboxsize = np.abs(self.diccoordpxl['16'])
            self.mirrored = 'X'
        elif i == 1:
            self.mirrored = None
        else:
            self.raiseErrorMessageBox('Problem with the geometry definition.')
            return None
        self.refreshAll()

    def refreshAll(self):
        self.setNewFilename()
        self.refreshScalePixel()
        self.writeGCode()
        self.drawText()

    def refreshScalePixel(self):
        self.initCoordDictionary(self.mirrored)

    def resetCoreText(self):
        self.coretext = ''

    def drawText(self):
        self.framePrevVisual.clearAllPreviousDrawings()
        self.framePrevVisual.makeSimulation()

    def writeGCode(self):
        self.makeCoreTextINCREMENTAL()
        self.cleanUnnecessaryOnOff()
        self.cmdwriter.setTextNameFile(  self.filename )
        self.cmdwriter.setDicVariable(   self.dicwritingvar )
        self.cmdwriter.initGroups()
        self.cmdwriter.initLoopVariables()
        self.cmdwriter.cleanUnnecessaryParameters()
        self.cmdwriter.writeTextFile(    self.cmdwriter.varDefinition() )
        self.cmdwriter.appendToTextFile( self.cmdwriter.paramDefinition() )
        self.cmdwriter.appendToTextFile( self.cmdwriter.initializeLaserWriting() )
        self.cmdwriter.appendToTextFile( "\n'~~~~ Writing ~~~~'\n" )
        self.cmdwriter.appendToTextFile( self.coretext )
        self.cmdwriter.appendToTextFile( self.cmdwriter.endOfScript() )
        self.previewcode.refreshTextFile()
        return None

    def raiseErrorMessageBox(self, text):
        msg_bx = QMessageBox()
        msg_bx.setIcon(QMessageBox.Critical)
        msg_bx.setText('ERROR:')
        msg_bx.setInformativeText(text)
        msg_bx.setWindowTitle('ERROR')
        msg_bx.exec_()
        return None

    def myLoadTxt(self, filename, comments='#', separator=' '):
        '''
        This function returns a table where each line is composed of:
            - the first character of the line
            - a list of the other elements (can be a number, word, ...)
        '''
        # --- open file --- #
        f = open(filename, 'r')
        # --- separating the rows --- #
        a = f.read().splitlines()
        # --- skipping the comment lines --- #
        for i in reversed(range(len(a))):
            line = a[i]
            if line[0] == comments:
                a.pop(i)
        # --- building the data array output --- #
        nrow = len(a)
        DATA = []
        for i in range(nrow):
            a_split = a[i].split(separator)
            data_i = [a_split[0], a_split[1:]]
            DATA.append(data_i)
        return DATA

    def drawCharactBox(self):
        charBox = np.array([0,6,10,13,3,13,16,0],dtype=str)
        if   self.mirrored == None:
            spacebtwnchar   = np.array([0,6,7,19,0],dtype=str)
        elif self.mirrored =='X':
            spacebtwnchar   = np.array([16,10,9,17,16],dtype=str)
        X = []
        for i in range(len(charBox)):
            coord     = self.diccoordpxl[charBox[i]]
            X.append( np.array([coord[0], coord[1]]) )
        for i in range(len(spacebtwnchar)):
            coord     = self.diccoordpxl[spacebtwnchar[i]]
            X.append( np.array([coord[0], coord[1]]) + self.diccoordpxl['xboxsize'])
        X = np.array(X)
        self.simuobcj.drawAblationText(X,color='w')

    def convertCharacterToCommandABSOLUTE(self, char, coordoffset):
        '''
        Returns the list of commands to draw the string 'char'.
        '''
        coretxt = ''
        # --- test if it is a special character --- #
        try:
            charcmdspecial = self.dicspeccommd[str(char)][0]
            coretxt += charcmdspecial
            coretxt  += '\n'
            return coretxt
        except:
            pass
        # --- initialisation --- #
        character = self.dicalphabnum[char]
        initcoord = self.diccoordpxl[character[0]] + coordoffset
        coretxt  += self.cmdwriter.cmdLINEAR(round(initcoord[0], 3), round(initcoord[1], 3) )
        coretxt  += self.cmdwriter.cmdSTART()
        # --- iteration --- #
        n = len(character)
        for i in range(1,n):
            coord     = self.diccoordpxl[character[i]] + coordoffset
            coretxt  += self.cmdwriter.cmdLINEAR(round(coord[0],3), round(coord[1],3))
        coretxt  += self.cmdwriter.cmdSTOP()
        coretxt  += '\n'
        return coretxt

    def convertTextToCommandABSOLUTE(self):
        text = self.texttowrite.text()
        text = text.upper() # for now, the lower case are not implemented
        n = len(text)
        coretxt = ''
        for i in range(n):
            char = text[i]
            coordoffset = self.coordpxlorigin + i*(self.diccoordpxl['xboxsize']+self.diccoordpxl['interspace'])
            coretxt += self.convertCharacterToCommandABSOLUTE(char, coordoffset)
            #coretxt += self.makeSpaceBetweenLetter() # not needed in absolute coordinate.
        return coretxt

    def makeCoreTextABSOLUTE(self):
        self.resetCoreText()
        self.coretext += self.cmdwriter.cmdLINEAR(self.coordpxlorigin[0], self.coordpxlorigin[1])
        self.coretext += self.cmdwriter.cmdSetDepthVariable()
        self.coretext += self.cmdwriter.cmdSetSpeedVariable()
        self.coretext += self.cmdwriter.cmdABSOLUTE()
        self.coretext += self.convertTextToCommandABSOLUTE()
        return None

    def convertCharacterToCommandINCREMENTAL(self, char, coordoffset):
        '''
        Returns the list of commands to draw the string 'char'.
        '''
        coretxt  = ''
        coretxt += "'~~~ character : {} ~~~'\n".format(char)
        character = self.dicalphabnum[char]
        # --- check if it is a space --- #
        if character[0] == 'space':
            return self.makeCharacterSpace('space')
        # --- initialisation --- #
        initcoord = self.diccoordpxl[character[0]]
        coretxt  += self.cmdwriter.cmdLINEAR(round(initcoord[0], 3), round(initcoord[1], 3) )
        coretxt  += self.cmdwriter.cmdSTART() #PSOCONTROL X ON
        coord_prev = initcoord
        # --- iteration --- #
        n = len(character)
        for i in range(1,n):
            # --- check if not special character --- #
            if   character[i] == 'dot':
                coretxt += self.makeDotCharacter(character[i])
                coord    = coord_prev
            elif character[i] == 'start':
                coretxt  += self.cmdwriter.cmdSTART() #PSOCONTROL X ON
                coord    = coord_prev
            elif character[i] == 'stop':
                coretxt  += self.cmdwriter.cmdSTOP()  #PSOCONTROL X ON
                coord    = coord_prev
            else:
                # --- if normal point coordinate --- #
                coord     = self.diccoordpxl[character[i]]
                increment = np.array([coord[0], coord[1]]) - coord_prev
                coretxt  += self.cmdwriter.cmdLINEAR(round(increment[0],3), round(increment[1],3))
            coord_prev = coord
        coretxt  += self.cmdwriter.cmdSTOP()  #PSOCONTROL X OFF 
        # --- return to initial --- #
        coord_last= coord #self.diccoordpxl[character[-1]] # coordinate where we should end.
        coretxt  += self.cmdwriter.cmdLINEAR(round(-coord[0],3), round(-coord[1],3)) # return to origin, ie point 0.
        # ---  --- #
        coretxt  += '\n'
        return coretxt

    def convertTextToCommandINCREMENTAL(self):
        text = self.texttowrite.text()
        #print('TEXT:',text)
        text = text.upper() # for now, the lower case are not implemented
        n = len(text)
        if self.mirrored == 'X':
            text = text[::-1]
        coretxt = ''
        coordoffset = self.coordpxlorigin.copy()
        for i in range(n):
            char         = text[i]
            coretxt     += self.convertCharacterToCommandINCREMENTAL(char, coordoffset)
            coretxt     += self.makeCharacterSpace('xboxsize')
            coretxt     += self.makeCharacterSpace('interspace')
            coretxt  += '\n'
            coordoffset += self.diccoordpxl['xboxsize']+self.diccoordpxl['interspace']
        return coretxt

    def makeCharacterSpace(self, char):
        coretxt = ''
        # --- verify if input is correct --- #
        if char!='space' and char!='interspace' and char!='xboxsize' and char!='yboxsize':
            self.raiseErrorMessageBox('Not the right input for makeCharacterSpace.')
            return None
        # --- initialisation --- #
        increment = self.diccoordpxl[char]
        # --- cmd text --- #
        coretxt  += self.cmdwriter.cmdLINEAR(round(increment[0], 3), round(increment[1], 3) )
        return coretxt

    def makeDotCharacter(self, char):
        coretxt = ''
        # --- verify if input is correct --- #
        if char!='dot':
            self.raiseErrorMessageBox('Not the right input for makeDotCharacter.')
            return None
        # ---  --- #
        coretxt  += 'G17\n'
        radius,theta_start,theta_end = self.diccoordpxl[char], 0, 360 #in degree
        #print('DOT PARAMETER:',radius,theta_start,theta_end)
        coretxt  += self.cmdwriter.cmdSTOP()  #PSOCONTROL X OFF 
        coretxt  += self.cmdwriter.cmdLINEAR(+round(radius,6))
        coretxt  += self.cmdwriter.cmdSTART() #PSOCONTROL X ON
        coretxt  += self.cmdwriter.cmdG3(theta_start, theta_end, radius)
        coretxt  += self.cmdwriter.cmdSTOP()  #PSOCONTROL X OFF 
        coretxt  += self.cmdwriter.cmdLINEAR(-round(radius,6))
        coretxt  += self.cmdwriter.cmdSTART() #PSOCONTROL X ON
        return coretxt

    def makeCoreTextINCREMENTAL(self):
        self.resetCoreText()
        self.coretext += self.cmdwriter.cmdLINEAR(self.coordpxlorigin[0], self.coordpxlorigin[1])
        self.coretext += self.cmdwriter.cmdSetDepthVariable()
        self.coretext += self.cmdwriter.cmdSetSpeedVariable()
        self.coretext += self.cmdwriter.cmdINCREMENTAL()
        self.coretext += self.convertTextToCommandINCREMENTAL()
        return None

    def cleanUnnecessaryOnOff(self):
        texttoclean = self.coretext
        texttoclean = texttoclean.splitlines()
        for i in reversed(range(2,len(texttoclean)-2)):
            line_pre = texttoclean[i-2]
            line_cur = texttoclean[i]
            line_aft = texttoclean[i+2]
            try:
                if   line_cur[-2:] == 'ON' and line_aft[-3:]=='OFF':
                    #print('WOOHOO')
                    texttoclean.pop(i+1)
                    texttoclean.pop(i)
                elif line_cur[-3:] == 'OFF' and line_aft[-2:]=='ON':
                    #print('YAAHAA')
                    texttoclean.pop(i+1)
                    texttoclean.pop(i)
            except: pass
        self.coretext = '\n'.join(texttoclean)
        return None

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
    appMain = QApplication(sys.argv)
    wind = AblationWriting()
    wind.show()
    sys.exit(appMain.exec_())
