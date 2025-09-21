import React, { useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import { TrendingUp, Target, Layers } from 'lucide-react';

interface DataPoint {
  id: string;
  superficie: number;
  precio: number;
  colonia: string;
  municipio: string;
  tipo_propiedad: string;
  pxm2: number;
  cluster?: number;
}

interface ClusterInfo {
  id: number;
  name: string;
  color: string;
  description: string;
  count: number;
  avgPrice: number;
  avgSurface: number;
  avgPxm2: number;
}

interface ScatterPlotWithClusteringProps {
  data: DataPoint[];
  loading?: boolean;
  height?: number;
  showTrendLine?: boolean;
  showClusters?: boolean;
  operacion: 'venta' | 'renta';
}

// Algoritmo simple de clustering K-means (simulado)
const performClustering = (data: DataPoint[], k: number = 4): { data: DataPoint[], clusters: ClusterInfo[] } => {
  if (data.length === 0) return { data: [], clusters: [] };

  // Normalizar datos para clustering
  const maxPrice = Math.max(...data.map(d => d.precio));
  const maxSurface = Math.max(...data.map(d => d.superficie));
  
  // Definir clusters predefinidos basados en rangos de precio y superficie
  const clusterDefinitions = [
    { 
      id: 0, 
      name: 'Económico Compacto', 
      color: '#10b981', 
      description: 'Propiedades pequeñas y accesibles',
      priceRange: [0, maxPrice * 0.3],
      surfaceRange: [0, maxSurface * 0.4]
    },
    { 
      id: 1, 
      name: 'Familiar Estándar', 
      color: '#3b82f6', 
      description: 'Propiedades familiares de tamaño medio',
      priceRange: [maxPrice * 0.25, maxPrice * 0.65],
      surfaceRange: [maxSurface * 0.35, maxSurface * 0.75]
    },
    { 
      id: 2, 
      name: 'Premium Espacioso', 
      color: '#8b5cf6', 
      description: 'Propiedades grandes y costosas',
      priceRange: [maxPrice * 0.6, maxPrice * 0.9],
      surfaceRange: [maxSurface * 0.7, maxSurface]
    },
    { 
      id: 3, 
      name: 'Ultra Lujo', 
      color: '#d4af37', 
      description: 'Propiedades de lujo excepcionales',
      priceRange: [maxPrice * 0.85, maxPrice],
      surfaceRange: [maxSurface * 0.6, maxSurface]
    }
  ];

  // Asignar puntos a clusters
  const clusteredData = data.map(point => {
    let assignedCluster = 0;
    
    for (const cluster of clusterDefinitions) {
      const inPriceRange = point.precio >= cluster.priceRange[0] && point.precio <= cluster.priceRange[1];
      const inSurfaceRange = point.superficie >= cluster.surfaceRange[0] && point.superficie <= cluster.surfaceRange[1];
      
      if (inPriceRange && inSurfaceRange) {
        assignedCluster = cluster.id;
        break;
      }
    }
    
    return { ...point, cluster: assignedCluster };
  });

  // Calcular estadísticas de clusters
  const clusters: ClusterInfo[] = clusterDefinitions.map(def => {
    const clusterPoints = clusteredData.filter(p => p.cluster === def.id);
    
    return {
      ...def,
      count: clusterPoints.length,
      avgPrice: clusterPoints.length > 0 ? clusterPoints.reduce((sum, p) => sum + p.precio, 0) / clusterPoints.length : 0,
      avgSurface: clusterPoints.length > 0 ? clusterPoints.reduce((sum, p) => sum + p.superficie, 0) / clusterPoints.length : 0,
      avgPxm2: clusterPoints.length > 0 ? clusterPoints.reduce((sum, p) => sum + p.pxm2, 0) / clusterPoints.length : 0,
    };
  }).filter(cluster => cluster.count > 0);

  return { data: clusteredData, clusters };
};

// Calcular línea de tendencia
const calculateTrendLine = (data: DataPoint[]) => {
  if (data.length < 2) return null;

  const n = data.length;
  const sumX = data.reduce((sum, d) => sum + d.superficie, 0);
  const sumY = data.reduce((sum, d) => sum + d.precio, 0);
  const sumXY = data.reduce((sum, d) => sum + (d.superficie * d.precio), 0);
  const sumXX = data.reduce((sum, d) => sum + (d.superficie * d.superficie), 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  const minX = Math.min(...data.map(d => d.superficie));
  const maxX = Math.max(...data.map(d => d.superficie));

  return {
    slope,
    intercept,
    start: { x: minX, y: slope * minX + intercept },
    end: { x: maxX, y: slope * maxX + intercept }
  };
};

const ScatterPlotWithClustering: React.FC<ScatterPlotWithClusteringProps> = ({
  data,
  loading = false,
  height = 400,
  showTrendLine = true,
  showClusters = true,
  operacion
}) => {
  const { clusteredData, clusters, trendLine } = useMemo(() => {
    const { data: clustered, clusters: clusterInfo } = performClustering(data);
    const trend = showTrendLine ? calculateTrendLine(data) : null;
    
    return {
      clusteredData: clustered,
      clusters: clusterInfo,
      trendLine: trend
    };
  }, [data, showTrendLine]);

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

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const cluster = clusters.find(c => c.id === data.cluster);
      
      return (
        <div className="bg-white p-4 border border-neutral-200 rounded-lg shadow-lg max-w-xs">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: cluster?.color || '#gray' }}
              />
              <span className="font-semibold text-neutral-900">{data.colonia}</span>
            </div>
            
            <div className="text-sm text-neutral-600">
              <p><span className="font-medium">Municipio:</span> {data.municipio}</p>
              <p><span className="font-medium">Tipo:</span> {data.tipo_propiedad}</p>
            </div>
            
            <div className="text-sm space-y-1">
              <p><span className="font-medium">Precio:</span> {formatPrice(data.precio)}</p>
              <p><span className="font-medium">Superficie:</span> {data.superficie}m²</p>
              <p><span className="font-medium">Precio/m²:</span> {formatPrice(data.pxm2)}/m²</p>
            </div>
            
            {cluster && (
              <div className="pt-2 border-t border-neutral-100">
                <p className="text-xs font-medium" style={{ color: cluster.color }}>
                  {cluster.name}
                </p>
                <p className="text-xs text-neutral-500">{cluster.description}</p>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-200 rounded w-1/2 mb-4"></div>
          <div className="h-80 bg-neutral-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-neutral-900 flex items-center gap-2">
            <Target size={20} className="text-primary-600" />
            Análisis Precio vs Superficie
          </h3>
          <p className="text-sm text-neutral-600 mt-1">
            Clustering automático con {clusters.length} segmentos identificados
          </p>
        </div>
        
        <div className="flex items-center gap-2 text-sm text-neutral-500">
          <Layers size={16} />
          {clusteredData.length.toLocaleString('es-MX')} propiedades
        </div>
      </div>

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            
            <XAxis 
              type="number"
              dataKey="superficie"
              name="Superficie"
              unit="m²"
              tick={{ fontSize: 12 }}
              label={{ 
                value: 'Superficie (m²)', 
                position: 'insideBottom', 
                offset: -10,
                style: { textAnchor: 'middle' }
              }}
            />
            
            <YAxis 
              type="number"
              dataKey="precio"
              name="Precio"
              tick={{ fontSize: 12 }}
              tickFormatter={formatPrice}
              label={{ 
                value: `Precio (${operacion === 'renta' ? 'mensual' : 'venta'})`, 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle' }
              }}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            {showClusters && (
              <Legend 
                verticalAlign="top" 
                height={36}
                iconType="circle"
              />
            )}

            {/* Línea de tendencia */}
            {showTrendLine && trendLine && (
              <ReferenceLine
                segment={[
                  { x: trendLine.start.x, y: trendLine.start.y },
                  { x: trendLine.end.x, y: trendLine.end.y }
                ]}
                stroke="#ef4444"
                strokeWidth={2}
                strokeDasharray="5 5"
              />
            )}

            {/* Scatter por cluster */}
            {showClusters ? (
              clusters.map(cluster => (
                <Scatter
                  key={cluster.id}
                  name={`${cluster.name} (${cluster.count})`}
                  data={clusteredData.filter(d => d.cluster === cluster.id)}
                  fill={cluster.color}
                  fillOpacity={0.7}
                  stroke={cluster.color}
                  strokeWidth={1}
                />
              ))
            ) : (
              <Scatter
                name="Propiedades"
                data={clusteredData}
                fill="#3b82f6"
                fillOpacity={0.6}
              />
            )}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Estadísticas de clusters */}
      {showClusters && clusters.length > 0 && (
        <div className="mt-6 pt-4 border-t border-neutral-100">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {clusters.map(cluster => (
              <div 
                key={cluster.id}
                className="p-3 rounded-lg border"
                style={{ borderColor: cluster.color + '40', backgroundColor: cluster.color + '10' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: cluster.color }}
                  />
                  <h4 className="font-semibold text-sm text-neutral-900">
                    {cluster.name}
                  </h4>
                </div>
                
                <div className="space-y-1 text-xs text-neutral-600">
                  <p><span className="font-medium">Propiedades:</span> {cluster.count}</p>
                  <p><span className="font-medium">Precio prom:</span> {formatPrice(cluster.avgPrice)}</p>
                  <p><span className="font-medium">Superficie prom:</span> {Math.round(cluster.avgSurface)}m²</p>
                  <p><span className="font-medium">Precio/m² prom:</span> {formatPrice(cluster.avgPxm2)}/m²</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights automáticos */}
      <div className="mt-4 p-4 bg-neutral-50 rounded-lg">
        <div className="flex items-start gap-3">
          <TrendingUp size={16} className="text-accent-600 mt-0.5" />
          <div className="text-sm text-neutral-700">
            <p className="font-medium mb-1">💡 Insight del Mercado:</p>
            <p>
              El análisis muestra {clusters.length} segmentos distintos. 
              {clusters.length > 0 && (
                <>
                  {' '}El segmento "{clusters.reduce((max, cluster) => cluster.count > max.count ? cluster : max, clusters[0]).name}" 
                  es el más representativo con {clusters.reduce((max, cluster) => cluster.count > max.count ? cluster : max, clusters[0]).count} propiedades.
                </>
              )}
              {trendLine && trendLine.slope > 0 && (
                <> Existe una correlación positiva entre superficie y precio.</>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScatterPlotWithClustering;
