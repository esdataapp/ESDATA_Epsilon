import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { formatNumber, formatPercentage } from '@/lib/utils';

interface SimplePieChartProps {
  data: Array<{
    name: string;
    value: number;
    percentage?: number;
    [key: string]: any;
  }>;
  dataKey?: string;
  nameKey?: string;
  colors?: string[];
  height?: number;
  loading?: boolean;
  showLegend?: boolean;
}

const DEFAULT_COLORS = [
  '#3b82f6', // blue-500
  '#10b981', // emerald-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#06b6d4', // cyan-500
  '#84cc16', // lime-500
  '#f97316', // orange-500
];

export function SimplePieChart({
  data,
  dataKey = 'value',
  nameKey = 'name',
  colors = DEFAULT_COLORS,
  height = 300,
  loading = false,
  showLegend = true,
}: SimplePieChartProps) {
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

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // No mostrar label si es menos del 5%
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderCustomLabel}
          outerRadius={80}
          fill="#8884d8"
          dataKey={dataKey}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value: number, name: string) => [
            formatNumber(value),
            name
          ]}
          contentStyle={{ 
            backgroundColor: 'white', 
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        {showLegend && (
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value) => value}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  );
}
