import React, { useState } from 'react';
import { Bed, Bath, DollarSign, Square, TrendingUp, Users } from 'lucide-react';

interface SegmentData {
  segment: string;
  recamaras: number;
  banos: number;
  count: number;
  precio_min: number;
  precio_max: number;
  precio_mean: number;
  precio_median: number;
  superficie_min: number;
  superficie_max: number;
  superficie_mean: number;
  pxm2_min: number;
  pxm2_max: number;
  pxm2_mean: number;
  percentage: number;
}

interface SegmentAnalysisProps {
  data: SegmentData[];
  loading?: boolean;
  operacion: 'venta' | 'renta';
  onSegmentSelect?: (segment: SegmentData) => void;
}

const SegmentAnalysis: React.FC<SegmentAnalysisProps> = ({
  data,
  loading = false,
  operacion,
  onSegmentSelect
}) => {
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);

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

  const getSegmentIcon = (recamaras: number, banos: number) => {
    if (recamaras <= 1 && banos <= 1.5) return '🏠'; // Starter
    if (recamaras <= 2 && banos <= 2.5) return '🏡'; // Familiar
    if (recamaras <= 3 && banos <= 3.5) return '🏘️'; // Premium
    return '🏰'; // Luxury
  };

  const getSegmentColor = (recamaras: number, banos: number) => {
    if (recamaras <= 1 && banos <= 1.5) return 'bg-green-50 border-green-200 text-green-800';
    if (recamaras <= 2 && banos <= 2.5) return 'bg-blue-50 border-blue-200 text-blue-800';
    if (recamaras <= 3 && banos <= 3.5) return 'bg-purple-50 border-purple-200 text-purple-800';
    return 'bg-yellow-50 border-yellow-200 text-yellow-800';
  };

  const handleSegmentClick = (segment: SegmentData) => {
    setSelectedSegment(selectedSegment === segment.segment ? null : segment.segment);
    if (onSegmentSelect) {
      onSegmentSelect(segment);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Users size={20} className="text-blue-600" />
              Segmentación por Recámaras + Baños
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Análisis de rangos de precio y superficie por configuración de propiedad
            </p>
          </div>
          <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {operacion === 'venta' ? 'Venta' : 'Renta'}
          </span>
        </div>
      </div>

      {/* Segmentos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((segment) => (
          <div
            key={segment.segment}
            className={`border-2 rounded-lg p-6 cursor-pointer transition-all hover:shadow-md ${
              selectedSegment === segment.segment
                ? 'border-blue-500 bg-blue-50'
                : getSegmentColor(segment.recamaras, segment.banos)
            }`}
            onClick={() => handleSegmentClick(segment)}
          >
            {/* Header del segmento */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">
                  {getSegmentIcon(segment.recamaras, segment.banos)}
                </span>
                <div>
                  <h4 className="font-semibold text-gray-900">
                    {segment.recamaras} Rec + {segment.banos} Baños
                  </h4>
                  <p className="text-xs text-gray-600">
                    {segment.count.toLocaleString('es-MX')} propiedades
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900">
                  {segment.percentage.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">del mercado</div>
              </div>
            </div>

            {/* Métricas principales */}
            <div className="space-y-3">
              {/* Precio */}
              <div className="flex items-center gap-2">
                <DollarSign size={16} className="text-green-600" />
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Precio</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatPrice(segment.precio_median)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatPrice(segment.precio_min)} - {formatPrice(segment.precio_max)}
                  </div>
                </div>
              </div>

              {/* Superficie */}
              <div className="flex items-center gap-2">
                <Square size={16} className="text-blue-600" />
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Superficie</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {Math.round(segment.superficie_mean)}m²
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round(segment.superficie_min)}m² - {Math.round(segment.superficie_max)}m²
                  </div>
                </div>
              </div>

              {/* Precio por m² */}
              <div className="flex items-center gap-2">
                <TrendingUp size={16} className="text-purple-600" />
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Precio/m²</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatPrice(segment.pxm2_mean)}/m²
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatPrice(segment.pxm2_min)}/m² - {formatPrice(segment.pxm2_max)}/m²
                  </div>
                </div>
              </div>
            </div>

            {/* Indicador de selección */}
            {selectedSegment === segment.segment && (
              <div className="mt-4 pt-3 border-t border-blue-200">
                <div className="text-xs text-blue-600 font-medium">
                  ✓ Segmento seleccionado para análisis detallado
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Análisis detallado del segmento seleccionado */}
      {selectedSegment && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">
            Análisis Detallado: {selectedSegment}
          </h4>
          
          {(() => {
            const segment = data.find(s => s.segment === selectedSegment);
            if (!segment) return null;

            return (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Distribución de precios */}
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                  <h5 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                    <DollarSign size={16} />
                    Distribución de Precios
                  </h5>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-green-700">Mínimo:</span>
                      <span className="text-sm font-semibold text-green-900">
                        {formatPrice(segment.precio_min)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-green-700">Promedio:</span>
                      <span className="text-sm font-semibold text-green-900">
                        {formatPrice(segment.precio_mean)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-green-700">Mediana:</span>
                      <span className="text-sm font-semibold text-green-900">
                        {formatPrice(segment.precio_median)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-green-700">Máximo:</span>
                      <span className="text-sm font-semibold text-green-900">
                        {formatPrice(segment.precio_max)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Distribución de superficie */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                  <h5 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                    <Square size={16} />
                    Distribución de Superficie
                  </h5>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-700">Mínima:</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {Math.round(segment.superficie_min)}m²
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-700">Promedio:</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {Math.round(segment.superficie_mean)}m²
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-700">Máxima:</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {Math.round(segment.superficie_max)}m²
                      </span>
                    </div>
                    <div className="text-xs text-blue-600 mt-2">
                      Rango: {Math.round(segment.superficie_max - segment.superficie_min)}m²
                    </div>
                  </div>
                </div>

                {/* Análisis de valor */}
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                  <h5 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
                    <TrendingUp size={16} />
                    Análisis de Valor
                  </h5>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-purple-700">Precio/m² Min:</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {formatPrice(segment.pxm2_min)}/m²
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-purple-700">Precio/m² Prom:</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {formatPrice(segment.pxm2_mean)}/m²
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-purple-700">Precio/m² Max:</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {formatPrice(segment.pxm2_max)}/m²
                      </span>
                    </div>
                    <div className="text-xs text-purple-600 mt-2">
                      {segment.count.toLocaleString('es-MX')} propiedades analizadas
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default SegmentAnalysis;
