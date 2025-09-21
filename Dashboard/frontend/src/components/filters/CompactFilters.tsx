import React, { useState } from 'react';
import { useOperationStore } from '@/store/operationStore';
import { MapPin, Home, Bed, Bath, DollarSign, Square } from 'lucide-react';

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

interface CompactFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  loading?: boolean;
}

const CompactFilters: React.FC<CompactFiltersProps> = ({
  filters,
  onFiltersChange,
  loading = false
}) => {
  const { currentOperation, setOperation } = useOperationStore();

  const handleOperationChange = (operation: 'venta' | 'renta') => {
    setOperation(operation);
    // Los filtros se aplican automáticamente al cambiar operación
  };

  const handleRangeChange = (field: string, minValue: number, maxValue: number) => {
    const newFilters = {
      ...filters,
      [`${field}Min`]: minValue,
      [`${field}Max`]: maxValue
    };
    onFiltersChange(newFilters);
    // Los filtros se aplican automáticamente al cambiar
  };

  const formatPrice = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    return `$${(value / 1000).toFixed(0)}K`;
  };

  const RangeSlider: React.FC<{
    label: string;
    icon: React.ReactNode;
    min: number;
    max: number;
    step: number;
    currentMin: number;
    currentMax: number;
    onChange: (min: number, max: number) => void;
    formatter?: (value: number) => string;
  }> = ({ label, icon, min, max, step, currentMin, currentMax, onChange, formatter }) => {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium text-neutral-700">{label}</span>
        </div>
        <div className="relative">
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={currentMin}
            onChange={(e) => onChange(Number(e.target.value), currentMax)}
            className="absolute w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer range-slider"
          />
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={currentMax}
            onChange={(e) => onChange(currentMin, Number(e.target.value))}
            className="absolute w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer range-slider"
          />
          <div className="flex justify-between text-xs text-neutral-500 mt-2">
            <span>{formatter ? formatter(currentMin) : currentMin}</span>
            <span>{formatter ? formatter(currentMax) : currentMax}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <div className="grid grid-cols-1 lg:grid-cols-6 gap-4">
        {/* Selector de Operación */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 flex items-center gap-2">
            <Home size={16} />
            Operación
          </label>
          <div className="flex bg-neutral-100 rounded-lg p-1">
            <button
              onClick={() => handleOperationChange('venta')}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all ${
                currentOperation === 'venta'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              Venta
            </button>
            <button
              onClick={() => handleOperationChange('renta')}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all ${
                currentOperation === 'renta'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              Renta
            </button>
          </div>
        </div>

        {/* Municipio */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 flex items-center gap-2">
            <MapPin size={16} />
            Municipio
          </label>
          <div className="space-y-1">
            {['Guadalajara', 'Zapopan'].map((municipio) => (
              <label key={municipio} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.municipios.includes(municipio)}
                  onChange={(e) => {
                    const newMunicipios = e.target.checked
                      ? [...filters.municipios, municipio]
                      : filters.municipios.filter(m => m !== municipio);
                    const newFilters = { ...filters, municipios: newMunicipios };
                    onFiltersChange(newFilters);
                    // Aplicar filtros automáticamente
                  }}
                  className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-neutral-700">{municipio}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Tipo de Propiedad */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 flex items-center gap-2">
            <Home size={16} />
            Tipo
          </label>
          <select
            multiple
            value={filters.tiposPropiedad}
            onChange={(e) => {
              const values = Array.from(e.target.selectedOptions, option => option.value);
              const newFilters = { ...filters, tiposPropiedad: values };
              onFiltersChange(newFilters);
              // Aplicar filtros automáticamente
            }}
            className="w-full text-sm border border-neutral-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="Casa">Casa</option>
            <option value="Departamento">Departamento</option>
            <option value="Casa en Condominio">Casa en Condominio</option>
            <option value="Terreno / Lote">Terreno / Lote</option>
            <option value="Oficina">Oficina</option>
          </select>
        </div>

        {/* Recámaras */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 flex items-center gap-2">
            <Bed size={16} />
            Recámaras
          </label>
          <div className="flex flex-wrap gap-1">
            {[1, 2, 3, 4, 5, 6].map((num) => (
              <button
                key={num}
                onClick={() => {
                  const newRecamaras = filters.recamaras.includes(num)
                    ? filters.recamaras.filter(r => r !== num)
                    : [...filters.recamaras, num];
                  const newFilters = { ...filters, recamaras: newRecamaras };
                  onFiltersChange(newFilters);
                  // Aplicar filtros automáticamente
                }}
                className={`px-2 py-1 text-xs rounded transition-all ${
                  filters.recamaras.includes(num)
                    ? 'bg-primary-600 text-white'
                    : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Baños */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 flex items-center gap-2">
            <Bath size={16} />
            Baños
          </label>
          <div className="flex flex-wrap gap-1">
            {[1, 1.5, 2, 2.5, 3, 3.5, 4].map((num) => (
              <button
                key={num}
                onClick={() => {
                  const newBanos = filters.banos.includes(num)
                    ? filters.banos.filter(b => b !== num)
                    : [...filters.banos, num];
                  const newFilters = { ...filters, banos: newBanos };
                  onFiltersChange(newFilters);
                  // Aplicar filtros automáticamente
                }}
                className={`px-2 py-1 text-xs rounded transition-all ${
                  filters.banos.includes(num)
                    ? 'bg-primary-600 text-white'
                    : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Estado de carga */}
        <div className="flex items-end">
          <div className="w-full text-center">
            {loading ? (
              <div className="flex items-center justify-center gap-2 text-sm text-neutral-500">
                <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
                Actualizando...
              </div>
            ) : (
              <div className="text-xs text-neutral-400">
                Filtros aplicados automáticamente
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rangos de Precio, Superficie y Precio/m² */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6 pt-4 border-t border-neutral-200">
        <RangeSlider
          label="Rango de Precio"
          icon={<DollarSign size={16} className="text-warning-600" />}
          min={0}
          max={50000000}
          step={100000}
          currentMin={filters.precioMin}
          currentMax={filters.precioMax}
          onChange={(min, max) => handleRangeChange('precio', min, max)}
          formatter={formatPrice}
        />

        <RangeSlider
          label="Superficie (m²)"
          icon={<Square size={16} className="text-accent-600" />}
          min={0}
          max={1000}
          step={10}
          currentMin={filters.superficieMin}
          currentMax={filters.superficieMax}
          onChange={(min, max) => handleRangeChange('superficie', min, max)}
          formatter={(value) => `${value}m²`}
        />

        <RangeSlider
          label="Precio por m²"
          icon={<DollarSign size={16} className="text-primary-600" />}
          min={0}
          max={200000}
          step={1000}
          currentMin={filters.pxm2Min}
          currentMax={filters.pxm2Max}
          onChange={(min, max) => handleRangeChange('pxm2', min, max)}
          formatter={(value) => `$${(value / 1000).toFixed(0)}K/m²`}
        />
      </div>
    </div>
  );
};

export default CompactFilters;
