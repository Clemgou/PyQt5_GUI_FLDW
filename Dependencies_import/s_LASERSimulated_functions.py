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

################################################################################################
# FUNCTIONS
################################################################################################

def doDVARcmd(self):
    '''
    Retrieve the variables name and add them to the corresponding dictionary,
    self.dicvariables
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    for i in range(1,n):
        wordi = codeline[i]
        if wordi[0]=='$':
            # --- need to check if varibale is an array --- #
            if wordi[-1] == ']':
                p = 1
                finished = False
                while p < len(wordi) and not finished:
                    if wordi[-p] == '[':
                        finished = True
                    else:
                        p+=1
                varname = wordi[:-p]
                arraysize = self.evalWord(wordi[-p+1:-1]) #eval(wordi[-p+1:-1]) # should be a number
                varval  = [0]*arraysize # generate a list of zeros of size arrasize
                self.dicvariables[varname] = varval
            else:
                self.dicvariables[wordi] = 0 #None
        else:
            print('Error: Wrong variable declaration. Must begin with "$".\n{}'.format(wordi))
            return None

def doLINEARcmd(self):
    '''
    Make the LINEAR command.
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    pos_init   = self.position.copy()
    newpos_abs = self.position.copy()
    newpos_inc = np.array([0,0,0],dtype=float)
    for i in range(1,n):
        coord    = codeline[i]
        if   coord[0] == 'X':
            newpos_abs[0] = self.evalWord(coord[1:])
            newpos_inc[0] = self.evalWord(coord[1:])
        elif coord[0] == 'Y':
            newpos_abs[1] = self.evalWord(coord[1:])
            newpos_inc[1] = self.evalWord(coord[1:])
        elif coord[0] == 'Z':
            newpos_abs[2] = self.evalWord(coord[1:])
            newpos_inc[2] = self.evalWord(coord[1:])
        elif coord[0] == 'F':
            self.setSpeed( self.evalWord(coord[1:]) )
        elif coord[0] == "'":
            pass
        else:
            print('Error: wrong command in doLINEAR.\n{}'.format(coord[0]))
            return None
    # --- set coord argument w.r.t the coordinate mode --- #
    if   self.coordmode == 'ABSOLUTE':
        pos_fin = newpos_abs
    elif self.coordmode == 'INCREMENTAL':
        pos_fin = self.position.copy() + newpos_inc
    else:
        print('Error: wrong coordmode.\n{}'.format(self.coordmode))
        return None
    self.position = pos_fin
    # --- make arguments to pass to the associated LINEAR function --- #
    args = [pos_init+self.origin, self.position+self.origin, self.coordmode, self.isON]
    # --- add new instruction --- #
    N = len( list(self.dicinstruction.keys()) ) # current number of instructions
    self.dicinstruction[N+1] = ['LINEAR', args] # we add instruction after instruction, because we made the lecture of the gcode linear in the executio, ie not in parallel.
    # --- add coord to waveguide --- #
    if self.isON:
        self.current_WG.append(pos_init     +self.origin)
        self.current_WG.append(self.position+self.origin)

def doABSOLUTEcmd(self):
    self.coordmode = 'ABSOLUTE'

def doINCREMENTALcmd(self):
    self.coordmode = 'INCREMENTAL'

def doPSOCONTROLcmd(self):
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    command, gate, status = codeline[0], codeline[1], codeline[2] #PSOCONTROL X ON/OFF
    old_state = self.isON
    if status == 'ON':
        self.isON = True
    elif status == 'OFF':
        self.isON = False
    # --- checking if we changed the continuous writing --- #
    if self.isON == old_state: #we continue to add coordinate to the current waveguide
        pass
    else:
        if self.isON: #we begin to write a new waveguide
            self.makeNewWaveGuide()
        else:
            self.storeWaveGuide()

