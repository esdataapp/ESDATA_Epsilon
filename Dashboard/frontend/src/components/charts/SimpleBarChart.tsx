import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatNumber } from '@/lib/utils';

interface SimpleBarChartProps {
  data: Array<{
    name: string;
    value: number;
    [key: string]: any;
  }>;
  dataKey?: string;
  nameKey?: string;
  color?: string;
  height?: number;
  loading?: boolean;
}

export function SimpleBarChart({
  data,
  dataKey = 'value',
  nameKey = 'name',
  color = '#3b82f6',
  height = 300,
  loading = false,
}: SimpleBarChartProps) {
  if (loading) {
    return (
      <div className="w-full bg-gray-100 rounded-lg animate-pulse" style={{ height }}>
        <div className="flex items-center justify-center h-full">
          <div className="text-gray-400">Cargando gráfica...</div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="w-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 flex items-center justify-center" style={{ height }}>
        <div className="text-gray-400">No hay datos disponibles</div>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis 
          dataKey={nameKey}
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={60}
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => formatNumber(value)}
        />
        <Tooltip 
          formatter={(value: number) => [formatNumber(value), 'Valor']}
          labelStyle={{ color: '#374151' }}
          contentStyle={{ 
            backgroundColor: 'white', 
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Bar 
          dataKey={dataKey} 
          fill={color}
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
