const express = require('express');
const csvService = require('../services/csvService');

const router = express.Router();

// GET /api/stats/overview - KPIs principales para vista Inicio
router.get('/overview', async (req, res) => {
  try {
    const startTime = Date.now();
    const { operacion = 'venta' } = req.query;
    
    // Obtener datos básicos por operación
    const kpis = csvService.getKPIs(operacion);
    const topColonies = csvService.getTopColonies(10, operacion);
    const propertyDistribution = csvService.getPropertyTypeDistribution(operacion);
    const timeSeries = csvService.getTimeSeries(operacion);
    
    // Generar insights automáticos básicos
    const insights = generateBasicInsights(kpis, topColonies, propertyDistribution);
    
    const executionTime = Date.now() - startTime;
    
    const response = {
      meta: {
        lastUpdate: new Date().toISOString(),
        dataVersion: 'v1.0',
        cached: true,
        executionTimeMs: executionTime,
        totalProperties: kpis.total_propiedades?.value || 0,
        operacion: operacion
      },
      data: {
        // KPIs principales
        totalProperties: kpis.total_propiedades?.value || 0,
        activeListings: kpis.total_propiedades?.value || 0,
        newListings30d: 0, // TODO: Calcular si hay datos temporales
        
        // Métricas de precio
        avgPrice: {
          value: kpis.precio_promedio?.value || 0,
          formatted: kpis.precio_promedio?.formatted || '$0',
          trend: 'stable'
        },
        medianPrice: {
          value: kpis.precio_mediana?.value || 0,
          formatted: kpis.precio_mediana?.formatted || '$0',
          trend: 'stable'
        },
        avgPxm2: {
          value: kpis.pxm2_promedio?.value || 0,
          formatted: kpis.pxm2_promedio?.formatted || '$0',
          trend: 'stable'
        },
        medianPxm2: {
          value: kpis.pxm2_mediana?.value || 0,
          formatted: kpis.pxm2_mediana?.formatted || '$0',
          trend: 'stable'
        },
        
        // Distribuciones
        byPropertyType: propertyDistribution.map(item => ({
          type: item.tipo_propiedad,
          count: item.precio_count,
          percentage: item.percentage,
          avgPrice: item.precio_mean,
          avgPxm2: item.precio_por_m2_mean || 0
        })),
        
        // Top colonias
        topColonies: topColonies.slice(0, 10).map(colony => ({
          name: colony.colonia,
          municipality: colony.municipio,
          count: colony.precio_count,
          avgPrice: colony.precio_mean,
          avgPxm2: colony.precio_por_m2_mean || 0,
          change30d: 0, // TODO: Calcular cambio real
          trend: 'stable'
        })),
        
        // Insights automáticos
        insights,
        
        // Tendencias (si hay datos)
        monthlyTrend: timeSeries.slice(-12).map(item => ({
          month: item.periodo,
          count: item.count,
          avgPrice: item.precio_mediano,
          changeFromPrevious: 0 // TODO: Calcular cambio
        })),
        
        // Estadísticas rápidas
        quickStats: {
          totalMunicipalities: 2, // Guadalajara y Zapopan
          totalColonies: topColonies.length,
          avgSurface: kpis.superficie_promedio?.value || 0,
          mostCommonBedrooms: 2, // TODO: Obtener de datos reales
          mostCommonBathrooms: 2
        }
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /overview:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo overview',
        details: error.message
      }
    });
  }
});

// POST /api/stats/filtered - Estadísticas con filtros aplicados
router.post('/filtered', async (req, res) => {
  try {
    const filters = req.body;
    const { operacion = 'venta' } = req.query;
    const startTime = Date.now();
    
    // Por ahora devolver datos sin filtrar (TODO: implementar filtrado real)
    const kpis = csvService.getKPIs(operacion);
    const topColonies = csvService.getTopColonies(20, operacion);
    
    const executionTime = Date.now() - startTime;
    
    const response = {
      meta: {
        totalMatches: kpis.total_propiedades?.value || 0,
        executionTimeMs: executionTime,
        filtersApplied: filters,
        cached: false,
        operacion: operacion
      },
      stats: {
        count: kpis.total_propiedades?.value || 0,
        price: {
          mean: kpis.precio_promedio?.value || 0,
          median: kpis.precio_mediana?.value || 0,
          min: 0, // TODO: Calcular desde datos
          max: 0  // TODO: Calcular desde datos
        },
        surface: {
          mean: kpis.superficie_promedio?.value || 0,
          median: 0, // TODO: Obtener mediana
          min: 0,
          max: 0
        },
        pxm2: {
          mean: kpis.pxm2_promedio?.value || 0,
          median: kpis.pxm2_mediana?.value || 0,
          min: 0,
          max: 0
        },
        byColony: topColonies.map(colony => ({
          colony: colony.colonia,
          municipality: colony.municipio,
          count: colony.precio_count,
          avgPrice: colony.precio_mean,
          avgPxm2: colony.precio_por_m2_mean || 0
        }))
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /filtered:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo estadísticas filtradas',
        details: error.message
      }
    });
  }
});

// GET /api/stats/histogram - Histograma pre-calculado
router.get('/histogram', async (req, res) => {
  try {
    const { variable = 'precios', geoLevel = 'zmg', geoId, operacion = 'venta' } = req.query;
    
    const histogram = csvService.getHistogram(variable, { geoLevel, geoId, operacion });
    
    res.json(histogram);
    
  } catch (error) {
    console.error('Error en /histogram:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo histograma',
        details: error.message
      }
    });
  }
});

