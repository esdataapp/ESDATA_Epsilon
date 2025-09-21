const express = require('express');
const csvService = require('../services/csvService');

const router = express.Router();

// GET /api/geo/heatmap - Datos para mapa de calor
router.get('/heatmap', async (req, res) => {
  try {
    const { 
      metric = 'pxm2', 
      geoLevel = 'colony',
      bounds,
      zoom = 10,
      operacion = 'venta'
    } = req.query;
    
    const mapData = csvService.getMapData(operacion);
    
    // Filtrar por bounds si se proporcionan
    let filteredData = mapData;
    if (bounds) {
      try {
        const boundsObj = JSON.parse(bounds);
        // TODO: Implementar filtrado por bounds geográficos
        // Por ahora devolver todos los datos
      } catch (error) {
        console.warn('Error parsing bounds:', error);
      }
    }
    
    // Generar escala de colores
    const values = filteredData.map(item => item.precio_mediano || 0).filter(v => v > 0);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    
    const colorScale = [
      { value: minValue, color: '#4575b4', label: `$${Math.round(minValue/1000)}K` },
      { value: minValue + (maxValue - minValue) * 0.25, color: '#abd9e9', label: `$${Math.round((minValue + (maxValue - minValue) * 0.25)/1000)}K` },
      { value: minValue + (maxValue - minValue) * 0.5, color: '#fdae61', label: `$${Math.round((minValue + (maxValue - minValue) * 0.5)/1000)}K` },
      { value: minValue + (maxValue - minValue) * 0.75, color: '#f46d43', label: `$${Math.round((minValue + (maxValue - minValue) * 0.75)/1000)}K` },
      { value: maxValue, color: '#d73027', label: `$${Math.round(maxValue/1000)}K` }
    ];
    
    const response = {
      type: 'FeatureCollection',
      features: filteredData.map(item => ({
        type: 'Feature',
        properties: {
          geoId: `${item.colonia}_${item.municipio}`,
          name: item.colonia,
          municipality: item.municipio,
          value: item.precio_mediano || 0,
          normalizedValue: item.percentile || 0,
          percentile: item.percentile || 0,
          color: item.color || '#4575b4',
          
          // Datos adicionales para tooltip
          count: item.count || 0,
          avgPrice: item.precio_mediano || 0,
          trend30d: 0 // TODO: Calcular tendencia real
        },
        geometry: {
          type: 'Point',
          coordinates: [
            item.longitud_mean || -103.3496, // Coordenada por defecto de Guadalajara
            item.latitud_mean || 20.6597
          ]
        }
      })),
      meta: {
        metric,
        geoLevel,
        colorScale,
        valueRange: [minValue, maxValue],
        totalFeatures: filteredData.length,
        zoom: parseInt(zoom)
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /geo/heatmap:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo datos del mapa de calor',
        details: error.message
      }
    });
  }
});

// GET /api/geo/clusters - Clustering para mapa según zoom
router.get('/clusters', async (req, res) => {
  try {
    const { 
      bounds,
      zoom = 10,
      filters = {}
    } = req.query;
    
    const mapData = csvService.getMapData();
    
    // Determinar estrategia de clustering según zoom
    let clusteredData;
    const zoomLevel = parseInt(zoom);
    
    if (zoomLevel <= 10) {
      // Zoom bajo: Agrupar por municipio
      clusteredData = clusterByMunicipality(mapData);
    } else if (zoomLevel <= 13) {
      // Zoom medio: Agrupar colonias cercanas
      clusteredData = clusterByProximity(mapData, 0.01); // ~1km
    } else {
      // Zoom alto: Mostrar colonias individuales
      clusteredData = mapData.map(item => ({
        type: 'Feature',
        properties: {
          cluster: false,
          propertyId: `${item.colonia}_${item.municipio}`,
          name: item.colonia,
          municipality: item.municipio,
          price: item.precio_mediano,
          count: item.count,
          propertyType: 'colony'
        },
        geometry: {
          type: 'Point',
          coordinates: [
            item.longitud_mean || -103.3496,
            item.latitud_mean || 20.6597
          ]
        }
      }));
    }
    
    const response = {
      type: 'FeatureCollection',
      features: clusteredData,
      meta: {
        zoom: zoomLevel,
        strategy: zoomLevel <= 10 ? 'municipality' : zoomLevel <= 13 ? 'proximity' : 'individual',
        totalFeatures: clusteredData.length
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Error en /geo/clusters:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo clusters del mapa',
        details: error.message
      }
    });
  }
});

