#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATION
################################################################################################

import sys
import PyQt5
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QBoxLayout
from PyQt5.QtGui     import QVector3D
from PyQt5.QtCore    import Qt

import pyqtgraph        as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt                    import QtCore, QtGui
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem


import numpy as np

################################################################################################
# FUNCTION
################################################################################################

class SimulationDesign():
    '''
    Class that allow to visualise the final design of the G-code for FLDW.
    It draw the design in a similar way that the G-code works, with a set of instruction.
    We will proceed by:
        1 - Make a GLViewWidget, where everything is displayed
        2 - Instructions that will return items or modify ones (eg magnification method,... )
        3 - Method that will build a dictionary of items to draw
        4 - Draw every items at once
    Moreover we want the SimulationDesign object to be cross plateform, ie that it can be shared
    beteween objects and all addons we will be displayed.
    '''
    def __init__(self):
        pg.mkQApp()
        self.view            = gl.GLViewWidget()
        self.drawingitems    = {}
        self.dicaxisorientation = {}
        # --- main attributes --- #
        self.sizeview      = 30.
        self.origin        = np.array([0., 0., 0.])
        self.unitx         = np.array([1., 0., 0.])
        self.unity         = np.array([0., 1., 0.])
        self.unitz         = np.array([0., 0., 1.])
        self.samplesize    = QVector3D(25.,25.,-1.)
        self.sampleorigin  = QVector3D(2., 1., 0.)
        self.centercamera  = np.array([0., 0., 0.])
        self.axisorientation = 'Normal'
        self.magnification_abs = QVector3D(1., 1., 1.)
        self.magnification_cur = QVector3D(1., 1., 1.)
        # --- init the fundamental --- #
        self.initDictionaryDrawingItem() # If not reset at each initUI, will allow to cross use the dic between different object generators...
        self.initUI()
        # --- init default config that should not necessarily be reset each time --- #
        self.initDefaultConfig()
        # --- show view --- #
        #self.view.show()

    def initUI(self):
        # --- init orientation axis seting dictionary  --- #
        self.dicaxisorientation['Normal'] = QVector3D(1., 1., 1.)
        self.dicaxisorientation['Line1']  = QVector3D(-1., 1., 1.)
        # --- init current magnification --- #
        axOrient = self.dicaxisorientation[self.axisorientation]
        self.magnification_cur.setX( self.magnification_abs.x()*axOrient.x() )
        self.magnification_cur.setY( self.magnification_abs.y()*axOrient.y() )
        self.magnification_cur.setZ( self.magnification_abs.z()*axOrient.z() )
        self.updateMagnification()
        # --- init main items --- #
        self.resetKeyItemDictionary('Grid')
        self.setGrid()
        self.resetKeyItemDictionary('Axis')
        self.plotAxis()
        self.resetKeyItemDictionary('SampleBox')
        self.sampleBox( self.samplesize.x(), self.samplesize.y(), self.samplesize.z() )
        self.setOriginCenterCamera()

    def initDefaultConfig(self):
        self.setCenterCamera( [self.samplesize.x()/2., self.samplesize.y()/2., 0.] )
        # ---  --- #
        #self.view.addItem( textItem )
        #self.paintGL(QVector3D(0., 0., 0.),'text verryyyyyy lloooooonnnnnggggg diyiQYDOISQYD')

    def initDictionaryDrawingItem(self):
        '''
        The drawing item dictionary will have predefine keys:
            - Grid, Axis, SampleBox, SWGItems, BWGItems
        '''
        self.drawingitems['Grid']       = []
        self.drawingitems['Axis']       = []
        self.drawingitems['SampleBox']  = []
        self.drawingitems['SWGItems']   = []
        self.drawingitems['BWGItems']   = []
        self.drawingitems['AblItems']   = []
        self.drawingitems['PieceItems'] = []

    def resetUnitVect(self):
        self.unitx      = np.array([1., 0., 0.])
        self.unity      = np.array([0., 1., 0.])
        self.unitz      = np.array([0., 0., 1.])

    def resetOrigin(self):
        self.origin     = np.array([0., 0., 0.])

    def resetKeyItemDictionary(self, key):
        '''
        Posible keys are:
            - 'Grid', 'Axis', 'SampleBox', 'SWGItems', 'BWGItems', 'AblItems'
        Special case if the key is ALL --> all the dictionaries are reset, ie new initialisation.
        '''
        if   key == 'ALL':
            self.initDictionaryDrawingItem()
            return None
        elif key == 'ITEMS':
            KEYS_items = ['SWGItems', 'BWGItems', 'AblItems','PieceItems']
            for key_ in KEYS_items:
                del self.drawingitems[key_][:]# = []
            return None
        del self.drawingitems[key][:]# = []

    def resetALL(self):
        self.view.setParent(None)
        self.__init__()

    def resetView(self):
        self.view.setParent(None)
        self.view = gl.GLViewWidget()

    def isDrawingitemsReset(self):
        if self.drawingitems == {}:
            return True
        KEYS = ['SWGItems','BWGItems','AblItems','PieceItems']
        for key in KEYS:
            if not self.drawingitems[key] == []:
                print("WHAT IS LEFT:", self.drawingitems[key] )
                return False
        return True

    def updateView(self):
        self.cleanView()
        self.drawAllItems()
        self.view.update()

    def cleanView(self):
        '''
        Reset the item list attribut of the GLViewWidget to an empty list.
        Allow to keep the existing view, and not rebuild an entire object each time 
        we want to redraw everything.
        '''
        self.view.items = []
        self.setCenterCamera( self.centercamera )
        self.view.update()

    def setUnitVectors(self, ux=None, uy=None, uz=None):
        if ux != None:
            self.unitx = ux
        if uy != None:
            self.unity = uy
        if uz != None:
            self.unitz = uz

    def setOrigin(self, O):
        self.origin = O

    def setSampleSize(self, lx,ly,lz ):
        self.samplesize = QVector3D(lx, ly, lz)
        self.resetKeyItemDictionary('SampleBox')
        self.sampleBox( self.samplesize.x(), self.samplesize.y(), self.samplesize.z() )
        self.drawAllItems()

    def setSampleOrigin(self, coord ):
        self.sampleorigin = QVector3D(coord[0], coord[1], coord[2])
        self.resetKeyItemDictionary('SampleBox')
        self.sampleBox( self.samplesize.x(), self.samplesize.y(), self.samplesize.z() )
        self.drawAllItems()

    def setCenterCamera(self, center):
        '''
        Take as argument a np.array([x,y,z])
        '''
        # --- return to origin --- #
        center_old = self.centercamera.copy()
        self.centercamera = -1*np.array(center_old)
        self.setOriginCenterCamera()
        # --- new center --- #
        self.centercamera = np.array(center)
        self.setOriginCenterCamera()

    def setOriginCenterCamera(self):
        '''
        Take as argument a 3 elements vector/list of coordinate.
        '''
        dx, dy, dz = self.centercamera[0], self.centercamera[1], self.centercamera[2]
        self.view.pan(dx, dy, dz, relative=False)

    def setOrientaionAxisKey(self, key_axis):
        '''
        '''
        self.axisorientation = key_axis
        self.updateMagnification()

    def setMagnificationAxis(self, M):
        '''
        set the magnification of the GraphicalObject, where M=[mx,my,mz]
        '''
        # --- reset magnification ratio to original --- #
        # self.resetTransform()
        invertXmagn = self.magnification_cur.x()**-1
        invertYmagn = self.magnification_cur.y()**-1
        invertZmagn = self.magnification_cur.z()**-1
        self.magnification_cur = QVector3D(invertXmagn, invertYmagn, invertZmagn)
        self.applyMagnification()
        # --- set the new magnification --- #
        self.magnification_abs = QVector3D(M[0], M[1], M[2])
        orientationAxis        = self.dicaxisorientation[self.axisorientation]
        Mx = self.magnification_abs.x()*orientationAxis.x()
        My = self.magnification_abs.y()*orientationAxis.y()
        Mz = self.magnification_abs.z()*orientationAxis.z()
        self.magnification_cur = QVector3D(Mx, My, Mz)
        # --- set again the magnification for previous items --- #
        self.applyMagnification()

    def applyMagnification(self):
        for key in self.drawingitems:
            for item in self.drawingitems[key]:
                item.scale(x=self.magnification_cur.x() , y=self.magnification_cur.y() , z=self.magnification_cur.z(), local=False )

    def updateMagnification(self):
        magnfct = np.array([self.magnification_abs.x(), self.magnification_abs.y(),self.magnification_abs.z()])
        self.setMagnificationAxis(magnfct)

    def magnifyItem(self, item):
        item.scale(x=self.magnification_cur.x() , y=self.magnification_cur.y() , z=self.magnification_cur.z(), local=False )
        return None

    def displaceCamera(self, X):
        '''
        Displace the camera center point of the 3D vector X = np.array([dx,dy,dz]).
        '''
        X0 = np.array(self.centercamera)
        self.setCenterCamera(X0+X)

    def updateItems(self):
        for key in self.drawingitems:
            for item in self.drawingitems[key]:
                item.update()
        self.view.update()

    def paintGL(self, qcoord, text, *args, **kwds):
        gl.GLViewWidget.paintGL(self.view, *args, **kwds)
        self.view.qglColor(Qt.white)
        self.view.renderText(qcoord.x(), qcoord.y(), qcoord.z(), text)

    def paint(self, qcoord, text):
        GtextItem = gl.GLGraphicsItem()
        GtextItem.qglColor(Qt.white)
        GtextItem.renderText(qcoord.x(), qcoord.y(), qcoord.z(), text)
        self.view.addItem(GtextItem)

    def setGrid(self):
        '''
        set the grid in the view window, with the specified size
        '''
        XYplane = gl.GLGridItem()
        XYplane.setSize(2*self.sizeview, 2*self.sizeview, 0,)
        spacing = int(self.sizeview/6.)
        XYplane.setSpacing(x=spacing, y=spacing,z=None)
        self.drawingitems['Grid'].append(XYplane)

    def plotAxis(self):
        '''
        set the axis the the 3D referencial
        '''
        O = self.origin
        X = self.unitx * (self.sizeview + 1.)
        Y = self.unity * (self.sizeview + 1.)
        Z = self.unitz
        xaxis = gl.GLLinePlotItem(pos=np.array([O,X]), color=pg.glColor('y'), width=3)
        yaxis = gl.GLLinePlotItem(pos=np.array([O,Y]), color=pg.glColor('y'), width=3)
        zaxis = gl.GLLinePlotItem(pos=np.array([O,Z]), color=pg.glColor('y'), width=3)
        Center = gl.GLScatterPlotItem(pos=O, color=pg.glColor('w'))
        self.drawingitems['Axis'].append( xaxis )
        self.drawingitems['Axis'].append( yaxis )
        self.drawingitems['Axis'].append( zaxis )
        self.drawingitems['Axis'].append( Center)
        # --- Set arrows at the end of the axes --- #
        self.drawingitems['Axis'].append(  self.arrowHeadItem(X=X[0],Y=X[1],Z=X[2], direction=self.unitx, color='y', size=0.5) )
        self.drawingitems['Axis'].append(  self.arrowHeadItem(X=Y[0],Y=Y[1],Z=Y[2], direction=self.unity, color='y', size=0.5) )
        self.drawingitems['Axis'].append(  self.arrowHeadItem(X=Z[0],Y=Z[1],Z=Z[2], direction=self.unitz, color='y', size=0.5) )
        # --- Set Labels of the axes --- #
        xlabel = GLTextItem( X[0]/2. , X[1]/2.-1 , X[2]/2. ,'X', fontsize=18.)
        ylabel = GLTextItem( Y[0]/2. , Y[1]/2.-1 , Y[2]/2. ,'Y', fontsize=18.)
        zlabel = GLTextItem( Z[0]/2. , Z[1]/2.-1 , Z[2]/2. ,'Z', fontsize=18.)
        xlabel.setGLViewWidget( self.view )
        ylabel.setGLViewWidget( self.view )
        zlabel.setGLViewWidget( self.view )
        self.drawingitems['Axis'].append( xlabel )
        self.drawingitems['Axis'].append( ylabel )
        self.drawingitems['Axis'].append( zlabel )

    def arrowHeadItem(self, X=0.,Y=0.,Z=0., direction=np.array([0.,0.,1.]), size=1., color='w'):
        '''
        The arrow if by default constructed and oriented along Z-axis
        '''
        ax = size*self.unitx
        ay = size*self.unity
        az = size*self.unitz
        tip = az*np.sqrt(2/3.) + ax*0.5 + ay*(1/3. * np.sin(np.pi/3.) )
        O  = self.origin
        cc = np.cos(np.pi/3.)
        ss = np.sin(np.pi/3.)
        # --- defining faces --- #
        face1 = np.array([O , ax           , tip])
        face2 = np.array([O , ax*cc + ay*ss, tip])
        face3 = np.array([ax, ax*cc + ay*ss, tip])
        face4 = np.array([O , ax , ax*cc + ay*ss])
        vertices = np.array([face1, face2, face3, face4])
        # --- centering --- #
        vertices = vertices -tip + (az*np.sqrt(2/3.))/2.
        # --- construct the mesh data item --- #
        arrowhead_meshdata = gl.MeshData()
        arrowhead_meshdata.setVertexes(vertices)
        arrowhead_meshdata.setFaceColors(np.array(vertices.shape[0]*[pg.glColor(color)]) )
        arrowhead = gl.GLMeshItem(meshdata=arrowhead_meshdata) 
        # --- orientation along direction --- #
        rotZangle  = 180/np.pi * np.arccos(np.sum(direction*self.unitz)**0.5) # angle in deg
        rotXYangle = 180/np.pi * np.arccos(np.sum(direction*self.unitx)**0.5) # angle in deg #* np.sign(np.arcsin(np.sum(direction*ax)**0.5))
        arrowhead.rotate(rotZangle , x=0,y=1,z=0 )
        arrowhead.rotate(rotXYangle, x=0,y=0,z=1 )
        # --- translation at the end of the axis --- #
        arrowhead.translate(X,Y,Z)
        return arrowhead

    def sampleBox(self, length, width, height):
        '''
        Generate the box representation of the sample
        '''
        O  = self.origin
        a1 = np.array([length, 0    , 0     ])
        a2 = np.array([0     , width, 0     ])
        a3 = np.array([0     , 0    , height])
        faceA = np.array([O   ,O+a1   ,O+a1+a2   ,O+a2   ,O   ]) 
        faceB = np.array([O+a3,O+a1+a3,O+a1+a2+a3,O+a2+a3,O+a3]) 
        X = np.array([O,O+a3 , O+a1,O+a1+a3 , O+a2,O+a2+a3 , O+a1+a2,O+a1+a2+a3])
        red = pg.glColor('r') # also red = [1,0,0,1]
        wid = 5.
        sample_A = gl.GLLinePlotItem(pos=faceA  , color=red, width=wid, mode='line_strip')
        sample_B = gl.GLLinePlotItem(pos=faceB  , color=red, width=wid, mode='line_strip')
        sample_connect= gl.GLLinePlotItem(pos=X , color=red, width=wid, mode='lines')
        # --- but sample at new origin --- #
        sample_A.translate(dx=self.sampleorigin.x(), dy=self.sampleorigin.y(), dz=self.sampleorigin.z(), local=False)
        sample_B.translate(dx=self.sampleorigin.x(), dy=self.sampleorigin.y(), dz=self.sampleorigin.z(), local=False)
        sample_connect.translate(dx=self.sampleorigin.x(), dy=self.sampleorigin.y(), dz=self.sampleorigin.z(), local=False)
        # ---  --- #
        self.magnifyItem( sample_A )
        self.magnifyItem( sample_B )
        self.magnifyItem( sample_connect )
        self.drawingitems['SampleBox'].append( sample_A )
        self.drawingitems['SampleBox'].append( sample_B )
        self.drawingitems['SampleBox'].append( sample_connect )

    def drawAllItems(self):
        self.updateMagnification()
        for key in self.drawingitems:
            for item in self.drawingitems[key]:
                self.view.addItem(item)

    def drawLine(self,X0,X1, width=2., color='b'):
        '''
        Draw a straight line fro X0 to X1 in the view window
        '''
        color_ = pg.glColor(color)
        line   = gl.GLLinePlotItem(pos=np.array([X0,X1]) , color=color_, width=width, mode='lines') # pos should be a (N,3) np.array type float !
        return line

    def drawContinuousLine(self, X, width=2., color='b'):
        '''
        Draw a straight continuous line with vertices at each X[i] of the (N,3) vector array.
        '''
        color_ = pg.glColor(color)
        line   = gl.GLLinePlotItem(pos=X, color=color_, width=width, mode='line_strip') 
        return line

    def drawCircularCurve(self,angle,radius, width=2., color='b', axis='Z'):
        '''
        Draw an circular curved line in the view window.
        The curve starts from the origin and will be aligned with the X-axis, ie the slope at the origin will be along the X-axis.
        Axis is to specify the rotation axis.

        '''
        step = 0.1 # um
        stepangle = step/radius
        N = np.abs(angle/stepangle)
        angvar = np.linspace(0,angle, N)
        # --- initialise the curve line in the XY plane --- #
        X = np.zeros([angvar.size,3])
        X[:,0] = radius*(np.cos(angvar)-1.)
        X[:,1] = radius*np.sin(angvar)
        X[:,2] = np.zeros(angvar.size)
        X = X.astype('float')
        color_ = pg.glColor(color)
        line   = gl.GLLinePlotItem(pos=X, color=color_, width=width, mode='line_strip')
        line.rotate(-90, x=0, y=0, z=1, local=False) # so that the slope aligns with X-axis
        if axis =='X':
            line.rotate(90, x=1, y=0, z=0, local=False)
        if axis =='Y':
            line.rotate(90, x=1, y=0, z=0, local=False)
        if axis =='Z':
            pass
        return line

    def drawCirclePiece(self, radius, angle_start, angle_end, planeXYZ='XY', width=2., color='b'):
        '''
        By default we will draw the circle piece in the XY plane, then we will rotate the plane
        according to the planeXYZ parameter.
        Then we will bring the starting point of the curve in the origin. But we will not align
        the slop of the curve with the X-axis.
        '''
        step = 0.1 # um
        stepangle = step/radius
        angle_tot = np.abs(angle_start - angle_end)
        N = int(np.abs(angle_tot/stepangle))
        angvar = np.linspace(angle_start, angle_end, N)
        # --- initialise the curve line in the XY plane --- #
        X = np.zeros([angvar.size,3])
        X[:,0] = radius*np.cos(angvar)
        X[:,1] = radius*np.sin(angvar)
        X[:,2] = np.zeros(angvar.size)
        X = X.astype('float')
        color_ = pg.glColor(color)
        line   = gl.GLLinePlotItem(pos=X, color=color_, width=width, mode='line_strip')
        # --- moving the object --- #
        Xinit = X[0]
        line.translate(dx=-Xinit[0], dy=-Xinit[1], dz=-Xinit[2], local=False) #moving to the origin
        if   planeXYZ =='XY':
            pass
        elif planeXYZ =='YZ':
            line.rotate(90, x=0, y=1, z=0, local=False)
        elif planeXYZ =='XZ':
            line.rotate(90, x=1, y=0, z=0, local=False)
        return line

    def drawGCommand(self, pos, radius, angle_start, angle_end, planeXYZ='XY', width=2., color='b'):
        arccirc = self.drawCirclePiece(radius, angle_start, angle_end, planeXYZ=planeXYZ, width=width, color=color)
        # ---  --- #
        arccirc.translate(dx=pos[0], dy=pos[1], dz=pos[2], local=False)
        # ---  --- #
        self.magnifyItem( arccirc )
        self.drawingitems['PieceItems'].append(arccirc)

    def drawArcCircle(self, pos, angle, radius, width=2.):
        '''
        Draw an arc of a circle in the XY plane with the initial vector direction along +X.
        '''
        arccirc = self.drawCircularCurve(angle,radius, width)
        # ---  --- #
        arccirc.translate(dx=pos[0], dy=pos[1], dz=pos[2], local=False)
        # ---  --- #
        self.magnifyItem( arccirc )
        self.drawingitems['PieceItems'].append(arccirc)

    def drawSWG(self, xInit, xEnd, Y, depth, scanNbr):
        X0 = np.array([xInit, Y, depth])
        X1 = np.array([xEnd , Y, depth])
        width = 1.*scanNbr
        swg = self.drawLine(X0, X1, width)
        self.magnifyItem( swg )
        self.drawingitems['SWGItems'].append(swg)

    def drawBWG(self, xInit, xCenter, xEnd, yInit, depth, radius, length, scanNbr):
        theta = length/(2*radius)
        width = 1.*scanNbr
        # --- first straight part --- #
        X0 = np.array([xInit, yInit, depth])
        xstop1 = xCenter - radius*np.sin(theta)
        X1 = np.array([xstop1 , yInit, depth])
        line1 = self.drawLine(X0,X1, width)
        #line1.translate(dx=0., dy=yInit, dz=0., local=False)
        # --- circular part 1 --- #
        circ1 = self.drawCircularCurve(theta,radius, width)
        circ1.translate(dx=xstop1, dy=yInit,dz=depth, local=False)
        # --- circular part 2 --- #
        xstop2 = xCenter + radius*np.sin(theta)
        ystop2 = yInit   + 2*radius*(1-np.cos(theta))
        circ2 = self.drawCircularCurve(theta,-radius, width)
        circ2.translate(dx=xstop2, dy=ystop2,dz=depth, local=False)
        # --- final straight part --- #
        X2 = np.array([xstop2, ystop2, depth])
        X3 = np.array([xEnd  , ystop2, depth])
        line2 = self.drawLine(X2,X3, width)
        #line2.translate(dx=0., dy=ystop2, dz=0.)
        # --- apply current magnification --- #
        self.magnifyItem( line1 )
        self.magnifyItem( circ1 )
        self.magnifyItem( circ2 )
        self.magnifyItem( line2 )
        # --- appending the dictionary --- #
        self.drawingitems['BWGItems'].append(line1)
        self.drawingitems['BWGItems'].append(circ1)
        self.drawingitems['BWGItems'].append(circ2)
        self.drawingitems['BWGItems'].append(line2)
        return None

    def drawAblationTextABSOLUTE(self, X, width=2., color='g'):
        depth = 0.
        X_ = []
        for i in range(X.shape[0]):
            X_.append( X[i,0]*self.unitx + X[i,1]*self.unity + depth*self.unitz)
        X_ = np.array(X_)
        abltxt = self.drawContinuousLine(X_, width=width, color=color)
        self.magnifyItem( abltxt )
        self.drawingitems['AblItems'].append(abltxt)

    def drawAblationTextINCREMENTAL(self, X, X0, width=2., color='g'):
        '''
        We rebuild the absolute coordinate of the draw lines with the set of incremental
        vectors in X.
        Then the drawing is translated to the X0 coordinate.
        '''
        depth = 0.
        X_ = []
        # --- initialisation --- #
        X_.append( X[0,0]*self.unitx + X[0,1]*self.unity + depth*self.unitz)
        # --- iteration --- #
        for i in range(1,X.shape[0]):
            X_.append( (X[i,0]+X[i-1,0])*self.unitx + (X[i,1]+X[i-1,1])*self.unity + depth*self.unitz)
        X_ = np.array(X_)
        abltxt = self.drawContinuousLine(X_, width=width, color=color)
        abltxt.translate(dx=X0[0], dy=X0[1],dz=0., local=False)
        self.magnifyItem( abltxt )
        self.drawingitems['AblItems'].append(abltxt)

    def drawLaserOnLine(self, X0,X1, width=2., color='b'):
        line = self.drawLine(X0,X1, width=width, color=color)
        self.magnifyItem( line )
        self.drawingitems['PieceItems'].append(line)

    def drawListCoordinate(self, X, width=2., color='b'):
        coord_list = np.array(X)
        line = self.drawContinuousLine(coord_list, width=width, color=color)
        self.magnifyItem( line )
        self.drawingitems['PieceItems'].append(line)

    def makeDefaultInstructions(self):
        xInit           = -1.
        xEnd            = 29
        dpth            = -0.2
        self.drawSWG(xInit, xEnd, 0.1, dpth, 5)
        self.drawBWG(xInit, self.samplesize.x()/2., xEnd, 2., dpth, radius=15., length=20., scanNbr=5)
        self.drawingitems['BWGItems'].append( self.drawCircularCurve(-np.pi, 2., width=4., color='w') )
        X = [np.array([0.,0.]),np.array([1,1]),np.array([1,10.]),np.array([2,15]),np.array([2.,2.])]
        X = np.array(X)
        self.drawAblationTextABSOLUTE(X)
        X = X + np.array([10,0])
        self.drawAblationTextABSOLUTE(X)
        angle_start = 90 *np.pi/180.
        angle_end   = (90+45) *np.pi/180.
        radius      = 30
        self.drawGCommand(np.array([4,4,0]), radius, angle_start, angle_end, width=5., color='y')

    def initDefault(self):
        self.view.setGeometry(100,100, 600, 400)
        self.makeDefaultInstructions()
        #self.setMagnificationAxis([-1., 1., 1.])
        self.drawAllItems()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

