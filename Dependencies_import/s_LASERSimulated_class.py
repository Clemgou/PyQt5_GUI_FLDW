#! usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATION
################################################################################################

import sys
import PyQt5
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from PyQt5.QtCore import Qt

import numpy as np
from numpy import sin
from numpy import cos
from numpy import sin as SIN
from numpy import cos as COS
from numpy import arctan as atan
from numpy import arccos as acos
from numpy import arcsin as asin

from s_LASERSimulated_functions import *

################################################################################################
# FUNCTIONS
################################################################################################

class LASERSimulated():
    '''
    This class will interpret a Gcode program and generate a set of instructions
    that can be drawn using the SimulationDesign class.
    It will play the role of the Laser writing process.
    The implementation will be simple: the Gcode is read line by line, when an instruction
    is recognised we translate it into drawing parameters, if not recognised, we pass to
    next line.
    '''
    def __init__(self):
        self.txtGcode       = ''
        self.dicGcodecmd    = {}
        self.dicinstruction = {}
        self.diccommands    = {}
        self.dicvariables   = {}
        self.dicforloop     = {}
        self.isON           = False
        self.position       = np.array([0,0,0], dtype=float)
        self.origin         = np.array([0,0,0], dtype=float)
        self.coordmode      = 'ABSOLUTE'
        self.current_WG     = [] #will be a list of coordinate
        self.dicwaveguides  = {} #will store the wave guides

        self.initDictionaryInstruction()
        self.setSpecialCommand()
        #self.initFunctionForEvaluation() # doesn't work

   # --- Method attribution from external modul --- #
    '''
    '''
    doDVARcmd        = doDVARcmd
    doLINEARcmd      = doLINEARcmd
    doABSOLUTEcmd    = doABSOLUTEcmd
    doINCREMENTALcmd = doINCREMENTALcmd
    doPSOCONTROLcmd  = doPSOCONTROLcmd
    doFORcmd         = doFORcmd
    doNEXTcmd        = doNEXTcmd
    doG2cmd          = doG2cmd
    doG3cmd          = doG3cmd
    doG92cmd         = doG92cmd
    G2G3Converter    = G2G3Converter

    def initFunctionForEvaluation(self):
        from numpy import sin as SIN
        from numpy import cos as COS
        from numpy import arctan as atan

    def initDictionaryInstruction(self):
        '''
        All key are upper case. This will facilitate the case incentivity of the gcode.
        '''
        # --- DVAR --- #
        self.diccommands['DVAR']   = self.doDVARcmd
        # --- LINEAR --- #
        self.diccommands['LINEAR'] = self.doLINEARcmd
        #self.diccommands['linear'] = self.doLINEARcmd
        # --- ABSOLUTE --- #
        self.diccommands['ABSOLUTE'] = self.doABSOLUTEcmd
        # --- INCREMENTAL --- #
        self.diccommands['INCREMENTAL'] = self.doINCREMENTALcmd
        # --- G3 --- #
        self.diccommands['G3'] = self.doG3cmd
        # --- G2 --- #
        self.diccommands['G2'] = self.doG2cmd
        # --- G92 --- #
        self.diccommands['G92'] = self.doG92cmd
        # --- DWELL --- #
        # --- F --- #
        # --- PSOCONTROL X --- #
        self.diccommands['PSOCONTROL']  = self.doPSOCONTROLcmd
        # --- FOR ... to ... --- #
        self.diccommands['FOR']  = self.doFORcmd
        # --- NEXT --- #
        self.diccommands['NEXT'] = self.doNEXTcmd

    def setLaserPosition(self, pos):
        self.position = pos

    def setLaserOrigin(self, orig):
        self.origin   = orig

    class STATUS_class():
        def __init__(self, position):
            self.X  = position[0]
            self.Y  = position[1]
            self.Z  = position[2]
        def updateStatusPosition(self, current_pos):
            self.X  = current_pos[0]
            self.Y  = current_pos[1]
            self.Z  = current_pos[2]

    def setSpecialCommand(self):
        #self.dicvariables['$_PositionCmdUnits'] = "str('Status_position')" # we add a symbol '$' to '_PositionCmdUnits', in order to be consistent with our declaration of global variable.
        global STATUS, _PositionCmdUnits
        STATUS = {'Status_position' : self.STATUS_class( self.position.copy() )}
        _PositionCmdUnits = 'Status_position'

    def resetInstructionDictionary(self):
        self.dicinstruction = {} #self.dicinstruction.clear()  will completely delete the dictionary, ie the attribute won't exist

    def resetWaveGuideDictionary(self):
        self.dicwaveguides  = {} #self.dicwaveguides.clear()  will completely delete the dictionary, ie the attribute won't exist

    def resetGCodeCommandDictionary(self):
        self.dicGcodecmd    = {}

    def doKeyExists(self, key):
        try:
            self.diccommands[key.upper()]
            return True
        except:
            return False

    def loadGCode(self, filename):
        self.txtGcode = open(filename,'r+').read()

    def breakdownTextCode(self):
        '''
        Split the string of the loaded GCode in lines, then each lines in words.
        '''
        # --- splitting the full text in lines and words --- #
        txtcode = self.txtGcode
        txtcodelines = txtcode.splitlines()
        N = len(txtcodelines)
        for i in range(N):
            txtcodelines_cleaned = self.cleanExpressionFromSpace(txtcodelines[i])
            self.dicGcodecmd[i]  = txtcodelines_cleaned.split()

    def removeSpaceFromString(self, string):
        '''
        Simple way of removing the spaces in a string: first split it wrt to the spaces,
        then recombine it without the spaces.
        '''
        str_int = string.split()
        str_fin = ''
        for char in str_int:
            str_fin += char
        return str_fin

    def cleanExpressionFromSpace(self, line_not_splitted):
        '''
        We want to remove the unnecessary space in a expression, ie between '(...)'.
        Indeed since we will breakdown each line wrt the spaces, it may happen that
        an expression will be cut in two words, thus rending it impossible to evaluate
        it, with our implementation.
        '''
        line = list(line_not_splitted)
        i    = 0
        while i < len(line):
            char = line[i]
            indx_bracket = 0
            if char == '(':
                indx_bracket +=1
                p = 0
                while indx_bracket > 0 and (i+p+1)<len(line):
                    p +=1
                    if   line[i+p]==' ':
                        charr = line.pop(i+p)
                        p -=1
                    elif line[i+p]=='(':
                        indx_bracket +=1
                    elif line[i+p]==')':
                        indx_bracket -=1
            i += 1
        # --- making back a string --- #
        line_out = ''
        for char in line:
            line_out += char
        # ---  --- #
        return line_out

    def readGCode(self):
        # --- reset dictionaries --- #
        self.resetGCodeCommandDictionary()
        self.resetInstructionDictionary()
        self.resetWaveGuideDictionary()
        # --- read code and make instructions  --- #
        self.breakdownTextCode()
        keys = list(self.dicGcodecmd.keys())
        N = len(keys)
        self.currentline_nbr = 0
        while self.currentline_nbr < N:
            line_nbr = self.currentline_nbr
            line     = self.dicGcodecmd[keys[line_nbr]]
            line     = self.cleanLineFromComment(line)
            if len(line)!=0:
                if self.isValueAssignement(line):
                    self.execValueAssignement(line)
                else:
                    word0 = line[0].upper()
                    if self.doKeyExists(word0):
                        self.currentline = [line , line_nbr]
                        word0 = word0.upper()
                        self.diccommands[word0]() # exec the method srocked in the dictionary
            #print(self.currentline_nbr)
            self.currentline_nbr += 1

    def declareVariables(self):
        self.dicvariables['$STATUS']['Status_position'].updateStatusPosition( self.position.copy() )
        for key in self.dicvariables:
            varname = key[1:] # indeed we get rid of the '$' symbol
            value   = self.dicvariables[key]
            exec( 'global '+varname )
            exec( varname+' = '+str(value) )
            print('global ', varname, eval(varname) )

    def cleanLineFromComment(self, line):
        '''
        Remove all the part of the line that is behind a comment character.
        Then return the line without any comment.
        '''
        ind_cmmt = 0
        for i in range(len(line)):
            word_i = line[i]
            if self.isComment(word_i):
                ind_cmmt = i
                return line[:i]
        return line

    def evaluate(self, str_to_eval):
        if type(str_to_eval) != type(''):
            print('Error: not a string in input.\nInput: {}'.format(str_to_eval))
            return None
        try:
            val = eval(str_to_eval)
            return val
        except:
            print('Error: the string to evaluate is not working.\nstring: {}'.format(str_to_eval))
            return None

    def isNumber(self, word):
        '''
        Test if word is a number
        '''
        try:
            nbr = eval(word)
            if type(nbr) == type(int(0)) or type(nbr) == type(float(0.)):
                return True
        except:
            return False

    def isStatusVariable(self, word):
        '''
        Test if the word is the Gcode command $STATUS[_PositionCmdUnits].X,Y,Z .
        '''
        n = len('$STATUS[_PositionCmdUnits]')
        if   len(word) < n:
            return False
        elif word[:n] == '$STATUS[_PositionCmdUnits]':
            return True
        else:
            return False

    def isVariable(self, word):
        '''
        Test if the word is a Gcode variable.
        '''
        if len(word)==0:
            return False
        elif word[0] == '$':
            if not self.isStatusVariable(word):
                return True
            else:
                return False

    def isExpression(self, word):
        '''
        Test if the word is an expression that must be evaluated.
        eg '($xInit/$depth)'
        '''
        if word[0] == '(':
            return True
        else:
            return False

    def isValueAssignement(self, line):
        '''
        Test if the line stand for assigning a value to a variable.
        Careful for the FOR loop, where their is a '=' symbole but the line itself,
        is not a simple value assignement.
        '''
        if self.doKeyExists(line[0]):
            return False
        for word in line:
            if word == '=':
                return True
            for char in word:
                if char=='=':
                    return True
        return False

    def isComment(self, word):
        if word[0] == "'":
            return True
        else:
            return False

    def evalWord(self, word):
        '''
        '''
        if   self.isVariable(word):
            return self.evalVariable(word)
        elif self.isStatusVariable(word):
            return self.evalStatusVariable(word)
        elif self.isExpression(word):
            return self.evalExpression(word)
        elif self.isNumber(word):
            return eval(word)
        elif self.isComment(word):
            return None
        else:
            print('Error: Could not evaluate the given word.\n{}'.format(word))
            return None

    def evalStatusVariable(self, stat_var):
        '''
        Evaluate the value associated to the status variable.
        Must differentiate retrieve the position of the laser, depending on which coordinate
        was called: '$STATUS[_PositionCmdUnits].X, or Y, or Z'.
        '''
        n = len('$STATUS[_PositionCmdUnits]')
        # --- discriminate the cases --- #
        if   stat_var == '$STATUS[_PositionCmdUnits].X':
            varval = self.position[0]
        elif stat_var == '$STATUS[_PositionCmdUnits].Y':
            varval = self.position[1]
        elif stat_var == '$STATUS[_PositionCmdUnits].Z':
            varval = self.position[2]
        # ---  --- #
        return varval

    def evalVariable(self, var):
        '''
        Evaluate the value associated to the variable.
        Must differentiate between simple variable: '$name', and array variable: '$name[..]'.
        '''
        # --- declare variables --- #
        self.setSpecialCommand()
        #STATUS = {'Status_position' : STATUS_class( self.position.copy() )}
        #_PositionCmdUnits = 'Status_position'
        for key in self.dicvariables:
            varname = key[1:] # indeed we get rid of the '$' symbol
            value   = self.dicvariables[key]
            exec( 'global '+varname )
            exec( varname+' = '+str(value) )
        # --- remove '$' in var --- #
        vareval = ''
        for char in var:
            if char != '$':
                vareval += char
        # ---  --- #
        varval = eval( vareval ) # indeed if array variable, we need to evaluate the index, so cannot use the dicvariable directly.
        return varval

    def evalExpression(self, word):
        '''
        After declaring variable, we built a full string of the expression to evaluate end remove
        the '$' symboles of the variables.
        However, the main issue is if there are spaces in the original expression, meaning it was
        broken down when splitting the line. Thus we need to reconstituate it. The main issue is to
        recover the relevent words in the line to build back the expression, when there are spaces.
        '''
        # --- declare variables --- #
        self.setSpecialCommand()
        #STATUS = {'Status_position' : STATUS_class( self.position.copy() )}
        #_PositionCmdUnits = 'Status_position'
        for key in self.dicvariables:
            varname = key[1:] # indeed we get rid of the '$' symbol
            value   = self.dicvariables[key]
            exec( 'global '+varname )
            exec( varname+' = '+str(value) )
            #print('global ',varname, value)
        # --- built the expression string to evaluate --- #
        exprss = ''
        for charac in word:
            if charac != '$':
                exprss += charac
        #print( 'Expression: ',exprss )
        value = eval( exprss )
        return value

    def execValueAssignement(self, line):
        '''
        We try to reconstruct the assignement of value with the '=' symbol.
        eg: $xInit = 2 + ($xZero - sin($theta))*3
            - First we declare all the variables
            - Then reconstruct the line in one string, to have the full expression.
            - Then remove the '$' so the variable can be interpreted by python in eval( )
            - Finally evaluate the string
        '''
        #self.declareVariables() # doesn't work :(
        # --- declare variables --- #
        self.setSpecialCommand()
        #STATUS = {'Status_position' : STATUS_class( self.position.copy() )}
        #_PositionCmdUnits = 'Status_position'
        for key in self.dicvariables:
            varname = key[1:] # indeed we get rid of the '$' symbol
            value   = self.dicvariables[key]
            exec( 'global '+varname )
            exec( varname+' = '+str(value) )
        # --- concatenate the string to evaluate --- #
        assgnmt = ''
        for word in line:
            assgnmt += word
        # --- remove '$' --- #
        assgnmt_new = ''
        for charac in assgnmt:
            if charac != '$':
                assgnmt_new += charac
        assgnmt = assgnmt_new
        # --- make assignement --- #
        #print('Assignement: ', assgnmt )
        exec( assgnmt )
        # --- reassigning all variables their new value --- #
        for key in self.dicvariables:
            varname = key[1:]
            self.dicvariables[key] = eval(varname)

    def makeNewWaveGuide(self):
        self.current_WG = []

    def storeWaveGuide(self):
        key_list = list(self.dicwaveguides.keys())
        n        = len(key_list)
        self.dicwaveguides[n+1] = self.current_WG

    def setSpeed(self, value):
        '''
        Function not implemented, yet.
        '''
        return None

################################################################################################
# CODE
################################################################################################
if __name__=='__main__':
    print('STARTING')
    Laser = LASERSimulated()
    Laser.loadGCode('Test1.txt')
    Laser.breakdownTextCode()
    Laser.readGCode()
    for key in Laser.dicinstruction:
        print(Laser.dicinstruction[key])
    print(len( list(Laser.dicinstruction.keys()) ))
    #print(Laser.dicvariables)
    print('FINNISHED')
