# 🏢 Dashboard Inmobiliario ZMG
## Inteligencia de Mercado con Toggle Venta/Renta

[![Estado](https://img.shields.io/badge/Estado-Funcional-brightgreen)](https://github.com)
[![Datos](https://img.shields.io/badge/Propiedades-8,748-blue)](https://github.com)
[![Venta](https://img.shields.io/badge/Venta-7,593-blue)](https://github.com)
[![Renta](https://img.shields.io/badge/Renta-1,155-green)](https://github.com)

---

## 🎯 **DASHBOARD COMPLETAMENTE FUNCIONAL**

### **✅ LO QUE ESTÁ IMPLEMENTADO**

#### **🔄 Toggle Venta/Renta**
- **Separación completa** de datos por operación
- **Cambio instantáneo** sin perder contexto
- **Datos reales** de 8,748 propiedades ZMG
- **Estados visuales** diferenciados (azul/verde)

#### **📊 Dashboard Principal**
- **KPIs en tiempo real**: Total, precios promedio/mediano, precio/m²
- **Top colonias** por precio/m² con datos reales
- **Distribución por tipos** de propiedad (gráfica circular)
- **Insights automáticos** generados del mercado

#### **🎨 UI/UX Optimizada**
- **Mobile-first** design responsivo
- **Loading states** y error handling
- **Gráficas interactivas** con Recharts
- **Formateo mexicano** de números y moneda

---

## 🚀 **INICIO RÁPIDO**

### **Opción 1: Scripts Automáticos**
```bash
# 1. Instalar dependencias
install.bat

# 2. Iniciar dashboard
start.bat
```

### **Opción 2: Manual**
```bash
# 1. Backend
cd backend_csv
npm install
npm start

# 2. Frontend (nueva terminal)
cd frontend
npm install  
npm run dev

# 3. Abrir http://localhost:5173
```

---

## 📊 **DATOS REALES PROCESADOS**

### **Estadísticas Generales**
- **📈 Total**: 8,748 propiedades
- **🧹 Limpias**: 7,840 propiedades (89.6%)
- **📍 Con colonia**: 96.1% de cobertura
- **🗺️ Colonias**: 1,062 mapeadas

### **Por Operación**
| Operación | Propiedades | Precio Promedio | Precio Mediano | Precio/m² |
|-----------|-------------|-----------------|----------------|-----------|
| 🏠 **Venta** | 7,593 | $7,077,459 | $5,400,000 | $39,321/m² |
| 🔑 **Renta** | 1,155 | $30,388/mes | $25,000/mes | $261/m²/mes |

### **Cobertura Geográfica**
- **Zapopan**: 770 colonias
- **Guadalajara**: 292 colonias
- **Superficie promedio**: 206m² (venta), 128m² (renta)

---

## 🔌 **ARQUITECTURA TÉCNICA**

### **Stack Implementado**
```
Frontend:  React + Vite + TypeScript + Tailwind CSS
Backend:   Node.js + Express + CSV (sin base de datos)
Datos:     Python + pandas (pipeline ESDATA_Epsilon)
Estado:    Zustand + TanStack Query
Gráficas:  Recharts
```

### **Flujo de Datos**
```
ESDATA_Epsilon → CSVs separados → Backend API → Frontend Dashboard
     ↓              ↓                ↓              ↓
  Pipeline       venta.csv         Express       React App
  Python         renta.csv         Cache         Toggle
```

### **Endpoints Activos**
- `GET /api/stats/overview?operacion=venta|renta` - KPIs principales
- `GET /api/stats/operations` - Operaciones disponibles
- `GET /api/stats/histogram?variable=precios&operacion=venta` - Histogramas
- `POST /api/stats/filtered?operacion=venta` - Estadísticas filtradas

---

## 🎯 **FUNCIONALIDADES IMPLEMENTADAS**

### **✅ Toggle Global Venta/Renta**
```typescript
// Cambio instantáneo entre operaciones
const { currentOperation, setOperation } = useOperationStore();

// Datos automáticamente actualizados
const { data } = useOverview(); // Se actualiza por operación
```

### **✅ KPIs Dinámicos**
- Total de propiedades por operación
- Precios promedio y mediano
- Precio por m² con formateo mexicano
- Superficie promedio

### **✅ Visualizaciones Interactivas**
- **Gráfica de barras**: Top 10 colonias por precio/m²
- **Gráfica circular**: Distribución por tipo de propiedad
- **Tooltips personalizados** con formateo de pesos
- **Colores consistentes** con la operación activa

### **✅ Performance Optimizada**
- **Cache inteligente** por operación (React Query)
- **Estados de carga** suaves sin parpadeos
- **Datos pre-agregados** en CSVs para velocidad
- **Responsive design** mobile-first

---

## 🔧 **CONFIGURACIÓN AVANZADA**

### **Variables de Entorno**
```env
# Backend (backend_csv/.env)
PORT=3001
NODE_ENV=development
CACHE_TTL_OVERVIEW=3600
DATA_PATH=../data

# Frontend (frontend/.env)
VITE_API_BASE_URL=http://localhost:3001
VITE_DEFAULT_OPERATION=venta
```

### **Personalización de Colores**
```css
/* tailwind.config.js */
colors: {
  primary: { 500: '#3b82f6' },    // Azul para venta
  secondary: { 500: '#10b981' },  // Verde para renta
}
```

---

## 📱 **EXPERIENCIA MOBILE**

### **Optimizaciones Implementadas**
- ✅ **Bottom navigation** para toggle
- ✅ **Área táctil mínima** de 44px
- ✅ **Grid responsivo** que se adapta
- ✅ **Gráficas touch-friendly**
- ✅ **Texto legible** en pantallas pequeñas

### **Breakpoints**
- **Mobile**: < 640px (1 columna)
- **Tablet**: 640px - 1024px (2 columnas)
- **Desktop**: > 1024px (4 columnas)

---

## 🧪 **TESTING**

### **Verificar Funcionamiento**
```bash
# 1. Probar backend directamente
curl "http://localhost:3001/api/stats/overview?operacion=venta"
curl "http://localhost:3001/api/stats/overview?operacion=renta"

# 2. Verificar datos
ls data/basicos/
# Debe mostrar: kpis_principales_venta.csv, kpis_principales_renta.csv

# 3. Probar toggle en frontend
# - Abrir http://localhost:5173
# - Hacer click entre Venta/Renta
# - Verificar que los números cambian
```

### **Casos de Prueba**
- [x] Toggle cambia datos instantáneamente
- [x] KPIs muestran valores correctos por operación
- [x] Gráficas se actualizan con datos correctos
- [x] Loading states funcionan correctamente
- [x] Error handling para datos faltantes
- [x] Responsive design en mobile/desktop

---

## 🔮 **ROADMAP PRÓXIMAS FUNCIONALIDADES**

### **🎯 Semana 1: Filtros Dinámicos**
- [ ] Filtros por municipio, tipo, rango de precios
- [ ] Slider de superficie con histograma
- [ ] Búsqueda de colonias con autocompletar
- [ ] Filtros que persisten al cambiar operación

### **🗺️ Semana 2: Vista Explorar**
- [ ] Mapa interactivo con Mapbox GL JS
- [ ] Heatmap de precios por colonia
- [ ] Clustering dinámico por zoom level
- [ ] Lista de propiedades con paginación

### **📊 Semana 3: Vista Segmentos**
- [ ] Segmentos predefinidos (Starter, Familiar, Premium)
- [ ] Constructor de segmentos personalizado
- [ ] Comparador lado a lado
- [ ] Análisis de ROI por segmento

### **🔬 Semana 4: Vista Analítica**
- [ ] Matriz de correlaciones interactiva
- [ ] Clustering de colonias por características
- [ ] Análisis de impacto de amenidades
- [ ] Exportación de reportes PDF/Excel

---

## 🤝 **CONTRIBUCIÓN**

### **Estructura del Proyecto**
```
Dashboard/
├── 📊 data/                    # CSVs generados por Python
├── 🐍 python_sync/            # Script generador de datos
├── 🌐 backend_csv/            # API Express.js
├── 🎨 frontend/               # React + Vite app
├── 📚 docs/                   # Documentación técnica
├── 🚀 install.bat             # Script de instalación
├── ▶️ start.bat               # Script de inicio
└── 📖 README_DASHBOARD.md     # Este archivo
```

### **Flujo de Desarrollo**
1. **Datos**: Modificar `python_sync/generate_dashboard_data.py`
2. **Backend**: Agregar endpoints en `backend_csv/src/routes/`
3. **Frontend**: Crear componentes en `frontend/src/components/`
4. **Probar**: Usar scripts automáticos o comandos manuales

---

## 🎉 **¡DASHBOARD LISTO PARA USAR!**

### **Lo que tienes ahora:**
- ✅ **Dashboard completamente funcional** con datos reales
- ✅ **Toggle venta/renta** que funciona perfectamente
- ✅ **8,748 propiedades** de la ZMG procesadas
- ✅ **Gráficas interactivas** con estadísticas por operación
- ✅ **Design moderno** y mobile-friendly
- ✅ **Performance optimizada** con cache inteligente

### **Próximos pasos:**
1. **Probar el dashboard** con los scripts automáticos
2. **Explorar los datos** cambiando entre venta y renta
3. **Personalizar** colores, textos o métricas
4. **Agregar funcionalidades** del roadmap según prioridades

**¡El dashboard está listo para demostrar y usar en producción!** 🚀

---

<div align="center">

**¿Te gusta el proyecto? ¡Compártelo!**

[📊 Dashboard](http://localhost:5173) • [🔌 API](http://localhost:3001/api) • [📚 Docs](./docs/) • [🐛 Issues](./issues/)

</div>
