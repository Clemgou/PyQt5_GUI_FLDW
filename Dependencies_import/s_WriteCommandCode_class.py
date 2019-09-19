#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATIONS
################################################################################################

import numpy as np

from s_MyPyQtObjects               import MyParameter
from s_WriteCommandCode_functions  import *

################################################################################################
# FUNCTIONS
################################################################################################

class WriteCommandCode():
    def __init__(self, nametextfile):
        self.nametextfile   = nametextfile
        self.headerline     =  "'***************************************************\n"
        self.CoreText       = None
        self.loopkeys       = []
        self.dicvariable    = {}
        self.loopindexlist  = ["$ii","$jj","$kk","$ll","$mm"] # We will use $nn for the repeated scan loop.
        self.groupvarname   = {} # Dictionary of groups with the list of parameter name associated.
        self.encoding       = 'UTF-8'
        self.newline        = '\r\n' # seems the only working newline option for Windows to understand. Other options are: None,'','\n','\r','\r\n'.
        self.diccmdmethod   = {}
        self.initCommandMethodDictionary()
        #self.initDefault()

    # --- Method attribution from external module --- #
    '''
    All the following method will return a string object. They all
    produce a part of the Gcode that will build the CoreText of thei
    final code.
    '''
    varDefinition          = varDefinition
    paramDefinition        = paramDefinition
    initializeLaserWriting = initializeLaserWriting
    scanSWG                = scanSWG
    scanBWG                = scanBWG
    loopFunctionSWG        = loopFunctionSWG
    loopFunctionBWG        = loopFunctionBWG
    endOfScript            = endOfScript
    setHeader              = setHeader
    cmdLINEAR              = cmdLINEAR
    cmdG2                  = cmdG2
    cmdG3                  = cmdG3
    cmdSetDepthValue       = cmdSetDepthValue
    cmdSetDepthVariable    = cmdSetDepthVariable
    cmdSetSpeedValue       = cmdSetSpeedValue
    cmdSetSpeedVariable    = cmdSetSpeedVariable
    cmdSTART               = cmdSTART
    cmdSTOP                = cmdSTOP
    cmdDWELL               = cmdDWELL
    cmdINCREMENTAL         = cmdINCREMENTAL
    cmdABSOLUTE            = cmdABSOLUTE
    # ---------------------------------------------- #

    def setTextNameFile(self, filename):
        self.nametextfile = filename

    def resetGroupVar(self):
        self.groupvarname = {}

    def resetLoopVar(self):
        self.loopkeys = []

    def addGroupVar(self, groupname, grouplist):
        self.groupvarname[groupname] = grouplist

    def doesGroupExist(self, grpname):
        for key in self.groupvarname:
            if grpname == key:
                return True
        return False

    def initCommandMethodDictionary(self):
        self.diccmdmethod['LINEAR'] = self.cmdLINEAR
        self.diccmdmethod['SPEED']  = self.cmdSetSpeedVariable
        self.diccmdmethod['START']  = self.cmdSTART
        self.diccmdmethod['STOP']   = self.cmdSTOP
        self.diccmdmethod['DWELL']  = self.cmdDWELL

    def initLoopVariables(self):
        '''
        Generate a list of loop variable name and associate to the corresponding parameter object their associated loop index name.
        - Uses self.loopkeys = ['loopkey1', ... ]
        - MyParameter.setLoopVariable( '$ii' )
        '''
        self.resetLoopVar() # make sure we restart from beginning
        i = 0
        for key in self.dicvariable:
            if self.dicvariable[key].type == 'loop':
                self.dicvariable[key].setLoopVariable( self.loopindexlist[i] )
                self.loopkeys.append(key)
                i += 1
        return None

    def initGroups(self):
        self.resetGroupVar() # make sure we restart from beginning
        for paramkey in self.dicvariable:
            grpparam = self.dicvariable[paramkey].group
            if self.doesGroupExist(grpparam):
                self.groupvarname[grpparam].append(self.dicvariable[paramkey].name)
            else:
                self.groupvarname[grpparam] = [self.dicvariable[paramkey].name]

    def indentBlockString(self, s, nbspace):
        '''
        Return a string where nbspace are placed before each lines.
        nbspace can also be negative if we want to remove spaces.
        '''
        s_ = s.split('\n')
        s_ = [(nbspace * ' ')+line for line in s_]  # to remove possible already existing space before the line, one can use the lstrip method: [(nbspace * ' ') + line.lstrip() for line in s_]
        s_ = '\n'.join(s_)
        return s_

    def passArgumtToMethod(self, methodname, arglist=[]):
        output = self.diccmdmethod[methodname](*arglist)
        return output

    def setDicVariable(self, dicvariable):
        self.dicvariable = dicvariable

    def writeTextFile(self, text):
        if type(text) != type(''):
            print('Error: Wrong format for name header')
            return None
        f = open(self.nametextfile, "w+", newline=self.newline, encoding=self.encoding)   # declare variable f, open a txt file to write in it "w", and create it if it doesn't exists already "+"
        f.write( text )
        f.close()
        return None

    def appendToTextFile(self, text):
        if type(text) != type(''):
            print('Error: Wrong format for name header')
            return None
        f = open(self.nametextfile, "a", newline=self.newline, encoding=self.encoding)   # declare variable f, open a txt file to write in it "w", and create it if it doesn't exists already "+"
        f.write( text )
        f.close()
        return None

    def doesKeyExist(self, key):
        '''
        Uses: self.dicvariable
        Simple try test to know if the key exists in the dictionary: self.dicvariable
        '''
        try:
            test = self.dicvariable[key]
            return True
        except:
            return False

    def cleanUnnecessaryParameters(self):
        olddicvariable = self.dicvariable.copy()
        for key in olddicvariable:
            paramval = self.dicvariable[key]
            if type(paramval) == type(float(0)):
                if paramval == -1:      # we set -1 as the convention for discarding a parameter because some useful ones can have 0 value, eg xInit.
                    del self.dicvariable[key]
        oldloopkeys = self.loopkeys.copy()
        for key in oldloopkeys:
            paramval = self.dicvariable[key]
            if type(paramval) == type(int(0)):
                if paramval == 1:   # indeed loops of one iteration are redondant, thus can be avoided
                    del self.dicvariable[key]
                    self.loopkeys.pop( np.where(self.loopkeys==key)[0] )

    def sortPriorityLoop(self):
        depthkeylist = []
        for key in self.loopkeys:
            depthkeylist.append([self.dicvariable[key].loopdepth , key])
        depthkeylist = np.array(depthkeylist)
        if len(depthkeylist) == 0:
            return []
        indsortedlist = np.argsort(depthkeylist, axis=0)
        sortedkey = depthkeylist[indsortedlist[:,0],1]
        return sortedkey

    def compileTextSWG(self):
        '''
        Make a text file and write the command lines for straight waveguide FLDW.
        Set the right options for SWG.
        '''
        #self.getParameters()
        self.writeTextFile( self.varDefinition() )
        self.appendToTextFile( self.paramDefinition() )
        self.appendToTextFile( self.initializeLaserWriting() )
        self.appendToTextFile( self.loopFunctionSWG() )
        self.appendToTextFile( self.endOfScript() )

    def compileTextBWG(self):
        '''
        Make a text file and write the command lines for bent waveguide FLDW.
        Set the right options for BWG.
        '''
        self.writeTextFile( self.varDefinition() )
        self.appendToTextFile( 'DVAR $theta $thetaDeg $Pi\n' )
        self.appendToTextFile( self.paramDefinition() )
        self.appendToTextFile( '$Pi = 4*atan(1)\n' )
        self.appendToTextFile( self.initializeLaserWriting() )
        self.appendToTextFile( self.loopFunctionBWG() )
        self.appendToTextFile( self.endOfScript() )

    def compileTextScript(self, text):
        '''
        Make a text file and write the command lines for straight waveguide FLDW.
        Set the right options for SWG.
        '''
        #self.getParameters()
        self.writeTextFile( self.varDefinition() )
        self.appendToTextFile( self.paramDefinition() )
        self.appendToTextFile( self.initializeLaserWriting() )
        self.appendToTextFile( text )
        self.appendToTextFile( self.endOfScript() )

    def getParameters(self): #(self, Param):
        '''
        Set the parameter value and return a list of list for
        the name and value of each parameter needed in the
        command file.
        The variable will be stack in groups:
            - fixed parameters                              ['name', float   ]
            - float parameters, for the distances, and gaps ['name', float   ]
            - int number parameters, eg numArray,numScan,.. ['name', int     ]
            - array parameters, they should be in the form: ['name', np.array]
        '''
        Param = [1.5, 0., 2.9, 0.1, -0.200, np.array([20, 40]), np.array([2, 5, 8]), 0.5, 0., 1, 3, 2]
        self.dicvariable['indRefr']     = MyParameter('indRefr'     , Param[0], group='fixed', type_='fab')
        self.dicvariable['xInit']       = MyParameter('xInit'       , Param[1], group='fixed', type_='fab')
        self.dicvariable['xEnd']        = MyParameter('xEnd'        , Param[2], group='fab'  , type_='fab')
        self.dicvariable['distSucc']    = MyParameter('distSucc'    , Param[3], group='fab'  , type_='fab')
        self.dicvariable['depth']       = MyParameter('depth'       , Param[4], group='var'  , type_='fab')
        self.dicvariable['speed']       = MyParameter('speed'       , Param[5], group='var'  , type_='fab')
        self.dicvariable['scanNbr']     = MyParameter('scanNbr'     , Param[6], group='var'  , type_='fab')
        self.dicvariable['distNewfab']  = MyParameter('distNewfab'  , Param[7], group='fab'  , type_='fab')
        self.dicvariable['distScan']    = MyParameter('distScan'    , Param[8], group='fab'  , type_='fab')
        self.dicvariable['numDepth']    = MyParameter('numDepth'    , Param[9], group='loop' , type_='loop')
        self.dicvariable['numScan']     = MyParameter('numScan'     , Param[10], group='loop', type_='loop')
        self.dicvariable['numSpeed']    = MyParameter('numSpeed'    , Param[11], group='loop', type_='loop')
        self.dicvariable['numDepth'].setLoopVariableAssociated( 'depth' )
        self.dicvariable['numScan' ].setLoopVariableAssociated( 'scanNbr' )
        self.dicvariable['numSpeed'].setLoopVariableAssociated( 'speed' )
        self.dicvariable['numDepth'].setLoopDepth( 2 )
        self.dicvariable['numScan' ].setLoopDepth( 0 )
        self.dicvariable['numSpeed'].setLoopDepth( 1 )
        return None

    def initDefault(self):
        self.initGroups()
        self.initLoopVariables()

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
    nametxtfile = "BWG_pygenerated.txt"
    Script = WriteCommandCode(nametxtfile)
    Script.getParameters()
    Script.initDefault()
    Script.cleanUnnecessaryParameters()
    Script.compileTextSWG()

