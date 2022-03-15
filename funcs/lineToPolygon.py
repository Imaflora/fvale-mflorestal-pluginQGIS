"""
Model exported as python.
Name : func 04 - lines to polygons
Group : implementacoes
"""

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDateTime)
import processing


class lineToPolygon(QgsProcessingAlgorithm):
    """
    This algorithm converts lines to polygons.
    """

    def initAlgorithm(self, config=None):
        """
        Definition of the inputs and output of the algorithm.
        """

        self.addParameter(QgsProcessingParameterVectorLayer('linhas', 'Selecione o arquivo de linhas', types=[QgsProcessing.TypeVectorLine], defaultValue=None))

        self.addParameter(QgsProcessingParameterFeatureSink('refatorado', 'Polígonos corrigidos para envio via Wrike', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        """
        The processing itself.
        """
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # Reprojetar camada
        alg_params = {
            'INPUT': parameters['linhas'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Explodir linhas
        alg_params = {
            'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExplodirLinhas'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Poligonize
        alg_params = {
            'INPUT': outputs['ExplodirLinhas']['OUTPUT'],
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
        return 'algorithm_name4'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return '04 - lines'

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
        return lineToPolygon()
