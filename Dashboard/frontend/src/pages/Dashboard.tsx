import { useOverview } from '@/hooks/useStatsAPI';
import { useOperationStore } from '@/store/operationStore';
import { KPICard, KPICardCompact } from '@/components/KPICard';
import { SimpleBarChart } from '@/components/charts/SimpleBarChart';
import { SimplePieChart } from '@/components/charts/PieChart';
import { formatNumber } from '@/lib/utils';
import { 
  Home, 
  DollarSign, 
  TrendingUp, 
  MapPin, 
  Building2,
  Users,
  Calendar,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';

export function Dashboard() {
  const { currentOperation } = useOperationStore();
  const { data: overview, isLoading, error } = useOverview();

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error al cargar datos</h3>
          <p className="text-gray-500">No se pudieron cargar las estadísticas del dashboard.</p>
        </div>
      </div>
    );
  }

  const operationConfig = {
    venta: {
      title: 'Mercado de Venta',
      color: 'blue',
      icon: '🏠',
      unitLabel: 'propiedades en venta'
    },
    renta: {
      title: 'Mercado de Renta',
      color: 'green', 
      icon: '🔑',
      unitLabel: 'propiedades en renta'
    }
  };

  const config = operationConfig[currentOperation];

  return (
    <div className="space-y-6">
      {/* Header con contexto de operación */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              {config.icon} {config.title}
            </h1>
            <p className="text-gray-600 mt-1">
              Análisis de inteligencia inmobiliaria para la ZMG
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Última actualización</div>
            <div className="text-sm font-medium text-gray-700">
              {overview?.meta.lastUpdate ? 
                new Date(overview.meta.lastUpdate).toLocaleString('es-MX') : 
                'Cargando...'
              }
            </div>
          </div>
        </div>
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total de Propiedades"
          value={overview?.data.totalProperties || 0}
          subtitle={config.unitLabel}
          icon={<Building2 size={20} />}
          loading={isLoading}
        />
        
        <KPICard
          title="Precio Promedio"
          value={overview?.data.avgPrice?.formatted || '$0'}
          subtitle="Promedio del mercado"
          icon={<DollarSign size={20} />}
          loading={isLoading}
        />
        
        <KPICard
          title="Precio Mediano"
          value={overview?.data.medianPrice?.formatted || '$0'}
          subtitle="Valor mediano"
          icon={<TrendingUp size={20} />}
          loading={isLoading}
        />
        
        <KPICard
          title="Precio por m²"
          value={overview?.data.avgPxm2?.formatted || '$0/m²'}
          subtitle="Promedio por metro cuadrado"
          icon={<Home size={20} />}
          loading={isLoading}
        />
      </div>

      {/* Gráficas principales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Colonias */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <MapPin size={20} />
              Top Colonias por Precio/m²
            </h2>
            <span className="text-sm text-gray-500">
              {overview?.data.topColonies?.length || 0} colonias
            </span>
          </div>
          
          <SimpleBarChart
            data={overview?.data.topColonies?.slice(0, 10).map(colony => ({
              name: colony.name || 'Sin nombre',
              value: colony.avgPxm2 || colony.avgPrice || 0,
              municipio: colony.municipality || 'N/A',
              count: colony.count || 0
            })) || []}
            height={350}
            loading={isLoading}
            color={currentOperation === 'venta' ? '#3b82f6' : '#10b981'}
          />
        </div>

        {/* Distribución por Tipo */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BarChart3 size={20} />
              Distribución por Tipo
            </h2>
            <span className="text-sm text-gray-500">
              {overview?.data.byPropertyType?.length || 0} tipos
            </span>
          </div>
          
          <SimplePieChart
            data={overview?.data.byPropertyType?.map(type => ({
              name: type.type || 'Sin tipo',
              value: type.count || 0,
              percentage: type.percentage || 0
            })) || []}
            height={350}
            loading={isLoading}
          />
        </div>
      </div>

      {/* Insights automáticos */}
      {overview?.data.insights && overview.data.insights.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Info size={20} />
            Insights del Mercado
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {overview.data.insights.map((insight, index) => (
              <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-full ${
                    insight.impact === 'high' ? 'bg-red-100 text-red-600' :
                    insight.impact === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-green-100 text-green-600'
                  }`}>
                    {insight.impact === 'high' ? <AlertCircle size={16} /> :
                     insight.impact === 'medium' ? <Info size={16} /> :
                     <CheckCircle size={16} />}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-1">{insight.title}</h3>
                    <p className="text-sm text-gray-600">{insight.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Estadísticas adicionales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Superficie Promedio</h3>
          <div className="text-2xl font-bold text-gray-900">
            {overview?.data.quickStats?.avgSurface ? `${Math.round(overview.data.quickStats.avgSurface)} m²` : '0 m²'}
          </div>
          <p className="text-sm text-gray-500 mt-1">Metros cuadrados promedio</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Listados Activos</h3>
          <div className="text-2xl font-bold text-gray-900">
            {formatNumber(overview?.data.activeListings || 0)}
          </div>
          <p className="text-sm text-gray-500 mt-1">Propiedades disponibles</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Tiempo de Respuesta</h3>
          <div className="text-2xl font-bold text-gray-900">
            {overview?.meta.executionTimeMs || 0}ms
          </div>
          <p className="text-sm text-gray-500 mt-1">Velocidad de consulta</p>
        </div>
      </div>
    </div>
  );
}
