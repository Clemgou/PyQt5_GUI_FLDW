#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATIONS
################################################################################################

import sys
import PyQt5 
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTableWidget
from PyQt5.QtWidgets import QBoxLayout,QGroupBox,QHBoxLayout,QVBoxLayout,QGridLayout,QSplitter,QScrollArea
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QInputDialog, QSpinBox, QListWidget, QListWidgetItem
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction
from PyQt5.QtGui     import QIcon, QFont
from PyQt5.QtCore    import QDate, QTime, QDateTime, Qt

from s_MyPyQtObjects           import MyQLabel,MyLineEdit,MyFrameFolding, MyParameter

import numpy as np
from functools import partial

################################################################################################
# FUNCTIONS
################################################################################################

class ParametersWindow(QFrame):
    '''
    Uses: MyParameter, MyQLabel, MyLineEdit, MyFrameFolding, ...
    This object will be a widget where we can enter the value for the different variables of
    the command file for the writting of Straight Waveguides, only !
    We will stack the possible parameter in several groups:
        - Fixed parameters: eg inRefr                                   ['name', float   ]
        - Loop parameter: int number parameters, eg numArray,numScan,.. ['name', int     ]
        - Fabrication parameters: array parameters                      ['name', np.array]
        - Distance inter-structure parameters: float parameters         ['name', float   ]
    Each group will be represented with a frame.
    Moreover, the name of the variable will be fixed.
    The parameters will be stock in a dictionnary with fixed keys, and the objects of the dictionary will be MyParameter.
    '''
    def __init__(self, defaultparamlist=[]):
        super().__init__()
        self.layout         = QVBoxLayout()
        self.dicparamwidget = {}
        self.dicvariable    = {} # in the form dicvariable['namevar'] = valuevar
        self.dicdefaultval  = {}
        self.dicgrouplist   = {} # in the form dicgrouplist['namegrp'] = ['namevar1', 'namevar2', ..]
        self.listloopname   = [] # list of string
        self.dicloopvar     = {}
        self.setMinimumWidth(250)   # set the minimum width of the QFrame widget
        self.setDefaultParam( defaultparamlist )
        #self.initUI()

    def setlistloopname(self, namelist):
        self.listloopname = namelist

    def addGroupParameter(self, grpname, paramnamelist):
        '''
        - Uses self.dicgrouplist dictionary
        '''
        self.dicgrouplist[grpname] = paramnamelist

    def setDefaultParam(self, defaultParam):
        '''
        Set the dictionary of default value associated to variable names.
        The default parameter can be entered as a list such as:
            [['varname', val], ...]
        - Uses self.dicdefaultval dictionary
        '''
        n = len(defaultParam)
        for i in range(n):
            self.dicdefaultval[defaultParam[i][0]] = defaultParam[i][1]

    def initUI(self):
        '''
        Initialise the display of the widget.
        - Use the self.dicgrouplist dictionary.
        - Set the self.dicparamwidget dictionary.
        '''
        # --- frame style --- #
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(3)
        self.setMidLineWidth(3)
        # --- parameter space editing --- #
        '''
        The parameters will be stack in groups:
        '''
        # --- layout of the parameter frame --- #
        self.setLoopManagementFrame()
        for grpkey in self.dicgrouplist: # for loop on dictionaries return their keys.
            grid  = QGridLayout()
            frame = MyFrameFolding(self, grpkey, True)
            frame.maincontent.setFrameStyle(QFrame.WinPanel | QFrame.Sunken)
            k = 0   # index for grid positioning
            for paramname in self.dicgrouplist[grpkey]:
                # --- add parameter widget to dicparamwidget --- #
                self.dicparamwidget[paramname, 'label']     = QLabel(paramname)
                self.dicparamwidget[paramname, 'editlist']  = MyLineEdit()
                self.dicparamwidget[paramname, 'paramlist'] = MyQLabel()
                self.dicparamwidget[paramname, 'paramchkb'] = QCheckBox()
                nameparam   = self.dicparamwidget[paramname, 'label']
                valueparam  = self.dicparamwidget[paramname, 'editlist']
                interpparam = self.dicparamwidget[paramname, 'paramlist']
                cbparam     = self.dicparamwidget[paramname, 'paramchkb']
                typeparam   = MyQLabel() # get the text from QLineEdit and get the type
                # --- initial values --- #
                try:
                    initvalue = self.dicdefaultval[paramname]
                except:
                    initvalue = '0' #ParamDefault[i][k]
                valueparam.setText(str(initvalue))
                interpparam.setInterpretedText(str(initvalue))
                typeparam.setInterpretedTextType(str(initvalue))
                # --- connections --- #
                cbparam.setTristate(True)
                cbparam.setCheckState(2) # readable state
                change_lineedit = partial( self.changeParameterState, cbparam, valueparam ) # here we generate a partial function that take the QtObjets in argument to be able to connect them. Otherwise, if we had used the lambda function, the QtObject would not have followed the links.
                cbparam.stateChanged.connect(change_lineedit)
                valueparam.textChanged.connect( typeparam.setInterpretedTextType )
                valueparam.textChanged.connect( interpparam.setInterpretedText )
                valueparam.textChanged.connect( self.detectLoopVariable )
                # --- position on grid --- #
                grid.addWidget(nameparam   , int(2*k)  , 1)
                grid.addWidget(cbparam     , int(2*k)  , 0)
                grid.addWidget(valueparam  , int(2*k)  , 2)
                grid.addWidget(typeparam   , int(2*k+1), 1)
                grid.addWidget(interpparam , int(2*k+1), 2)
                k += 1
            # --- layout for subgroups --- #
            frame.maincontentlayout.addLayout(grid)
            self.layout.addWidget(frame)
        # --- make buttons at bottom to confirme --- #
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        okButton.clicked.connect( self.getParameters )
        cancelButton.clicked.connect( self.resetParameters )
        # --- make layout --- #
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)
        self.layout.addLayout(hbox)
        self.layout.addStretch(1)
        self.layout.setAlignment(Qt.AlignTop)
        # ---  --- #
        self.setLayout(self.layout)
        self.detectLoopVariable()

    def changeParameterState(self, checkB, valP):
        state = checkB.checkState()
        if   state==0: # unreadable state
            valP.changeReadOptionLine(False)
        elif state==2: # readable state
            valP.changeReadOptionLine(True)
        elif state==1: # loop variable state
            valP.setStyleSheet("QLineEdit { background-color: white ; color: green }")
            valP.setReadOnly(False)
        self.refreshLoopManagement()

    def setLoopManagementFrame(self):
        self.loopmanagframe = MyFrameFolding(self, 'Loop Management', False)
        self.loopmanagframe.maincontent.setFrameStyle(QFrame.WinPanel | QFrame.Sunken)
        # --- Refresh button --- #
        #refreshbutton = QPushButton('Refresh')
        #refreshbutton.clicked.connect( self.refreshLoopManagement )
        #self.loopmanagframe.maincontentlayout.setMainContentNewLayout( GridL )
        # ---  --- #
        self.layout.addWidget( self.loopmanagframe )

    def isInList(self, item, L):
        for itm in L:
            if item == itm: return True
        return False

    def clearLoopVariable(self, loopvarname):
        layout = self.loopmanagframe.maincontentlayout
        removedname = []
        nameinloopman = [layout.count()]
        msg_bx = QMessageBox()
        msg_bx.setIcon(QMessageBox.Critical)
        for i in reversed(range(layout.count())):
            layoutitem = layout.takeAt(i)
            widgetitem = layoutitem.widget()
            qlabel = widgetitem.findChildren(QLabel)[0] # should be the QLabel with the loopvarname of the widgetitem.
            nameinloopman.append(widgetitem)
            if loopvarname == qlabel.text():
                removedname.append([i, qlabel.text()])
                widgetitem.hide()
                #for w in widgetitem.findChildren(QWidget):
                #    w.close()
                #    layout.removeWidget(w)
                #layout.removeWidget(widgetitem)
                #widgetitem.close()
                #widgetitem.setParent(None) # use that when QObject parent is deleted the object is also deleted.
                #widgetitem.destroy()
        self.loopmanagframe.maincontent.setLayout( self.loopmanagframe.maincontentlayout )
        msg_bx.setText('Initial state:{0} {1} '.format(nameinloopman[0], nameinloopman[1:] ))
        msg_bx.setInformativeText('Remaining items: {0}\nRemoved items: {1}'.format(layout.count(), removedname ))
        msg_bx.setWindowTitle('Display')
        msg_bx.exec_()

    def detectLoopVariable(self):
        for grpkey in self.dicgrouplist: # for loop on dictionaries return their keys.
            for paramname in self.dicgrouplist[grpkey]:
                value_var  = self.dicparamwidget[paramname, 'editlist']
                checkB_var = self.dicparamwidget[paramname, 'paramchkb']
                try:
                    type_var   = type(eval(value_var.text()))
                except:
                    if checkB_var.checkState() !=0:
                        checkB_var.setCheckState(2)
                        self.changeParameterState(checkB_var, value_var)
                    return None
                if type_var == type(np.array([])) or type(eval(self.dicparamwidget[paramname, 'editlist'].text())) == type([]):
                    checkB_var.setCheckState(1)
                    self.changeParameterState(checkB_var, value_var)
                    self.refreshLoopManagement()

    def refreshLoopManagement_old(self):
        # --- We verify if the parameter is still checked for looping --- #
        for loopvarname in self.listloopname:
            paramassocname = self.dicloopvar[loopvarname, 'paramassoc']
            for grpkey in self.dicgrouplist:
                for paramname in self.dicgrouplist[grpkey]:
                    if paramname==paramassocname and self.dicparamwidget[paramname, 'paramchkb'].checkState() != 1:
                        self.clearLoopVariable(loopvarname)
                        self.listloopname.remove(loopvarname)
        # --- We look for possible new parameters to loop --- #
        for grpkey in self.dicgrouplist: # for loop on dictionaries return their keys.
            for paramname in self.dicgrouplist[grpkey]:
                if self.dicparamwidget[paramname, 'paramchkb'].checkState() == 1:
                    if type(eval(self.dicparamwidget[paramname, 'editlist'].text())) == type(np.array([])) or type(eval(self.dicparamwidget[paramname, 'editlist'].text())) == type([]):
                        loopvarname = 'num'+paramname[0].upper()+paramname[1:]
                        if not self.isInList(loopvarname, self.listloopname): 
                            self.setNewLoopVariable(paramname)
        return None

    def refreshLoopManagement(self):
        '''
        Save a list of already existing loop variables, then delete everything and rebuild
        the loop management frame. If some vairable are the same as the old ones, we conserve
        their depth.
        It is clearly a redondant method, although I did not succeed to use a more subtule one, only
        updating the frame.
        '''
        old_listloopname = self.listloopname.copy()
        dicdeptholdloopname = {}
        for loopvarname in old_listloopname:
            dicdeptholdloopname[loopvarname] = self.dicloopvar[loopvarname, 'depthspinb'].value()
        self.clearLayout(self.loopmanagframe.maincontentlayout)
        self.listloopname = []
        self.dicloopvar   = {}
        # --- We look for possible new parameters to loop --- #
        for grpkey in self.dicgrouplist: # for loop on dictionaries return their keys.
            for paramname in self.dicgrouplist[grpkey]:
                if self.dicparamwidget[paramname, 'paramchkb'].checkState() == 1:
                    if type(eval(self.dicparamwidget[paramname, 'editlist'].text())) == type(np.array([])) or type(eval(self.dicparamwidget[paramname, 'editlist'].text())) == type([]):
                        loopvarname = 'num'+paramname[0].upper()+paramname[1:]
                        if not self.isInList(loopvarname, old_listloopname): 
                            self.setNewLoopVariable(paramname)
                        else:
                            self.setNewLoopVariable(paramname, dicdeptholdloopname[loopvarname])
                    else:
                        err_msg = QMessageBox()
                        err_msg.setIcon(QMessageBox.Critical)
                        err_msg.setText('Error:\nThe parameter must be a list or a np.array')
                        err_msg.setWindowTitle("Error")
                        err_msg.exec_()
                        self.dicparamwidget[paramname, 'paramchkb'].setCheckState(2)
                        pass

    def setNewLoopVariable(self, paramname, defaultdepth=0):
        loopvarname = 'num'+paramname[0].upper()+paramname[1:]
        itemwidget = QWidget()
        self.dicloopvar[loopvarname, 'paramassoc'] = paramname
        self.dicloopvar[loopvarname, 'namelabel']  = QLabel(loopvarname, itemwidget)
        self.dicloopvar[loopvarname, 'valuelabel'] = QLabel(itemwidget)
        self.dicloopvar[loopvarname, 'depthspinb'] = QSpinBox(itemwidget)
        label      = self.dicloopvar[loopvarname, 'namelabel']
        valuelabel = self.dicloopvar[loopvarname, 'valuelabel']
        valuelabel.setText(str(int(len( eval(self.dicparamwidget[paramname, 'editlist'].text())) )))
        spinbox    = self.dicloopvar[loopvarname, 'depthspinb']
        spinbox.setRange(0, 5)
        spinbox.setValue( defaultdepth )
        grid = QGridLayout(itemwidget)
        grid.addWidget(label     , 0, 0)
        grid.addWidget(valuelabel, 0, 1)
        grid.addWidget(spinbox   , 0, 2)
        itemwidget.setLayout(grid)
        self.loopmanagframe.maincontentlayout.addWidget(itemwidget)
        self.listloopname.append(loopvarname)

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().close()
            layout.itemAt(i).widget().setParent(None) # use that when QObject parent is deleted the object is also deleted.
        '''
        alternatively:
            layout.itemAt(i).widget().deleteLater() #Qt will 'schedule delation for later, but the layout may still have some items afterwards.

        while layout.count() > 1:
            item = layout.takeAt(0)
            if not item:
                continue
            w = item.widget().close() #otherwise it does not remove the Labels, etc...
            layout.removeItem( item )
            item.widget().deleteLater()
            del item
        '''

    def getParameters(self):
        '''
        Generate a dictionary of the parameters defined in the widget.
        Also generate a liste of the group and their name.
        - Generate the self.dicvariable dictionary.
        - Uses the self.dicgrouplist, 
        '''
        self.refreshLoopManagement()
        self.dicvariable = {}
        for grpkey in self.dicgrouplist:
            for paramname in self.dicgrouplist[grpkey]:
                if not self.dicparamwidget[paramname, 'editlist'].isReadOnly():
                    try:
                        varvalue  = eval(self.dicparamwidget[paramname, 'editlist'].text())
                        varname   = self.dicparamwidget[paramname, 'label'].text()
                        parameter = MyParameter(varname, varvalue, group=grpkey, type_='fab')
                        self.dicvariable[varname] =  parameter # where we define the variable list
                    except:
                        err_msg = QMessageBox()
                        err_msg.setIcon(QMessageBox.Critical)
                        err_msg.setText("Error:")
                        err_msg.setInformativeText('One of the parameter is not acceptable')
                        err_msg.setInformativeText( self.dicparamwidget[paramname, 'editlist'].text() )
                        err_msg.setWindowTitle("Error")
                        err_msg.exec_()
                        return None
        # --- In the Loop Management frame --- #
        for loopvarname in self.listloopname:
            varvalue  = eval(self.dicloopvar[loopvarname, 'valuelabel'].text())
            depth     = self.dicloopvar[loopvarname, 'depthspinb'].value()
            parameter = MyParameter( loopvarname, varvalue, type_='loop')
            # --- Association of the loop parameters --- #
            assocparamname = self.dicloopvar[loopvarname, 'paramassoc']  # self.dicloopvar[loopvarname, 'paramassoc'] gives us the paramname of the physical quantity
            parameter.setLoopVariableAssociated( assocparamname )
            self.dicvariable[assocparamname].setLoopVariableAssociated( loopvarname )
            parameter.setLoopDepth( depth )
            # ---  --- #
            self.dicvariable[loopvarname] =  parameter # where we define the variable list
        self.checkLoopVariableDeclaration()
        self.displayDictionaryParam()
        return None

    def checkLoopVariableDeclaration(self):
        self.refreshLoopManagement()
        for paramname in self.dicvariable:
            paramval = self.dicvariable[paramname].value
            if type(paramval) == type(np.array([])) or type(paramval) == type([]):
                try:
                    loopvarassoc = self.dicvariable[paramname   ].paramassoc
                    paramname_l  = self.dicvariable[loopvarassoc].paramassoc # self.dicloopvar[loopvarassoc, 'valuelabel']
                    if paramname_l != paramname:
                        err_msg = QMessageBox()
                        err_msg.setIcon(QMessageBox.Critical)
                        err_msg.setText('Error:\n.association do not match')
                        err_msg.setInformativeText( 'Issue witht parameter: {}'.format(paramname) )
                        err_msg.setWindowTitle("Error")
                        err_msg.exec_()
                except:
                    err_msg = QMessageBox()
                    err_msg.setIcon(QMessageBox.Critical)
                    err_msg.setText('Error:\nLoop variables are missing, or some parameters have more than one element.')
                    err_msg.setInformativeText( 'Issue witht parameter: {0}\nlistloopname:{1}'.format(paramname, self.listloopname) )
                    err_msg.setWindowTitle("Error")
                    err_msg.exec_()
                    return None

    def resetParameters(self):
        self.dicvariable = {}
        return None

    def displayParam(self):
        self.refreshLoopManagement()
        displbox = QMessageBox()
        font = QFont()
        font.setFamily("Python")
        font.setPointSize(12)
        displbox.setFont(font)
        displbox.setWindowTitle("Parameter")
        parammessg = ''
        for grpkey in self.dicgrouplist:
            for paramname in self.dicgrouplist[grpkey]:
                if not self.dicparamwidget[paramname, 'editlist'].isReadOnly():
                    varname  = self.dicparamwidget[paramname, 'label'].text()
                    parammessg += '{0:<12} : {1}\n'.format(varname , str(self.dicvariable[varname].value) )
            parammessg += '\n'
        for paramname in self.listloopname:
            parammessg += '{0:<12} : {1}\n'.format(paramname , str(self.dicvariable[paramname].value) )
            parammessg += '  {0:<10} : {1}\n'.format('depth' , str(self.dicvariable[paramname].loopdepth) )
        displbox.setText(parammessg)
        displbox.exec_()

    def displayDictionaryParam(self):
        displbox = QMessageBox()
        font = QFont()
        font.setFamily("Python")
        font.setPointSize(12)
        displbox.setFont(font)
        displbox.setWindowTitle("Parameter")
        parammessg = ''
        for paramname in self.dicvariable:
            parameter = self.dicvariable[paramname]
            parammessg += '{0:<12}: {1}\n'.format(paramname , parameter.value )
            if parameter.type == 'loop':
                parammessg += 'depth: {}\n'.format(parameter.loopdepth)
        displbox.setText(parammessg)
        displbox.exec_()

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    appMain = QApplication(sys.argv)
    paramdefaultlist = [['inRefr',1.5],['xInit',0.],['xEnd',2.9],['scanNbr',5],['distNewfab', 0.5],['distArray',0.2],['distSucc',0.1],['distScan',0.0],['depth',0.2],['speed', [20,40,60]]]
    wind = ParametersWindow( paramdefaultlist )
    wind.addGroupParameter('Fixed parameters'          , ['inRefr','xInit','xEnd'] ) 
    wind.addGroupParameter('Fabrication parameters'    , ['scanNbr','depth','speed'] )
    wind.addGroupParameter('Distansce inter-structures', ['distNewfab','distSucc','distScan'] )
    wind.initUI()
    wind.show()
    sys.exit(appMain.exec_())
