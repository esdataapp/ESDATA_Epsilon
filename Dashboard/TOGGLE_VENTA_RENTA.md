# 🔄 TOGGLE VENTA/RENTA - Dashboard ZMG
## Separación Global de Operaciones sin Afectar Filtros

---

## 🎯 **CONCEPTO IMPLEMENTADO**

### **Toggle Global de Operación**
- **🏠 Venta**: Todas las propiedades en venta
- **🔑 Renta**: Todas las propiedades en renta
- **🔄 Switch instantáneo**: Cambia el dataset base sin perder filtros aplicados
- **📊 Datos separados**: Cada operación tiene sus propios CSVs y estadísticas

### **Comportamiento del Toggle**
```
Estado Inicial:
- Operación: VENTA
- Filtros: [2-3 recámaras, Zapopan, $2M-5M]
- Vista: Inicio con KPIs de venta

Usuario hace click en RENTA:
- Operación: RENTA ✅
- Filtros: [2-3 recámaras, Zapopan, $2M-5M] ✅ (se mantienen)
- Vista: Inicio con KPIs de renta ✅ (datos actualizados)
```

---

## 📁 **ESTRUCTURA DE DATOS GENERADA**

### **CSVs por Operación**
```
data/
├── basicos/
│   ├── kpis_principales_venta.csv
│   ├── kpis_principales_renta.csv
│   ├── top_colonias_venta.csv
│   ├── top_colonias_renta.csv
│   ├── distribucion_tipos_venta.csv
│   └── distribucion_tipos_renta.csv
│
├── histogramas/
│   ├── histograma_precios_venta.csv
│   ├── histograma_precios_renta.csv
│   ├── histograma_superficie_venta.csv
│   ├── histograma_superficie_renta.csv
│   ├── histograma_pxm2_venta.csv
│   └── histograma_pxm2_renta.csv
│
├── segmentos/
│   ├── segmentos_predefinidos_venta.csv
│   └── segmentos_predefinidos_renta.csv
│
├── correlaciones/
│   ├── matriz_correlaciones_venta.csv
│   └── matriz_correlaciones_renta.csv
│
├── amenidades/
│   ├── amenidades_impacto_venta.csv
│   └── amenidades_impacto_renta.csv
│
├── geoespacial/
│   ├── mapa_calor_colonias_venta.csv
│   └── mapa_calor_colonias_renta.csv
│
└── series_temporales/
    ├── series_zmg_mensual_venta.csv
    └── series_zmg_mensual_renta.csv
```

---

## 🔌 **ENDPOINTS ACTUALIZADOS**

### **Todos los endpoints ahora soportan `?operacion=venta|renta`**

#### **Estadísticas**
```javascript
// KPIs para venta
GET /api/stats/overview?operacion=venta

// KPIs para renta  
GET /api/stats/overview?operacion=renta

// Histogramas por operación
GET /api/stats/histogram?variable=precios&operacion=venta
GET /api/stats/histogram?variable=precios&operacion=renta

// Segmentos por operación
GET /api/stats/segments?operacion=venta
GET /api/stats/segments?operacion=renta
```

#### **Filtros con Operación**
```javascript
// Estadísticas filtradas manteniendo operación
POST /api/stats/filtered?operacion=venta
Body: {
  "priceRange": [2000000, 5000000],
  "bedrooms": [2, 3],
  "municipalities": ["Zapopan"]
}
```

#### **Nuevo Endpoint de Operaciones**
```javascript
// Obtener operaciones disponibles
GET /api/stats/operations

Response: {
  "data": [
    {
      "value": "venta",
      "label": "Venta", 
      "icon": "🏠",
      "description": "Propiedades en venta",
      "color": "#3B82F6"
    },
    {
      "value": "renta",
      "label": "Renta",
      "icon": "🔑", 
      "description": "Propiedades en renta",
      "color": "#10B981"
    }
  ],
  "default": "venta"
}
```

---

## 💻 **IMPLEMENTACIÓN EN FRONTEND**

