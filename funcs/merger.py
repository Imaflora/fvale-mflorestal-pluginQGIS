"""
Model exported as python.
Name : func 02 - merger
Group : implementacoes
With QGIS : 32000
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDateTime,
                       QgsProcessingParameterField,
                       QgsProcessingParameterEnum)
import processing
import os

from .lineToPolygon import lineToPolygon
from .pointToPolygon import pointToPolygon

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]

class merger(QgsProcessingAlgorithm):
    """
    This algorithm merge many files in many possibilities
    and run func01refactor.py
    """

    def initAlgorithm(self, config=None):
        """
        Definition of the inputs and output of the algorithm.
        """

        self.addParameter(QgsProcessingParameterMultipleLayers('polgonos', 'Arquivos de Polígonos', optional=True, layerType=QgsProcessing.TypeVectorPolygon, defaultValue=None))
        self.addParameter(QgsProcessingParameterMultipleLayers('linhas', 'Arquivos de Linhas', optional=True, layerType=QgsProcessing.TypeVectorLine, defaultValue=None))
        self.addParameter(QgsProcessingParameterMultipleLayers('pontos', 'Arquivos de Pontos', optional=True, layerType=QgsProcessing.TypeVectorPoint, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterField('group', 'Grupo (Caso os pontos representem mais de um polígono)', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterField('idsequencia', 'Sequência (Atributo que define a sequência dos pontos como Data ou ID)', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue=''))

        self.addParameter(QgsProcessingParameterFeatureSink('merged', 'Polígonos Corrigidos para envio ao Wrike', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        """
        The processing itself.
        """
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        geoms = []
        
        try:
            len(parameters['polgonos'])
        
            # Mesclar camadas vetoriais - poligonos
            alg_params = {
                'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                'LAYERS': parameters['polgonos'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Poligonos'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}

            geoms.append(outputs['Poligonos']['OUTPUT'])

        except:
            pass


        try:
            len(parameters['linhas'])

            # Mesclar camadas vetoriais - linhas
            alg_params = {
                'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                'LAYERS': parameters['linhas'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['MesclarCamadasVetoriaisLinhas'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}


            # Func04LinhasPolgonos
            alg_params = {
                'linhas': outputs['MesclarCamadasVetoriaisLinhas']['OUTPUT'],
                'refatorado': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Linhas'] = processing.run(lineToPolygon(), alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            geoms.append(outputs['Linhas']['refatorado'])

        except:
            pass


        try:
            len(parameters['pontos'])

            # Mesclar camadas vetoriais - pontos
            alg_params = {
                'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                'LAYERS': parameters['pontos'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['MesclarCamadasVetoriaisPontos'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}


            # Func03Pontospolgonos
            alg_params = {
                'pontos': outputs['MesclarCamadasVetoriaisPontos']['OUTPUT'],
                'group': parameters['group'],
                'idsequencia': parameters['idsequencia'],
                'refatorado': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Pontos'] = processing.run(pointToPolygon(), alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            geoms.append(outputs['Pontos']['refatorado'])

        except:
            pass


        # Mesclar camadas vetoriais - final
        alg_params = {
            'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'LAYERS': geoms,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [],
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'OUTPUT': parameters['merged']
        }
        outputs['EditarCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['merged'] = outputs['EditarCampos']['OUTPUT']
        return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'algorithm_name2'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return 'Unir Arquivos'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Implementações'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'implementacoes'

    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return merger()
