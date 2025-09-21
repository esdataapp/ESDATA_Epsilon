# 🏢 Dashboard Inmobiliario ZMG
## Inteligencia de Mercado para la Zona Metropolitana de Guadalajara

[![Estado](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow)](https://github.com)
[![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)](https://github.com)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green)](https://github.com)

---

## 📊 **DESCRIPCIÓN**

Dashboard dinámico para análisis de inteligencia de mercado inmobiliario de la Zona Metropolitana de Guadalajara (ZMG). Diseñado para asesores inmobiliarios, brokers, constructoras, inversionistas y profesionales del sector inmobiliario.

### **Características Principales**
- 📈 **25,851 propiedades** procesadas y analizadas
- 🗺️ **1,062 colonias** mapeadas (770 Zapopan + 292 Guadalajara)
- 📱 **Mobile-first** optimizado para uso con una mano
- ⚡ **Tiempo real** con filtros dinámicos
- 🎯 **Segmentación avanzada** por recámaras, baños y características
- 🔗 **Correlaciones** y análisis estadístico profundo

---

## 🚀 **INICIO RÁPIDO**

### **Prerrequisitos**
- Python 3.9+ (para generar datos)
- Node.js 18+ (para backend)
- Git

### **Instalación en 3 pasos**

#### 1. Generar datos desde ESDATA_Epsilon
```bash
cd Dashboard
python python_sync/generate_dashboard_data.py
```

#### 2. Iniciar backend
```bash
cd backend_csv
npm install
npm start
```

#### 3. Verificar funcionamiento
```bash
curl http://localhost:3001/api/health
```

¡Listo! El backend estará corriendo en `http://localhost:3001`

---

## 🏗️ **ARQUITECTURA**

### **Stack Tecnológico**
```
Frontend:  Vite + React + TypeScript + Tailwind CSS
Backend:   Node.js + Express + CSV (sin base de datos)
Análisis:  Python + pandas (pipeline ESDATA_Epsilon)
Mapas:     Mapbox GL JS
Gráficas:  Recharts
Estado:    Zustand + TanStack Query
```

### **Flujo de Datos**
```
ESDATA_Epsilon → CSVs → Backend API → Frontend Dashboard
     ↓              ↓         ↓           ↓
  Pipeline       Datos    REST API    React App
  Python       Estáticos  Express      Vite
```

---

## 📁 **ESTRUCTURA DEL PROYECTO**

```
Dashboard/
├── 📚 DOCUMENTACIÓN/
│   ├── README.md
│   ├── CALCULOS_Y_CSVS_NECESARIOS.md
│   ├── ARQUITECTURA_TECNICA.md
│   ├── AJUSTES_CRITICOS.md
│   └── GUIA_IMPLEMENTACION_LOCAL.md
│
├── 🐍 PYTHON_SYNC/
│   └── generate_dashboard_data.py
│
├── 🗄️ BACKEND_CSV/
│   ├── src/
│   │   ├── index.js
│   │   ├── services/csvService.js
│   │   └── routes/
│   │       ├── stats.js
│   │       ├── geo.js
│   │       └── filters.js
│   └── package.json
│
├── 🎨 FRONTEND/ (próximamente)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
└── 📊 DATA/ (generado automáticamente)
    ├── basicos/
    ├── histogramas/
    ├── segmentos/
    ├── correlaciones/
    ├── amenidades/
    ├── geoespacial/
    ├── series_temporales/
    └── filtros/
```

---

## 🔌 **API ENDPOINTS**

### **Estadísticas**
- `GET /api/stats/overview` - KPIs principales
- `POST /api/stats/filtered` - Estadísticas filtradas
- `GET /api/stats/histogram` - Histogramas pre-calculados
- `GET /api/stats/segments` - Segmentos predefinidos
- `GET /api/stats/correlations` - Matriz de correlaciones
- `GET /api/stats/amenities` - Análisis de amenidades

### **Geoespacial**
- `GET /api/geo/heatmap` - Mapa de calor por colonias
- `GET /api/geo/clusters` - Clustering dinámico
- `GET /api/geo/boundaries` - Límites geográficos

### **Filtros**
- `GET /api/filters/property-types` - Tipos de propiedad
- `GET /api/filters/municipalities` - Municipios
- `GET /api/filters/price-ranges` - Rangos sugeridos
- `GET /api/filters/presets` - Filtros predefinidos

### **Utilidades**
- `GET /api/health` - Estado del sistema
- `GET /api/stats/colonies/search` - Búsqueda de colonias

---

## 📊 **DATOS Y MÉTRICAS**

### **Cobertura Geográfica**
- **Guadalajara**: 292 colonias mapeadas
- **Zapopan**: 770 colonias mapeadas
- **Total ZMG**: 1,062 colonias

### **Calidad de Datos**
- ✅ **100%** propiedades con precio válido
- ✅ **96.1%** propiedades con colonia asignada
- ✅ **Sistema robusto** de detección de outliers
- ✅ **Validación automática** de datos

### **Tipos de Análisis**
- 📊 **Estadísticas descriptivas** (media, mediana, percentiles)
- 🔗 **Correlaciones** entre variables
- 🎯 **Segmentación** por características
- 🏠 **Análisis de amenidades** y su impacto en precio
- 🗺️ **Análisis geoespacial** por colonia
- 📈 **Series temporales** (cuando hay datos históricos)

---

## 🎯 **FUNCIONALIDADES PRINCIPALES**

### **Vista Inicio (Overview)**
- KPIs principales del mercado ZMG
- Top 10 colonias por precio/m²
- Distribución por tipo de propiedad
- Insights automáticos generados
- Tendencias mensuales

### **Vista Explorar**
- Mapa de calor interactivo
- Clustering dinámico por zoom
- Lista de propiedades filtrable
- Histogramas para ajustar rangos

### **Vista Segmentos**
- Segmentos predefinidos (Starter, Familiar, Premium)
- Constructor de segmentos personalizado
- Comparador lado a lado
- Rangos automáticos (P25-P75)

### **Vista Analítica**
- Matriz de correlaciones interactiva
- Análisis de clusters de colonias
- Impacto de amenidades en precio
- Estadísticas avanzadas

---

## 🔧 **CONFIGURACIÓN**

### **Variables de Entorno**
```env
# Backend
PORT=3001
NODE_ENV=development
CORS_ORIGINS=http://localhost:5173

# Cache
CACHE_TTL_OVERVIEW=3600
CACHE_TTL_FILTERED=1800

# Datos
DATA_PATH=../data
MAX_RESULTS=1000
```

### **Configuración de Cache**
- **Overview**: 1 hora (datos cambian poco)
- **Filtros**: 30 minutos (consultas frecuentes)
- **Histogramas**: 2 horas (cálculos costosos)
- **Correlaciones**: 24 horas (análisis estático)

---

## 📱 **DISEÑO MOBILE-FIRST**

### **Principios de UX**
- ✅ **Navegación con pulgar** (bottom tabs)
- ✅ **Área táctil mínima** de 44px
- ✅ **Respuesta < 200ms** en filtros
- ✅ **Progresión clara**: vislumbra → explora → detalla
- ✅ **Lenguaje claro**: cifra + contexto + tendencia

### **Optimizaciones Mobile**
- 📱 Bottom sheets para filtros
- 🎯 Clustering automático en mapas
- ⚡ Virtualización de listas largas
- 🎨 Componentes touch-friendly

---

## 🧪 **TESTING**

### **Verificar Backend**
```bash
# Health check
curl http://localhost:3001/api/health

# Overview
curl http://localhost:3001/api/stats/overview

# Búsqueda de colonias
curl "http://localhost:3001/api/stats/colonies/search?q=providencia"

# Histograma
curl "http://localhost:3001/api/stats/histogram?variable=precios"
```

### **Verificar Datos**
```bash
# Verificar CSVs generados
ls -la data/basicos/
cat data/metadata.json

# Verificar conteos
wc -l data/**/*.csv
```

---

## 🚀 **ROADMAP**

### **✅ Fase 1: MVP Backend (Completada)**
- [x] Script Python para generar CSVs
- [x] Backend API con Express
- [x] 15+ endpoints funcionales
- [x] Sistema de cache optimizado
- [x] Documentación completa

### **🔄 Fase 2: Frontend MVP (En progreso)**
- [ ] Setup React + Vite + Tailwind
- [ ] Vista Inicio con KPIs
- [ ] Vista Explorar con mapa básico
- [ ] Filtros dinámicos
- [ ] Responsive design

### **📋 Fase 3: Funcionalidades Avanzadas**
- [ ] Vista Segmentos completa
- [ ] Vista Analítica con correlaciones
- [ ] Mapas interactivos con Mapbox
- [ ] Exportación de reportes
- [ ] Sistema de alertas

### **🎯 Fase 4: Optimización y Deploy**
- [ ] Performance optimization
- [ ] Testing automatizado
- [ ] CI/CD pipeline
- [ ] Deploy en producción
- [ ] Monitoreo y analytics

---

## 🤝 **CONTRIBUCIÓN**

### **Cómo Contribuir**
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### **Estándares de Código**
- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ESLint, Prettier, JSDoc
- **React**: TypeScript, hooks, componentes funcionales
- **CSS**: Tailwind CSS, mobile-first

---

## 📞 **SOPORTE**

### **Problemas Comunes**
- **Error "No se encontró directorio de datos"**: Ejecutar `python python_sync/generate_dashboard_data.py`
- **Puerto 3001 ocupado**: Cambiar `PORT=3002` en `.env`
- **CSVs vacíos**: Verificar que el pipeline ESDATA_Epsilon haya corrido exitosamente

### **Contacto**
- 📧 Email: dashboard@zmg.com
- 💬 Issues: [GitHub Issues](https://github.com/dashboard-zmg/issues)
- 📖 Docs: [Documentación completa](./docs/)

---

## 📄 **LICENCIA**

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🙏 **AGRADECIMIENTOS**

- **Pipeline ESDATA_Epsilon**: Por el procesamiento robusto de datos inmobiliarios
- **Comunidad ZMG**: Por los datos y feedback constante
- **Equipo de desarrollo**: Por hacer posible este proyecto

---

<div align="center">

**¿Te gusta el proyecto? ¡Dale una ⭐ en GitHub!**

[🏠 Inicio](/) • [📊 Documentación](./docs/) • [🔧 API](./api/) • [🤝 Contribuir](./CONTRIBUTING.md)

</div>
