"""
Model exported as python.
Name : func 04 - edit file
Group : outras ferramentas
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,)
import processing
import os

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]


class f4_edit(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('bloqueado', 'Arquivo Bloqueado', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('edit', 'Arquivo Editável', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # renomeando arquivo de saída
        parameters['edit'].destinationName = 'Arquivo Editável'

        # Extrair por expressão
        alg_params = {
            'EXPRESSION': '$id is not null',
            'INPUT': parameters['bloqueado'],
            'OUTPUT': parameters['edit']
        }
        outputs['ExtrairPorExpresso'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['edit'] = outputs['ExtrairPorExpresso']['OUTPUT']
        return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'f4_edit'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return 'Permitir Edição de Arquivo'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Outras Ferramentas'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'outras'


    def shortHelpString(self):
        """
        Returns the help text as HTML displayed to the users when executed.
        """
        return f"""<html>
  <body bgcolor=#fcfcfc style="font-family:Tahoma;text-align:justify;">      
    <h2>Sistema de Validação de Polígonos (SVP) Compromisso Florestal</h2>
    <h3>Realizar edições em um arquivo bloqueado</h3>
    <br>    Ferramenta utilizada para liberar edições em um arquivo bloqueado.
    Geralmente arquivos abertos em outros programas ou zipados ficam bloqueados para edição.
        O arquivo de saída será uma cópia exata do arquivo original e poderá ser editado.
    
    Não é necessário salvar ou enviar este arquivo.
    <br>    Para mais esclarecimentos clique no botão <b>Help</b> abaixo.
    
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'fundoVale.png')}"></center>
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'imafloraLogo.png')}"></center>

    Autor do algoritmo: Imaflora - Herbert Lincon R. A. dos Santos
    herbert.santos@imaflora.org
  </body>
</html>"""

    def icon(self):
        return QIcon(os.path.join(PLUGINPATH, 'imgs', 'pencil.png'))
        
    def helpUrl(self):
        return 'File:///' + os.path.join(PLUGINPATH, 'manuals', 'f4_edit.pdf')

    def tr(self, string):
        return QCoreApplication.translate('Processing2', string)

    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return f4_edit()
