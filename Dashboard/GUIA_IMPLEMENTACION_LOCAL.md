# 🚀 GUÍA DE IMPLEMENTACIÓN LOCAL - Dashboard ZMG
## Configuración paso a paso sin base de datos

---

## 📋 **RESUMEN DE LO IMPLEMENTADO**

### ✅ **Completado**
1. **Script Python**: `generate_dashboard_data.py` - Genera todos los CSVs necesarios
2. **Backend CSV**: API en Node.js/Express que lee CSVs directamente
3. **Endpoints completos**: 15+ endpoints para todas las funcionalidades
4. **Sistema de cache**: Cache en memoria para optimizar performance
5. **Documentación completa**: Listado de cálculos y CSVs necesarios

### 🎯 **Arquitectura Simplificada**
```
ESDATA_Epsilon → CSVs → Backend Node.js → Frontend React
     ↓              ↓         ↓              ↓
  Pipeline      Datos     API REST      Dashboard
  Python      Estáticos   Express        Vite
```

---

## 🛠️ **PASOS PARA IMPLEMENTAR**

### **Paso 1: Generar los Datos (Python)**

#### A. Ejecutar el script generador
```bash
# Ir al directorio del dashboard
cd c:\Users\criss\Desktop\ESDATA_Epsilon\Dashboard

# Ejecutar el script Python
python python_sync/generate_dashboard_data.py
```

#### B. Verificar que se generaron los CSVs
```bash
# Verificar estructura de datos
ls -la data/
```

**Estructura esperada:**
```
data/
├── basicos/
│   ├── kpis_principales.csv
│   ├── top_colonias.csv
│   ├── distribucion_tipos.csv
│   └── quick_stats.csv
├── histogramas/
│   ├── histograma_precios_all.csv
│   ├── histograma_superficie_all.csv
│   └── histograma_pxm2_all.csv
├── segmentos/
│   └── segmentos_predefinidos.csv
├── correlaciones/
│   └── matriz_correlaciones_all.csv
├── amenidades/
│   └── amenidades_impacto.csv
├── geoespacial/
│   └── mapa_calor_colonias.csv
├── series_temporales/
│   └── series_zmg_mensual.csv
├── filtros/
│   ├── opciones_tipos.csv
│   └── opciones_municipios.csv
└── metadata.json
```

### **Paso 2: Configurar el Backend**

#### A. Instalar dependencias
```bash
cd backend_csv
npm install
```

#### B. Iniciar el servidor
```bash
# Modo desarrollo
npm run dev

# O modo producción
npm start
```

#### C. Verificar que funciona
```bash
# Test del health check
curl http://localhost:3001/api/health

# Test del overview
curl http://localhost:3001/api/stats/overview
```

### **Paso 3: Configurar el Frontend** (Próximo paso)

#### A. Crear proyecto React con Vite
```bash
cd Dashboard
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

#### B. Instalar dependencias adicionales
```bash
npm install @tanstack/react-query zustand
npm install recharts mapbox-gl react-map-gl
npm install @radix-ui/react-slider @radix-ui/react-select
npm install tailwindcss @tailwindcss/forms
npm install lucide-react clsx tailwind-merge
npm install react-hook-form @hookform/resolvers zod
```

---

## 📊 **ENDPOINTS DISPONIBLES**

### **Estadísticas (`/api/stats`)**
- `GET /overview` - KPIs principales para vista Inicio
- `POST /filtered` - Estadísticas con filtros aplicados
- `GET /histogram?variable=precios` - Histogramas pre-calculados
- `GET /colonies/search?q=providencia` - Búsqueda de colonias
- `GET /segments` - Segmentos predefinidos
- `GET /correlations` - Matriz de correlaciones
- `GET /amenities` - Análisis de amenidades

### **Geoespacial (`/api/geo`)**
- `GET /heatmap` - Datos para mapa de calor
- `GET /clusters?zoom=12` - Clustering dinámico por zoom
- `GET /boundaries` - Límites geográficos
- `GET /search?q=guadalajara` - Búsqueda geográfica

### **Filtros (`/api/filters`)**
- `GET /property-types` - Tipos de propiedad
- `GET /operations` - Tipos de operación
- `GET /municipalities` - Municipios disponibles
- `GET /price-ranges` - Rangos de precio sugeridos
- `GET /surface-ranges` - Rangos de superficie
- `GET /amenities` - Amenidades disponibles
- `GET /bedrooms-bathrooms` - Combinaciones rec/baños
- `POST /validate` - Validar filtros
- `GET /presets` - Filtros predefinidos

---

## 🎯 **EJEMPLO DE USO**

### **1. Obtener KPIs para la vista Inicio**
```javascript
// Frontend React
const { data: overview } = useQuery({
  queryKey: ['overview'],
  queryFn: () => fetch('/api/stats/overview').then(res => res.json())
});

