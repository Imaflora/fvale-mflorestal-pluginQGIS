# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Sistema de Validação de Polígonos (SVP) Meta Florestal

                                 A QGIS plugin

 plugin used in the Meta Florestal project
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
    begin                : 2021-12-15
    copyright            : (C) 2021 by Herbert Lincon R. A. Santos / Imaflora
    email                : herbert.santos@imaflora.org
 ***************************************************************************/
"""

__author__ = 'Herbert Lincon R. A. Santos / Imaflora'
__date__ = '2022-01-15'
__copyright__ = '(C) 2021 by Herbert Lincon R. A. Santos / Imaflora'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsApplication
from .fvale_mflorestal_provider import fvaleMetaProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class fvaleMetaPlugin(object):

    def __init__(self):
        """
        Default constructor.
        """
        self.provider = None

    def initProcessing(self):
        """
        Init Processing provider for QGIS >= 3.8
        """
        self.provider = fvaleMetaProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)