import { useQuery } from '@tanstack/react-query';
import { useOperationStore } from '@/store/operationStore';

const API_BASE = '/api';

// Types
export interface KPI {
  value: number;
  formatted: string;
}

export interface OverviewData {
  meta: {
    lastUpdate: string;
    totalProperties: number;
    operacion: string;
    executionTimeMs: number;
  };
  data: {
    totalProperties: number;
    activeListings: number;
    newListings30d: number;
    avgPrice: KPI;
    medianPrice: KPI;
    avgPxm2: KPI;
    medianPxm2: KPI;
    avgSurface: KPI;
    topColonies: Array<{
      name: string;
      municipality: string;
      count: number;
      avgPrice: number;
      avgPxm2: number;
      change30d: number;
      trend: string;
    }>;
    byPropertyType: Array<{
      type: string;
      count: number;
      percentage: number;
      avgPrice: number;
      avgPxm2: number;
    }>;
    insights: Array<{
      type: string;
      title: string;
      description: string;
      impact: string;
    }>;
    quickStats: {
      totalMunicipalities: number;
      totalColonies: number;
      avgSurface: number;
      mostCommonBedrooms: number;
      mostCommonBathrooms: number;
    };
  };
}

export interface HistogramData {
  bins: Array<{
    min: number;
    max: number;
    count: number;
    percentage: number;
    label: string;
  }>;
  metadata: {
    variable: string;
    totalCount: number;
    method: string;
  };
}

// Hooks
export function useOverview() {
  const { currentOperation } = useOperationStore();
  
  return useQuery({
    queryKey: ['overview', currentOperation],
    queryFn: async (): Promise<OverviewData> => {
      const response = await fetch(`${API_BASE}/stats/overview?operacion=${currentOperation}`);
      if (!response.ok) {
        throw new Error('Error fetching overview data');
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
    refetchOnWindowFocus: false,
  });
}

export function useHistogram(variable: string = 'precios') {
  const { currentOperation } = useOperationStore();
  
  return useQuery({
    queryKey: ['histogram', variable, currentOperation],
    queryFn: async (): Promise<HistogramData> => {
      const response = await fetch(
        `${API_BASE}/stats/histogram?variable=${variable}&operacion=${currentOperation}`
      );
      if (!response.ok) {
        throw new Error('Error fetching histogram data');
      }
      return response.json();
    },
    staleTime: 10 * 60 * 1000, // 10 minutos
    refetchOnWindowFocus: false,
  });
}

export function useOperations() {
  return useQuery({
    queryKey: ['operations'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/stats/operations`);
      if (!response.ok) {
        throw new Error('Error fetching operations');
      }
      return response.json();
    },
    staleTime: 60 * 60 * 1000, // 1 hora
    refetchOnWindowFocus: false,
  });
}

export function useFilteredStats(filters: any = {}) {
  const { currentOperation } = useOperationStore();
  
  return useQuery({
    queryKey: ['filtered-stats', currentOperation, filters],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/stats/filtered?operacion=${currentOperation}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(filters),
        }
      );
      if (!response.ok) {
        throw new Error('Error fetching filtered stats');
      }
      return response.json();
    },
    enabled: Object.keys(filters).length > 0,
    staleTime: 2 * 60 * 1000, // 2 minutos
    refetchOnWindowFocus: false,
  });
}
