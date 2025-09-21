const fs = require('fs').promises;
const path = require('path');
const csv = require('csv-parser');
const NodeCache = require('node-cache');

class CSVService {
  constructor() {
    // Cache con TTL de 30 minutos
    this.cache = new NodeCache({ stdTTL: 1800, checkperiod: 120 });
    this.dataPath = null;
    this.loadedFiles = [];
    this.data = {};
  }

  async initialize() {
    // Buscar directorio de datos
    const possiblePaths = [
      path.join(__dirname, '..', '..', '..', 'data'),
      path.join(__dirname, '..', '..', 'data'),
      path.join(process.cwd(), 'data')
    ];

    for (const dataPath of possiblePaths) {
      try {
        await fs.access(dataPath);
        this.dataPath = dataPath;
        break;
      } catch (error) {
        continue;
      }
    }

    if (!this.dataPath) {
      throw new Error('No se encontró el directorio de datos. Ejecuta primero el script generate_dashboard_data.py');
    }

    console.log(`📁 Directorio de datos: ${this.dataPath}`);

    // Cargar todos los CSVs
    await this.loadAllCSVs();
  }

  async loadAllCSVs() {
    const subdirs = ['basicos', 'histogramas', 'segmentos', 'correlaciones', 'amenidades', 'geoespacial', 'series_temporales', 'filtros'];
    
    for (const subdir of subdirs) {
      const subdirPath = path.join(this.dataPath, subdir);
      
      try {
        const files = await fs.readdir(subdirPath);
        const csvFiles = files.filter(file => file.endsWith('.csv'));
        
        for (const file of csvFiles) {
          const filePath = path.join(subdirPath, file);
          const key = `${subdir}/${file.replace('.csv', '')}`;
          
          try {
            const data = await this.loadCSV(filePath);
            this.data[key] = data;
            this.loadedFiles.push(key);
            console.log(`  ✅ Cargado: ${key} (${data.length} filas)`);
          } catch (error) {
            console.warn(`  ⚠️ Error cargando ${key}:`, error.message);
          }
        }
      } catch (error) {
        console.warn(`  ⚠️ No se pudo acceder a ${subdir}:`, error.message);
      }
    }

    console.log(`📊 Total archivos cargados: ${this.loadedFiles.length}`);
  }

  async loadCSV(filePath) {
    return new Promise((resolve, reject) => {
      const results = [];
      const stream = require('fs').createReadStream(filePath);
      
      stream
        .pipe(csv())
        .on('data', (data) => {
          // Convertir strings numéricos a números
          const processedData = {};
          for (const [key, value] of Object.entries(data)) {
            if (value === '' || value === null || value === undefined) {
              processedData[key] = null;
            } else if (!isNaN(value) && !isNaN(parseFloat(value))) {
              processedData[key] = parseFloat(value);
            } else {
              processedData[key] = value;
            }
          }
          results.push(processedData);
        })
        .on('end', () => {
          resolve(results);
        })
        .on('error', (error) => {
          reject(error);
        });
    });
  }

  // Métodos para obtener datos específicos
  getKPIs(operacion = 'venta') {
    const cacheKey = `kpis_processed_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const kpis = this.data[`basicos/kpis_principales_${operacion}`] || [];
    
    // Convertir array a objeto para fácil acceso
    const kpisObj = {};
    kpis.forEach(row => {
      kpisObj[row.metric] = {
        value: row.value,
        formatted: row.formatted || this.formatNumber(row.value, row.metric)
      };
    });

    this.cache.set(cacheKey, kpisObj);
    return kpisObj;
  }

  getTopColonies(limit = 20, operacion = 'venta') {
    const cacheKey = `top_colonies_${limit}_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const topColonies = this.data[`basicos/top_colonias_${operacion}`] || [];
    const result = topColonies.slice(0, limit);

    this.cache.set(cacheKey, result);
    return result;
  }

  getPropertyTypeDistribution(operacion = 'venta') {
    const cacheKey = `property_distribution_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const distribution = this.data[`basicos/distribucion_tipos_${operacion}`] || [];
    this.cache.set(cacheKey, distribution);
    return distribution;
  }

  getHistogram(variable, filters = {}) {
    const operacion = filters.operacion || 'venta';
    const cacheKey = `histogram_${variable}_${JSON.stringify(filters)}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    // Histogramas por operación
    const histogramKey = `histogramas/histograma_${variable}_${operacion}`;
    const histogram = this.data[histogramKey] || [];

    const result = {
      bins: histogram.map(row => ({
        min: row.bin_min,
        max: row.bin_max,
        count: row.count,
        percentage: row.percentage,
        label: this.generateBinLabel(row.bin_min, row.bin_max, variable)
      })),
      meta: {
        variable,
        totalCount: histogram.reduce((sum, row) => sum + (row.count || 0), 0),
        method: 'freedman_diaconis',
        calculatedAt: new Date().toISOString(),
        filters
      }
    };

    this.cache.set(cacheKey, result);
    return result;
  }