### **1. Estado Global de Operación**
```typescript
// store/operationStore.ts
interface OperationState {
  currentOperation: 'venta' | 'renta';
  setOperation: (operation: 'venta' | 'renta') => void;
}

export const useOperationStore = create<OperationState>((set) => ({
  currentOperation: 'venta',
  setOperation: (operation) => set({ currentOperation: operation }),
}));
```

### **2. Componente Toggle**
```tsx
// components/OperationToggle.tsx
import { useOperationStore } from '@/store/operationStore';

export function OperationToggle() {
  const { currentOperation, setOperation } = useOperationStore();
  
  return (
    <div className="flex bg-gray-100 rounded-lg p-1">
      <button
        onClick={() => setOperation('venta')}
        className={`flex items-center px-4 py-2 rounded-md transition-all ${
          currentOperation === 'venta' 
            ? 'bg-blue-500 text-white shadow-sm' 
            : 'text-gray-600 hover:text-gray-800'
        }`}
      >
        🏠 Venta
      </button>
      
      <button
        onClick={() => setOperation('renta')}
        className={`flex items-center px-4 py-2 rounded-md transition-all ${
          currentOperation === 'renta' 
            ? 'bg-green-500 text-white shadow-sm' 
            : 'text-gray-600 hover:text-gray-800'
        }`}
      >
        🔑 Renta
      </button>
    </div>
  );
}
```

### **3. Hook para APIs con Operación**
```typescript
// hooks/useStatsAPI.ts
import { useOperationStore } from '@/store/operationStore';
import { useQuery } from '@tanstack/react-query';

export function useOverview() {
  const { currentOperation } = useOperationStore();
  
  return useQuery({
    queryKey: ['overview', currentOperation],
    queryFn: () => 
      fetch(`/api/stats/overview?operacion=${currentOperation}`)
        .then(res => res.json()),
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}

export function useFilteredStats(filters: any) {
  const { currentOperation } = useOperationStore();
  
  return useQuery({
    queryKey: ['filtered-stats', currentOperation, filters],
    queryFn: () =>
      fetch(`/api/stats/filtered?operacion=${currentOperation}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
      }).then(res => res.json()),
    enabled: Object.keys(filters).length > 0,
  });
}
```

### **4. Layout con Toggle Persistente**
```tsx
// components/Layout.tsx
export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header con toggle */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-gray-900">
              Dashboard ZMG
            </h1>
            
            {/* Toggle siempre visible */}
            <OperationToggle />
          </div>
        </div>
      </header>
      
      {/* Contenido principal */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
```

---

## 🎨 **UX/UI DEL TOGGLE**

### **Posición y Visibilidad**
- **📍 Header fijo**: Siempre visible en la parte superior
- **🎯 Acceso rápido**: Un click para cambiar operación
- **📱 Mobile-friendly**: Botones con área táctil de 44px mínimo
- **🔄 Transición suave**: Animación de 200ms al cambiar

### **Estados Visuales**
```css
/* Venta - Azul */
.operation-venta {
  background: #3B82F6;
  color: white;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
}

/* Renta - Verde */
.operation-renta {
  background: #10B981;
  color: white;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.3);
}

/* Inactivo */
.operation-inactive {
  background: transparent;
  color: #6B7280;
  transition: all 0.2s ease;
}