// GET /api/geo/boundaries - Límites geográficos simplificados
router.get('/boundaries', async (req, res) => {
  try {
    const { level = 'municipality' } = req.query;
    
    // Por ahora devolver boundaries básicos de Guadalajara y Zapopan
    const boundaries = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            name: 'Guadalajara',
            type: 'municipality',
            population: 1385629
          },
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [-103.4, 20.6],
              [-103.3, 20.6],
              [-103.3, 20.7],
              [-103.4, 20.7],
              [-103.4, 20.6]
            ]]
          }
        },
        {
          type: 'Feature',
          properties: {
            name: 'Zapopan',
            type: 'municipality',
            population: 1476491
          },
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [-103.5, 20.6],
              [-103.4, 20.6],
              [-103.4, 20.8],
              [-103.5, 20.8],
              [-103.5, 20.6]
            ]]
          }
        }
      ]
    };
    
    res.json(boundaries);
    
  } catch (error) {
    console.error('Error en /geo/boundaries:', error);
    res.status(500).json({
      error: {
        message: 'Error obteniendo límites geográficos',
        details: error.message
      }
    });
  }
});

// GET /api/geo/search - Búsqueda geográfica
router.get('/search', async (req, res) => {
  try {
    const { q: query = '', type = 'all' } = req.query;
    
    if (!query || query.length < 2) {
      return res.json([]);
    }
    
    const mapData = csvService.getMapData();
    
    let results = [];
    
    // Buscar colonias
    if (type === 'all' || type === 'colony') {
      const colonies = mapData
        .filter(item => 
          item.colonia && 
          item.colonia.toLowerCase().includes(query.toLowerCase())
        )
        .map(item => ({
          type: 'colony',
          name: item.colonia,
          municipality: item.municipio,
          displayName: `${item.colonia}, ${item.municipio}`,
          coordinates: [
            item.longitud_mean || -103.3496,
            item.latitud_mean || 20.6597
          ],
          properties: item.count || 0
        }))
        .slice(0, 10);
      
      results = results.concat(colonies);
    }
    
    // Buscar municipios
    if (type === 'all' || type === 'municipality') {
      const municipalities = ['Guadalajara', 'Zapopan']
        .filter(muni => muni.toLowerCase().includes(query.toLowerCase()))
        .map(muni => ({
          type: 'municipality',
          name: muni,
          displayName: muni,
          coordinates: muni === 'Guadalajara' ? [-103.3496, 20.6597] : [-103.4500, 20.7333],
          properties: mapData.filter(item => item.municipio === muni).length
        }));
      
      results = results.concat(municipalities);
    }
    
    res.json(results);
    
  } catch (error) {
    console.error('Error en /geo/search:', error);
    res.status(500).json({
      error: {
        message: 'Error en búsqueda geográfica',
        details: error.message
      }
    });
  }
});

