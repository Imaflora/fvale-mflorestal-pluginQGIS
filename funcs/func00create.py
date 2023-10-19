"""
Model exported as python.
Name : func 00 - create file
Group : implementacoes
"""

from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingMultiStepFeedback)
import processing
import os

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]

class f0_criar(QgsProcessingAlgorithm):
    """
    This algorithm creates an empty vector with CRS:4326.
    """

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'

    def initAlgorithm(self, config):
        """
        Definition of the inputs and output of the algorithm.
        """

        self.addParameter(QgsProcessingParameterFeatureSink('novaArea', 'Novo Arquivo para Desenho', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        """
        The processing itself.
        """

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        parameters['novaArea'].destinationName = 'Desenhar Nova Área'

        # Criar camada pela extensão
        alg_params = {
            'INPUT': '-60.014603942,-39.256933375,-24.505255098,-3.615706065 [EPSG:4326]',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CriarCamadaPelaExtenso'] = processing.run('native:extenttolayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Extrair por expressão
        alg_params = {
            'EXPRESSION': '\"id\" = 99',
            'INPUT': outputs['CriarCamadaPelaExtenso']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorExpresso'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [],
            'INPUT': outputs['ExtrairPorExpresso']['OUTPUT'],
            'OUTPUT': parameters['novaArea']
        }
        outputs['EditarCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['novaArea'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'f0_create'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return ' Desenhar Áreas'

    """
    group session is deactivated until it's needed to create another one

    def group(self):
        \"""
        Returns the name of the group this algorithm belongs to.
        \"""
        return 'Implementações'

    def groupId(self):
        \"""
        Returns the unique ID of the group this algorithm belongs to.
        \"""
        return 'implementacoes'
    """

    def shortHelpString(self):
        """
        Returns the help text as HTML displayed to the users when executed.
        """
        return f"""<html>
  <body bgcolor=#fcfcfc style="font-family:Tahoma;text-align:justify;">      
    <h2>Sistema de Validação de Polígonos (SVP) Meta Florestal</h2>
    <h3>Desenhar Polígonos</h3>
    <br>    Ferramenta utilizada para desenhar diretamente no QGIS os polígonos das áreas contratadas ou implantadas.
       O arquivo gerado estará vazio.
    Crie nele as geometrias que representem <b>apenas uma propriedade OU área em execução (ID)</b> e salve.
       Após isto, utilize a ferramenta <b>"Preparar Polígonos (Shapefile)"</b>.
    <br>    Para mais esclarecimentos clique no botão <b>Help</b> abaixo.
    
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'fundoVale.png')}"></center>
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'imafloraLogo.png')}"></center>

    Autor do algoritmo: Imaflora - Herbert Lincon R. A. dos Santos
    herbert.santos@imaflora.org
  </body>
</html>"""

    def icon(self):
        return QIcon(os.path.join(PLUGINPATH, 'imgs', 'newFile.png'))

    def helpUrl(self):
        return 'File:///' + os.path.join(PLUGINPATH, 'manuals', 'f0_desenhar.pdf')

    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return f0_criar()
