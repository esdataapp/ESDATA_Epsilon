const express = require('express');
const csvService = require('../services/csvService');

const router = express.Router();

// GET /api/filters/property-types - Tipos de propiedad disponibles
router.get('/property-types', async (req, res) => {
  try {
    const types = csvService.getFilterOptions('tipos');
    
    const response = types.map(type => ({
      value: type.tipo,
      label: type.tipo,
      count: type.count
    }));
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /property-types:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo tipos de propiedad',
        details: error.message
      }
    });
  }
});

// GET /api/filters/operations - Tipos de operación disponibles
router.get('/operations', async (req, res) => {
  try {
    // Por ahora devolver operaciones estándar
    const operations = [
      { value: 'venta', label: 'Venta', count: 0 },
      { value: 'renta', label: 'Renta', count: 0 },
      { value: 'remate', label: 'Remate', count: 0 }
    ];
    
    res.json(operations);
    
  } catch (error) {
    console.error('Error en /operations:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo tipos de operación',
        details: error.message
      }
    });
  }
});

// GET /api/filters/municipalities - Municipios disponibles
router.get('/municipalities', async (req, res) => {
  try {
    const municipalities = csvService.getFilterOptions('municipios');
    
    const response = municipalities.map(muni => ({
      value: muni.municipio,
      label: muni.municipio,
      count: muni.count
    }));
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /municipalities:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo municipios',
        details: error.message
      }
    });
  }
});

// GET /api/filters/price-ranges - Rangos de precio sugeridos
router.get('/price-ranges', async (req, res) => {
  try {
    const kpis = csvService.getKPIs();
    
    // Generar rangos basados en los datos disponibles
    const avgPrice = kpis.precio_promedio?.value || 3000000;
    
    const ranges = {
      min: Math.round(avgPrice * 0.2), // 20% del promedio
      max: Math.round(avgPrice * 3),   // 300% del promedio
      suggested: [
        {
          label: 'Económico',
          min: Math.round(avgPrice * 0.2),
          max: Math.round(avgPrice * 0.6),
          description: 'Hasta $1.8M'
        },
        {
          label: 'Medio',
          min: Math.round(avgPrice * 0.6),
          max: Math.round(avgPrice * 1.4),
          description: '$1.8M - $4.2M'
        },
        {
          label: 'Premium',
          min: Math.round(avgPrice * 1.4),
          max: Math.round(avgPrice * 2.5),
          description: '$4.2M - $7.5M'
        },
        {
          label: 'Luxury',
          min: Math.round(avgPrice * 2.5),
          max: Math.round(avgPrice * 3),
          description: 'Más de $7.5M'
        }
      ],
      percentiles: {
        p25: Math.round(avgPrice * 0.7),
        p50: Math.round(avgPrice),
        p75: Math.round(avgPrice * 1.5),
        p90: Math.round(avgPrice * 2)
      }
    };
    
    res.json(ranges);
    
  } catch (error) {
    console.error('Error en /price-ranges:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo rangos de precio',
        details: error.message
      }
    });
  }
});

// GET /api/filters/surface-ranges - Rangos de superficie sugeridos
router.get('/surface-ranges', async (req, res) => {
  try {
    const kpis = csvService.getKPIs();
    
    // Generar rangos basados en los datos disponibles
    const avgSurface = kpis.superficie_promedio?.value || 100;
    
    const ranges = {
      min: 20,
      max: 500,
      suggested: [
        {
          label: 'Compacto',
          min: 20,
          max: 60,
          description: '20-60 m²'
        },
        {
          label: 'Estándar',
          min: 60,
          max: 120,
          description: '60-120 m²'
        },
        {
          label: 'Amplio',
          min: 120,
          max: 200,
          description: '120-200 m²'
        },
        {
          label: 'Mansión',
          min: 200,
          max: 500,
          description: 'Más de 200 m²'
        }
      ],
      percentiles: {
        p25: Math.round(avgSurface * 0.7),
        p50: Math.round(avgSurface),
        p75: Math.round(avgSurface * 1.4),
        p90: Math.round(avgSurface * 2)
      }
    };
    
    res.json(ranges);
    
  } catch (error) {
    console.error('Error en /surface-ranges:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo rangos de superficie',
        details: error.message
      }
    });
  }
});

// GET /api/filters/amenities - Amenidades disponibles
router.get('/amenities', async (req, res) => {
  try {
    const amenities = csvService.getAmenities();
    
    const response = amenities.map(amenity => ({
      value: amenity.amenidad,
      label: amenity.amenidad.charAt(0).toUpperCase() + amenity.amenidad.slice(1),
      category: categorizeAmenity(amenity.amenidad),
      impact: amenity.lift_porcentaje,
      popularity: amenity.count_con
    }));
    
    // Agrupar por categoría
    const grouped = response.reduce((acc, amenity) => {
      if (!acc[amenity.category]) {
        acc[amenity.category] = [];
      }
      acc[amenity.category].push(amenity);
      return acc;
    }, {});
    
    res.json({
      all: response,
      byCategory: grouped,
      categories: Object.keys(grouped)
    });
    
  } catch (error) {
    console.error('Error en /amenities:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo amenidades',
        details: error.message
      }
    });
  }
});

