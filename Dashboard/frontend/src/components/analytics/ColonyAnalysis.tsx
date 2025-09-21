import React from 'react';
import { MapPin, TrendingUp, TrendingDown, Minus, DollarSign, Square } from 'lucide-react';
import { SimpleBarChart } from '../charts/SimpleBarChart';

interface ColonyData {
  colonia: string;
  municipio: string;
  count: number;
  precio_mean: number;
  precio_median: number;
  precio_por_m2_mean: number;
  precio_por_m2_median: number;
  superficie_mean: number;
  trend: 'up' | 'down' | 'stable';
  change_percent: number;
}

interface ColonyAnalysisProps {
  data: ColonyData[];
  loading?: boolean;
  operacion: 'venta' | 'renta';
}

const ColonyAnalysis: React.FC<ColonyAnalysisProps> = ({
  data,
  loading = false,
  operacion
}) => {
  const formatPrice = (value: number) => {
    if (operacion === 'renta') {
      return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    }
    
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp size={16} className="text-green-500" />;
      case 'down':
        return <TrendingDown size={16} className="text-red-500" />;
      default:
        return <Minus size={16} className="text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up':
        return 'text-green-600 bg-green-50';
      case 'down':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Top 10 colonias por precio/m²
  const topColonies = data
    .sort((a, b) => b.precio_por_m2_mean - a.precio_por_m2_mean)
    .slice(0, 10);

  // Preparar datos para gráfica
  const chartData = topColonies.map(colony => ({
    name: colony.colonia,
    value: colony.precio_por_m2_mean,
    municipio: colony.municipio,
    count: colony.count
  }));

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Gráfica de Top Colonias */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <MapPin size={20} className="text-blue-600" />
            Top Colonias por Precio/m²
          </h3>
          <span className="text-sm text-gray-500">
            {operacion === 'venta' ? 'Venta' : 'Renta'}
          </span>
        </div>
        
        <SimpleBarChart
          data={chartData}
          height={400}
          color="#3b82f6"
          loading={false}
        />
      </div>

      {/* Tabla detallada de colonias */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Análisis Detallado por Colonia
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Métricas clave de las principales colonias de la ZMG
          </p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Colonia
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Municipio
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Propiedades
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Precio Promedio
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Precio/m²
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Superficie Prom.
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tendencia
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {topColonies.map((colony, index) => (
                <tr key={`${colony.colonia}-${colony.municipio}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          {index + 1}
                        </span>
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          {colony.colonia}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {colony.municipio}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {colony.count.toLocaleString('es-MX')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {formatPrice(colony.precio_mean)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Mediana: {formatPrice(colony.precio_median)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {formatPrice(colony.precio_por_m2_mean)}/m²
                    </div>
                    <div className="text-xs text-gray-500">
                      Mediana: {formatPrice(colony.precio_por_m2_median)}/m²
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {Math.round(colony.superficie_mean)}m²
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getTrendColor(colony.trend)}`}>
                      {getTrendIcon(colony.trend)}
                      {colony.change_percent !== 0 && (
                        <span>{Math.abs(colony.change_percent).toFixed(1)}%</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights de colonias */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp size={20} className="text-green-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Colonia Premium</h4>
              <p className="text-sm text-gray-600">
                {topColonies[0]?.colonia || 'N/A'}
              </p>
              <p className="text-xs text-gray-500">
                {formatPrice(topColonies[0]?.precio_por_m2_mean || 0)}/m²
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <DollarSign size={20} className="text-blue-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Precio Promedio ZMG</h4>
              <p className="text-sm text-gray-600">
                {formatPrice(
                  data.reduce((sum, colony) => sum + colony.precio_mean, 0) / data.length || 0
                )}
              </p>
              <p className="text-xs text-gray-500">
                {data.length} colonias analizadas
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Square size={20} className="text-purple-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Superficie Promedio</h4>
              <p className="text-sm text-gray-600">
                {Math.round(
                  data.reduce((sum, colony) => sum + colony.superficie_mean, 0) / data.length || 0
                )}m²
              </p>
              <p className="text-xs text-gray-500">
                Promedio general ZMG
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ColonyAnalysis;
