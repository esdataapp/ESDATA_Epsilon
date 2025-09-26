import React, { useState, useEffect } from 'react';
import { useOperationStore } from '@/store/operationStore';
import ColonyScatterPlot from '@/components/charts/ColonyScatterPlot';
import { 
  MapPin, 
  TrendingUp, 
  BarChart3,
  Users,
  DollarSign,
  Calculator
} from 'lucide-react';

interface ColoniaData {
  periodo: string;
  ciudad: string;
  operacion: string;
  tipo: string;
  colonia: string;
  n: number;
  precio_representativo: number;
  precio_min: number;
  precio_max: number;
  precio_skew: number;
  precio_metodo: string;
  area_m2_representativo: number;
  area_m2_min: number;
  area_m2_max: number;
  area_m2_skew: number;
  area_m2_metodo: string;
  PxM2_representativo: number;
  PxM2_min: number;
  PxM2_max: number;
  PxM2_skew: number;
  PxM2_metodo: string;
}

interface SummaryStats {
  totalColonias: number;
  totalPropiedades: number;
  precioPromedio: number;
  areaPromedio: number;
  pxm2Promedio: number;
  tipoMasComun: string;
  coloniaConMasPropiedades: string;
  coloniaConMayorPrecio: string;
}

interface ScatterPoint {
  superficie: number;
  pxm2: number;
  colonia: string;
}


