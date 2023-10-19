# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Sistema de Validação de Polígonos (SVP) Meta Florestal

                                 A QGIS plugin

 plugin used in the Meta Florestal project
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
    begin                : 2022-01-15
    copyright            : (C) 2022 by Herbert Lincon R. A. Santos / Imaflora
    email                : herbert.santos@imaflora.org
 ***************************************************************************/
"""

__author__ = 'Herbert Lincon R. A. Santos / Imaflora'
__date__ = '2022-01-15'
__copyright__ = '(C) 2022 by Herbert Lincon R. A. Santos / Imaflora'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .funcs.func00create import *
from .funcs.func01propriedade import *
#from .funcs.func02implement import *
from .funcs.func03calcarea import *
from .funcs.fund04edit import *


import os

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]

class fvaleMetaProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(f0_criar())
        self.addAlgorithm(f1_propriedade())
        #self.addAlgorithm(f2_implement())
        self.addAlgorithm(f3_calcarea())
        self.addAlgorithm(f4_edit())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider.
        """
        return 'FundoValeMeta'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.
        """
        return self.tr('SVP Meta Florestal')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(os.path.join(
                    PLUGINPATH,
                    'fvale-mflorestal-pluginQGIS-main',
                    'imgs',
                    'fundoValeLogo.png'
                    )
                    )

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers.
        """
        return self.name()