  getSegments(operacion = 'venta') {
    const cacheKey = `segments_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const segments = this.data[`segmentos/segmentos_predefinidos_${operacion}`] || [];
    this.cache.set(cacheKey, segments);
    return segments;
  }

  getCorrelations(operacion = 'venta') {
    const cacheKey = `correlations_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const correlations = this.data[`correlaciones/matriz_correlaciones_${operacion}`] || [];
    this.cache.set(cacheKey, correlations);
    return correlations;
  }

  getAmenities(operacion = 'venta') {
    const cacheKey = `amenities_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const amenities = this.data[`amenidades/amenidades_impacto_${operacion}`] || [];
    this.cache.set(cacheKey, amenities);
    return amenities;
  }

  getMapData(operacion = 'venta') {
    const cacheKey = `map_data_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const mapData = this.data[`geoespacial/mapa_calor_colonias_${operacion}`] || [];
    
    // Calcular percentiles para colores
    const prices = mapData.map(row => row.precio_mediano || 0).filter(p => p > 0);
    prices.sort((a, b) => a - b);
    
    const result = mapData.map(row => ({
      ...row,
      percentile: this.calculatePercentile(row.precio_mediano || 0, prices),
      color: this.getColorForPercentile(this.calculatePercentile(row.precio_mediano || 0, prices))
    }));

    this.cache.set(cacheKey, result);
    return result;
  }

  getTimeSeries(operacion = 'venta') {
    const cacheKey = `time_series_${operacion}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const timeSeries = this.data[`series_temporales/series_zmg_mensual_${operacion}`] || [];
    this.cache.set(cacheKey, timeSeries);
    return timeSeries;
  }

  getFilterOptions(type) {
    const cacheKey = `filter_options_${type}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    let options = [];
    
    switch (type) {
      case 'tipos':
        options = this.data['filtros/opciones_tipos'] || [];
        break;
      case 'municipios':
        options = this.data['filtros/opciones_municipios'] || [];
        break;
      default:
        options = [];
    }

    this.cache.set(cacheKey, options);
    return options;
  }

  // Métodos de búsqueda y filtrado
  searchColonies(query, limit = 10) {
    const cacheKey = `search_colonies_${query}_${limit}`;
    let cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    const mapData = this.data['geoespacial/mapa_calor_colonias'] || [];
    
    const filtered = mapData
      .filter(row => 
        row.colonia && 
        row.colonia.toLowerCase().includes(query.toLowerCase())
      )
      .map(row => ({
        colony: row.colonia,
        municipality: row.municipio,
        count: row.count,
        label: `${row.colonia}, ${row.municipio}`,
        value: `${row.colonia}|${row.municipio}`
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);

    this.cache.set(cacheKey, filtered);
    return filtered;
  }

  // Métodos de utilidad
  formatNumber(value, type) {
    if (value === null || value === undefined || isNaN(value)) {
      return 'N/A';
    }

    if (type && type.includes('precio')) {
      return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    }

    if (type && type.includes('superficie')) {
      return `${Math.round(value)} m²`;
    }

    return new Intl.NumberFormat('es-MX').format(value);
  }

  generateBinLabel(min, max, variable) {
    if (variable === 'precios') {
      return `$${Math.round(min/1000)}K - $${Math.round(max/1000)}K`;
    } else if (variable === 'superficie') {
      return `${Math.round(min)} - ${Math.round(max)} m²`;
    } else if (variable === 'pxm2') {
      return `$${Math.round(min/1000)}K - $${Math.round(max/1000)}K /m²`;
    }
    return `${min.toFixed(1)} - ${max.toFixed(1)}`;
  }

  calculatePercentile(value, sortedArray) {
    if (sortedArray.length === 0) return 0;
    
    const index = sortedArray.findIndex(v => v >= value);
    if (index === -1) return 100;
    
    return (index / sortedArray.length) * 100;
  }

  getColorForPercentile(percentile) {
    // Escala de colores del azul al rojo
    if (percentile >= 90) return '#d73027';      // Rojo intenso
    if (percentile >= 75) return '#f46d43';      // Naranja
    if (percentile >= 50) return '#fdae61';      // Amarillo
    if (percentile >= 25) return '#abd9e9';      // Azul claro
    return '#4575b4';                            // Azul intenso
  }

  // Getters
  getDataPath() {
    return this.dataPath;
  }

  getLoadedFiles() {
    return this.loadedFiles;
  }

  // Limpiar cache
  clearCache() {
    this.cache.flushAll();
    console.log('🧹 Cache limpiado');
  }
}

module.exports = new CSVService();