def doFORcmd(self):
    '''
    The FOR command will be very simple:
        - we first set the initial value of the iteration variable
        - we retrieve the final value, ie the limit
    Then the idea is the we assign the line_nbr to the loop FOR, and as long as the iteration
    variable has not attained the limit, we return to that line at every NEXT command.
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- breakdown FOR command line --- #
    ind_FOR = 0
    ind_TO  = 0
    for i in range(n):
        if codeline[i].upper() == 'TO':
            ind_TO = i
    # --- set initial incremental value --- #
    line_assgnmt = codeline[ind_FOR+1:ind_TO]
    self.execValueAssignement( line_assgnmt )
    # --- retrieve boundary --- #
    exprss = ''
    for word in codeline[ind_TO+1:]:
        exprss += word
    limit_val = self.evalWord(exprss)#self.evalExpression(exprss)
    # --- retrieve the iteration variable name --- #
    var_exprss = codeline[ind_FOR+1]
    iter_varname = var_exprss # here we assume that the iteration variable is separated from the '=' symbol, as in: '$ii = 0'.
    for i in range(len(var_exprss)): # but if not we need the 'cut it out', as in: '$ii=0'.
        if var_exprss[i]=='=':
            iter_varname = var_exprss[:i]
    # --- Set the dictionary for the loop FOR --- #
    current_value = self.dicvariables[iter_varname]
    FOR_line_nbr  = line_nbr
    final_value   = limit_val
    self.dicforloop[iter_varname] = [FOR_line_nbr, current_value, final_value]
    return None

def doNEXTcmd(self):
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- retrieve the iteration variable --- #
    iter_varname = codeline[1]
    # --- check if we are done with the FOR loop --- #
    final_val = self.dicforloop[iter_varname][2]
    iter_varval = self.dicvariables[iter_varname]
    if iter_varval == final_val:
        return None
    # --- increment the variable --- #
    ligne_assgnmt = [iter_varname, '+=1']
    self.execValueAssignement(ligne_assgnmt)
    self.dicforloop[iter_varname][1] = self.dicvariables[iter_varname] # we update the for loop dictionary
    # --- got to associated FOR lign --- #
    self.currentline_nbr = self.dicforloop[iter_varname][0]
    # ---  --- #
    #print('NEXT: ',iter_varname, iter_varval)
    return None

def G2G3Converter(self):
    '''
    This method convert any type of G2 or G3 into the output of the 'PQR' method.
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- make method variable --- #
    method = ''
    # --- retrieve all possible parameters  --- #
    for word in codeline:
        if   word[0].upper() == 'P':
            start_ang = self.evalWord(word[1:])
            method   += 'P'
        elif word[0].upper() == 'Q':
            end_ang   = self.evalWord(word[1:])
            method   += 'Q'
        elif word[0].upper() == 'R':
            R         = self.evalWord(word[1:])
            method   += 'R'
            R         = abs(R)
        elif word[0].upper() == 'X':
            end_point_x = self.evalWord(word[1:])
            method   += 'X'
        elif word[0].upper() == 'Y':
            end_point_y = self.evalWord(word[1:])
            method   += 'Y'
        elif word[0].upper() == 'I':
            center_point_i = self.evalWord(word[1:])
            method   += 'I'
        elif word[0].upper() == 'J':
            center_point_j = self.evalWord(word[1:])
            method   += 'J'
    # --- action according to method --- #
    current_pos = self.position.copy()
    if   method == 'PQR':
        R         = R
        start_ang = start_ang
        end_ang   = end_ang
    elif method == 'XYIJ':
        vect_init = np.array([current_pos[0]-center_point_i , current_pos[1]-center_point_j])
        vect_fina = np.array([end_point_x   -center_point_i , end_point_y   -center_point_j])
        R = np.sqrt( vect_init[0]**2 + vect_init[1]**2 )
        start_ang = np.angle(vect_init[0] + 1j*vect_init[1]) * 180/np.pi
        end_ang   = np.angle(vect_fina[0] + 1j*vect_fina[1]) * 180/np.pi
    elif method == 'XYR':
        vect_tot  = np.array([current_pos[0]-end_point_x , current_pos[1]-end_point_y])
        vect_norm = np.sum(vect_tot**2)**0.5
        vec_dir   = vect_tot/vect_tot_norm
        vec_ortho = np.array([ vec_dir[1] , -vec_dir[0] ])
        middle_pos= np.array([current_pos[0]+end_point_x , current_pos[1]+end_point_y]) * 0.5
        h         = 0.5 * np.sqrt( 4*R**2 - vect_tot_norm**2 )
        center_point = middle_pos + h*middle_pos
        vect_init = current_pos - center_point
        vect_fina = np.array([end_point_x, end_point_y]) - center_point
        R         = R
        start_ang = np.angle(vect_init[0] + 1j*vect_init[1]) * 180/np.pi
        end_ang   = np.angle(vect_fina[0] + 1j*vect_fina[1]) * 180/np.pi
    elif method == 'QIJ':
        vect_init = np.array([current_pos[0]-center_point_i , current_pos[1]-center_point_j])
        R = np.sqrt( vect_init[0]**2 + vect_init[1]**2 )
        start_ang = np.angle(vect_init[0] + 1j*vect_init[1]) * 180/np.pi
        end_ang   = end_ang
    else:
        print('Error: with method of G2, G3.\nOne might have forgotten or written something wrong.\nHere the method: {}'.format(method))
        print('Codeline where is the error: ',codeline)
        return None
    # --- returning staring, ending angles and radius --- #
    return R, start_ang, end_ang

