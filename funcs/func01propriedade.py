"""
Model exported as python.
Name : func 01 - refactor
Group : implementacoes
"""

from asyncio.windows_events import NULL
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDateTime,
                       QgsProcessingParameterField,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDefinition)
import processing
import os

from .merger import merger

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]

class f1_propriedade(QgsProcessingAlgorithm):
    """
    This algorithm refactor and dissolve the files to create a unique
    and safe file for the indicated ID_Area.
    """

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        """
        Definition of the inputs and output of the algorithm.
        """
        self.addParameter(QgsProcessingParameterMultipleLayers('polgonos', 'Arquivos de Polígonos', optional=True, layerType=QgsProcessing.TypeVectorPolygon, defaultValue=None))
        self.addParameter(QgsProcessingParameterMultipleLayers('linhas', 'Arquivos de Linhas', optional=True, layerType=QgsProcessing.TypeVectorLine, defaultValue=None))
        self.addParameter(QgsProcessingParameterMultipleLayers('pontos', 'Arquivos de Pontos', optional=True, layerType=QgsProcessing.TypeVectorPoint, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterNumber('id', 'ID da Área Implementada', type=QgsProcessingParameterNumber.Integer, minValue=0, maxValue=9999, defaultValue=0))

        self.addParameter(QgsProcessingParameterEnum('investida', 'Investida que atuou nesta área', options=['Belterra','Bioenergia','Caaporã','Inocas','Regenera'], allowMultiple=False, usesStaticStrings=False, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterString('propriet', 'Proprietário da Área', multiLine=False, defaultValue='Nome do Proprietário da Área'))

        # configurações de pontos como avançados para que fiquem destacados
        group = QgsProcessingParameterField('group', 'Grupo (Caso os pontos representem mais de um polígono)', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue='')
        group.setFlags(group.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(group)
        idsequencia = QgsProcessingParameterField('idsequencia', 'Sequência (Atributo que define a sequência dos pontos como Data ou ID)', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue='')
        idsequencia.setFlags(idsequencia.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(idsequencia)

        self.addParameter(QgsProcessingParameterFeatureSink('refatorado', 'Polígonos Corrigidos para envio ao Wrike', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        """
        The processing itself.
        """
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}

        # checagem de preenchimentos inválidos
        if parameters['polgonos'] == None and parameters['linhas'] == None and parameters['pontos'] == None:
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Nenhum arquivo foi selecionado. Selecione ao menos um arquivo de polígonos, linhas ou pontos e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return {}

        if parameters['id'] == 0:
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Nenhum número foi inserido para o ID. Insira o número desta área e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return {}

        if str(parameters['propriet']).strip() == 'Nome do Proprietário da Área' or str(parameters['propriet']).strip() == '':
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Valor inválido para PROPRIETÁRIO. Preencha corretamente o campo e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return {}

        else:
            proprietario = str(parameters['propriet']).strip()   

        # receiving the inputs into variables
        if parameters['investida'] == 0:
            sigla = 'BEL'

        elif parameters['investida'] == 1:
            sigla = 'BIO'

        elif parameters['investida'] == 2:
            sigla = 'CAA'

        elif parameters['investida'] == 3:
            sigla = 'INO'

        elif parameters['investida'] == 4:
            sigla = 'REG'

        else:
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Valor inválido para INVESTIDA. Selecione uma opção válida e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return {}

        id = sigla + str(parameters['id']).zfill(4)
       
        # renomeando arquivo de saída
        parameters['refatorado'].destinationName = 'Salvar e Enviar ao Wrike'

        # Merger
        alg_params = {
            'polgonos': parameters['polgonos'],
            'linhas': parameters['linhas'],
            'pontos': parameters['pontos'],
            'group': parameters['group'],
            'idsequencia': parameters['idsequencia'],
            'merged': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['merged'] = processing.run(merger(), alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Polígonos para linhas
        alg_params = {
            'INPUT': outputs['merged']['merged'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PolgonosParaLinhas'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Centroides
        alg_params = {
            'ALL_PARTS': True,
            'INPUT': outputs['merged']['merged'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Centroides'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Explodir linhas
        alg_params = {
            'INPUT': outputs['PolgonosParaLinhas']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExplodirLinhas'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Poligonize
        alg_params = {
            'INPUT': outputs['ExplodirLinhas']['OUTPUT'],
            'KEEP_FIELDS': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Poligonize'] = processing.run('native:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Associar atributos por local
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['Poligonize']['OUTPUT'],
            'JOIN': outputs['Centroides']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 2,  # Aceite atributos da feição com maior sobreposição (um a um)
            'PREDICATE': [0],  # intersecta
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssociarAtributosPorLocal'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 9,
            'FIELD_NAME': 'id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': '\''+id+'\'',
            'INPUT': outputs['AssociarAtributosPorLocal']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Dissolver
        alg_params = {
            'FIELD': ['id'],
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo - Proprietario
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'proprietar',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': '\'' + proprietario + '\'',
            'INPUT': outputs['Dissolver']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoProprietario'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo - Tipo
        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'tipo',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Número inteiro
            'FORMULA': 0,     # 0 = propriedade; 1 = área implementada
            'INPUT': outputs['CalculadoraDeCampoProprietario']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoTipo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}
        
        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '\"id\"','length': 9,'name': 'id','precision': 0,'type': 10},{'expression': 'proprietar','length': 255,'name': 'proprietar','precision': 0,'type': 10},{'expression': 'to_date(now())','length': 0,'name': 'dt_arquivo','precision': 0,'type': 14},{'expression': '\"tipo\"','length': 1,'name': 'tipo','precision': 0,'type': 2}],
            'INPUT': outputs['CalculadoraDeCampoTipo']['OUTPUT'],
            'OUTPUT': parameters['refatorado']
        }
        outputs['EditarCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['refatorado'] = outputs['EditarCampos']['OUTPUT']
        return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'f2_refactor'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return 'Área Contratada / Propriedade'


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
    <h3>Preparar Arquivo da propriedade para envio ao Wrike</h3>
    <br>    Ferramenta utilizada para corrigir e preparar o arquivo da Área Contratada / Propriedade para ser carregado no Wrike.
        Selecione os arquivos que representem <b>apenas uma área em intervenção (ID_Area)</b>.
    Os arquivos selecionados podem ser de qualquer tipo de geometria: pontos, linhas ou polígonos, simultaneamente.
        Se arquivos de pontos forem selecionados, é possível definir em <b>Parâmetros avançados</b>, no campo <b>GRUPO</b>, um atributo destes pontos que delimite diferentes áreas, e no campo <b>SEQUÊNCIA</b> um atributo que indique a ordem ou sequência deles (Ex: data; vertex_id).
        Insira o número do ID da Área Implementada, selecione a Investida atuante, e indique o nome do Proprietário da Área.
    
    <b>O arquivo gerado deverá ser <font color=red>salvo</font> e estará pronto para <font color=red>envio</font> ao Wrike</b>.
    <br>    Para mais esclarecimentos clique no botão <b>Help</b> abaixo.
    
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'fundoVale.png')}"></center>
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'imafloraLogo.png')}"></center>

    Autor do algoritmo: Imaflora - Herbert Lincon R. A. dos Santos
    herbert.santos@imaflora.org
  </body>
</html>"""

    def icon(self):
        return QIcon(os.path.join(PLUGINPATH, 'imgs', 'wrikeLogo.svg'))
        
    def helpUrl(self):
        return 'www.'
        #TODO

    def tr(self, string):
        return QCoreApplication.translate('Processing2', string)

    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return f1_propriedade()
