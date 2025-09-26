import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ZAxis } from 'recharts';

interface ScatterPoint {
  superficie: number;
  pxm2: number;
  colonia: string;
}

interface ColonyScatterPlotProps {
  data: ScatterPoint[];
  topColonies: string[];
}

// Paleta de colores para las 10 colonias principales
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE',
  '#00C49F', '#FFBB28', '#FF8042', '#A4DE6C', '#D0ED57'
];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border rounded-lg shadow-lg">
        <p className="font-bold text-neutral-800">{data.colonia}</p>
        <p className="text-sm text-neutral-600">Superficie: {data.superficie.toFixed(0)} m²</p>
        <p className="text-sm text-neutral-600">Precio/m²: ${data.pxm2.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</p>
      </div>
    );
  }
  return null;
};

const ColonyScatterPlot: React.FC<ColonyScatterPlotProps> = ({ data, topColonies }) => {
  if (!data || data.length === 0) {
    return <div className="text-center text-neutral-500">No hay datos suficientes para la gráfica de dispersión.</div>;
  }

  return (
    <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
            Dispersión de Propiedades (Top 10 Colonias)
        </h3>
        <ResponsiveContainer width="100%" height={400}>
            <ScatterChart
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                    type="number" 
                    dataKey="superficie" 
                    name="Superficie" 
                    unit="m²" 
                    domain={['dataMin', 'dataMax']}
                />
                <YAxis 
                    type="number" 
                    dataKey="pxm2" 
                    name="Precio/m²" 
                    unit="$"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(value) => `$${(Number(value) / 1000).toFixed(0)}K`}
                />
                <ZAxis type="category" dataKey="colonia" name="Colonia" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                <Legend />
                {
                    topColonies.map((colonia, index) => (
                        <Scatter 
                            key={colonia} 
                            name={colonia} 
                            data={data.filter(p => p.colonia === colonia)}
                            fill={COLORS[index % COLORS.length]} 
                            shape="circle"
                        />
                    ))
                }
            </ScatterChart>
        </ResponsiveContainer>
    </div>
  );
};

export default ColonyScatterPlot;