def doG2cmd(self):
    '''
    G2: CW (clockwise) circular interpolation on coordinate system 1
    clockwise = counter-trogonometric
    Here we only implement the:
        G2 P.. Q.. R..
    where P in the begining angle, ang Q the final one in a circle of radius R that has starting point
    the position we are in.
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- retrieve starting and ending angles, radius  --- #
    R_angl = self.G2G3Converter()
    if R_angl == None:
        return None
    else:
        R, start_ang, end_ang = R_angl
    # --- make arguments --- #
    theta_start = start_ang *np.pi/180. # the command G2 recieve deg unity # since it is counter-clockwise
    theta_end   = end_ang   *np.pi/180.
    Theta    = theta_start - theta_end
    pos_init = self.position.copy() # + np.array([R*np.sin(Theta), R*(1-np.cos(Theta)), 0])
    args     = [pos_init+self.origin, theta_start, theta_end, R, self.coordmode, self.isON] 
    # --- add new instruction --- #
    N = len( list(self.dicinstruction.keys()) ) # current number of instructions
    self.dicinstruction[N+1] = ['G2', args] # we add instruction after instruction, because we made the lecture of the gcode linear in the executio, ie not in parallel.
    # --- update current position --- #
    displacement  = np.array([R*np.cos(theta_end), R*np.sin(theta_end), 0]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0])
    self.position = self.position.copy() + displacement
    # --- add coord to waveguide --- #
    if self.isON:
        dx = 0.1
        L  = 2*R*Theta
        N  = int(np.max([L/dx, 10]))
        if   theta_start < theta_end: # careful we are clockwise !
            theta_var = np.linspace(theta_start+2*np.pi, theta_end, N)
        elif theta_start >= theta_end:
            theta_var = np.linspace(theta_start, theta_end, N)
        x  = R*np.cos(theta_var)
        y  = R*np.sin(theta_var)
        for i in range(N):
            self.current_WG.append( pos_init+self.origin + np.array([x[i], y[i], 0.]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0]))

def doG3cmd(self):
    '''
    G3: CCW (counter-clockwise) circular interpolation on coordinate system 1
    counter-clockwise = trogonometric
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- retrieve starting and ending angles, radius  --- #
    R_angl = self.G2G3Converter()
    if R_angl == None:
        return None
    else:
        R, start_ang, end_ang = R_angl
    # --- make arguments --- #
    theta_start = start_ang *np.pi/180. # the command G2 recieve deg unity # since it is counter-clockwise
    theta_end   = end_ang   *np.pi/180.
    Theta    = theta_end - theta_start
    pos_init = self.position.copy()
    args     = [pos_init+self.origin, theta_start, theta_end, R, self.coordmode, self.isON] 
    # --- add new instruction --- #
    N = len( list(self.dicinstruction.keys()) ) # current number of instructions
    self.dicinstruction[N+1] = ['G3', args] # we add instruction after instruction, because we made the lecture of the gcode linear in the executio, ie not in parallel.
    # --- update current position --- #
    displacement  = np.array([R*np.cos(theta_end), R*np.sin(theta_end), 0]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0])
    self.position = self.position.copy() + displacement
    # --- add coord to waveguide --- #
    if self.isON:
        dx = 0.1
        L  = 2*R*Theta
        N  = int(np.max([L/dx, 10]))
        if   theta_start <= theta_end: # careful we are counter-clockwise !
            theta_var = np.linspace(theta_start, theta_end, N)
        elif theta_start >  theta_end:
            theta_var = np.linspace(theta_start, theta_end+2*np.pi, N)
        x  = R*np.cos(theta_var)
        y  = R*np.sin(theta_var)
        for i in range(N):
            self.current_WG.append( pos_init+self.origin + np.array([x[i], y[i], 0.]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0]))

