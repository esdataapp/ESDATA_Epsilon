import React from 'react';
import { X, Filter, MapPin, Home, Bed, Bath, DollarSign, Square } from 'lucide-react';

interface FilterChip {
  id: string;
  label: string;
  value: string | number | string[];
  type: 'municipio' | 'tipo' | 'recamaras' | 'banos' | 'precio' | 'superficie' | 'pxm2' | 'colonia';
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}

interface ActiveFiltersChipsProps {
  filters: FilterChip[];
  onRemoveFilter: (filterId: string) => void;
  onClearAll: () => void;
  className?: string;
}

const ActiveFiltersChips: React.FC<ActiveFiltersChipsProps> = ({
  filters,
  onRemoveFilter,
  onClearAll,
  className = ''
}) => {
  const getFilterIcon = (type: FilterChip['type']) => {
    switch (type) {
      case 'municipio':
      case 'colonia':
        return <MapPin size={14} />;
      case 'tipo':
        return <Home size={14} />;
      case 'recamaras':
        return <Bed size={14} />;
      case 'banos':
        return <Bath size={14} />;
      case 'precio':
        return <DollarSign size={14} />;
      case 'superficie':
      case 'pxm2':
        return <Square size={14} />;
      default:
        return <Filter size={14} />;
    }
  };

  const getFilterColor = (type: FilterChip['type'], color?: FilterChip['color']) => {
    if (color) {
      const colorMap = {
        blue: 'bg-blue-100 text-blue-800 border-blue-200',
        green: 'bg-accent-100 text-accent-800 border-accent-200',
        purple: 'bg-purple-100 text-purple-800 border-purple-200',
        orange: 'bg-warning-100 text-warning-800 border-warning-200',
        red: 'bg-danger-100 text-danger-800 border-danger-200',
      };
      return colorMap[color];
    }

    // Colores por tipo de filtro
    switch (type) {
      case 'municipio':
      case 'colonia':
        return 'bg-primary-100 text-primary-800 border-primary-200';
      case 'tipo':
        return 'bg-accent-100 text-accent-800 border-accent-200';
      case 'recamaras':
      case 'banos':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'precio':
        return 'bg-warning-100 text-warning-800 border-warning-200';
      case 'superficie':
      case 'pxm2':
        return 'bg-neutral-100 text-neutral-800 border-neutral-200';
      default:
        return 'bg-neutral-100 text-neutral-800 border-neutral-200';
    }
  };

  const formatFilterValue = (filter: FilterChip) => {
    const { value, type } = filter;

    if (Array.isArray(value)) {
      return value.length > 2 
        ? `${value.slice(0, 2).join(', ')} +${value.length - 2}`
        : value.join(', ');
    }

    if (type === 'precio' && typeof value === 'number') {
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      return `$${(value / 1000).toFixed(0)}K`;
    }

    if (type === 'superficie' && typeof value === 'number') {
      return `${value}m²`;
    }

    if (type === 'pxm2' && typeof value === 'number') {
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(0)}K/m²`;
      }
      return `$${value}/m²`;
    }

    return String(value);
  };

  if (filters.length === 0) {
    return null;
  }

  return (
    <div className={`bg-white rounded-lg border p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-neutral-500" />
          <span className="text-sm font-medium text-neutral-700">
            Filtros Activos ({filters.length})
          </span>
        </div>
        
        {filters.length > 0 && (
          <button
            onClick={onClearAll}
            className="text-xs text-neutral-500 hover:text-neutral-700 transition-colors"
          >
            Limpiar todo
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {filters.map((filter) => (
          <div
            key={filter.id}
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border transition-all duration-200 hover:shadow-sm ${getFilterColor(filter.type, filter.color)}`}
          >
            {getFilterIcon(filter.type)}
            
            <span className="flex items-center gap-1">
              <span className="font-medium">{filter.label}:</span>
              <span>{formatFilterValue(filter)}</span>
            </span>
            
            <button
              onClick={() => onRemoveFilter(filter.id)}
              className="ml-1 p-0.5 rounded-full hover:bg-black hover:bg-opacity-10 transition-colors"
              aria-label={`Remover filtro ${filter.label}`}
            >
              <X size={12} />
            </button>
          </div>
        ))}
      </div>

      {/* Indicador de resultados */}
      <div className="mt-3 pt-3 border-t border-neutral-100">
        <div className="flex items-center justify-between text-xs text-neutral-500">
          <span>
            Filtros aplicados a la consulta actual
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 bg-accent-400 rounded-full animate-pulse-soft"></div>
            Actualizando resultados...
          </span>
        </div>
      </div>
    </div>
  );
};

// Hook para manejar filtros activos
export const useActiveFilters = () => {
  const [activeFilters, setActiveFilters] = React.useState<FilterChip[]>([]);

  const addFilter = (filter: Omit<FilterChip, 'id'>) => {
    const newFilter: FilterChip = {
      ...filter,
      id: `${filter.type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };
    
    setActiveFilters(prev => {
      // Remover filtros del mismo tipo si existe
      const filtered = prev.filter(f => f.type !== filter.type);
      return [...filtered, newFilter];
    });
  };

  const removeFilter = (filterId: string) => {
    setActiveFilters(prev => prev.filter(f => f.id !== filterId));
  };

  const clearAllFilters = () => {
    setActiveFilters([]);
  };

  const updateFilter = (filterId: string, updates: Partial<FilterChip>) => {
    setActiveFilters(prev => 
      prev.map(f => f.id === filterId ? { ...f, ...updates } : f)
    );
  };

  const getFiltersByType = (type: FilterChip['type']) => {
    return activeFilters.filter(f => f.type === type);
  };

  const hasActiveFilters = activeFilters.length > 0;

  return {
    activeFilters,
    addFilter,
    removeFilter,
    clearAllFilters,
    updateFilter,
    getFiltersByType,
    hasActiveFilters
  };
};

// Componente de ejemplo de uso
export const FilterChipsExample: React.FC = () => {
  const {
    activeFilters,
    addFilter,
    removeFilter,
    clearAllFilters
  } = useActiveFilters();

  // Ejemplos de filtros
  const handleAddExampleFilters = () => {
    addFilter({
      label: 'Municipio',
      value: ['Zapopan', 'Guadalajara'],
      type: 'municipio'
    });
    
    addFilter({
      label: 'Tipo',
      value: 'Departamento',
      type: 'tipo'
    });
    
    addFilter({
      label: 'Precio',
      value: 5000000,
      type: 'precio'
    });
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleAddExampleFilters}
        className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
      >
        Agregar Filtros de Ejemplo
      </button>
      
      <ActiveFiltersChips
        filters={activeFilters}
        onRemoveFilter={removeFilter}
        onClearAll={clearAllFilters}
      />
    </div>
  );
};

export default ActiveFiltersChips;
