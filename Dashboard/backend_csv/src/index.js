const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const path = require('path');

const csvService = require('./services/csvService');
const statsRoutes = require('./routes/stats');
const geoRoutes = require('./routes/geo');
const filtersRoutes = require('./routes/filters');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware de seguridad
app.use(helmet());
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 1000, // máximo 1000 requests por ventana
  message: 'Demasiadas solicitudes desde esta IP'
});
app.use(limiter);

// CORS
app.use(cors({
  origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:5173', 'http://localhost:3000'],
  credentials: true
}));

// Parsear JSON
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Middleware para logging
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  });
  
  next();
});

// Rutas de la API
app.use('/api/stats', statsRoutes);
app.use('/api/geo', geoRoutes);
app.use('/api/filters', filtersRoutes);

// Ruta de salud
app.get('/api/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    dataPath: csvService.getDataPath(),
    filesLoaded: csvService.getLoadedFiles()
  });
});

// Ruta raíz
app.get('/', (req, res) => {
  res.json({
    name: 'Dashboard ZMG API',
    version: '1.0.0',
    description: 'API para Dashboard de Inteligencia Inmobiliaria ZMG',
    endpoints: {
      health: '/api/health',
      stats: '/api/stats',
      geo: '/api/geo',
      filters: '/api/filters'
    },
    docs: '/api/docs'
  });
});

// Middleware de manejo de errores
app.use((err, req, res, next) => {
  console.error('Error:', err);
  
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Error interno del servidor',
      status: err.status || 500,
      timestamp: new Date().toISOString()
    }
  });
});

// Middleware para rutas no encontradas
app.use('*', (req, res) => {
  res.status(404).json({
    error: {
      message: 'Ruta no encontrada',
      status: 404,
      path: req.originalUrl
    }
  });
});

// Inicializar servidor
async function startServer() {
  try {
    console.log('🚀 Iniciando Dashboard ZMG API...');
    
    // Inicializar servicio CSV
    console.log('📊 Cargando datos CSV...');
    await csvService.initialize();
    console.log('✅ Datos CSV cargados exitosamente');
    
    // Iniciar servidor
    app.listen(PORT, () => {
      console.log(`🌐 Servidor ejecutándose en http://localhost:${PORT}`);
      console.log(`📚 Documentación disponible en http://localhost:${PORT}/api/docs`);
      console.log(`❤️  Health check en http://localhost:${PORT}/api/health`);
    });
    
  } catch (error) {
    console.error('❌ Error iniciando servidor:', error);
    process.exit(1);
  }
}

// Manejo de señales de cierre
process.on('SIGINT', () => {
  console.log('\n🛑 Cerrando servidor...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Cerrando servidor...');
  process.exit(0);
});

// Iniciar servidor
startServer();