// GET /api/filters/bedrooms-bathrooms - Combinaciones de recámaras y baños
router.get('/bedrooms-bathrooms', async (req, res) => {
  try {
    const combinations = [
      { bedrooms: 1, bathrooms: [1, 1.5], label: '1 Rec + 1-1.5 Baños', segment: 'starter' },
      { bedrooms: 2, bathrooms: [2, 2.5], label: '2 Rec + 2-2.5 Baños', segment: 'family' },
      { bedrooms: 3, bathrooms: [3, 3.5], label: '3 Rec + 3-3.5 Baños', segment: 'premium' },
      { bedrooms: 4, bathrooms: [4, 4.5], label: '4+ Rec + 4+ Baños', segment: 'luxury' }
    ];
    
    res.json({
      combinations,
      individual: {
        bedrooms: [
          { value: 1, label: '1 Recámara', count: 0 },
          { value: 2, label: '2 Recámaras', count: 0 },
          { value: 3, label: '3 Recámaras', count: 0 },
          { value: 4, label: '4+ Recámaras', count: 0 }
        ],
        bathrooms: [
          { value: 1, label: '1 Baño', count: 0 },
          { value: 1.5, label: '1.5 Baños', count: 0 },
          { value: 2, label: '2 Baños', count: 0 },
          { value: 2.5, label: '2.5 Baños', count: 0 },
          { value: 3, label: '3 Baños', count: 0 },
          { value: 3.5, label: '3.5 Baños', count: 0 },
          { value: 4, label: '4+ Baños', count: 0 }
        ]
      }
    });
    
  } catch (error) {
    console.error('Error en /bedrooms-bathrooms:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo combinaciones de recámaras y baños',
        details: error.message
      }
    });
  }
});

// POST /api/filters/validate - Validar filtros
router.post('/validate', async (req, res) => {
  try {
    const filters = req.body;
    const validation = {
      valid: true,
      errors: [],
      warnings: [],
      suggestions: []
    };
    
    // Validar rangos de precio
    if (filters.priceRange) {
      const [min, max] = filters.priceRange;
      if (min >= max) {
        validation.valid = false;
        validation.errors.push('El precio mínimo debe ser menor al máximo');
      }
      if (min < 0) {
        validation.valid = false;
        validation.errors.push('El precio mínimo no puede ser negativo');
      }
      if (max > 50000000) {
        validation.warnings.push('El precio máximo es muy alto, podrías no encontrar resultados');
      }
    }
    
    // Validar rangos de superficie
    if (filters.surfaceRange) {
      const [min, max] = filters.surfaceRange;
      if (min >= max) {
        validation.valid = false;
        validation.errors.push('La superficie mínima debe ser menor a la máxima');
      }
      if (min < 10) {
        validation.warnings.push('La superficie mínima es muy pequeña');
      }
      if (max > 1000) {
        validation.warnings.push('La superficie máxima es muy grande');
      }
    }
    
    // Validar combinaciones lógicas
    if (filters.bedrooms && filters.bathrooms) {
      const maxBedrooms = Math.max(...filters.bedrooms);
      const maxBathrooms = Math.max(...filters.bathrooms);
      
      if (maxBathrooms > maxBedrooms + 2) {
        validation.warnings.push('Es inusual tener más baños que recámaras + 2');
      }
    }
    
    // Sugerencias basadas en filtros
    if (filters.priceRange && filters.surfaceRange) {
      const [minPrice, maxPrice] = filters.priceRange;
      const [minSurface, maxSurface] = filters.surfaceRange;
      const minPxm2 = minPrice / maxSurface;
      const maxPxm2 = maxPrice / minSurface;
      
      validation.suggestions.push(`Precio por m² estimado: $${Math.round(minPxm2/1000)}K - $${Math.round(maxPxm2/1000)}K`);
    }
    
    res.json(validation);
    
  } catch (error) {
    console.error('Error en /validate:', error);
    res.status(500).json({
      error: {
        message: 'Error validando filtros',
        details: error.message
      }
    });
  }
});

// GET /api/filters/presets - Filtros predefinidos
router.get('/presets', async (req, res) => {
  try {
    const presets = [
      {
        id: 'starter',
        name: 'Starter',
        description: 'Ideal para solteros o parejas jóvenes',
        icon: '🏠',
        filters: {
          bedrooms: [1],
          bathrooms: [1, 1.5],
          priceRange: [800000, 2500000],
          surfaceRange: [40, 80]
        }
      },
      {
        id: 'family',
        name: 'Familiar',
        description: 'Perfecto para familias pequeñas',
        icon: '👨‍👩‍👧‍👦',
        filters: {
          bedrooms: [2, 3],
          bathrooms: [2, 2.5, 3],
          priceRange: [2000000, 5000000],
          surfaceRange: [80, 150]
        }
      },
      {
        id: 'premium',
        name: 'Premium',
        description: 'Para quienes buscan exclusividad',
        icon: '✨',
        filters: {
          bedrooms: [3, 4],
          bathrooms: [3, 3.5, 4],
          priceRange: [4000000, 10000000],
          surfaceRange: [120, 250]
        }
      },
      {
        id: 'investment',
        name: 'Inversión',
        description: 'Propiedades con potencial de renta',
        icon: '💰',
        filters: {
          propertyType: ['Departamento'],
          priceRange: [1500000, 4000000],
          surfaceRange: [60, 120],
          amenitiesRequired: ['seguridad']
        }
      }
    ];
    
    res.json(presets);
    
  } catch (error) {
    console.error('Error en /presets:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo filtros predefinidos',
        details: error.message
      }
    });
  }
});

// Función auxiliar para categorizar amenidades
function categorizeAmenity(amenity) {
  const categories = {
    'seguridad': ['seguridad', 'vigilancia', 'caseta'],
    'recreacion': ['piscina', 'gym', 'alberca', 'juegos', 'salon'],
    'servicios': ['elevador', 'estacionamiento', 'lavanderia'],
    'espacios': ['terraza', 'jardin', 'roof', 'balcon'],
    'otros': []
  };
  
  for (const [category, keywords] of Object.entries(categories)) {
    if (keywords.some(keyword => amenity.toLowerCase().includes(keyword))) {
      return category;
    }
  }
  
  return 'otros';
}

module.exports = router;
