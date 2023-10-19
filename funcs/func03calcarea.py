"""
Model exported as python.
Name : func 03 - calculate area
Group : outras ferramentas
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem)
import processing
import os

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]

class f3_calcarea(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('poligonos', 'Arquivo de Polígonos', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('area', 'Área Calculada', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('erro', 'Arquivo com Erro', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(40, model_feedback)
        results = {}
        outputs = {}

        # renomeando arquivos de saída
        parameters['area'].destinationName = 'Área Calculada'
        parameters['erro'].destinationName = 'Arquivo com Erro'

        # Reprojetar camada
        alg_params = {
            'INPUT': parameters['poligonos'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Field calculator
        alg_params = {
            'FIELD_LENGTH': 6,
            'FIELD_NAME': 'id_a_utm',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Número inteiro
            'FORMULA': '$id',
            'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Diferença
        alg_params = {
            'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
            'OVERLAY': str(os.path.join(PLUGINPATH, 'data', 'br_grade_utm_wgs.shp')).replace('\\','/'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Diferena'] = processing.run('native:difference', alg_params, context=context, feedback=feedback)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        count_erro = outputs['Diferena']['OUTPUT']

        if count_erro.featureCount() > 0:

            # Diferença
            alg_params = {
                'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
                'OVERLAY': str(os.path.join(PLUGINPATH, 'data', 'br_grade_utm_wgs.shp')).replace('\\','/'),
                'OUTPUT': parameters['erro']
            }
            outputs['Diferena2'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['erro'] = outputs['Diferena2']['OUTPUT']
            
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Existem polígonos em seu arquivo que estão fora do Brasil. Corrija o arquivo e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return results


        # Multipart to singleparts
        alg_params = {
            'INPUT': outputs['FieldCalculator']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MultipartToSingleparts'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Interseção 
        alg_params = {
            'INPUT': outputs['MultipartToSingleparts']['OUTPUT'],
            'INPUT_FIELDS': ['id_a_utm'],
            'OVERLAY': str(os.path.join(PLUGINPATH, 'data', 'br_grade_utm_wgs.shp')).replace('\\','/'),
            'OVERLAY_FIELDS': ['UTM'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Interseo'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo area base
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_base',
            'FIELD_PRECISION': 6,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)',
            'INPUT': outputs['Interseo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAreaBase'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo area base 2
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'UTM',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Número inteiro
            'FORMULA': 'if( "area_base" = maximum( "area_base","id_a_utm"),"UTM",NULL)',
            'INPUT': outputs['CalculadoraDeCampoAreaBase']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAreaBase2'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['CalculadoraDeCampoAreaBase2']['OUTPUT'],
            'OPERATOR': 9,  # não é nulo
            'VALUE': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Unir atributos pelo valor do campo - major UTM
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id_a_utm',
            'FIELDS_TO_COPY': ['UTM'],
            'FIELD_2': 'id_a_utm',
            'INPUT': outputs['MultipartToSingleparts']['OUTPUT'],
            'INPUT_2': outputs['ExtrairPorAtributo']['OUTPUT'],
            'METHOD': 1,  # Tomar atributos apenas da primeira feição coincidente (uma-por-uma)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnirAtributosPeloValorDoCampoMajorUtm'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 18
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '18',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo18'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 19
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '19',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo19'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 19
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo19']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31979'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada19'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 22
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '22',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo22'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 25
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '25',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo25'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 19
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada19']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea19'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 23
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '23',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo23'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 25
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo25']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31985'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada25'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 24
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '24',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo24'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 18
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo18']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31978'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada18'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 25
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada25']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea25'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 20
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '20',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo20'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 24
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo24']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31984'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada24'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo 21
        alg_params = {
            'FIELD': 'UTM',
            'INPUT': outputs['UnirAtributosPeloValorDoCampoMajorUtm']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '21',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo21'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 20
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo20']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31980'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada20'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 18
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada18']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea18'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 22
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo22']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31982'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada22'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 23
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo23']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31983'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada23'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada 21
        alg_params = {
            'INPUT': outputs['ExtrairPorAtributo21']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31981'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojetarCamada21'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 22
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada22']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea22'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 21
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada21']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea21'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 23
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada23']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea23'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 24
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada24']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea24'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo AREA 20
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'area($geometry)/10000',
            'INPUT': outputs['ReprojetarCamada20']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoArea20'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(33)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais UTM
        alg_params = {
            'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'LAYERS': [outputs['CalculadoraDeCampoArea18']['OUTPUT'],outputs['CalculadoraDeCampoArea22']['OUTPUT'],outputs['CalculadoraDeCampoArea20']['OUTPUT'],outputs['CalculadoraDeCampoArea19']['OUTPUT'],outputs['CalculadoraDeCampoArea21']['OUTPUT'],outputs['CalculadoraDeCampoArea25']['OUTPUT'],outputs['CalculadoraDeCampoArea24']['OUTPUT'],outputs['CalculadoraDeCampoArea23']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriaisUtm'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(34)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'areaha_utm',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'sum("area_utm","id_a_utm")',
            'INPUT': outputs['MesclarCamadasVetoriaisUtm']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(35)
        if feedback.isCanceled():
            return {}

        # Dissolver
        alg_params = {
            'FIELD': ['id_a_utm'],
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(36)
        if feedback.isCanceled():
            return {}

        # Drop field(s)
        alg_params = {
            'COLUMN': ['area_utm'],
            'INPUT': outputs['Dissolver']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DropFields'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(37)
        if feedback.isCanceled():
            return {}

        # Drop field(s) 2
        alg_params = {
            'COLUMN': ['id_a_utm'],
            'INPUT': outputs['DropFields']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DropFields2'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(38)
        if feedback.isCanceled():
            return {}

        # Drop field(s) 3
        alg_params = {
            'COLUMN': ['layer'],
            'INPUT': outputs['DropFields2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DropFields3'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(39)
        if feedback.isCanceled():
            return {}

        # Drop field(s) 4
        alg_params = {
            'COLUMN': ['path'],
            'INPUT': outputs['DropFields3']['OUTPUT'],
            'OUTPUT': parameters['area']
        }
        outputs['DropFields4'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Area'] = outputs['DropFields4']['OUTPUT']
        return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'f3_calcarea'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return 'Calcular Área Planimétrica'

    # def group(self):
    #     """
    #     Returns the name of the group this algorithm belongs to.
    #     """
    #     return 'Outras Ferramentas'

    # def groupId(self):
    #     """
    #     Returns the unique ID of the group this algorithm belongs to.
    #     """
    #     return 'outras'


    def shortHelpString(self):
        """
        Returns the help text as HTML displayed to the users when executed.
        """
        return f"""<html>
  <body bgcolor=#fcfcfc style="font-family:Tahoma;text-align:justify;">      
    <h2>Sistema de Validação de Polígonos (SVP) Meta Florestal</h2>
    <h3>Calcular a área planimétrica dos polígonos</h3>
    <br>    Ferramenta utilizada para calcular a área planimétrica dos polígonos inseridos.
        Selecione o arquivo com os polígonos que deseja calcular (é possível inserir o resultado da função Preparar Polígonos (Shapefile)).
        Apenas arquivos de polígonos são aceitos.
        A área é calculada respeitando a <b>Zona UTM</b> majoritária do polígono e através da função <b>area($geometry)</b>.
        O arquivo de saída terá duas novas colunas em sua tabela de atributos onde:<br><b>UTM</b> - é a Zona UTM em que o polígono foi enquadrado<br><b>areaha_utm</b> - Área em hectares calculada
    
    Não é necessário salvar ou enviar este arquivo.
    <br>    Para mais esclarecimentos clique no botão <b>Help</b> abaixo.
    
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'fundoVale.png')}"></center>
    <center><img width=200 src="{os.path.join(PLUGINPATH, 'imgs', 'imafloraLogo.png')}"></center>

    Autor do algoritmo: Imaflora - Herbert Lincon R. A. dos Santos
    herbert.santos@imaflora.org
  </body>
</html>"""

    def icon(self):
        return QIcon(os.path.join(PLUGINPATH, 'imgs', 'area.png'))
        
    def helpUrl(self):
        return 'File:///' + os.path.join(PLUGINPATH, 'manuals', 'f3_calcarea.pdf')

    def tr(self, string):
        return QCoreApplication.translate('Processing2', string)

    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return f3_calcarea()