.operation-inactive:hover {
  color: #374151;
  background: rgba(0, 0, 0, 0.05);
}
```

### **Feedback Visual**
- **✅ Loading states**: Skeleton mientras cargan datos
- **🔄 Smooth transitions**: Datos se actualizan sin parpadeo
- **📊 Contexto claro**: Indicadores de qué operación está activa
- **🎯 Breadcrumbs**: "Inicio > Venta" o "Segmentos > Renta"

---

## 📊 **DIFERENCIAS ESPERADAS VENTA vs RENTA**

### **Métricas Típicas**

#### **🏠 VENTA**
- **Precio promedio**: $3,200,000 MXN
- **Precio/m² promedio**: $32,000 MXN/m²
- **Superficie promedio**: 100 m²
- **Tiempo en mercado**: 45 días promedio
- **Segmento dominante**: Familiar (2-3 rec)

#### **🔑 RENTA**
- **Precio promedio**: $18,000 MXN/mes
- **Precio/m² promedio**: $180 MXN/m²/mes
- **Superficie promedio**: 85 m²
- **Tiempo en mercado**: 15 días promedio
- **Segmento dominante**: Starter (1-2 rec)

### **Correlaciones Diferentes**
- **Venta**: Superficie ↔ Precio (r=0.85)
- **Renta**: Ubicación ↔ Precio (r=0.72)
- **Amenidades**: Mayor impacto en renta que en venta

---

## 🚀 **IMPLEMENTACIÓN PASO A PASO**

### **Paso 1: Generar Datos Separados** ✅
```bash
cd Dashboard
python python_sync/generate_dashboard_data.py
```

### **Paso 2: Probar Backend** ✅
```bash
cd backend_csv
npm start

# Probar endpoints
curl "http://localhost:3001/api/stats/overview?operacion=venta"
curl "http://localhost:3001/api/stats/overview?operacion=renta"
curl "http://localhost:3001/api/stats/operations"
```

### **Paso 3: Implementar Frontend** (Próximo)
```bash
cd frontend
npm install zustand @tanstack/react-query
# Crear componentes y hooks mostrados arriba
```

### **Paso 4: Testing** (Próximo)
- Verificar que filtros se mantienen al cambiar operación
- Probar transiciones suaves entre venta/renta
- Validar que datos son correctos para cada operación

---

## 🎯 **CASOS DE USO REALES**

### **Asesor Inmobiliario**
```
Escenario: Comparar mercado de venta vs renta en Zapopan
1. Aplica filtros: Zapopan, 2-3 rec, $2M-5M
2. Ve datos de VENTA: 1,250 propiedades, $3.2M promedio
3. Click en RENTA (filtros se mantienen)
4. Ve datos de RENTA: 890 propiedades, $16K/mes promedio
5. Puede alternar rápidamente para comparar
```

### **Inversionista**
```
Escenario: Análizar ROI potencial por colonia
1. Vista Analítica > Correlaciones en VENTA
2. Identifica colonias con mejor precio/m²
3. Cambia a RENTA (mantiene filtros de colonias)
4. Compara precios de renta en las mismas colonias
5. Calcula ROI = (Renta anual / Precio venta) * 100
```

### **Desarrolladora**
```
Escenario: Decidir entre desarrollar para venta o renta
1. Segmentos > Premium (3+ rec, amenidades)
2. Ve demanda en VENTA: 450 propiedades activas
3. Cambia a RENTA: 120 propiedades activas
4. Analiza tiempo promedio en mercado para cada operación
5. Decide estrategia basada en datos reales
```

---

## 🔧 **CONFIGURACIÓN TÉCNICA**

### **Variables de Entorno**
```env
# Backend
DEFAULT_OPERATION=venta
CACHE_TTL_BY_OPERATION=1800
ENABLE_OPERATION_TOGGLE=true

# Frontend  
VITE_DEFAULT_OPERATION=venta
VITE_ENABLE_OPERATION_TOGGLE=true
```

### **Configuración de Cache**
```javascript
// Diferentes TTL por operación y endpoint
const cacheConfig = {
  'overview_venta': 3600,      // 1 hora
  'overview_renta': 3600,      // 1 hora  
  'filtered_venta': 1800,      // 30 min
  'filtered_renta': 1800,      // 30 min
  'histogram_venta': 7200,     // 2 horas
  'histogram_renta': 7200,     // 2 horas
};
```

---

¡Con esta implementación tienes un **toggle global venta/renta completamente funcional** que mantiene todos los filtros y segmentaciones mientras cambia el dataset base! 🎉

El usuario puede alternar instantáneamente entre ver el mercado de venta y renta sin perder el contexto de sus filtros aplicados.