// Funciones auxiliares para clustering
function clusterByMunicipality(mapData) {
  const municipalityGroups = {};
  
  mapData.forEach(item => {
    const muni = item.municipio;
    if (!municipalityGroups[muni]) {
      municipalityGroups[muni] = {
        items: [],
        totalCount: 0,
        totalPrice: 0,
        coordinates: []
      };
    }
    
    municipalityGroups[muni].items.push(item);
    municipalityGroups[muni].totalCount += item.count || 0;
    municipalityGroups[muni].totalPrice += (item.precio_mediano || 0) * (item.count || 0);
    
    if (item.longitud_mean && item.latitud_mean) {
      municipalityGroups[muni].coordinates.push([item.longitud_mean, item.latitud_mean]);
    }
  });
  
  return Object.entries(municipalityGroups).map(([muni, group]) => {
    const avgLng = group.coordinates.length > 0 
      ? group.coordinates.reduce((sum, coord) => sum + coord[0], 0) / group.coordinates.length
      : (muni === 'Guadalajara' ? -103.3496 : -103.4500);
    
    const avgLat = group.coordinates.length > 0
      ? group.coordinates.reduce((sum, coord) => sum + coord[1], 0) / group.coordinates.length
      : (muni === 'Guadalajara' ? 20.6597 : 20.7333);
    
    return {
      type: 'Feature',
      properties: {
        cluster: true,
        clusterId: muni,
        pointCount: group.totalCount,
        pointCountAbbreviated: group.totalCount > 1000 ? `${Math.round(group.totalCount/1000)}K` : group.totalCount.toString(),
        avgPrice: group.totalCount > 0 ? group.totalPrice / group.totalCount : 0,
        municipality: muni,
        colonies: group.items.length
      },
      geometry: {
        type: 'Point',
        coordinates: [avgLng, avgLat]
      }
    };
  });
}

function clusterByProximity(mapData, threshold) {
  // Clustering simple por proximidad
  const clusters = [];
  const processed = new Set();
  
  mapData.forEach((item, index) => {
    if (processed.has(index)) return;
    
    const cluster = {
      items: [item],
      totalCount: item.count || 0,
      totalPrice: (item.precio_mediano || 0) * (item.count || 0),
      coordinates: [[item.longitud_mean || -103.3496, item.latitud_mean || 20.6597]]
    };
    
    processed.add(index);
    
    // Buscar items cercanos
    mapData.forEach((otherItem, otherIndex) => {
      if (processed.has(otherIndex)) return;
      
      const distance = calculateDistance(
        item.latitud_mean || 20.6597,
        item.longitud_mean || -103.3496,
        otherItem.latitud_mean || 20.6597,
        otherItem.longitud_mean || -103.3496
      );
      
      if (distance < threshold) {
        cluster.items.push(otherItem);
        cluster.totalCount += otherItem.count || 0;
        cluster.totalPrice += (otherItem.precio_mediano || 0) * (otherItem.count || 0);
        cluster.coordinates.push([otherItem.longitud_mean || -103.3496, otherItem.latitud_mean || 20.6597]);
        processed.add(otherIndex);
      }
    });
    
    clusters.push(cluster);
  });
  
  return clusters.map((cluster, index) => {
    const avgLng = cluster.coordinates.reduce((sum, coord) => sum + coord[0], 0) / cluster.coordinates.length;
    const avgLat = cluster.coordinates.reduce((sum, coord) => sum + coord[1], 0) / cluster.coordinates.length;
    
    if (cluster.items.length === 1) {
      // Item individual
      const item = cluster.items[0];
      return {
        type: 'Feature',
        properties: {
          cluster: false,
          propertyId: `${item.colonia}_${item.municipio}`,
          name: item.colonia,
          municipality: item.municipio,
          price: item.precio_mediano,
          count: item.count
        },
        geometry: {
          type: 'Point',
          coordinates: [avgLng, avgLat]
        }
      };
    } else {
      // Cluster
      return {
        type: 'Feature',
        properties: {
          cluster: true,
          clusterId: `cluster_${index}`,
          pointCount: cluster.totalCount,
          pointCountAbbreviated: cluster.totalCount > 1000 ? `${Math.round(cluster.totalCount/1000)}K` : cluster.totalCount.toString(),
          avgPrice: cluster.totalCount > 0 ? cluster.totalPrice / cluster.totalCount : 0,
          colonies: cluster.items.length
        },
        geometry: {
          type: 'Point',
          coordinates: [avgLng, avgLat]
        }
      };
    }
  });
}

function calculateDistance(lat1, lng1, lat2, lng2) {
  const R = 6371; // Radio de la Tierra en km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

module.exports = router;
