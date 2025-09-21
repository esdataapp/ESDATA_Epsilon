import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface HistogramBin {
  min: number;
  max: number;
  count: number;
  percentage: number;
  label: string;
}

interface DistributionHistogramProps {
  data: HistogramBin[];
  title: string;
  variable: 'precios' | 'superficie' | 'pxm2';
  height?: number;
  loading?: boolean;
  color?: string;
}

const DistributionHistogram: React.FC<DistributionHistogramProps> = ({
  data,
  title,
  variable,
  height = 300,
  loading = false,
  color = '#3b82f6'
}) => {
  const formatValue = (value: number) => {
    if (variable === 'precios') {
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(0)}K`;
      }
      return `$${value}`;
    } else if (variable === 'superficie') {
      return `${value}m²`;
    } else if (variable === 'pxm2') {
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(0)}K/m²`;
      }
      return `$${value}/m²`;
    }
    return value.toString();
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.label}</p>
          <p className="text-blue-600">
            Propiedades: <span className="font-semibold">{data.count.toLocaleString('es-MX')}</span>
          </p>
          <p className="text-gray-600">
            Porcentaje: <span className="font-semibold">{data.percentage.toFixed(1)}%</span>
          </p>
          <div className="text-xs text-gray-500 mt-1">
            Rango: {formatValue(data.min)} - {formatValue(data.max)}
          </div>
        </div>
      );
    }
    return null;
  };

  // Calcular color más intenso para barras con mayor frecuencia
  const maxCount = Math.max(...data.map(d => d.count));
  const getBarColor = (count: number) => {
    const intensity = count / maxCount;
    const baseColor = color === '#3b82f6' ? [59, 130, 246] : [16, 185, 129];
    return `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${0.3 + intensity * 0.7})`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <div className="text-4xl mb-2">📊</div>
            <p>No hay datos disponibles</p>
          </div>
        </div>
      </div>
    );
  }

  // Estadísticas adicionales
  const totalProperties = data.reduce((sum, bin) => sum + bin.count, 0);
  const mostCommonBin = data.reduce((max, bin) => bin.count > max.count ? bin : max, data[0]);

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">
            {totalProperties.toLocaleString('es-MX')} propiedades analizadas
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-600">Rango más común</div>
          <div className="text-sm font-semibold text-gray-900">
            {mostCommonBin.label}
          </div>
          <div className="text-xs text-gray-500">
            {mostCommonBin.percentage.toFixed(1)}% de propiedades
          </div>
        </div>
      </div>

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="label"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
              interval={0}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              label={{ 
                value: 'Número de Propiedades', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle' }
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="count" 
              radius={[2, 2, 0, 0]}
              stroke={color}
              strokeWidth={1}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.count)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Estadísticas resumidas */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900">
            {data.length}
          </div>
          <div className="text-sm text-gray-600">Rangos</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900">
            {mostCommonBin.count.toLocaleString('es-MX')}
          </div>
          <div className="text-sm text-gray-600">Máx. Frecuencia</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900">
            {mostCommonBin.percentage.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Del Total</div>
        </div>
      </div>
    </div>
  );
};

export default DistributionHistogram;
