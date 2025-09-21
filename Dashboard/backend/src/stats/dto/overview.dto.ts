import { ApiProperty } from '@nestjs/swagger';

export interface KPIMetric {
  value: number;
  change30d?: number;
  change90d?: number;
  trend?: 'up' | 'down' | 'stable';
  formatted: string;
}

export interface TopColony {
  name: string;
  municipality: string;
  count: number;
  avgPrice: number;
  avgPxm2: number;
  change30d: number;
  trend: 'up' | 'down' | 'stable';
}

export interface MarketInsight {
  type: 'trend' | 'opportunity' | 'alert' | 'milestone';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  actionItems?: string[];
  relatedData?: any;
}

export interface PropertyTypeDistribution {
  type: string;
  count: number;
  percentage: number;
  avgPrice: number;
  avgPxm2: number;
}

export interface PriceDistribution {
  range: string;
  count: number;
  percentage: number;
  minPrice: number;
  maxPrice: number;
}

export interface MonthlyTrend {
  month: string;
  avgPrice: number;
  medianPxm2: number;
  count: number;
  changeFromPrevious?: number;
}

export class OverviewResponseDto {
  @ApiProperty({
    description: 'Metadatos de la respuesta'
  })
  meta: {
    lastUpdate: string;
    dataVersion: string;
    cached: boolean;
    cacheExpires?: string;
    totalProperties: number;
  };

  @ApiProperty({
    description: 'Datos principales del overview'
  })
  data: {
    // KPIs principales
    totalProperties: number;
    activeListings: number;
    newListings30d: number;

    // Métricas de precio
    avgPrice: KPIMetric;
    medianPrice: KPIMetric;
    avgPxm2: KPIMetric;
    medianPxm2: KPIMetric;

    // Distribuciones
    byPropertyType: PropertyTypeDistribution[];
    priceDistribution: PriceDistribution[];

    // Top performers
    topColonies: TopColony[];

    // Insights automáticos
    insights: MarketInsight[];

    // Tendencias (si hay datos históricos)
    monthlyTrend?: MonthlyTrend[];

    // Datos para gráficas rápidas
    quickStats: {
      totalMunicipalities: number;
      totalColonies: number;
      avgSurface: number;
      mostCommonBedrooms: number;
      mostCommonBathrooms: number;
    };
  };
}
