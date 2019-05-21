#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATIONS
################################################################################################

import numpy as np

################################################################################################
# FUNCTIONS
################################################################################################

def varDefinition(self):
        '''
        Write the definition of the variable in the txtfile.
        Each sublist will be treated as a group written after the same 'DVAR '.
        - Uses the self.groupvarname, self.dicvariable dictionaries
        '''
        header  = self.setHeader("'Variable definition")
        coretxt = ''
        coretxt += header
        # --- writing the variable declaration --- #
        for grpname in self.groupvarname:
            coretxt += "\nDVAR "
            for varname in self.groupvarname[grpname]:
                if self.doesKeyExist(varname):
                    parameter = self.dicvariable[varname] # to test if the varname has not been cleaned.
                    if type(parameter.value) == type(int(1)) or type(parameter.value) == type(float(1)):
                        coretxt += "${} ".format(varname)
                    elif type(parameter.value) == type([]) or type(parameter.value) == type(np.array([1])):
                        arrayval = parameter.value
                        coretxt += "${}[{}] ".format(varname, (len(arrayval)//5+1)*5) # we want to preset the size of the var array, with extra space. Here we choose at least 5 more.
                    else:
                        print('Error: The parameter is in an unknown format')
                        return None
                    if parameter.type == 'loop':
                        coretxt += "{} ".format(parameter.loopvar)
        coretxt += '\nDVAR $ss' # we define the arbitrary chosen loop variable of the scanNbr loop.
        # --- ending: we let some space --- #
        coretxt += "\n\n\n"
        return coretxt

# ------------------------------------------------------ #

def paramDefinition(self):
        '''
        Write the part of the code where we set the variable.
        The varlist should contain the name and the value of the variables.
        '''
        header  = self.setHeader("'Parameters")
        coretxt = ''
        coretxt += header
        # --- writing variables --- #
        for grpname in self.groupvarname:
            coretxt += "\n"
            for varname in self.groupvarname[grpname]:
                if self.doesKeyExist(varname):
                    parameter = self.dicvariable[varname]
                    if type(parameter.value) == type([]) or type(parameter.value) == type(np.array([])):
                        for k in range(len(parameter.value)):
                            braket = "[{:d}]".format(int(k))
                            coretxt += "${0:12} = {1}\n".format(parameter.name+braket, parameter.value[k])
                    else:
                        coretxt += "${0:12} = {1}\n".format(parameter.name, parameter.value)
        # --- ending --- #
        coretxt += "\n\n\n"
        return coretxt

# ------------------------------------------------------ #

def initializeLaserWriting(self):
        '''
        Write the first command that initialize the laser and sets it to the origin.
        '''
        coretxt = ''
        header  = self.setHeader("'Fabrication: Laser Line 1")
        coretxt += header
        # ---  --- #
        coretxt += "\n'~~~~ Initialisation ~~~~'\n"
        coretxt += "ENABLE X Y Z\nMETRIC\nSECONDS\nWAIT MODE NOWAIT\nVELOCITY ON\nPSOCONTROL X RESET\nPSOCONTROL X OFF\n"
        coretxt += "F5\nG18\nABSOLUTE\nLINEAR Z0 X$xInit\nDWELL 0.5\n"
        coretxt += "\n"
        return coretxt

# ------------------------------------------------------ #

def scanSWG(self):
        '''
        Generate the string of one scan, ie the smallest loop in the command file.
        This is the smallest loop in the G-code, and needs to know if we iterated on the speed.
        '''
        scanStr = ''
        # --- condition on the speed varaible --- #
        if self.doesKeyExist('speed'):
            speed = self.dicvariable['speed'].value
        else:
            print('Error: The writing speed has not been specified')
            return None
        if type(speed) == type([]) or type(speed) == type(np.array([])):
            scanStr = scanStr + 'F$speed[{}]\n'.format( str(self.dicvariable['numSpeed'].loopvar) )
        else:
            scanStr = scanStr + 'F$speed\n'
        # ---  --- #
        scanStr = scanStr +\
        '\nPSOCONTROL X ON\n'+\
        'DWELL 0.5\n'+\
        'LINEAR X$xEnd\n'+\
        'PSOCONTROL X OFF\n'+\
        'DWELL 0.5\n\n'+\
        'F20\n'+\
        'LINEAR X$xInit\n'+\
        'DWELL 0.5\n'
        if self.doesKeyExist('distScan'):
            distScan = self.dicvariable['distScan']
            if distScan.value != 0.: # it seems redondant, but to facilitate in case we want to implement a choice on the name of all the parameters
                scanStr = scanStr +\
                'INCREMENTAL\n'+\
                'F0.001\n'+\
                'LINEAR Y${}\n'.format(distScan.name)+\
                'ABSOLUTE\n'+\
                'DWELL 0.5\n'
        return scanStr

# ------------------------------------------------------ #

def loopFunctionSWG(self):
        '''
        - Write all the loop needed for the writing. Moreover, skeep the unecessary loop,
        ie if there is only one increment, we don't write the loop.
        - The loopvarnamelist is the list of all the loops and their associated incremental
        variable (eg '$ii','$jj',...). Careful ! The loopvarnamelist is ordered by priority !
        - Thus in the script, the loop will be written by decreasing order of priority.
        '''
        coretxt = ''
        coretxt += "'~~~~ Loops ~~~~'\n"
        nbspace = 4
        loopStr = ''
        # --- set loop scan --- #
        scanStr = self.scanSWG()
        loopStr = scanStr
        if self.doesKeyExist('numScanNbr'): # try if numScanNbr has not been cleaned
            numScanNbr = self.dicvariable['numScanNbr']
            if numScanNbr.value > 1:
                loopStr = self.indentBlockString( loopStr, nbspace)
                loopStr = ("FOR {0}=0 to ($scanNbr[{1}]-1)\n"+loopStr+"\nNEXT {0}\n").format('$ss' , str(self.dicvariable['numScanNbr'].loopvar)) # arbitrary chosen loop variable: $ss (s for scan).
                loopStr += "F0.5\nINCREMENTAL\nLINEAR Y$distSucc\nABSOLUTE\nDWELL 0.5\n"
                if self.doesKeyExist('distScan'):
                    loopStr += ("F0.5\nINCREMENTAL\nLINEAR Y(-($scanNbr[{0}]-1)*$distScan)\nABSOLUTE\nDWELL 0.5\n").format(str(self.dicvariable['numScanNbr'].loopvar)) # move to next waveguide accounting for the 'width' due to the scan distance.
                loopStr = self.indentBlockString( loopStr, nbspace)
                loopStr = ("FOR {0}=0 to ($numScanNbr-1)\n"+loopStr+"\nNEXT {0}\n").format(str(self.dicvariable['numScanNbr'].loopvar))
            else:
                loopStr = self.indentBlockString( loopStr, nbspace)
                loopStr = ("FOR {0}=0 to ($scanNbr-1)\n"+loopStr+"\nNEXT {0}\n").format(self.loopindexlist[-1]) #the newline before NEXT... is to avoid auto-indentation, don't know how to disable it.
                loopStr += "F0.5\nINCREMENTAL\nLINEAR Y$distSucc\nABSOLUTE\nDWELL 0.5\n" # move to next waveguide accounting for the 'width' due to the scan distance.
                if self.doesKeyExist('distScan'):
                    loopStr += "F0.5\nINCREMENTAL\nLINEAR Y(-($scanNbr-1)*$distScan)\nABSOLUTE\nDWELL 0.5\n" # move to next waveguide accounting for the 'width' due to the scan distance.
        else:
            loopStr = self.indentBlockString( loopStr, nbspace)
            loopStr = ("FOR {0}=0 to ($scanNbr-1)\n"+loopStr+"\nNEXT {0}\n").format('$ss') #the newline before NEXT... is to avoid auto-indentation, don't know how to disable it.
            loopStr += "F0.5\nINCREMENTAL\nLINEAR Y$distSucc\nABSOLUTE\nDWELL 0.5\n" # move to next waveguide accounting for the 'width' due to the scan distance.
            if self.doesKeyExist('distScan'):
                loopStr += "F0.5\nINCREMENTAL\nLINEAR Y(-($scanNbr-1)*$distScan)\nABSOLUTE\nDWELL 0.5\n" # move to next waveguide accounting for the 'width' due to the scan distance.
        # --- set other loops --- #
        listpriority = self.sortPriorityLoop()
        self.isdepthset = False
        for loopvarkey in listpriority:
            if loopvarkey == 'numScanNbr': pass
            else:
                if self.doesKeyExist(loopvarkey): # try if numLoopvar has not been cleaned
                    loopparam = self.dicvariable[loopvarkey]
                    if loopparam.value > 1:
                        loopStr = self.indentBlockString( loopStr, nbspace)
                        if loopparam.name == 'numDepth':
                            setdpeth = 'F0.3\nLINEAR Z($depth[{0}]/$indRefr)\nDWELL 0.5\n\n'.format(str(self.dicvariable['numDepth'].loopvar))
                            loopStr = setdpeth + loopStr
                            self.isdepthset = True
                        loopStr = ("FOR {0}=0 to (${1}-1)\n"+loopStr+"\nNEXT {0}\n").format(loopparam.loopvar, loopparam.name)
        if not self.isdepthset:
            setdpeth = 'F0.3\nLINEAR Z($depth/$indRefr)\nDWELL 0.5\n\n'
            loopStr = setdpeth + loopStr
        # --- ending --- #
        coretxt += loopStr
        return coretxt

# ------------------------------------------------------ #

def scanBWG(self):
        '''
        Generate the string of one scan, ie the smallest loop in the command file.
        This is the smallest loop in the G-code, and needs to know if we iterated on the speed.
        '''
        scanStr = ''
        # --- setting angle variables --- #
        if self.doesKeyExist('radius'):
            radius = self.dicvariable['radius'].value
        else:
            print('Error: The radius of the Bend-Waveguides has not been specified')
            return None
        if type(radius) == type([]) or type(radius) == type(np.array([])):
            scanStr += '$theta = $length/(2*$radius[{}])\n'.format( str(self.dicvariable['numRadius'].loopvar) )
        else:
            scanStr += '$theta = $length/(2*$radius)\n'
        scanStr += '$thetaDeg = (180/$Pi)*$theta\n'
        # --- condition on the speed varaible --- #
        if self.doesKeyExist('speed'):
            speed = self.dicvariable['speed'].value
        else:
            print('Error: The writing speed has not been specified')
            return None
        if type(speed) == type([]) or type(speed) == type(np.array([])):
            scanStr = scanStr + 'F$speed[{}]\n'.format( str(self.dicvariable['numSpeed'].loopvar) )
        else:
            scanStr = scanStr + 'F$speed\n'
        # ---  --- #
        scanStr += '\nPSOCONTROL X ON\n'+\
        'DWELL 0.5\n'
        if type(radius) == type([]) or type(radius) == type(np.array([])):
            scanStr += 'LINEAR X($xCenter-$radius[{}]*SIN($theta))\n'.format( str(self.dicvariable['numRadius'].loopvar) )
            scanStr += 'G17\n'
            scanStr += 'G3 P(270) Q(270+$thetaDeg) R$radius[{}]\n'.format( str(self.dicvariable['numRadius'].loopvar) )
            scanStr += 'G2 P(90+$thetaDeg) Q(90) R$radius[{}]\n'.format( str(self.dicvariable['numRadius'].loopvar) )
        else:
            scanStr += 'LINEAR X($xCenter-$radius*SIN($theta))\n'
            scanStr += 'G17\n'
            scanStr += 'G3 P(270) Q(270+$thetaDeg) R$radius\n'
            scanStr += 'G2 P(90+$thetaDeg) Q(90) R$radius\n'
        scanStr += 'LINEAR X$xEnd\n'+\
        'PSOCONTROL X OFF\n'+\
        'DWELL 0.5\n\n'+\
        'ABSOLUTE\n'+\
        'F20\n'+\
        'LINEAR X$xInit Y$yInit\n'+\
        'DWELL 0.5\n\n'
        if self.doesKeyExist('distScan'):
            distScan = self.dicvariable['distScan']
            if distScan.value != 0.: # it seems redondant, but to facilitate in case we want to implement a choice on the name of all the parameters
                scanStr += 'INCREMENTAL\n'+\
                'F0.001\n'+\
                'LINEAR Y${}\n'.format(distScan.name)+\
                'ABSOLUTE\n'+\
                'DWELL 0.5\n'
        return scanStr

# ------------------------------------------------------ #

def loopFunctionBWG(self):
        '''
        - Write all the loop needed for the writing. Moreover, skeep the unecessary loop,
        ie if there is only one increment, we don't write the loop.
        - The loopvarnamelist is the list of all the loops and their associated incremental
        variable (eg '$ii','$jj',...). Careful ! The loopvarnamelist is ordered by priority !
        - Thus in the script, the loop will be written by decreasing order of priority.
        '''
        coretxt = ''
        coretxt += "'~~~~ Loops ~~~~'\n"
        coretxt += 'LINEAR Z0 X$xInit Y$yInit\n'
        nbspace = 4
        loopStr = ''
        # --- set loop scan --- #
        scanStr = self.scanBWG()
        loopStr = scanStr
        if self.doesKeyExist('numScanNbr'): # try if numScanNbr has not been cleaned
            numScanNbr = self.dicvariable['numScanNbr']
            if numScanNbr.value > 1:
                loopStr = self.indentBlockString( loopStr, nbspace)
                loopStr = ("FOR {0}=0 to ($scanNbr[{1}]-1)\n"+loopStr+"\nNEXT {0}\n").format('$ss' , str(self.dicvariable['numScanNbr'].loopvar)) # arbitrary chosen loop variable: $ss (s for scan).
                loopStr += 'DWELL 0.5\nABSOLUTE\nF20\nLINEAR Y$yInit\n$yInit = $yInit+$distSucc\nLINEAR Y$yInit\nABSOLUTE\nDWELL 0.5\n'
                loopStr = self.indentBlockString( loopStr, nbspace)
                loopStr = ("FOR {0}=0 to ($numScanNbr-1)\n"+loopStr+"\nNEXT {0}\n").format(str(self.dicvariable['numScanNbr'].loopvar))
            else:
                loopStr = self.indentBlockString( loopStr, nbspace)
                loopStr = ("FOR {0}=0 to ($scanNbr-1)\n"+loopStr+"\nNEXT {0}\n").format(self.loopindexlist[-1]) #the newline before NEXT... is to avoid auto-indentation, don't know how to disable it.
                loopStr += 'DWELL 0.5\nABSOLUTE\nF20\nLINEAR Y$yInit\n$yInit = $yInit+$distSucc\nLINEAR Y$yInit\nABSOLUTE\nDWELL 0.5\n'
                if self.doesKeyExist('distScan'):
                    loopStr += "F0.5\nINCREMENTAL\nLINEAR Y(-($scanNbr-1)*$distScan)\nABSOLUTE\nDWELL 0.5\n" # move to next waveguide accounting for the 'width' due to the scan distance.
        else:
            loopStr = self.indentBlockString( loopStr, nbspace)
            loopStr = ("FOR {0}=0 to ($scanNbr-1)\n"+loopStr+"\nNEXT {0}\n").format('$ss') #the newline before NEXT... is to avoid auto-indentation, don't know how to disable it.
            loopStr += 'DWELL 0.5\nABSOLUTE\nF20\nLINEAR Y$yInit\n$yInit = $yInit+$distSucc\nLINEAR Y$yInit\nABSOLUTE\nDWELL 0.5\n'
        # --- set other loops --- #
        listpriority = self.sortPriorityLoop()
        self.isdepthset = False
        for loopvarkey in listpriority:
            if loopvarkey == 'numScanNbr': pass
            elif self.doesKeyExist(loopvarkey): # try if numLoopvar has not been cleaned
                loopparam = self.dicvariable[loopvarkey]
                if loopparam.value > 1:
                    loopStr = self.indentBlockString( loopStr, nbspace)
                    if loopparam.name == 'numDepth':
                        setdpeth = 'F0.3\nLINEAR Z($depth[{0}]/$indRefr)\nDWELL 0.5\n\n'.format(str(self.dicvariable['numDepth'].loopvar))
                        loopStr = setdpeth + loopStr
                        self.isdepthset = True
                    loopStr = ("FOR {0}=0 to (${1}-1)\n"+loopStr+"\nNEXT {0}\n").format(loopparam.loopvar, loopparam.name)
        if not self.isdepthset:
            setdpeth = 'F0.3\nLINEAR Z($depth/$indRefr)\nDWELL 0.5\n\n'
            loopStr = setdpeth + loopStr
        # --- ending --- #
        coretxt += loopStr
        return coretxt

# ------------------------------------------------------ #

def endOfScript(self):
        '''
        Write the end of the script such as the laser is in a position ready to
        begin another writing.
        '''
        coretxt  = ''
        coretxt += "\n'~~~~ Finishing and Initialisation for next writting ~~~~'\n"
        coretxt += "PSOCONTROL X OFF\nDWELL 0.5\nF5\nLINEAR Z0 X$xInit\nDWELL 0.5\nINCREMENTAL\n"
        if self.doesKeyExist('distSucc'):
            coretxt += "LINEAR Y($distNewfab-$distSucc)\n"
        else:
            coretxt += "LINEAR Y$distNewfab\n"
        coretxt += "ABSOLUTE\nDWELL 0.5\n"
        return coretxt

# ------------------------------------------------------ #

def setHeader(self, name):
        if type(name) != type(''):
            print('Error: Wrong format for name header')
            return None
        coretxt = self.headerline+name+"\n"+self.headerline
        return coretxt

# ------------------------------------------------------ #

def cmdLINEAR(self,X=None,Y=None):
	'''
	Returns the string sequence of the gcode that take as float, int, value X,Y.
	'''
	if   X!=None and Y==None:
		gcodetxt = 'LINEAR X{}\n'.format(X)
	elif X==None and Y==None:
		gcodetxt = 'LINEAR Y{}\n'.format(Y)
	elif X!=None and Y!=None:
		gcodetxt = 'LINEAR X{0} Y{1}\n'.format(X,Y)
	else:
		return ''
	return gcodetxt

# ------------------------------------------------------ #

def cmdG2(self,P,Q,R):
	'''
	Returns the string sequence of the gcode that take as float, int, value X,Y.
	'''
	gcodetxt  = ''
	gcodetxt += 'G2 P{0} Q{1} R{2:.6f}\n'.format(P,Q,float(R))
	return gcodetxt

# ------------------------------------------------------ #

def cmdG3(self,P,Q,R):
	'''
	Returns the string sequence of the gcode that take as float, int, value X,Y.
	'''
	gcodetxt  = ''
	gcodetxt += 'G3 P{0} Q{1} R{2:.6f}\n'.format(P,Q,float(R))
	return gcodetxt

# ------------------------------------------------------ #

def cmdSetDepthValue(self,depth, indRefr):
	'''
	Returns the string sequence of the gcode that take as float value depth, indRefr.
	'''
	gcodetxt = 'F0.3\nLINEAR Z{:.3}\nDWELL 0.5\n'.format(float(depth/indRefr))
	return gcodetxt

# ------------------------------------------------------ #

def cmdSetDepthVariable(self,depth='depth', indRefr='indRefr'):
	'''
	Returns the string sequence of the gcode that take as string value depth, indRefr.
	'''
	gcodetxt = 'F0.3\nLINEAR Z(${0}/${1})\nDWELL 0.5\n'.format(depth, indRefr)
	return gcodetxt

# ------------------------------------------------------ #

def cmdSetSpeedValue(self,speed):
	'''
	Returns the string sequence of the gcode that take as string value depth, indRefr.
	'''
	gcodetxt = 'F{:.2}\n'.format(speed)
	return gcodetxt

# ------------------------------------------------------ #

def cmdSetSpeedVariable(self,speed='speed'):
	'''
	Returns the string sequence of the gcode that take as string value depth, indRefr.
	'''
	gcodetxt = 'F${}\n'.format(speed)
	return gcodetxt

# ------------------------------------------------------ #

def cmdSTART(self):
	gcodetxt = 'PSOCONTROL X ON\nDWELL 0.1\n'
	return gcodetxt

# ------------------------------------------------------ #

def cmdSTOP(self):
	gcodetxt = 'PSOCONTROL X OFF\n\nDWELL 0.1\n'
	return gcodetxt

# ------------------------------------------------------ #

def cmdDWELL(self, time):
	gcodetxt = 'DWELL {:.2}\n'.format(time)
	return gcodetxt

# ------------------------------------------------------ #

def cmdINCREMENTAL(self):
	gcodetxt = 'INCREMENTAL\n'
	return gcodetxt

# ------------------------------------------------------ #

def cmdABSOLUTE(self):
	gcodetxt = 'ABSOLUTE\n'
	return gcodetxt


################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print('STARTING')
