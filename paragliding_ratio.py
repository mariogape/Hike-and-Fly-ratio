"""
Model exported as python.
Name : prpnt_prueba
Group : 
With QGIS : 33408
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsCoordinateReferenceSystem
import processing


class Prpnt_prueba(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('mdt', 'MDT', defaultValue=None))
        self.addParameter(QgsProcessingParameterPoint('point', 'point', defaultValue='0.000000,0.000000'))
        self.addParameter(QgsProcessingParameterRasterDestination('ReaDePlaneo', 'Área de planeo', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(12, model_feedback)
        results = {}
        outputs = {}

        # vector punto
        alg_params = {
            'INPUT': parameters['point'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VectorPunto'] = processing.run('native:pointtolayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 2000,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['VectorPunto']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 10,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Sample raster values
        alg_params = {
            'COLUMN_PREFIX': 'SAMPLE_',
            'INPUT': outputs['VectorPunto']['OUTPUT'],
            'RASTERCOPY': parameters['mdt'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SampleRasterValues'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Vertices distancia
        alg_params = {
            'INPUT': outputs['Buffer']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerticesDistancia'] = processing.run('native:extractvertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Buffer clip
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 10000,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['VectorPunto']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferClip'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Join attributes by location
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['Buffer']['OUTPUT'],
            'JOIN': outputs['SampleRasterValues']['OUTPUT'],
            'JOIN_FIELDS': ['SAMPLE_1'],
            'METHOD': 2,  # Take attributes of the feature with largest overlap only (one-to-one)
            'PREDICATE': [1],  # contain
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByLocation'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Merge vector layers
        alg_params = {
            'CRS': QgsCoordinateReferenceSystem('EPSG:25830'),
            'LAYERS': [outputs['VerticesDistancia']['OUTPUT'],outputs['VectorPunto']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MergeVectorLayers'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Rasterize (vector to raster)
        alg_params = {
            'BURN': 0,
            'DATA_TYPE': 5,  # Float32
            'EXTENT': None,
            'EXTRA': '',
            'FIELD': 'SAMPLE_1',
            'HEIGHT': 1,
            'INIT': None,
            'INPUT': outputs['JoinAttributesByLocation']['OUTPUT'],
            'INVERT': False,
            'NODATA': -99,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeVectorToRaster'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Vertices rasterizados
        alg_params = {
            'BURN': 0,
            'DATA_TYPE': 5,  # Float32
            'EXTENT': None,
            'EXTRA': '',
            'FIELD': 'id',
            'HEIGHT': 1,
            'INIT': None,
            'INPUT': outputs['MergeVectorLayers']['OUTPUT'],
            'INVERT': False,
            'NODATA': -99,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VerticesRasterizados'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Proximity (raster distance)
        alg_params = {
            'BAND': 1,
            'DATA_TYPE': 5,  # Float32
            'EXTRA': '',
            'INPUT': outputs['VerticesRasterizados']['OUTPUT'],
            'MAX_DISTANCE': 2000,
            'NODATA': 0,
            'OPTIONS': '',
            'REPLACE': 0,
            'UNITS': 0,  # Georeferenced coordinates
            'VALUES': '1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ProximityRasterDistance'] = processing.run('gdal:proximity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTENT_OPT': 0,  # Ignore
            'EXTRA': '',
            'FORMULA': 'A-B-(C/5)',
            'INPUT_A': outputs['RasterizeVectorToRaster']['OUTPUT'],
            'INPUT_B': 'OUTPUT_c51b83ea_6e83_41da_b970_3b96fcf34a50',
            'INPUT_C': outputs['ProximityRasterDistance']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'PROJWIN': outputs['ProximityRasterDistance']['OUTPUT'],
            'RTYPE': 5,  # Float32
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Clip raster by mask layer
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['RasterCalculator']['OUTPUT'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['BufferClip']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': 0,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': outputs['RasterCalculator']['OUTPUT'],
            'TARGET_CRS': outputs['BufferClip']['OUTPUT'],
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['ReaDePlaneo']
        }
        outputs['ClipRasterByMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['ReaDePlaneo'] = outputs['ClipRasterByMaskLayer']['OUTPUT']
        return results

    def name(self):
        return 'prpnt_prueba'

    def displayName(self):
        return 'prpnt_prueba'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Prpnt_prueba()
