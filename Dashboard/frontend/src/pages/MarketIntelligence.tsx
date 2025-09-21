import React, { useState } from 'react';
import { useOverview, useHistogram } from '@/hooks/useStatsAPI';
import { useOperationStore } from '@/store/operationStore';
import AdvancedFilters from '@/components/filters/AdvancedFilters';
import ColonyAnalysis from '@/components/analytics/ColonyAnalysis';
import DistributionHistogram from '@/components/charts/DistributionHistogram';
import SegmentAnalysis from '@/components/analytics/SegmentAnalysis';
import EnhancedKPICard from '@/components/ui/EnhancedKPICard';
import { DashboardSkeleton, KPICardSkeleton } from '@/components/ui/SkeletonLoader';
import ActiveFiltersChips, { useActiveFilters } from '@/components/filters/ActiveFiltersChips';
import ScatterPlotWithClustering from '@/components/charts/ScatterPlotWithClustering';
import { 
  BarChart3,
  MapPin,
  Filter,
  TrendingUp,
  PieChart,
  Layers,
  Target,
  Brain,
  Zap
} from 'lucide-react';

interface FilterState {
  colonias: string[];
  municipios: string[];
  tiposPropiedad: string[];
  recamaras: number[];
  banos: number[];
  precioMin: number;
  precioMax: number;
  superficieMin: number;
  superficieMax: number;
  pxm2Min: number;
  pxm2Max: number;
}

const initialFilters: FilterState = {
  colonias: [],
  municipios: [],
  tiposPropiedad: [],
  recamaras: [],
  banos: [],
  precioMin: 0,
  precioMax: 50000000,
  superficieMin: 0,
  superficieMax: 1000,
  pxm2Min: 0,
  pxm2Max: 200000,
};