console.log(overview.data.totalProperties); // 25,851
console.log(overview.data.avgPrice.formatted); // "$3,200,000"
console.log(overview.data.topColonies); // Array de top colonias
```

### **2. Aplicar filtros dinámicos**
```javascript
// Filtros del usuario
const filters = {
  propertyType: ['Departamento'],
  priceRange: [2000000, 5000000],
  bedrooms: [2, 3],
  municipalities: ['Zapopan']
};

// Enviar filtros al backend
const { data: filtered } = useMutation({
  mutationFn: (filters) => 
    fetch('/api/stats/filtered', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters)
    }).then(res => res.json())
});

console.log(filtered.stats.count); // Propiedades que coinciden
console.log(filtered.stats.byColony); // Distribución por colonia
```

### **3. Obtener histograma para filtros**
```javascript
// Histograma de precios
const { data: histogram } = useQuery({
  queryKey: ['histogram', 'precios'],
  queryFn: () => fetch('/api/stats/histogram?variable=precios').then(res => res.json())
});

console.log(histogram.bins); // Array de bins para gráfica
// [{ min: 1000000, max: 1500000, count: 1250, percentage: 12.5 }, ...]
```

### **4. Búsqueda de colonias**
```javascript
// Autocompletar colonias
const searchColonies = async (query) => {
  const response = await fetch(`/api/stats/colonies/search?q=${query}&limit=10`);
  return response.json();
};

// Resultado: [{ colony: "Providencia", municipality: "Guadalajara", count: 148 }]
```

---

## 🔧 **CONFIGURACIÓN AVANZADA**

### **Variables de Entorno**
```env
# backend_csv/.env
PORT=3001
NODE_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Cache settings
CACHE_TTL_DEFAULT=1800
CACHE_TTL_OVERVIEW=3600
CACHE_TTL_FILTERS=7200

# Data settings
DATA_PATH=../data
MAX_RESULTS=1000
```

### **Configuración de Cache**
```javascript
// Ajustar TTL por endpoint
const cacheConfig = {
  overview: 3600,      // 1 hora
  filtered: 1800,      // 30 minutos
  histogram: 7200,     // 2 horas
  correlations: 86400, // 24 horas
  amenities: 86400     // 24 horas
};
```

### **Logging y Monitoreo**
```javascript
// El backend incluye logging automático
// Ejemplo de salida:
// 2025-09-20T19:30:00.000Z - GET /api/stats/overview - 200 - 45ms
// 2025-09-20T19:30:05.000Z - POST /api/stats/filtered - 200 - 123ms
```

---

## 📱 **PRÓXIMOS PASOS**

### **Inmediato (Esta semana)**
1. ✅ Ejecutar script Python para generar CSVs
2. ✅ Probar backend con datos reales
3. 🔄 Crear frontend MVP con 2 vistas básicas
4. 🔄 Implementar filtros básicos

### **Corto plazo (Próxima semana)**
1. 📋 Agregar todas las vistas (Segmentos, Analítica)
2. 📋 Implementar mapas con Mapbox
3. 📋 Optimizar para mobile
4. 📋 Testing completo

### **Mediano plazo (Próximo mes)**
1. 📋 Integración automática con pipeline ESDATA_Epsilon
2. 📋 Sistema de alertas y notificaciones
3. 📋 Exportación de reportes
4. 📋 Deploy en producción

---

## 🚨 **TROUBLESHOOTING**

### **Error: "No se encontró el directorio de datos"**
```bash
# Verificar que existe el directorio data/
ls -la Dashboard/data/

# Si no existe, ejecutar el script Python
python Dashboard/python_sync/generate_dashboard_data.py
```

### **Error: "Cannot read CSV file"**
```bash
# Verificar permisos de archivos
chmod 644 Dashboard/data/**/*.csv

# Verificar formato de CSVs
head -5 Dashboard/data/basicos/kpis_principales.csv
```

### **Error: "Port 3001 already in use"**
```bash
# Cambiar puerto en package.json o matar proceso
lsof -ti:3001 | xargs kill -9

# O usar puerto diferente
PORT=3002 npm start
```

### **Performance lenta**
```bash
# Verificar tamaño de CSVs
du -sh Dashboard/data/**/*.csv

# Limpiar cache si es necesario
curl -X DELETE http://localhost:3001/api/cache/clear
```

---

## 💡 **TIPS DE OPTIMIZACIÓN**

### **1. Cache Inteligente**
- Los datos se cachean automáticamente en memoria
- Cache se limpia cada 30 minutos por defecto
- Endpoints más usados tienen cache más largo

### **2. Filtrado Eficiente**
- Los filtros se aplican sobre datos pre-agregados
- Búsquedas de texto usan índices en memoria
- Resultados se limitan automáticamente

### **3. Datos Optimizados**
- CSVs se cargan una sola vez al iniciar
- Números se convierten automáticamente
- Datos nulos se manejan correctamente

---

¡Con esta implementación tienes un dashboard completamente funcional usando solo CSVs! 🎉
