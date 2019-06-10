#! /usr/bin/env python
# -*- coding: utf-8 -*-


################################################################################################
# IMPORTATIONS
################################################################################################
import sys
import PyQt5 
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTableWidget
from PyQt5.QtWidgets import QBoxLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QGridLayout, QSplitter
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QInputDialog
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction
from PyQt5.QtGui     import QIcon, QFont, QPainter, QColor
from PyQt5.QtCore    import Qt, QPoint, QPointF, pyqtSignal, pyqtSlot

import numpy as np

################################################################################################
# FUNCTIONS
################################################################################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class MyLineEdit(QLineEdit):
    '''
    This Widget uses:
        PyQt5.QTWidgets --> QLineEdit
    '''
    def __init__(self):
        super().__init__()
        self.isable = 1 # if 1, the line edite is enable, if 0, the line edit id disable

    def changeReadOptionLine(self,booleen=None):
        if booleen==None:
            if self.isReadOnly():
                self.setStyleSheet("QLineEdit { background-color: white; color: black }") 
                self.setReadOnly(False)
            else:
                self.setStyleSheet("QLineEdit { background-color: rgba(0,0,0,0.1); color: red }")
                self.setReadOnly(True)
        elif booleen==True:
            self.setStyleSheet("QLineEdit { background-color: white; color: black }") 
            self.setReadOnly(False)
        elif booleen==False:
            self.setStyleSheet("QLineEdit { background-color: rgba(0,0,0,0.1); color: red }")
            self.setReadOnly(True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class MyQLabel(QLabel):
    '''
    This Widget uses:
        PyQt5.QTWidgets --> QLabel
    '''
    def __init__(self, initString=''):
        super().__init__(initString)

    def setInterpretedText(self, QString):
        try:
            ev = eval(QString)
        except:
            ev = "###"
        self.setText(str(ev))

    def setInterpretedTextType(self, QString):
        try:
            ev = eval(QString)
            if type(ev) == type(int(1)):
                evtype = "int     "
            elif type(ev) == type(float(1)):
                evtype = "float   "
            elif type(ev) == type(np.array([])):
                evtype = "np.array"
            elif type(ev) == type([]):
                evtype = "list    "
            else:
                evtype = "other   "
        except:
            evtype = "###" 
        self.setText(evtype)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class MyFrameFolding(QFrame):
    '''
    This Widget uses:
        PyQt5.QtCore    --> Qt
        PyQt5.QTWidgets --> QFrame,QVBoxLayout,QHBoxLayout,QCheckBox
    '''
    def __init__(self,parent=None, title='', defaultcollapse=False):
        super().__init__(parent)
        self.iscollapse = defaultcollapse
        self.title      = title
        self.initUI()

    def initUI(self):
        # --- set widget general config --- #
        self.layout           = QVBoxLayout(self)
        #self.layout.setAlignment(Qt.AlignTop) #make the arrow position swapp don't work. ???
        # --- set TitleFrame --- #
        self.titlewidget = self.TitleFrame(self, self.title, self.iscollapse)
        # --- main content window --- #
        self.maincontent = QFrame()
        self.maincontentlayout = QVBoxLayout()
        self.maincontent.setLayout( self.maincontentlayout )
        self.maincontent.setVisible( not self.iscollapse )
        # --- set layout --- #
        self.layout.addWidget( self.titlewidget )
        self.layout.addWidget( self.maincontent )
        self.initCollapse()

    def addWidget(self, qwidget):
        self.maincontentlayout.addWidget( qwidget )

    def setMainContentNewLayout(self, layout):
        self.maincontentlayout = layout
        self.maincontent.setLayout( self.maincontentlayout )

    def initCollapse(self):
        self.titlewidget.clickesignal.connect( self.toggleCollapse )

    def toggleCollapse(self):
        self.maincontent.setVisible( self.iscollapse )
        self.iscollapse = not self.iscollapse 
        self.titlewidget.arrow.setArrow( self.iscollapse )

    def mousePressEvent(self, event):
        self.titlewidget.clickesignal.emit()

    class TitleFrame(QFrame):
        clickesignal = pyqtSignal()
        def __init__(self, parent=None, title='', collapse=False):
            super().__init__(parent=parent)
            self.collapse  = collapse
            self.titletext = title
            self.initUI()

        def initUI(self):
            self.layout = QHBoxLayout()
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.setSpacing(0)
            # --- init Arrow --- #
            self.arrow = Arrow(self, self.collapse)
            self.arrow.setStyleSheet("border:0px")
            # --- init Title --- #
            self.title = QLabel(self.titletext)
            self.title.setStyleSheet("border:0px")
            # --- set layout --- #
            self.layout.addWidget( self.arrow )
            self.layout.addWidget( self.title )
            self.setLayout(self.layout)



    #def collapseFrame(self):
    #    if self.collapsebutton.isChecked():
    #        self.collapsibleframe.hide()
    #    else:
    #        self.collapsibleframe.show()

    #def setCollapseLayout(self, QLayout ):
    #    self.collapsibleframe.setLayout(QLayout)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class Arrow(QFrame):
    '''
    Object that draw an arrow in two direction: vertical, horizontal.
    Used for the collapse widget.
    Initially found at:
        https://github.com/By0ute/pyqt-collapsible-widget/blob/master/code/FrameLayout.py
    This Widget uses:
        PyQt5.QtGui     --> QPainter, QColor
        PyQt5.QtCore    --> QPointF
        PyQt5.QTWidgets --> QFrame
    '''
    def __init__(self, parent=None, collapsed=False):
        QFrame.__init__(self, parent=parent)

        self.setMaximumSize(24, 24)

        # horizontal == 0
        self._arrow_horizontal = (QPointF(7.0, 8.0), QPointF(17.0, 8.0), QPointF(12.0, 13.0))
        # vertical == 1
        self._arrow_vertical   = (QPointF(8.0, 7.0), QPointF(13.0, 12.0), QPointF(8.0, 17.0))
        # arrow
        self._arrow = None
        self.setArrow(int(collapsed))

    def setArrow(self, arrow_dir):
        if arrow_dir:
            self._arrow = self._arrow_vertical
        else:
            self._arrow = self._arrow_horizontal

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setBrush(QColor(192, 192, 192))
        painter.setPen(QColor(64, 64, 64))
        painter.drawPolygon(*self._arrow)
        painter.end()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class MyParameter():
    '''
    Class object for manipulating fabrication parameters in the Femtosecond Laser Direct Writing.
    The parameters will be gathered in groups and will be assigned a type:
        - groups are for display: fixed param., loop 
        - types : 'fab' = physical param for the design, 'loop' = loop param used for iteration
        - loop depth: the higher, the outer the loop content will be, eg 0 is for the smallest loop, ie the one that will be repeated the more.
    The value -1, will be my convention for discarding parameters, ie parameters that have no purpose.
    '''
    def __init__(self, name='noname', value=-1, group='',type_='None'):
        self.value      = value
        self.name       = name
        self.group      = group
        self.type       = type_  # 'fab', 'loop', 
        self.loopvar    = '$##'
        self.loopdepth  = -1
        #self.paramassoc = None

    def setValue(self, val):
        self.value = val

    def setName(self, newname):
        self.name = newname

    def setGroup(self, grp):
        self.group = grp

    def setType(self, typ):
        self.type = typ

    def setLoopVariableAssociated(self, paramname):
        self.paramassoc = paramname
        '''
        if self.type == 'loop':
            self.paramassoc = paramname
        else:
            print("Error: This is not a loop variable")
            return None
        '''

    def setLoopVariable(self, loopvar):
        if self.type == 'loop':
            self.loopvar = loopvar
        else:
            print("Error: This is not a loop variable")
            return None

    def setLoopDepth(self, depth):
        if self.type == 'loop':
            self.loopdepth = depth
        else:
            print("Error: This is not a loop variable")
            return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class MyErrorBox(QMessageBox):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.displaytext   = ''
        self.displaywidget = None
        self.layout        = None

    def initGUi(self):
        return None

    def displayErrorBox(self):
        self.show()

    def selfClosing(self):
        self.exec_()

    def addText(self, text):
        self.displaytext += text

    def resetText(self):
        self.displaytext = ''

    def makeLayout(self):
        return None

################################################################################################
# CODE
################################################################################################

if __name__=='__main__':
    app = QApplication(sys.argv) # every application must begin by declaring a Qapplication. The sys.argv parameter is a list of arguments from a command line. Since python scripts can be run from the shell, it is a way how we can control the startup of our scripts.
    # --- create a window and set some of its parameters --- #
    windows = MyFrameFolding(None,  "Very long title test super long") # a widget with no parent is simply a windows
    #windows.resize(400,600)
    windows.move(100,100)
    # --- put some stuff inside example --- #
    layout = QVBoxLayout()
    windows.addWidget( QPushButton() )
    windows.addWidget( QLineEdit() )
    # --- display window --- #
    windows.show()
    # --- mandatory to set the action of the exit button --- #
    sys.exit(app.exec_())