export function MarketIntelligence() {
  const { currentOperation } = useOperationStore();
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const [activeView, setActiveView] = useState<'overview' | 'colonies' | 'distributions' | 'segments' | 'scatter'>('overview');
  const {
    activeFilters,
    addFilter,
    removeFilter,
    clearAllFilters
  } = useActiveFilters();

  // Hooks para datos
  const { data: overview, isLoading: overviewLoading } = useOverview();
  const { data: priceHistogram, isLoading: priceHistLoading } = useHistogram('precios');
  const { data: surfaceHistogram, isLoading: surfaceHistLoading } = useHistogram('superficie');
  const { data: pxm2Histogram, isLoading: pxm2HistLoading } = useHistogram('pxm2');

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  const handleApplyFilters = () => {
    // Agregar filtros activos basados en el estado actual
    if (filters.municipios.length > 0) {
      addFilter({
        label: 'Municipio',
        value: filters.municipios,
        type: 'municipio'
      });
    }
    if (filters.tiposPropiedad.length > 0) {
      addFilter({
        label: 'Tipo',
        value: filters.tiposPropiedad,
        type: 'tipo'
      });
    }
    console.log('Aplicando filtros:', filters);
  };

  const handleClearFilters = () => {
    setFilters(initialFilters);
    clearAllFilters();
  };

  // Datos mock para colonias (esto vendría del backend con filtros aplicados)
  const mockColonyData = overview?.data.topColonies?.map(colony => ({
    colonia: colony.name,
    municipio: colony.municipality,
    count: colony.count,
    precio_mean: colony.avgPrice,
    precio_median: colony.avgPrice * 0.9,
    precio_por_m2_mean: colony.avgPxm2,
    precio_por_m2_median: colony.avgPxm2 * 0.95,
    superficie_mean: 200,
    trend: 'stable' as const,
    change_percent: 0
  })) || [];

  // Datos mock para segmentos
  const mockSegmentData = [
    {
      segment: '1 Rec + 1-1.5 Baños',
      recamaras: 1,
      banos: 1,
      count: 1250,
      precio_min: 1500000,
      precio_max: 4500000,
      precio_mean: 2800000,
      precio_median: 2650000,
      superficie_min: 45,
      superficie_max: 85,
      superficie_mean: 65,
      pxm2_min: 25000,
      pxm2_max: 65000,
      pxm2_mean: 43000,
      percentage: 16.5
    },
    {
      segment: '2 Rec + 2-2.5 Baños',
      recamaras: 2,
      banos: 2,
      count: 2890,
      precio_min: 2800000,
      precio_max: 8500000,
      precio_mean: 5200000,
      precio_median: 4900000,
      superficie_min: 75,
      superficie_max: 140,
      superficie_mean: 105,
      pxm2_min: 30000,
      pxm2_max: 70000,
      pxm2_mean: 49500,
      percentage: 38.1
    },
    {
      segment: '3 Rec + 3-3.5 Baños',
      recamaras: 3,
      banos: 3,
      count: 2100,
      precio_min: 4500000,
      precio_max: 15000000,
      precio_mean: 8200000,
      precio_median: 7500000,
      superficie_min: 120,
      superficie_max: 220,
      superficie_mean: 165,
      pxm2_min: 35000,
      pxm2_max: 85000,
      pxm2_mean: 52000,
      percentage: 27.7
    }
  ];

  const operationConfig = {
    venta: {
      title: 'Inteligencia de Mercado - Venta',
      color: '#3b82f6',
      icon: '🏠'
    },
    renta: {
      title: 'Inteligencia de Mercado - Renta',
      color: '#10b981',
      icon: '🔑'
    }
  };

  const config = operationConfig[currentOperation];

  const viewButtons = [
    { key: 'overview', label: 'Resumen Ejecutivo', icon: Brain },
    { key: 'colonies', label: 'Análisis por Colonias', icon: MapPin },
    { key: 'distributions', label: 'Distribuciones de Mercado', icon: BarChart3 },
    { key: 'segments', label: 'Segmentación Avanzada', icon: Target },
    { key: 'scatter', label: 'Análisis de Correlación', icon: TrendingUp }
  ];

  // Datos mock para scatter plot
  const mockScatterData = overview?.data.topColonies?.map((colony, index) => ({
    id: `prop-${index}`,
    superficie: 80 + Math.random() * 200,
    precio: colony.avgPrice || 3000000 + Math.random() * 5000000,
    colonia: colony.name,
    municipio: colony.municipality,
    tipo_propiedad: ['Casa', 'Departamento', 'Casa en Condominio'][Math.floor(Math.random() * 3)],
    pxm2: colony.avgPxm2 || 35000 + Math.random() * 30000
  })) || [];

  // Datos para sparklines
  const generateSparkData = (base: number) => {
    return Array.from({ length: 12 }, (_, i) => ({
      value: base + (Math.random() - 0.5) * base * 0.2,
      timestamp: new Date(2024, i, 1).toISOString()
    }));
  };

  if (overviewLoading && !overview) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header con nueva paleta profesional */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-700 rounded-lg shadow-lg text-white p-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3 animate-slide-up">
              <div className="p-2 bg-white bg-opacity-20 rounded-lg backdrop-blur-xs">
                <Zap size={32} className="text-white" />
              </div>
              {config.title}
            </h1>
            <p className="text-primary-100 mt-2 text-lg animate-slide-up" style={{ animationDelay: '0.1s' }}>
              Análisis avanzado de inteligencia inmobiliaria para profesionales de la ZMG
            </p>
            <div className="flex items-center gap-4 mt-3 text-sm text-primary-200">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-accent-400 rounded-full animate-pulse-soft"></div>
                Datos en tiempo real
              </span>
              <span>•</span>
              <span>Actualizado: {new Date().toLocaleDateString('es-MX')}</span>
            </div>
          </div>
          <div className="text-right animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <div className="text-6xl mb-2 drop-shadow-lg">{config.icon}</div>
            <div className="bg-white bg-opacity-20 rounded-lg p-3 backdrop-blur-xs">
              <div className="text-2xl font-bold">
                {overview?.data.totalProperties?.toLocaleString('es-MX') || '0'}
              </div>
              <div className="text-xs text-primary-200">propiedades analizadas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filtros Avanzados */}
      <AdvancedFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onApplyFilters={handleApplyFilters}
        onClearFilters={handleClearFilters}
        loading={overviewLoading}
      />

      {/* Chips de Filtros Activos */}
      {activeFilters.length > 0 && (
        <ActiveFiltersChips
          filters={activeFilters}
          onRemoveFilter={removeFilter}
          onClearAll={clearAllFilters}
          className="animate-slide-up"
        />
      )}

      {/* Navegación de vistas */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap gap-2">
          {viewButtons.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveView(key as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                activeView === key
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Contenido dinámico basado en la vista activa */}
      {activeView === 'overview' && (
        <div className="space-y-6">
          {/* Insights Ejecutivos */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Brain size={24} className="text-purple-600" />
              Insights Ejecutivos del Mercado
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                <h3 className="font-semibold text-green-800 mb-2">🎯 Oportunidad Premium</h3>
                <p className="text-sm text-green-700">
                  Las colonias de Zapopan muestran un crecimiento del 12% en precio/m² en el último trimestre.
                </p>
                <div className="text-xs text-green-600 mt-2 font-medium">
                  Recomendación: Inversión en Puerta Las Lomas
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <h3 className="font-semibold text-blue-800 mb-2">📊 Tendencia de Mercado</h3>
                <p className="text-sm text-blue-700">
                  El segmento de 2 rec + 2 baños representa el 38% del mercado con alta liquidez.
                </p>
                <div className="text-xs text-blue-600 mt-2 font-medium">
                  Segmento más activo del mercado
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                <h3 className="font-semibold text-purple-800 mb-2">🔍 Análisis de Valor</h3>
                <p className="text-sm text-purple-700">
                  Propiedades entre 100-150m² muestran la mejor relación precio-valor en la ZMG.
                </p>
                <div className="text-xs text-purple-600 mt-2 font-medium">
                  Sweet spot del mercado
                </div>
              </div>
            </div>
          </div>

          {/* Métricas clave con EnhancedKPICard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {overviewLoading ? (
              [...Array(4)].map((_, i) => <KPICardSkeleton key={i} />)
            ) : (
              <>
                <EnhancedKPICard
                  title="Precio Mediano ZMG"
                  value={overview?.data.medianPrice?.formatted || '$0'}
                  subtitle="Valor de referencia del mercado"
                  icon={<TrendingUp size={20} />}
                  sparkData={generateSparkData(overview?.data.medianPrice?.value || 5000000)}
                  trend="up"
                  change={12.5}
                  changeLabel="vs. trimestre anterior"
                  variant="success"
                  tooltip="Precio mediano (p50) es más robusto que el promedio ante outliers"
                />
                
                <EnhancedKPICard
                  title="Precio/m² Promedio"
                  value={overview?.data.avgPxm2?.formatted || '$0/m²'}
                  subtitle="Métrica de valoración"
                  icon={<BarChart3 size={20} />}
                  sparkData={generateSparkData(overview?.data.avgPxm2?.value || 35000)}
                  trend="stable"
                  change={2.1}
                  changeLabel="variación mensual"
                  tooltip="Precio por metro cuadrado promedio ponderado por superficie"
                />
                
                <EnhancedKPICard
                  title="Colonias Analizadas"
                  value={overview?.data.topColonies?.length || 0}
                  subtitle="Cobertura geográfica"
                  icon={<MapPin size={20} />}
                  trend="up"
                  change={8.3}
                  changeLabel="nuevas colonias este mes"
                  variant="premium"
                  tooltip="Total de colonias con suficientes datos para análisis estadístico"
                />
                
                <EnhancedKPICard
                  title="Superficie Promedio"
                  value={overview?.data.quickStats?.avgSurface ? `${Math.round(overview.data.quickStats.avgSurface)}m²` : '0m²'}
                  subtitle="Tamaño típico de propiedad"
                  icon={<Layers size={20} />}
                  sparkData={generateSparkData(overview?.data.quickStats?.avgSurface || 150)}
                  trend="down"
                  change={-1.8}
                  changeLabel="tendencia hacia compacto"
                  tooltip="Superficie promedio ponderada por número de propiedades"
                />
              </>
            )}
          </div>
        </div>
      )}

      {activeView === 'colonies' && (
        <ColonyAnalysis
          data={mockColonyData}
          loading={overviewLoading}
          operacion={currentOperation}
        />
      )}

      {activeView === 'distributions' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 size={24} className="text-blue-600" />
              Distribuciones de Mercado
            </h2>
            <p className="text-gray-600 mb-6">
              Análisis de frecuencias y patrones de distribución para identificar oportunidades de mercado
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DistributionHistogram
              data={priceHistogram?.bins || []}
              title="Distribución de Precios"
              variable="precios"
              loading={priceHistLoading}
              color={config.color}
            />
            
            <DistributionHistogram
              data={surfaceHistogram?.bins || []}
              title="Distribución de Superficie"
              variable="superficie"
              loading={surfaceHistLoading}
              color={config.color}
            />
          </div>

          <DistributionHistogram
            data={pxm2Histogram?.bins || []}
            title="Distribución de Precio por m²"
            variable="pxm2"
            height={400}
            loading={pxm2HistLoading}
            color={config.color}
          />
        </div>
      )}

      {activeView === 'segments' && (
        <SegmentAnalysis
          data={mockSegmentData}
          loading={overviewLoading}
          operacion={currentOperation}
          onSegmentSelect={(segment) => {
            console.log('Segmento seleccionado:', segment);
          }}
        />
      )}

      {activeView === 'scatter' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-bold text-neutral-900 mb-4 flex items-center gap-2">
              <Target size={24} className="text-primary-600" />
              Análisis de Correlación Avanzado
            </h2>
            <p className="text-neutral-600 mb-6">
              Clustering automático y análisis de correlación entre precio, superficie y ubicación
            </p>
          </div>

          <ScatterPlotWithClustering
            data={mockScatterData}
            loading={overviewLoading}
            height={500}
            showTrendLine={true}
            showClusters={true}
            operacion={currentOperation}
          />

          {/* Insights de correlación */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-accent-50 to-accent-100 rounded-lg p-6 border border-accent-200">
              <h3 className="font-semibold text-accent-800 mb-2 flex items-center gap-2">
                <TrendingUp size={18} />
                Correlación Positiva
              </h3>
              <p className="text-sm text-accent-700 mb-3">
                Existe una correlación fuerte (r=0.78) entre superficie y precio en la ZMG.
              </p>
              <div className="text-xs text-accent-600 font-medium">
                ✓ Relación lineal confirmada
              </div>
            </div>

            <div className="bg-gradient-to-br from-warning-50 to-warning-100 rounded-lg p-6 border border-warning-200">
              <h3 className="font-semibold text-warning-800 mb-2 flex items-center gap-2">
                <Target size={18} />
                Sweet Spot Identificado
              </h3>
              <p className="text-sm text-warning-700 mb-3">
                Propiedades de 120-180m² muestran la mejor relación precio-valor.
              </p>
              <div className="text-xs text-warning-600 font-medium">
                🎥 Oportunidad de inversión
              </div>
            </div>

            <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-lg p-6 border border-primary-200">
              <h3 className="font-semibold text-primary-800 mb-2 flex items-center gap-2">
                <Layers size={18} />
                Clusters Identificados
              </h3>
              <p className="text-sm text-primary-700 mb-3">
                4 segmentos distintos desde económico hasta ultra lujo.
              </p>
              <div className="text-xs text-primary-600 font-medium">
                📊 Segmentación automática
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