const FinalTablesOverview: React.FC = () => {
  const { currentOperation } = useOperationStore();
  const [data, setData] = useState<ColoniaData[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [selectedMunicipio, setSelectedMunicipio] = useState<'Gdl' | 'Zap' | 'Ambos'>('Ambos');
  const [selectedTipo, setSelectedTipo] = useState<string>('Todos');
  const [scatterData, setScatterData] = useState<ScatterPoint[]>([]);
  const [allColonies, setAllColonies] = useState<string[]>([]);
  const [selectedColonies, setSelectedColonies] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Simulación de datos basados en las tablas reales
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      
      // Simulamos datos basados en la estructura real de las tablas
      const mockData: ColoniaData[] = [
        // Zapopan - Casas
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Alamitos',
          n: 5,
          precio_representativo: 6300000,
          precio_min: 3660000,
          precio_max: 7120000,
          precio_skew: -0.52,
          precio_metodo: 'mediana_rango',
          area_m2_representativo: 230,
          area_m2_min: 147,
          area_m2_max: 282,
          area_m2_skew: -0.78,
          area_m2_metodo: 'mediana_rango',
          PxM2_representativo: 24898,
          PxM2_min: 19488,
          PxM2_max: 30957,
          PxM2_skew: 0.04,
          PxM2_metodo: 'mediana_rango'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Base Aérea Militar No 5',
          n: 34,
          precio_representativo: 8110000,
          precio_min: 4500000,
          precio_max: 24950000,
          precio_skew: 2.26,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 210,
          area_m2_min: 136,
          area_m2_max: 457,
          area_m2_skew: 1.50,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 36905,
          PxM2_min: 25281,
          PxM2_max: 61458,
          PxM2_skew: 0.97,
          PxM2_metodo: 'mediana_IQR'
        },
        // Guadalajara - Departamentos
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Americana',
          n: 83,
          precio_representativo: 4300000,
          precio_min: 1730484,
          precio_max: 8300000,
          precio_skew: 0.53,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 68,
          area_m2_min: 30,
          area_m2_max: 140,
          area_m2_skew: 0.63,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 63346,
          PxM2_min: 40714,
          PxM2_max: 106169,
          PxM2_skew: 0.89,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Colomos Providencia',
          n: 100,
          precio_representativo: 6350000,
          precio_min: 3161934,
          precio_max: 15089000,
          precio_skew: 1.36,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 100.5,
          area_m2_min: 51,
          area_m2_max: 190,
          area_m2_skew: 0.58,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 69170,
          PxM2_min: 37153,
          PxM2_max: 100767,
          PxM2_skew: 0.14,
          PxM2_metodo: 'media_desv'
        },
        // Más colonias para completar las 10 principales
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Providencia',
          n: 95,
          precio_representativo: 8500000,
          precio_min: 4200000,
          precio_max: 18500000,
          precio_skew: 1.2,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 185,
          area_m2_min: 120,
          area_m2_max: 350,
          area_m2_skew: 0.8,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 45900,
          PxM2_min: 28000,
          PxM2_max: 65000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Zona Centro',
          n: 78,
          precio_representativo: 3200000,
          precio_min: 1800000,
          precio_max: 6500000,
          precio_skew: 0.9,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 65,
          area_m2_min: 35,
          area_m2_max: 120,
          area_m2_skew: 0.7,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 49230,
          PxM2_min: 35000,
          PxM2_max: 68000,
          PxM2_skew: 0.2,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Ciudad del Sol',
          n: 72,
          precio_representativo: 7200000,
          precio_min: 3800000,
          precio_max: 14500000,
          precio_skew: 1.1,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 195,
          area_m2_min: 140,
          area_m2_max: 280,
          area_m2_skew: 0.6,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 36900,
          PxM2_min: 25000,
          PxM2_max: 52000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Chapalita',
          n: 68,
          precio_representativo: 5800000,
          precio_min: 2900000,
          precio_max: 11200000,
          precio_skew: 0.8,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 165,
          area_m2_min: 110,
          area_m2_max: 250,
          area_m2_skew: 0.5,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 35100,
          PxM2_min: 22000,
          PxM2_max: 48000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Puerta de Hierro',
          n: 65,
          precio_representativo: 9200000,
          precio_min: 5500000,
          precio_max: 18000000,
          precio_skew: 1.4,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 125,
          area_m2_min: 80,
          area_m2_max: 200,
          area_m2_skew: 0.9,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 73600,
          PxM2_min: 55000,
          PxM2_max: 95000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Jardines del Bosque',
          n: 58,
          precio_representativo: 6800000,
          precio_min: 3500000,
          precio_max: 13500000,
          precio_skew: 1.0,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 180,
          area_m2_min: 125,
          area_m2_max: 280,
          area_m2_skew: 0.7,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 37800,
          PxM2_min: 24000,
          PxM2_max: 55000,
          PxM2_skew: 0.5,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Lomas del Valle',
          n: 52,
          precio_representativo: 7800000,
          precio_min: 4100000,
          precio_max: 15200000,
          precio_skew: 1.2,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 205,
          area_m2_min: 150,
          area_m2_max: 320,
          area_m2_skew: 0.8,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 38100,
          PxM2_min: 26000,
          PxM2_max: 52000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Lafayette',
          n: 48,
          precio_representativo: 4500000,
          precio_min: 2200000,
          precio_max: 8500000,
          precio_skew: 0.9,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 85,
          area_m2_min: 55,
          area_m2_max: 140,
          area_m2_skew: 0.6,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 52900,
          PxM2_min: 38000,
          PxM2_max: 72000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        // Colonias adicionales para mayor variedad
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Santa Anita',
          n: 42,
          precio_representativo: 5200000,
          precio_min: 2800000,
          precio_max: 9500000,
          precio_skew: 0.8,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 175,
          area_m2_min: 120,
          area_m2_max: 260,
          area_m2_skew: 0.6,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 29700,
          PxM2_min: 20000,
          PxM2_max: 42000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Monraz',
          n: 38,
          precio_representativo: 4800000,
          precio_min: 2500000,
          precio_max: 8200000,
          precio_skew: 0.7,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 155,
          area_m2_min: 100,
          area_m2_max: 220,
          area_m2_skew: 0.5,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 31000,
          PxM2_min: 22000,
          PxM2_max: 45000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Arcos Vallarta',
          n: 35,
          precio_representativo: 7500000,
          precio_min: 4200000,
          precio_max: 12800000,
          precio_skew: 1.1,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 110,
          area_m2_min: 75,
          area_m2_max: 165,
          area_m2_skew: 0.8,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 68200,
          PxM2_min: 48000,
          PxM2_max: 88000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Del Valle',
          n: 32,
          precio_representativo: 3800000,
          precio_min: 2000000,
          precio_max: 6500000,
          precio_skew: 0.8,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 72,
          area_m2_min: 45,
          area_m2_max: 110,
          area_m2_skew: 0.6,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 52800,
          PxM2_min: 38000,
          PxM2_max: 70000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Tabachines',
          n: 28,
          precio_representativo: 6200000,
          precio_min: 3500000,
          precio_max: 11000000,
          precio_skew: 0.9,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 190,
          area_m2_min: 140,
          area_m2_max: 280,
          area_m2_skew: 0.7,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 32600,
          PxM2_min: 23000,
          PxM2_max: 46000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Ladron de Guevara',
          n: 25,
          precio_representativo: 5500000,
          precio_min: 3000000,
          precio_max: 9200000,
          precio_skew: 0.8,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 160,
          area_m2_min: 110,
          area_m2_max: 230,
          area_m2_skew: 0.6,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 34400,
          PxM2_min: 25000,
          PxM2_max: 48000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Valle Real',
          n: 22,
          precio_representativo: 8800000,
          precio_min: 5200000,
          precio_max: 15500000,
          precio_skew: 1.3,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 135,
          area_m2_min: 90,
          area_m2_max: 200,
          area_m2_skew: 0.9,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 65200,
          PxM2_min: 48000,
          PxM2_max: 85000,
          PxM2_skew: 0.4,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Gdl',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Dep',
          colonia: 'Minerva',
          n: 18,
          precio_representativo: 4200000,
          precio_min: 2300000,
          precio_max: 7500000,
          precio_skew: 0.9,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 78,
          area_m2_min: 50,
          area_m2_max: 120,
          area_m2_skew: 0.7,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 53800,
          PxM2_min: 40000,
          PxM2_max: 72000,
          PxM2_skew: 0.3,
          PxM2_metodo: 'mediana_IQR'
        },
        {
          periodo: 'Sep25',
          ciudad: 'Zap',
          operacion: currentOperation === 'venta' ? 'Ven' : 'Ren',
          tipo: 'Cas',
          colonia: 'Real del Valle',
          n: 15,
          precio_representativo: 9500000,
          precio_min: 5800000,
          precio_max: 18200000,
          precio_skew: 1.4,
          precio_metodo: 'mediana_IQR',
          area_m2_representativo: 220,
          area_m2_min: 160,
          area_m2_max: 350,
          area_m2_skew: 1.0,
          area_m2_metodo: 'mediana_IQR',
          PxM2_representativo: 43200,
          PxM2_min: 30000,
          PxM2_max: 62000,
          PxM2_skew: 0.5,
          PxM2_metodo: 'mediana_IQR'
        }
      ];

      // Filtrar datos según selecciones
      let filteredData = mockData;
      
      if (selectedMunicipio !== 'Ambos') {
        filteredData = filteredData.filter(item => item.ciudad === selectedMunicipio);
      }
      
      if (selectedTipo !== 'Todos') {
        filteredData = filteredData.filter(item => item.tipo === selectedTipo);
      }

      // Calcular estadísticas resumen
      const totalColonias = filteredData.length;
      const totalPropiedades = filteredData.reduce((sum, item) => sum + item.n, 0);
      const precioPromedio = filteredData.reduce((sum, item) => sum + item.precio_representativo, 0) / totalColonias;
      const areaPromedio = filteredData.reduce((sum, item) => sum + item.area_m2_representativo, 0) / totalColonias;
      const pxm2Promedio = filteredData.reduce((sum, item) => sum + item.PxM2_representativo, 0) / totalColonias;
      
      const tipoCount = filteredData.reduce((acc, item) => {
        acc[item.tipo] = (acc[item.tipo] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      const tipoMasComun = Object.keys(tipoCount).reduce((a, b) => tipoCount[a] > tipoCount[b] ? a : b);
      
      const coloniaConMasPropiedades = filteredData.reduce((max, item) => 
        item.n > max.n ? item : max
      ).colonia;
      
      const coloniaConMayorPrecio = filteredData.reduce((max, item) => 
        item.precio_representativo > max.precio_representativo ? item : max
      ).colonia;

      setSummary({
        totalColonias,
        totalPropiedades,
        precioPromedio,
        areaPromedio,
        pxm2Promedio,
        tipoMasComun,
        coloniaConMasPropiedades,
        coloniaConMayorPrecio
      });

      // --- Lógica para la gráfica de dispersión ---
      if (totalColonias > 0) {
        // 1. Obtener todas las colonias disponibles (ordenadas por número de propiedades)
        const sortedByN = [...filteredData].sort((a, b) => b.n - a.n);
        const coloniaNames = sortedByN.map(c => c.colonia);
        setAllColonies(coloniaNames);
        
        // Inicializar vacío para que el usuario seleccione manualmente
        // No seleccionar colonias automáticamente

        // 2. Simular puntos de datos individuales para la gráfica
        const generateScatterPoints = (colonia: ColoniaData): ScatterPoint[] => {
          const points: ScatterPoint[] = [];
          for (let i = 0; i < colonia.n; i++) {
            // Generar valores aleatorios dentro del rango min-max
            const superficie = colonia.area_m2_min + Math.random() * (colonia.area_m2_max - colonia.area_m2_min);
            const pxm2 = colonia.PxM2_min + Math.random() * (colonia.PxM2_max - colonia.PxM2_min);
            points.push({ superficie, pxm2, colonia: colonia.colonia });
          }
          return points;
        };

        const allScatterPoints = sortedByN.flatMap(generateScatterPoints);
        setScatterData(allScatterPoints);
      } else {
        setScatterData([]);
        setAllColonies([]);
      }

      setData(filteredData);
      setLoading(false);
    };

    loadData();
  }, [currentOperation, selectedMunicipio, selectedTipo]);

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  const getTipoLabel = (tipo: string) => {
    const labels: Record<string, string> = {
      'Cas': 'Casa',
      'Dep': 'Departamento',
      'CasC': 'Casa en Condominio',
      'Terreno___Lote': 'Terreno/Lote',
      'Ofc': 'Oficina',
      'LocC': 'Local Comercial'
    };
    return labels[tipo] || tipo;
  };

  // Funciones para controlar la selección de colonias en la gráfica
  const handleColonyToggle = (colonia: string) => {
    setSelectedColonies(prev => 
      prev.includes(colonia) 
        ? prev.filter(c => c !== colonia)
        : [...prev, colonia]
    );
  };

  const handleSelectAll = () => {
    setSelectedColonies([...allColonies]);
  };

  const handleClearAll = () => {
    setSelectedColonies([]);
  };

  const handleSelectByMunicipality = (municipality: 'Gdl' | 'Zap') => {
    const coloniesInMunicipality = data
      .filter(item => item.ciudad === municipality)
      .map(item => item.colonia)
      .filter(colonia => allColonies.includes(colonia));
    setSelectedColonies(coloniesInMunicipality);
  };

  // Filtrar datos de dispersión según colonias seleccionadas
  const filteredScatterData = scatterData.filter(point => 
    selectedColonies.includes(point.colonia)
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-neutral-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-neutral-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-neutral-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900 flex items-center gap-2">
            <BarChart3 className="text-primary-600" size={28} />
            Análisis de Tablas Finales - Sep25
          </h2>
          <p className="text-neutral-600 mt-1">
            Datos procesados por colonia con métricas estadísticas avanzadas
          </p>
        </div>

        {/* Filtros */}
        <div className="flex gap-3">
          <select
            value={selectedMunicipio}
            onChange={(e) => setSelectedMunicipio(e.target.value as 'Gdl' | 'Zap' | 'Ambos')}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="Ambos">Ambos Municipios</option>
            <option value="Gdl">Guadalajara</option>
            <option value="Zap">Zapopan</option>
          </select>

          <select
            value={selectedTipo}
            onChange={(e) => setSelectedTipo(e.target.value)}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="Todos">Todos los Tipos</option>
            <option value="Cas">Casas</option>
            <option value="Dep">Departamentos</option>
            <option value="CasC">Casas en Condominio</option>
            <option value="Terreno___Lote">Terrenos/Lotes</option>
            <option value="Ofc">Oficinas</option>
          </select>
        </div>
      </div>

      {/* KPIs Resumen */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-600">Total Colonias</p>
                <p className="text-2xl font-bold text-neutral-900">{summary.totalColonias}</p>
              </div>
              <MapPin className="text-primary-600" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-600">Total Propiedades</p>
                <p className="text-2xl font-bold text-neutral-900">{summary.totalPropiedades.toLocaleString()}</p>
              </div>
              <Users className="text-accent-600" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-600">Precio Promedio</p>
                <p className="text-2xl font-bold text-neutral-900">{formatPrice(summary.precioPromedio)}</p>
              </div>
              <DollarSign className="text-warning-600" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-600">Precio/m² Promedio</p>
                <p className="text-2xl font-bold text-neutral-900">{formatPrice(summary.pxm2Promedio)}/m²</p>
              </div>
              <Calculator className="text-success-600" size={24} />
            </div>
          </div>
        </div>
      )}

      {/* Tabla de Colonias */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="px-6 py-4 border-b bg-neutral-50">
          <h3 className="text-lg font-semibold text-neutral-900">
            Colonias Analizadas - {currentOperation === 'venta' ? 'Venta' : 'Renta'}
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-neutral-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Colonia
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Ciudad
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  n
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Precio Rep.
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Área m²
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Precio/m²
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Método
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200">
              {data.map((item, index) => (
                <tr key={index} className="hover:bg-neutral-50">
                  <td className="px-4 py-3 text-sm font-medium text-neutral-900">
                    {item.colonia}
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-600">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      item.ciudad === 'Gdl' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {item.ciudad === 'Gdl' ? 'Guadalajara' : 'Zapopan'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-600">
                    {getTipoLabel(item.tipo)}
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-900 text-right font-medium">
                    {item.n}
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-900 text-right font-medium">
                    {formatPrice(item.precio_representativo)}
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-900 text-right">
                    {Math.round(item.area_m2_representativo)}m²
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-900 text-right font-medium">
                    {formatPrice(item.PxM2_representativo)}/m²
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      item.precio_metodo === 'mediana_IQR' 
                        ? 'bg-purple-100 text-purple-800' 
                        : item.precio_metodo === 'mediana_rango'
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {item.precio_metodo.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="text-blue-600" size={20} />
              <h4 className="font-semibold text-blue-900">Tipo Más Común</h4>
            </div>
            <p className="text-blue-800 text-lg font-bold">{getTipoLabel(summary.tipoMasComun)}</p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="flex items-center gap-2 mb-2">
              <Users className="text-green-600" size={20} />
              <h4 className="font-semibold text-green-900">Mayor Volumen</h4>
            </div>
            <p className="text-green-800 text-lg font-bold">{summary.coloniaConMasPropiedades}</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="text-purple-600" size={20} />
              <h4 className="font-semibold text-purple-900">Mayor Precio</h4>
            </div>
            <p className="text-purple-800 text-lg font-bold">{summary.coloniaConMayorPrecio}</p>
          </div>
        </div>
      )}

      {/* Gráfica de Dispersión con Controles */}
      <div className="mt-6">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Panel de Control */}
            <div className="lg:w-1/3">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">
                Control de Colonias ({allColonies.length} disponibles)
              </h3>
              
              {/* Barra de Búsqueda */}
              <div className="mb-4">
                <input
                  type="text"
                  placeholder="Buscar colonia..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              {/* Botones de Control Rápido */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  onClick={handleSelectAll}
                  className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
                >
                  Todas ({allColonies.length})
                </button>
                <button
                  onClick={handleClearAll}
                  className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                >
                  Limpiar
                </button>
                <button
                  onClick={() => handleSelectByMunicipality('Gdl')}
                  className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
                >
                  Solo Gdl
                </button>
                <button
                  onClick={() => handleSelectByMunicipality('Zap')}
                  className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition-colors"
                >
                  Solo Zap
                </button>
              </div>

              {/* Lista de Colonias con Checkboxes */}
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {allColonies
                  .filter(colonia => 
                    colonia.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((colonia: string, index: number) => {
                    const coloniaData = data.find(d => d.colonia === colonia);
                    const isSelected = selectedColonies.includes(colonia);
                  
                  return (
                    <label
                      key={colonia}
                      className="flex items-center space-x-3 p-2 rounded hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleColonyToggle(colonia)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A4DE6C', '#D0ED57'][index % 10] }}
                          />
                          <span className="text-sm font-medium text-gray-900 truncate">
                            {colonia}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {coloniaData?.ciudad === 'Gdl' ? 'Guadalajara' : 'Zapopan'} • {coloniaData?.n} propiedades
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>

              {/* Contador de Puntos */}
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">
                  <strong>{selectedColonies.length}</strong> colonias seleccionadas
                </div>
                <div className="text-sm text-gray-600">
                  <strong>{filteredScatterData.length}</strong> puntos en la gráfica
                </div>
              </div>
            </div>

            {/* Gráfica */}
            <div className="lg:w-2/3">
              {selectedColonies.length === 0 ? (
                <div className="bg-white rounded-lg border p-4 h-96 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <div className="text-6xl mb-4">📊</div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">
                      Gráfica de Dispersión
                    </h3>
                    <p className="text-sm text-gray-500 mb-4">
                      Selecciona una o más colonias del panel izquierdo<br />
                      para ver la dispersión de superficie vs precio/m²
                    </p>
                    <div className="text-xs text-gray-400">
                      💡 Tip: Comienza seleccionando 2-3 colonias para una mejor visualización
                    </div>
                  </div>
                </div>
              ) : (
                <ColonyScatterPlot 
                  data={filteredScatterData} 
                  topColonies={selectedColonies} 
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinalTablesOverview;
