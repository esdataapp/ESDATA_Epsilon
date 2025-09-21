# 🚀 SETUP COMPLETO - Dashboard ZMG

## ✅ **LO QUE YA ESTÁ LISTO**

### **1. Datos Generados** ✅
- ✅ Script Python ejecutado exitosamente
- ✅ **8,748 propiedades** procesadas (7,840 limpias)
- ✅ **7,593 en VENTA** | **1,155 en RENTA**
- ✅ Todos los CSVs separados por operación

### **2. Backend API** ✅
- ✅ Backend CSV con Express.js
- ✅ 15+ endpoints con soporte venta/renta
- ✅ Sistema de cache optimizado

### **3. Frontend Completo** ✅
- ✅ React + Vite + TypeScript + Tailwind
- ✅ Toggle global venta/renta
- ✅ Dashboard con KPIs y gráficas
- ✅ Componentes reutilizables

---

## 🚀 **PASOS PARA EJECUTAR**

### **Paso 1: Instalar Backend**
```bash
cd Dashboard/backend_csv
npm install
```

### **Paso 2: Instalar Frontend**
```bash
cd ../frontend
npm install
```

### **Paso 3: Iniciar Backend**
```bash
cd ../backend_csv
npm start
```
**Debería mostrar:**
```
🚀 Servidor CSV iniciado en puerto 3001
📊 Datos cargados desde: ../data
✅ Cache inicializado
```

### **Paso 4: Iniciar Frontend**
```bash
cd ../frontend
npm run dev
```
**Debería mostrar:**
```
  VITE v4.4.5  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### **Paso 5: Abrir Dashboard**
Ir a: **http://localhost:5173**

---

## 🎯 **LO QUE VERÁS**

### **Dashboard Principal**
- **Header con toggle** 🏠 Venta / 🔑 Renta
- **KPIs principales**: Total propiedades, precios promedio/mediano, precio/m²
- **Gráfica de barras**: Top colonias por precio/m²
- **Gráfica circular**: Distribución por tipo de propiedad
- **Insights automáticos**: Análisis generado del mercado

### **Funcionalidad del Toggle**
1. **Estado inicial**: Venta (datos de 7,593 propiedades)
2. **Click en Renta**: Cambia a datos de 1,155 propiedades
3. **Datos actualizados**: KPIs, gráficas, top colonias
4. **Transición suave**: Sin parpadeos, loading states

### **Datos Reales Mostrados**
- **Venta**: Precio promedio ~$7.07M, mediano $5.4M
- **Renta**: Precio promedio ~$30K/mes, mediano $25K/mes
- **Top colonias** con precios reales por m²
- **Distribución real** por tipos de propiedad

---

## 🔧 **TROUBLESHOOTING**

### **Error: Puerto 3001 ocupado**
```bash
# Windows
netstat -ano | findstr :3001
taskkill /PID <PID> /F

# Cambiar puerto en backend_csv/src/index.js
const PORT = process.env.PORT || 3002;
```

### **Error: No se encuentran datos**
```bash
# Verificar que existen los CSVs
ls Dashboard/data/basicos/
# Debería mostrar: kpis_principales_venta.csv, kpis_principales_renta.csv, etc.

# Si no existen, ejecutar de nuevo:
cd Dashboard
python python_sync/generate_dashboard_data.py
```

### **Error: Dependencias no instaladas**
```bash
# Backend
cd Dashboard/backend_csv
rm -rf node_modules package-lock.json
npm install

# Frontend  
cd ../frontend
rm -rf node_modules package-lock.json
npm install
```

### **Error: CORS**
El frontend está configurado para hacer proxy a `localhost:3001`. Si cambias el puerto del backend, actualiza `frontend/vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:3002', // Cambiar aquí
    },
  },
}
```

---

## 📊 **ENDPOINTS DISPONIBLES**

### **Probar Backend Directamente**
```bash
# KPIs de venta
curl "http://localhost:3001/api/stats/overview?operacion=venta"

# KPIs de renta
curl "http://localhost:3001/api/stats/overview?operacion=renta"

# Operaciones disponibles
curl "http://localhost:3001/api/stats/operations"

# Histograma de precios
curl "http://localhost:3001/api/stats/histogram?variable=precios&operacion=venta"
```

---

## 🎨 **CARACTERÍSTICAS IMPLEMENTADAS**

### **✅ Toggle Venta/Renta**
- Botones con iconos 🏠 y 🔑
- Colores diferenciados (azul/verde)
- Estado persistente en la sesión
- Cambio instantáneo de datos

### **✅ Dashboard Responsivo**
- Mobile-first design
- Grid adaptativo
- Componentes optimizados para touch
- Loading states y error handling

### **✅ Gráficas Interactivas**
- Recharts con tooltips personalizados
- Formateo de números en pesos mexicanos
- Colores consistentes con la operación
- Responsive y accesible

### **✅ Performance Optimizada**
- React Query con cache inteligente
- Zustand para estado global ligero
- Lazy loading de componentes
- Debouncing en filtros futuros

---

## 🔮 **PRÓXIMAS FUNCIONALIDADES**

### **Semana 1: Filtros Dinámicos**
- [ ] Filtros por municipio, tipo, precio
- [ ] Rangos deslizantes para superficie
- [ ] Búsqueda de colonias
- [ ] Filtros que se mantienen al cambiar operación

### **Semana 2: Vista Explorar**
- [ ] Mapa interactivo con Mapbox
- [ ] Clustering dinámico por zoom
- [ ] Heatmap de precios por colonia
- [ ] Lista de propiedades filtrable

### **Semana 3: Vista Segmentos**
- [ ] Segmentos predefinidos (Starter, Familiar, Premium)
- [ ] Constructor de segmentos personalizado
- [ ] Comparador lado a lado
- [ ] Análisis de ROI por segmento

### **Semana 4: Vista Analítica**
- [ ] Matriz de correlaciones interactiva
- [ ] Análisis de clusters de colonias
- [ ] Impacto de amenidades en precio
- [ ] Exportación de reportes

---

## 🎉 **¡DASHBOARD LISTO!**

Con estos pasos tendrás un **dashboard completamente funcional** con:

- ✅ **Toggle venta/renta** que funciona perfectamente
- ✅ **Datos reales** de 8,748 propiedades de la ZMG
- ✅ **Gráficas interactivas** con estadísticas por operación
- ✅ **Design moderno** y mobile-friendly
- ✅ **Performance optimizada** con cache y loading states

**¡El dashboard está listo para usar y demostrar!** 🚀
