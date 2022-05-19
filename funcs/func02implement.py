"""
Model exported as python.
Name : func 01 - refactor
Group : implementacoes
"""

from matplotlib import lines
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDateTime,
                       QgsProcessingParameterField,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterBoolean,
                       QgsCoordinateReferenceSystem)
import processing
import os

from .merger import merger

PLUGINPATH = os.path.split(os.path.dirname(__file__))[0]

class f2_implement(QgsProcessingAlgorithm):
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
        self.addParameter(QgsProcessingParameterNumber('talhao', 'Número do talhão, parcela ou módulo (subdivisão do ID)', type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=99, defaultValue=1))

        self.addParameter(QgsProcessingParameterEnum('investida', 'Investida que atuou nesta área', options=['Belterra','Bioenergia','Caaporã','Inocas','Regenera'], allowMultiple=False, usesStaticStrings=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum('estado', 'Estado (UF) da área', options=['Acre','Alagoas','Amapá','Amazonas','Bahia','Ceará','Distrito Federal','Espírito Santo','Goiás','Maranhão','Mato Grosso','Mato Grosso do Sul','Minas Gerais','Pará','Paraíba','Paraná','Pernambuco','Piauí','Rio de Janeiro','Rio Grande do Norte','Rio Grande do Sul','Rondônia','Roraima','Santa Catarina','São Paulo','Sergipe','Tocantins'], allowMultiple=False, usesStaticStrings=False, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterEnum('culturas', 'Culturas utilizadas na Implementação (Apenas para Arquivo de Área Implementada)', options=['Abacaxi','Açaí','Andiroba','Banana','Cacau','Caju','Carnaúba','Castanha brasileira','Cedro australiano','Cedro brasileiro','Cumaru','Eucalipto','Freijó','Guanandi','Ipe','Ipê felpudo','Itaúba','Jacarandá','Jatobá','Jequetibá rosa','Limão','Louro pardo','Macaúba','Manga ','Maracujá ','Mogno africano','Moringa','Outras','Paricá','Pau de balsa','Pau rainha','Putumuju','Sucupira','Tatajuba','Teca','Vinhático','Outros - Descrever no campo abaixo'], optional=True, allowMultiple=True, usesStaticStrings=False, defaultValue=[]))
        self.addParameter(QgsProcessingParameterString('outros', 'Outras Culturas (separar por vírgulas)', optional=True, multiLine=False, defaultValue='Outra cultura não listada acima'))
       
        self.addParameter(QgsProcessingParameterDateTime('dataimplant', 'Data Final de Implementação', type=QgsProcessingParameterDateTime.Date, defaultValue='2022-01-01'))

        # configurações de pontos como avançados para que fiquem destacados
        group = QgsProcessingParameterField('group', 'Grupo (Caso os pontos representem mais de um polígono)', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue='')
        group.setFlags(group.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(group)
        idsequencia = QgsProcessingParameterField('idsequencia', 'Sequência (Atributo que define a sequência dos pontos como Data ou ID)', optional=True, type=QgsProcessingParameterField.Any, parentLayerParameterName='pontos', allowMultiple=False, defaultValue='')
        idsequencia.setFlags(idsequencia.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(idsequencia)

        linha = QgsProcessingParameterBoolean('emlinha', 'Plantio realizado em linhas ou faixas?', optional=True, defaultValue=False)
        linha.setFlags(linha.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(linha)
        buffer = QgsProcessingParameterNumber('buffer', 'Distância entre linhas', optional=True, type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=99, defaultValue=4)
        buffer.setFlags(buffer.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(buffer)
        
        self.addParameter(QgsProcessingParameterFeatureSink('refatorado', 'Polígonos Corrigidos para envio ao Wrike', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        """
        The processing itself.
        """
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(13, model_feedback)
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

        # receiving the inputs into variables
        data = parameters['dataimplant'].toString(Qt.ISODate)

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

        if parameters['estado'] == 0:
            uf = 'AC'

        elif parameters['estado'] == 1:
            uf = 'AL'

        elif parameters['estado'] == 2:
            uf = 'AP'

        elif parameters['estado'] == 3:
            uf = 'AM'

        elif parameters['estado'] == 4:
            uf = 'BA'

        elif parameters['estado'] == 5:
            uf = 'CE'

        elif parameters['estado'] == 6:
            uf = 'DF'

        elif parameters['estado'] == 7:
            uf = 'ES'

        elif parameters['estado'] == 8:
            uf = 'GO'

        elif parameters['estado'] == 9:
            uf = 'MA'

        elif parameters['estado'] == 10:
            uf = 'MT'

        elif parameters['estado'] == 11:
            uf = 'MS'

        elif parameters['estado'] == 12:
            uf = 'MG'

        elif parameters['estado'] == 13:
            uf = 'PA'

        elif parameters['estado'] == 14:
            uf = 'PB'

        elif parameters['estado'] == 15:
            uf = 'PR'

        elif parameters['estado'] == 16:
            uf = 'PE'

        elif parameters['estado'] == 17:
            uf = 'PI'

        elif parameters['estado'] == 18:
            uf = 'RJ'

        elif parameters['estado'] == 19:
            uf = 'RN'

        elif parameters['estado'] == 20:
            uf = 'RS'

        elif parameters['estado'] == 21:
            uf = 'RO'

        elif parameters['estado'] == 22:
            uf = 'RR'

        elif parameters['estado'] == 23:
            uf = 'SC'

        elif parameters['estado'] == 24:
            uf = 'SP'

        elif parameters['estado'] == 25:
            uf = 'SE'

        elif parameters['estado'] == 26:
            uf = 'TO'

        else:
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Valor inválido para ESTADO. Selecione uma opção válida e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return {}

        id = sigla + '-' + uf + str(parameters['id']).zfill(4) + '-' + str(parameters['talhao']).zfill(2)

        if str(parameters['outros']).strip() == 'Outra cultura não listada acima' or str(parameters['outros']).strip() == '':
            outros = ''

        else:
            outros = str(parameters['outros']).strip()
        
        if outros == '' and parameters['culturas'] == []:
            feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
            
            



            """)
            feedback.pushInfo("""Nenhuma CULTURA foi selecionada ou indicada no campo OUTRAS CULTURAS. Indique ao menos uma cultura e execute novamente.
            


            

            """)
            feedback.pushWarning("""Processo Encerrado.
            
            
            """)
            return {}

        # renomeando arquivo de saída
        parameters['refatorado'].destinationName = 'Salvar e Enviar ao Wrike'


        if parameters['emlinha'] is False:
            # plantio não foi realizado em linhas, será considerado polígono

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

            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            # Centroides
            alg_params = {
                'ALL_PARTS': True,
                'INPUT': outputs['merged']['merged'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Centroides'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}

            # Explodir linhas
            alg_params = {
                'INPUT': outputs['PolgonosParaLinhas']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ExplodirLinhas'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(4)
            if feedback.isCanceled():
                return {}

            # Poligonize
            alg_params = {
                'INPUT': outputs['ExplodirLinhas']['OUTPUT'],
                'KEEP_FIELDS': False,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Poligonize'] = processing.run('native:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(5)
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

            feedback.setCurrentStep(6)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo
            alg_params = {
                'FIELD_LENGTH': 15,
                'FIELD_NAME': 'id',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': '\''+id+'\'',
                'INPUT': outputs['AssociarAtributosPorLocal']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(7)
            if feedback.isCanceled():
                return {}

            # Dissolver
            alg_params = {
                'FIELD': ['id'],
                'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(8)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - Outros
            alg_params = {
                'FIELD_LENGTH': 255,
                'FIELD_NAME': 'outros',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': '\'' + outros + '\'',
                'INPUT': outputs['Dissolver']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoOutros'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(9)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - Culturas
            alg_params = {
                'FIELD_LENGTH': 255,
                'FIELD_NAME': 'culturas',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': '\''+ str(parameters['culturas']) + '\'',
                'INPUT': outputs['CalculadoraDeCampoOutros']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoCulturas'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(10)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - Tipo
            alg_params = {
                'FIELD_LENGTH': 1,
                'FIELD_NAME': 'tipo',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1,  # Número inteiro
                'FORMULA': 1,     # 0 = propriedade; 1 = área implementada
                'INPUT': outputs['CalculadoraDeCampoCulturas']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoTipo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(11)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - dt_implan
            alg_params = {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': 'dt_implant',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 3,  # Data
                'FORMULA': '\''+data+'\'',
                'INPUT': outputs['CalculadoraDeCampoTipo']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoDt_implan'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
            feedback.setCurrentStep(12)
            if feedback.isCanceled():
                return {}
            
            # Editar campos
            alg_params = {
                'FIELDS_MAPPING': [{'expression': '\"id\"','length': 15,'name': 'id','precision': 0,'type': 10},{'expression': 'if(\"culturas\"=0,NULL,\"culturas\")','length': 255,'name': 'culturas','precision': 0,'type': 10},{'expression': '\"outros\"','length': 255,'name': 'outros','precision': 0,'type': 10},{'expression': '\"dt_implant\"','length': 0,'name': 'dt_implant','precision': 0,'type': 14},{'expression': 'to_date(now())','length': 0,'name': 'dt_arquivo','precision': 0,'type': 14},{'expression': '\"tipo\"','length': 1,'name': 'tipo','precision': 0,'type': 2}],
                'INPUT': outputs['CalculadoraDeCampoDt_implan']['OUTPUT'],
                'OUTPUT': parameters['refatorado']
            }
            outputs['EditarCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['refatorado'] = outputs['EditarCampos']['OUTPUT']
            return results

        else:
            # plantio realizado em linhas, recusará polígonos
            if parameters['polgonos'] != None:
                feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
                
                



                """)
                feedback.pushInfo("""Foram inseridos polígonos e selecionado Plantio em Linhas. Esta combinação não é possível, corrija os dados de entrada e execute novamente.
                


                

                """)
                feedback.pushWarning("""Processo Encerrado.
                
                
                """)
                return {}

            elif parameters['pontos'] == None and parameters['linhas'] == None:
                feedback.reportError("""ATENÇÃO! OBSERVE O ERRO ABAIXO:
                
                



                """)
                feedback.pushInfo("""Não foram inseridos linhas ou pontos mas foi selecionado Plantio em Linhas. Corrija os dados de entrada e execute novamente.
                


                

                """)
                feedback.pushWarning("""Processo Encerrado.
                
                
                """)
                return {}

            geoms = []

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

                # Pontos para linhas
                alg_params = {
                    'CLOSE_PATH': True,
                    'GROUP_EXPRESSION': parameters['group'],
                    'INPUT': outputs['MesclarCamadasVetoriaisPontos']['OUTPUT'],
                    'NATURAL_SORT': True,
                    'ORDER_EXPRESSION': parameters['idsequencia'],
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['PontosParaLinhas'] = processing.run('native:pointstopath', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(2)
                if feedback.isCanceled():
                    return {}

                geoms.append(outputs['PontosParaLinhas']['OUTPUT'])

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

                geoms.append(outputs['MesclarCamadasVetoriaisLinhas']['OUTPUT'])

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

            # Drop field(s)
            alg_params = {
                'COLUMN': ['UTM'],
                'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DropFields'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(37)
            if feedback.isCanceled():
                return {}

            # Field calculator
            alg_params = {
                'FIELD_LENGTH': 6,
                'FIELD_NAME': 'id_a_utm',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1,  # Número inteiro
                'FORMULA': '$id',
                'INPUT': outputs['DropFields']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['FieldCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            # Diferença
            alg_params = {
                'INPUT': outputs['DropFields']['OUTPUT'],
                'OVERLAY': str(os.path.join(PLUGINPATH, 'data', 'br_grade_utm_wgs.shp')).replace('\\','/'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Diferena'] = processing.run('native:difference', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}

            count_erro = outputs['Diferena']['OUTPUT']

            if count_erro.featureCount() > 0:
                
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
                'FIELD_NAME': 'compr_base',
                'FIELD_PRECISION': 6,
                'FIELD_TYPE': 0,  # Float
                'FORMULA': 'length($geometry)',
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
                'FORMULA': 'if( "compr_base" = maximum( "compr_base","id_a_utm"),"UTM",NULL)',
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

            buffers = []

            buffer = int(parameters['buffer'])/2

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

            # Reprojetar camada 18
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo18']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31978'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada18'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(19)
            if feedback.isCanceled():
                return {}

            z18 = outputs['ReprojetarCamada18']['OUTPUT']
            
            if z18.featureCount() > 0:

                # Buffer 18
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada18']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer18'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer18']['OUTPUT'])

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
            outputs['ReprojetarCamada19'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(12)
            if feedback.isCanceled():
                return {}

            z19 = outputs['ReprojetarCamada19']['OUTPUT']
            
            if z19.featureCount() > 0:

                # Buffer 19
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada19']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer19'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer19']['OUTPUT'])

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

            # Reprojetar camada 20
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo20']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31980'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada20'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(24)
            if feedback.isCanceled():
                return {}

            z20 = outputs['ReprojetarCamada20']['OUTPUT']
            
            if z20.featureCount() > 0:

                # Buffer 20
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada20']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer20'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer20']['OUTPUT'])

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

            # Reprojetar camada 21
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo21']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31981'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada21'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(28)
            if feedback.isCanceled():
                return {}

            z21 = outputs['ReprojetarCamada21']['OUTPUT']
            
            if z21.featureCount() > 0:

                # Buffer 21
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada21']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer21'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer21']['OUTPUT'])

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

            # Reprojetar camada 22
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo22']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31982'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada22'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(26)
            if feedback.isCanceled():
                return {}

            z22 = outputs['ReprojetarCamada22']['OUTPUT']
            
            if z22.featureCount() > 0:

                # Buffer 22
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada22']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer22'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer22']['OUTPUT'])

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

            # Reprojetar camada 23
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo23']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31983'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada23'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(27)
            if feedback.isCanceled():
                return {}

            z23 = outputs['ReprojetarCamada23']['OUTPUT']
            
            if z23.featureCount() > 0:

                # Buffer 23
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada23']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer23'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer23']['OUTPUT'])

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

            # Reprojetar camada 24
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo24']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31984'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada24'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(22)
            if feedback.isCanceled():
                return {}

            z24 = outputs['ReprojetarCamada24']['OUTPUT']
            
            if z24.featureCount() > 0:

                # Buffer 24
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada24']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer24'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer24']['OUTPUT'])

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

            # Reprojetar camada 25
            alg_params = {
                'INPUT': outputs['ExtrairPorAtributo25']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:31985'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojetarCamada25'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback)

            feedback.setCurrentStep(17)
            if feedback.isCanceled():
                return {}

            z25 = outputs['ReprojetarCamada25']['OUTPUT']
            
            if z25.featureCount() > 0:

                # Buffer 25
                alg_params = {
                    'DISSOLVE': True,
                    'DISTANCE': buffer,
                    'END_CAP_STYLE': 1,  # Plano
                    'INPUT': outputs['ReprojetarCamada25']['OUTPUT'],
                    'JOIN_STYLE': 0,  # Arredondado
                    'MITER_LIMIT': 2,
                    'SEGMENTS': 5,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Buffer25'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                feedback.setCurrentStep(1)
                if feedback.isCanceled():
                    return {}

                buffers.append(outputs['Buffer25']['OUTPUT'])



            # Mesclar camadas vetoriais UTM
            alg_params = {
                'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                'LAYERS': buffers,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['MesclarCamadasVetoriaisUtm'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(34)
            if feedback.isCanceled():
                return {}

            # Dissolver
            alg_params = {
                'FIELD': ['id_a_utm'],
                'INPUT': outputs['MesclarCamadasVetoriaisUtm']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(36)
            if feedback.isCanceled():
                return {}



            # Calculadora de campo
            alg_params = {
                'FIELD_LENGTH': 15,
                'FIELD_NAME': 'id',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': '\''+id+'\'',
                'INPUT': outputs['Dissolver']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(7)
            if feedback.isCanceled():
                return {}

            # Dissolver
            alg_params = {
                'FIELD': ['id'],
                'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(8)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - Outros
            alg_params = {
                'FIELD_LENGTH': 255,
                'FIELD_NAME': 'outros',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': '\'' + outros + '\'',
                'INPUT': outputs['Dissolver']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoOutros'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(9)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - Culturas
            alg_params = {
                'FIELD_LENGTH': 255,
                'FIELD_NAME': 'culturas',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 2,  # String
                'FORMULA': '\''+ str(parameters['culturas']) + '\'',
                'INPUT': outputs['CalculadoraDeCampoOutros']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoCulturas'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(10)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - Tipo
            alg_params = {
                'FIELD_LENGTH': 1,
                'FIELD_NAME': 'tipo',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1,  # Número inteiro
                'FORMULA': 1,     # 0 = propriedade; 1 = área implementada
                'INPUT': outputs['CalculadoraDeCampoCulturas']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoTipo'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(11)
            if feedback.isCanceled():
                return {}

            # Calculadora de campo - dt_implan
            alg_params = {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': 'dt_implant',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 3,  # Data
                'FORMULA': '\''+data+'\'',
                'INPUT': outputs['CalculadoraDeCampoTipo']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['CalculadoraDeCampoDt_implan'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
            feedback.setCurrentStep(12)
            if feedback.isCanceled():
                return {}
            
            # Editar campos
            alg_params = {
                'FIELDS_MAPPING': [{'expression': '\"id\"','length': 15,'name': 'id','precision': 0,'type': 10},{'expression': 'if(\"culturas\"=0,NULL,\"culturas\")','length': 255,'name': 'culturas','precision': 0,'type': 10},{'expression': '\"outros\"','length': 255,'name': 'outros','precision': 0,'type': 10},{'expression': '\"dt_implant\"','length': 0,'name': 'dt_implant','precision': 0,'type': 14},{'expression': 'to_date(now())','length': 0,'name': 'dt_arquivo','precision': 0,'type': 14},{'expression': '\"tipo\"','length': 1,'name': 'tipo','precision': 0,'type': 2}],
                'INPUT': outputs['CalculadoraDeCampoDt_implan']['OUTPUT'],
                'OUTPUT': parameters['refatorado']
            }
            outputs['EditarCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['refatorado'] = outputs['EditarCampos']['OUTPUT']
            return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'f1_refactor'

    def displayName(self):
        """
        Returns the translated algorithm name, used for any
        user-visible display of the algorithm name.
        """
        return 'Área Implementada (Final)'


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
    <h2>Sistema de Validação de Polígonos (SVP) Compromisso Florestal</h2>
    <h3>Preparar Arquivo da área implementada para envio ao Wrike</h3>
    <br>    Ferramenta utilizada para corrigir e preparar o arquivo da Área Implementada para ser carregado no Wrike.
        Selecione os arquivos que representem <b>apenas uma área em intervenção (ID_Area)</b>.
    Os arquivos selecionados podem ser de qualquer tipo de geometria: pontos, linhas ou polígonos, simultaneamente.
        Se arquivos de pontos forem selecionados, é possível definir em <b>Parâmetros avançados</b>, no campo <b>GRUPO</b>, um atributo destes pontos que delimite diferentes áreas, e no campo <b>SEQUÊNCIA</b> um atributo que indique a ordem ou sequência deles (Ex: data; vertex_id).
        Insira o número do ID da Área Implementada, selecione a Investida atuante, selecione as Culturas utilizadas e/ou descreva em Outros caso tenha utilizado alguma que <u>não esteja abrangida na listagem</u> e indique a <b>Data Final</b> de implementação.
    
    <b>O arquivo gerado deverá ser <font color=red>salvo</font> com a nomenclatura <b>AAA-UF0000-00_implementado</b> e estará pronto para <font color=red>envio</font> ao Wrike</b>.
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
        return 'File:///' + os.path.join(PLUGINPATH, 'manuals', 'f2_implementacao.pdf')

    def tr(self, string):
        return QCoreApplication.translate('Processing2', string)

    def createInstance(self):
        """
        Create the instance accessed by fvale_mflorestal_provider.
        """
        return f2_implement()