def doG92cmd(self):
    '''
    Make the G92 command, ie change the origin reference of the laser.
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    new_origin = self.origin.copy()
    for i in range(1,n):
        coord    = codeline[i]
        if   coord[0] == 'X':
            new_origin[0] = -self.evalWord(coord[1:]) + self.position[0] + self.origin[0]
        elif coord[0] == 'Y':
            new_origin[1] = -self.evalWord(coord[1:]) + self.position[1] + self.origin[1]
        elif coord[0] == 'Z':
            new_origin[2] = -self.evalWord(coord[1:]) + self.position[2] + self.origin[2]
        else:
            print('Error: wrong command in doLINEAR.\n{}'.format(coord[0]))
            return None
    # --- set coord argument w.r.t the coordinate mode --- #
    self.setLaserPosition( self.position + self.origin - new_origin )
    self.setLaserOrigin( new_origin )

################################

def doG2cmd_old(self):
    '''
    G2: CW (clockwise) circular interpolation on coordinate system 1
    clockwise = counter-trogonometric
    Here we only implement the:
        G2 P.. Q.. R..
    where P in the begining angle, ang Q the final one in a circle of radius R that has starting point
    the position we are in.
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- retrieve starting and ending angles, radius  --- #
    for word in codeline:
        if   word[0].upper() == 'P':
            start_ang = self.evalWord(word[1:])
        elif word[0].upper() == 'Q':
            end_ang   = self.evalWord(word[1:])
        elif word[0].upper() == 'R':
            R         = self.evalWord(word[1:])
            R         = abs(R)
    # --- make arguments --- #
    theta_start = start_ang *np.pi/180. # the command G2 recieve deg unity # since it is counter-clockwise
    theta_end   = end_ang   *np.pi/180.
    Theta    = theta_start - theta_end
    pos_init = self.position.copy() # + np.array([R*np.sin(Theta), R*(1-np.cos(Theta)), 0])
    args     = [pos_init+self.origin, theta_start, theta_end, R, self.coordmode, self.isON] 
    # --- add new instruction --- #
    N = len( list(self.dicinstruction.keys()) ) # current number of instructions
    self.dicinstruction[N+1] = ['G2', args] # we add instruction after instruction, because we made the lecture of the gcode linear in the executio, ie not in parallel.
    # --- update current position --- #
    displacement  = np.array([R*np.cos(theta_end), R*np.sin(theta_end), 0]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0])
    self.position = self.position.copy() + displacement
    # --- add coord to waveguide --- #
    if self.isON:
        dx = 0.1
        L  = 2*R*Theta
        N  = int(np.max([L/dx, 10]))
        if   theta_start < theta_end: # careful we are clockwise !
            theta_var = np.linspace(theta_start+2*np.pi, theta_end, N)
        elif theta_start >= theta_end:
            theta_var = np.linspace(theta_start, theta_end, N)
        x  = R*np.cos(theta_var)
        y  = R*np.sin(theta_var)
        for i in range(N):
            self.current_WG.append( pos_init+self.origin + np.array([x[i], y[i], 0.]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0]))

def doG3cmd_old(self):
    '''
    G3: CCW (counter-clockwise) circular interpolation on coordinate system 1
    counter-clockwise = trogonometric
    '''
    line, line_nbr = self.currentline
    codeline = self.dicGcodecmd[line_nbr]
    n = len(codeline)
    # --- retrieve starting and ending angles, radius  --- #
    for word in codeline:
        if   word[0].upper() == 'P':
            start_ang = self.evalWord(word[1:])
        elif word[0].upper() == 'Q':
            end_ang   = self.evalWord(word[1:])
        elif word[0].upper() == 'R':
            R         = self.evalWord(word[1:])
            R         = abs(R)
    # --- make arguments --- #
    theta_start = start_ang *np.pi/180. # the command G2 recieve deg unity # since it is counter-clockwise
    theta_end   = end_ang   *np.pi/180.
    Theta    = theta_end - theta_start
    pos_init = self.position.copy()
    args     = [pos_init+self.origin, theta_start, theta_end, R, self.coordmode, self.isON] 
    # --- add new instruction --- #
    N = len( list(self.dicinstruction.keys()) ) # current number of instructions
    self.dicinstruction[N+1] = ['G3', args] # we add instruction after instruction, because we made the lecture of the gcode linear in the executio, ie not in parallel.
    # --- update current position --- #
    displacement  = np.array([R*np.cos(theta_end), R*np.sin(theta_end), 0]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0])
    self.position = self.position.copy() + displacement
    # --- add coord to waveguide --- #
    if self.isON:
        dx = 0.1
        L  = 2*R*Theta
        N  = int(np.max([L/dx, 10]))
        if   theta_start <= theta_end: # careful we are counter-clockwise !
            theta_var = np.linspace(theta_start, theta_end, N)
        elif theta_start >  theta_end:
            theta_var = np.linspace(theta_start, theta_end+2*np.pi, N)
        x  = R*np.cos(theta_var)
        y  = R*np.sin(theta_var)
        for i in range(N):
            self.current_WG.append( pos_init+self.origin + np.array([x[i], y[i], 0.]) - np.array([R*np.cos(theta_start), R*np.sin(theta_start), 0]))