// GET /api/stats/colonies/search - Búsqueda de colonias
router.get('/colonies/search', async (req, res) => {
  try {
    const { q: query = '', limit = 10 } = req.query;
    
    if (!query || query.length < 2) {
      return res.json([]);
    }
    
    const colonies = csvService.searchColonies(query, parseInt(limit));
    
    res.json(colonies);
    
  } catch (error) {
    console.error('Error en /colonies/search:', error);
    res.status(500).json({
      error: {
        message: 'Error buscando colonias',
        details: error.message
      }
    });
  }
});

// GET /api/stats/segments - Segmentos predefinidos
router.get('/segments', async (req, res) => {
  try {
    const { operacion = 'venta' } = req.query;
    const segments = csvService.getSegments(operacion);
    
    const response = {
      data: segments.map(segment => ({
        id: segment.segmento_id,
        name: segment.segmento_nombre,
        count: segment.count,
        priceRange: [segment.precio_p25, segment.precio_p75],
        medianPrice: segment.precio_mediana,
        surfaceRange: segment.superficie_mediana ? [segment.superficie_mediana * 0.8, segment.superficie_mediana * 1.2] : null,
        pxm2Range: segment.pxm2_mediana ? [segment.pxm2_p25, segment.pxm2_p75] : null
      }))
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /segments:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo segmentos',
        details: error.message
      }
    });
  }
});

// GET /api/stats/correlations - Matriz de correlaciones
router.get('/correlations', async (req, res) => {
  try {
    const { operacion = 'venta' } = req.query;
    const correlations = csvService.getCorrelations(operacion);
    
    const response = {
      data: {
        correlations: correlations.map(corr => ({
          variable1: corr.variable_1,
          variable2: corr.variable_2,
          correlation: corr.correlation,
          absCorrelation: corr.abs_correlation,
          interpretation: interpretCorrelation(corr.correlation)
        })),
        strongestPositive: correlations
          .filter(c => c.correlation > 0)
          .sort((a, b) => b.correlation - a.correlation)
          .slice(0, 5),
        strongestNegative: correlations
          .filter(c => c.correlation < 0)
          .sort((a, b) => a.correlation - b.correlation)
          .slice(0, 5)
      },
      meta: {
        totalPairs: correlations.length,
        calculatedAt: new Date().toISOString()
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /correlations:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo correlaciones',
        details: error.message
      }
    });
  }
});

// GET /api/stats/amenities - Análisis de amenidades
router.get('/amenities', async (req, res) => {
  try {
    const { operacion = 'venta' } = req.query;
    const amenities = csvService.getAmenities(operacion);
    
    const response = {
      data: amenities.map(amenity => ({
        amenityName: amenity.amenidad,
        countWith: amenity.count_con,
        priceWith: amenity.precio_con,
        priceWithout: amenity.precio_sin,
        liftPercentage: amenity.lift_porcentaje,
        significance: amenity.lift_porcentaje > 10 ? 'high' : amenity.lift_porcentaje > 5 ? 'medium' : 'low'
      })).sort((a, b) => b.liftPercentage - a.liftPercentage),
      meta: {
        totalAmenities: amenities.length,
        calculatedAt: new Date().toISOString()
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /amenities:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo análisis de amenidades',
        details: error.message
      }
    });
  }
});

// GET /api/stats/operations - Operaciones disponibles (venta/renta)
router.get('/operations', async (req, res) => {
  try {
    const operations = [
      {
        value: 'venta',
        label: 'Venta',
        icon: '🏠',
        description: 'Propiedades en venta',
        color: '#3B82F6'
      },
      {
        value: 'renta',
        label: 'Renta',
        icon: '🔑',
        description: 'Propiedades en renta',
        color: '#10B981'
      }
    ];
    
    res.json({
      data: operations,
      default: 'venta',
      meta: {
        total: operations.length,
        description: 'Toggle global para cambiar entre venta y renta sin afectar filtros'
      }
    });
    
  } catch (error) {
    console.error('Error en /operations:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo operaciones',
        details: error.message
      }
    });
  }
});

// Funciones auxiliares
function generateBasicInsights(kpis, topColonies, propertyDistribution) {
  const insights = [];
  
  // Insight sobre mercado
  insights.push({
    type: 'trend',
    title: 'Mercado Estable',
    description: `Se analizaron ${kpis.total_propiedades?.formatted || '0'} propiedades en la ZMG`,
    impact: 'medium'
  });
  
  // Insight sobre colonia top
  if (topColonies.length > 0) {
    const topColony = topColonies[0];
    insights.push({
      type: 'opportunity',
      title: `${topColony.colonia} Lidera Precios`,
      description: `La colonia con mayor precio por m² es ${topColony.colonia} en ${topColony.municipio}`,
      impact: 'high'
    });
  }
  
  // Insight sobre tipo de propiedad más común
  if (propertyDistribution.length > 0) {
    const mostCommon = propertyDistribution[0];
    insights.push({
      type: 'milestone',
      title: `${mostCommon.tipo_propiedad} Domina el Mercado`,
      description: `${mostCommon.percentage}% de las propiedades son ${mostCommon.tipo_propiedad.toLowerCase()}`,
      impact: 'medium'
    });
  }
  
  return insights;
}

function interpretCorrelation(r) {
  const abs_r = Math.abs(r);
  if (abs_r >= 0.7) return 'Fuerte';
  if (abs_r >= 0.5) return 'Moderada';
  if (abs_r >= 0.3) return 'Débil';
  return 'Muy débil';
}

module.exports = router;
