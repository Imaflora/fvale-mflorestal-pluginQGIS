"""
Model exported as python.
Name : func 03 - pontos-polígonos
Group : implementacoes
With QGIS : 32000
"""

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDateTime)
import processing


class pointToPolygon(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        """
        Definition of the inputs and output of the algorithm.
        """
        self.addParameter(QgsProcessingParameterField('group', 'group', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterField('idsequencia', 'id - sequencia', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterVectorLayer('pontos', 'pontos', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('refatorado', 'refatorado', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        """
        The processing itself.
        """
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Reprojetar camada
        alg_params = {
            'INPUT': parameters['pontos'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Pontos para linhas
        alg_params = {
            'CLOSE_PATH': True,
            'GROUP_EXPRESSION': parameters['group'],
            'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
            'NATURAL_SORT': False,
            'ORDER_EXPRESSION': parameters['idsequencia'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PontosParaLinhas'] = processing.run('native:pointstopath', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Poligonize
        alg_params = {
            'INPUT': outputs['PontosParaLinhas']['OUTPUT'],
            'KEEP_FIELDS': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Poligonize'] = processing.run('native:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [],
            'INPUT': outputs['Poligonize']['OUTPUT'],
            'OUTPUT': parameters['refatorado']
        }
        outputs['EditarCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['refatorado'] = outputs['EditarCampos']['OUTPUT']
        return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'algorithm_name3'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return '03 - pontos'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'group2'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'algorithm_group'


    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return pointToPolygon()