class GLTextItem(GLGraphicsItem):
    '''
    Class take from: https://groups.google.com/forum/#!topic/pyqtgraph/JHviWSaGhck
    And a bit modified to siut my needs.
    '''
    def __init__(self, X=None, Y=None, Z=None, text=None, fontsize=1., color='w'):
        super().__init__() # also work with: GLGraphicsItem.__init__(self)

        self.text       = text
        self.coordtext  = QVector3D(X,Y,Z)
        self.fontsize   = fontsize
        self.color      = QtCore.Qt.white   # #ffffff' #pg.glColor(color)

    def setGLViewWidget(self, GLViewWidget):
        self.GLViewWidget = GLViewWidget

    def setText(self, text):
        self.text = text
        self.update()

    def setX(self, X):
        self.coordtext.setX(X)
        self.update()

    def setY(self, Y):
        self.coordtext.setY(Y)
        self.update()

    def setZ(self, Z):
        self.coordtext.setZ(Z)
        self.update()

    def paint(self):
        self.GLViewWidget.qglColor(self.color)
        self.GLViewWidget.renderText(self.coordtext.x(), self.coordtext.y(), self.coordtext.z(), self.text, font=QtGui.QFont("Latex", int(self.fontsize)) )
# ========================================== #
class WaveGuide:
    def __init__(self):
        self.currentpos = QVector3D(0., 0., 0.) # initiate at the origin
        self.direction  = QVector3D(1., 0., 0.) # initiate along X-axis
        self.trajectory = []    # record the trajectory of the waveguide

    def goTo(self, X):
        '''
        set the current position to the wanted one, where X = np.array([x,y,z],dtype='float')
        '''
        self.currentpos.setX(X[0])
        self.currentpos.setY(X[1])
        self.currentpos.setZ(X[2])
# ========================================== #
class LASER:
    '''
    This object will play the role of the laser/stage.
    The goal is to interprete directly Gcode and transform it to drawing items.
    '''
    def __init__(self):
        self.txtinstruction = ''
        self.dicinstruction = {}
        self.isON           = False
        self.position       = np.array([0., 0., 0.])

    def initDictionaryInstructions(self):
        self.dicinstruction = {}


################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    print("STARTING")
    appMain = QApplication(sys.argv)
    Simu = SimulationDesign()
    Simu.initDefault()
    Simu.view.show()
    sys.exit(appMain.exec_())
