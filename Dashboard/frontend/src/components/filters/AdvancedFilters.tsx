import React, { useState } from 'react';
import { Filter, MapPin, Home, Bed, Bath, DollarSign, Square, ChevronDown, X } from 'lucide-react';

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

interface AdvancedFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onApplyFilters: () => void;
  onClearFilters: () => void;
  loading?: boolean;
}

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onApplyFilters,
  onClearFilters,
  loading = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Opciones predefinidas
  const municipiosOptions = ['Guadalajara', 'Zapopan'];
  const tiposOptions = ['Casa', 'Departamento', 'Casa en Condominio', 'Terreno / Lote', 'Oficina', 'Local Comercial'];
  const recamarasOptions = [1, 2, 3, 4, 5, 6];
  const banosOptions = [1, 1.5, 2, 2.5, 3, 3.5, 4];

  const handleMultiSelect = (field: keyof FilterState, value: any) => {
    const currentValues = filters[field] as any[];
    const newValues = currentValues.includes(value)
      ? currentValues.filter(v => v !== value)
      : [...currentValues, value];
    
    onFiltersChange({
      ...filters,
      [field]: newValues
    });
  };

  const handleRangeChange = (field: keyof FilterState, value: number) => {
    onFiltersChange({
      ...filters,
      [field]: value
    });
  };

  const formatPrice = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value}`;
  };

  const hasActiveFilters = () => {
    return filters.colonias.length > 0 ||
           filters.municipios.length > 0 ||
           filters.tiposPropiedad.length > 0 ||
           filters.recamaras.length > 0 ||
           filters.banos.length > 0 ||
           filters.precioMin > 0 ||
           filters.precioMax < 50000000 ||
           filters.superficieMin > 0 ||
           filters.superficieMax < 1000 ||
           filters.pxm2Min > 0 ||
           filters.pxm2Max < 200000;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header del filtro */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-blue-600" />
            <h3 className="font-semibold text-gray-900">Filtros de Mercado</h3>
            {hasActiveFilters() && (
              <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                Activos
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClearFilters}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              disabled={loading}
            >
              <X size={16} />
              Limpiar
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <ChevronDown 
                size={20} 
                className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Filtros expandidos */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* Ubicación */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <MapPin size={16} />
                Municipio
              </label>
              <div className="space-y-2">
                {municipiosOptions.map(municipio => (
                  <label key={municipio} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.municipios.includes(municipio)}
                      onChange={() => handleMultiSelect('municipios', municipio)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{municipio}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <Home size={16} />
                Tipo de Propiedad
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {tiposOptions.map(tipo => (
                  <label key={tipo} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.tiposPropiedad.includes(tipo)}
                      onChange={() => handleMultiSelect('tiposPropiedad', tipo)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{tipo}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Características */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <Bed size={16} />
                Recámaras
              </label>
              <div className="flex flex-wrap gap-2">
                {recamarasOptions.map(rec => (
                  <button
                    key={rec}
                    onClick={() => handleMultiSelect('recamaras', rec)}
                    className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                      filters.recamaras.includes(rec)
                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {rec}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <Bath size={16} />
                Baños
              </label>
              <div className="flex flex-wrap gap-2">
                {banosOptions.map(bano => (
                  <button
                    key={bano}
                    onClick={() => handleMultiSelect('banos', bano)}
                    className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                      filters.banos.includes(bano)
                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {bano}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Rangos de precio */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <DollarSign size={16} />
                Rango de Precio
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="range"
                    min="0"
                    max="50000000"
                    step="100000"
                    value={filters.precioMin}
                    onChange={(e) => handleRangeChange('precioMin', Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600 mt-1">
                    Mín: {formatPrice(filters.precioMin)}
                  </div>
                </div>
                <div>
                  <input
                    type="range"
                    min="0"
                    max="50000000"
                    step="100000"
                    value={filters.precioMax}
                    onChange={(e) => handleRangeChange('precioMax', Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600 mt-1">
                    Máx: {formatPrice(filters.precioMax)}
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <Square size={16} />
                Superficie (m²)
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="range"
                    min="0"
                    max="1000"
                    step="10"
                    value={filters.superficieMin}
                    onChange={(e) => handleRangeChange('superficieMin', Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600 mt-1">
                    Mín: {filters.superficieMin}m²
                  </div>
                </div>
                <div>
                  <input
                    type="range"
                    min="0"
                    max="1000"
                    step="10"
                    value={filters.superficieMax}
                    onChange={(e) => handleRangeChange('superficieMax', Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600 mt-1">
                    Máx: {filters.superficieMax}m²
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Precio por m²
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="range"
                    min="0"
                    max="200000"
                    step="1000"
                    value={filters.pxm2Min}
                    onChange={(e) => handleRangeChange('pxm2Min', Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600 mt-1">
                    Mín: {formatPrice(filters.pxm2Min)}/m²
                  </div>
                </div>
                <div>
                  <input
                    type="range"
                    min="0"
                    max="200000"
                    step="1000"
                    value={filters.pxm2Max}
                    onChange={(e) => handleRangeChange('pxm2Max', Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600 mt-1">
                    Máx: {formatPrice(filters.pxm2Max)}/m²
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Botón aplicar */}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onApplyFilters}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Aplicando...
                </>
              ) : (
                <>
                  <Filter size={16} />
                  Aplicar Filtros
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedFilters;
