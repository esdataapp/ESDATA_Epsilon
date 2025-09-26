import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, DollarSign, Square, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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
  const [selectedColonies, setSelectedColonies] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Obtener todas las colonias disponibles
  const allColonies = data.map(item => item.colonia);

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

  // Funciones de control para selección de colonias
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

  const handleSelectByMunicipality = (municipality: string) => {
    const coloniesInMunicipality = data
      .filter(item => item.municipio === municipality)
      .map(item => item.colonia);
    setSelectedColonies(coloniesInMunicipality);
  };

  // Preparar datos para las gráficas
  const selectedData = data.filter(item => selectedColonies.includes(item.colonia));

  const priceChartData = selectedData.map(item => ({
    colonia: item.colonia.length > 15 ? item.colonia.substring(0, 15) + '...' : item.colonia,
    precio: item.precio_mean,
    municipio: item.municipio
  }));

  const surfaceChartData = selectedData.map(item => ({
    colonia: item.colonia.length > 15 ? item.colonia.substring(0, 15) + '...' : item.colonia,
    superficie: item.superficie_mean,
    municipio: item.municipio
  }));

  const pxm2ChartData = selectedData.map(item => ({
    colonia: item.colonia.length > 15 ? item.colonia.substring(0, 15) + '...' : item.colonia,
    pxm2: item.precio_por_m2_mean,
    municipio: item.municipio
  }));

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="text-green-600" size={16} />;
      case 'down':
        return <TrendingDown className="text-red-600" size={16} />;
      default:
        return <Minus className="text-gray-600" size={16} />;
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
      {/* Panel de Control */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Controles de Selección */}
          <div className="lg:w-1/3">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">
              Seleccionar Colonias ({allColonies.length} disponibles)
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
                onClick={() => handleSelectByMunicipality('Guadalajara')}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
              >
                Solo Gdl
              </button>
              <button
                onClick={() => handleSelectByMunicipality('Zapopan')}
                className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition-colors"
              >
                Solo Zap
              </button>
            </div>

            {/* Lista de Colonias */}
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {allColonies
                .filter(colonia => 
                  colonia.toLowerCase().includes(searchTerm.toLowerCase())
                )
                .map((colonia: string) => {
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
                          <span className="text-sm font-medium text-gray-900 truncate">
                            {colonia}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {coloniaData?.municipio} • {coloniaData?.count} propiedades
                        </div>
                      </div>
                    </label>
                  );
                })}
            </div>

            {/* Contador */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600">
                <strong>{selectedColonies.length}</strong> colonias seleccionadas
              </div>
            </div>
          </div>

          {/* Vista Previa */}
          <div className="lg:w-2/3">
            {selectedColonies.length === 0 ? (
              <div className="bg-white rounded-lg border p-4 h-64 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="text-4xl mb-4">📊</div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">
                    Gráficas Comparativas
                  </h3>
                  <p className="text-sm text-gray-500">
                    Selecciona colonias para ver comparaciones de precios, superficies y precio/m²
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Comparación de {selectedColonies.length} Colonias
                </h4>
                <p className="text-sm text-gray-600">
                  Las gráficas aparecerán abajo con los datos seleccionados
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Gráficas Comparativas */}
      {selectedColonies.length > 0 && (
        <>
          {/* Gráfica de Comparación de Precios */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign size={20} className="text-green-600" />
              Comparación de Precios Promedio
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={priceChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="colonia" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis 
                  tickFormatter={(value) => formatPrice(value)}
                  fontSize={12}
                />
                <Tooltip 
                  formatter={(value: number) => [formatPrice(value), 'Precio Promedio']}
                  labelStyle={{ color: '#374151' }}
                />
                <Bar dataKey="precio" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Gráfica de Comparación de Superficies */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Square size={20} className="text-blue-600" />
              Comparación de Superficies Promedio
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={surfaceChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="colonia" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis 
                  tickFormatter={(value) => `${value}m²`}
                  fontSize={12}
                />
                <Tooltip 
                  formatter={(value: number) => [`${Math.round(value)}m²`, 'Superficie Promedio']}
                  labelStyle={{ color: '#374151' }}
                />
                <Bar dataKey="superficie" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Gráfica de Comparación de Precio/m² */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 size={20} className="text-purple-600" />
              Comparación de Precio por m²
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pxm2ChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="colonia" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis 
                  tickFormatter={(value) => `$${(value/1000).toFixed(0)}K`}
                  fontSize={12}
                />
                <Tooltip 
                  formatter={(value: number) => [formatPrice(value) + '/m²', 'Precio por m²']}
                  labelStyle={{ color: '#374151' }}
                />
                <Bar dataKey="pxm2" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
};

export default ColonyAnalysis;
