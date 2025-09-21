import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { FilterDto, FilteredStatsDto } from './dto/filter.dto';
import { HistogramRequestDto, HistogramResponseDto, HistogramBin } from './dto/histogram.dto';
import { OverviewResponseDto, KPIMetric, TopColony, MarketInsight } from './dto/overview.dto';

@Injectable()
export class StatsService {
  private readonly logger = new Logger(StatsService.name);

  constructor(private prisma: PrismaService) {}

  async getOverview(): Promise<OverviewResponseDto> {
    const startTime = Date.now();
    
    try {
      // Obtener estadísticas básicas
      const totalProperties = await this.prisma.listingProcessed.count({
        where: { isOutlier: false }
      });

      const newListings30d = await this.prisma.listingProcessed.count({
        where: {
          isOutlier: false,
          createdAt: {
            gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
          }
        }
      });

      // Métricas de precio agregadas
      const priceStats = await this.prisma.listingProcessed.aggregate({
        where: { isOutlier: false },
        _avg: { price: true, pricePerSqm: true },
        _count: { id: true }
      });

      // Top colonias por precio por m²
      const topColonies = await this.getTopColonies();

      // Distribución por tipo de propiedad
      const propertyTypeDistribution = await this.getPropertyTypeDistribution();

      // Insights automáticos
      const insights = await this.generateInsights();

      // Estadísticas rápidas
      const quickStats = await this.getQuickStats();

      const executionTime = Date.now() - startTime;
      this.logger.log(`Overview generated in ${executionTime}ms`);

      return {
        meta: {
          lastUpdate: new Date().toISOString(),
          dataVersion: 'v1.0',
          cached: true,
          totalProperties
        },
        data: {
          totalProperties,
          activeListings: totalProperties,
          newListings30d,
          
          avgPrice: {
            value: this.prisma.toNumber(priceStats._avg.price),
            formatted: this.formatCurrency(this.prisma.toNumber(priceStats._avg.price))
          },
          
          medianPrice: {
            value: 0, // TODO: Calcular mediana
            formatted: '$0'
          },
          
          avgPxm2: {
            value: this.prisma.toNumber(priceStats._avg.pricePerSqm),
            formatted: this.formatCurrency(this.prisma.toNumber(priceStats._avg.pricePerSqm))
          },
          
          medianPxm2: {
            value: 0, // TODO: Calcular mediana
            formatted: '$0'
          },

          byPropertyType: propertyTypeDistribution,
          priceDistribution: [], // TODO: Implementar
          topColonies,
          insights,
          quickStats
        }
      };
    } catch (error) {
      this.logger.error('Error generating overview', error);
      throw error;
    }
  }

  async getFilteredStats(filters: FilteredStatsDto) {
    const startTime = Date.now();
    
    try {
      const whereClause = this.prisma.buildWhereClause(filters);
      
      // Conteo total
      const totalCount = await this.prisma.listingProcessed.count({
        where: whereClause
      });

      // Estadísticas agregadas
      const aggregates = await this.prisma.listingProcessed.aggregate({
        where: whereClause,
        _avg: { price: true, surfaceBuiltM2: true, pricePerSqm: true },
        _min: { price: true, surfaceBuiltM2: true, pricePerSqm: true },
        _max: { price: true, surfaceBuiltM2: true, pricePerSqm: true }
      });

      // Distribución por colonia
      const byColony = await this.prisma.listingProcessed.groupBy({
        by: ['colony', 'municipality'],
        where: whereClause,
        _count: { id: true },
        _avg: { price: true, pricePerSqm: true },
        orderBy: { _count: { id: 'desc' } },
        take: 20
      });

      // Propiedades individuales si se solicitan
      let listings = [];
      if (filters.includeListings) {
        listings = await this.prisma.listingProcessed.findMany({
          where: whereClause,
          select: {
            id: true,
            propertyType: true,
            operation: true,
            city: true,
            municipality: true,
            colony: true,
            price: true,
            surfaceBuiltM2: true,
            pricePerSqm: true,
            bedrooms: true,
            bathrooms: true,
            createdAt: true
          },
          orderBy: { createdAt: 'desc' },
          take: filters.maxListings || 50
        });
      }

      const executionTime = Date.now() - startTime;
      this.logger.log(`Filtered stats generated in ${executionTime}ms for ${totalCount} properties`);

      return {
        meta: {
          totalMatches: totalCount,
          executionTimeMs: executionTime,
          filtersApplied: filters,
          cached: false
        },
        stats: {
          count: totalCount,
          price: {
            mean: this.prisma.toNumber(aggregates._avg.price),
            min: this.prisma.toNumber(aggregates._min.price),
            max: this.prisma.toNumber(aggregates._max.price)
          },
          surface: {
            mean: this.prisma.toNumber(aggregates._avg.surfaceBuiltM2),
            min: this.prisma.toNumber(aggregates._min.surfaceBuiltM2),
            max: this.prisma.toNumber(aggregates._max.surfaceBuiltM2)
          },
          pxm2: {
            mean: this.prisma.toNumber(aggregates._avg.pricePerSqm),
            min: this.prisma.toNumber(aggregates._min.pricePerSqm),
            max: this.prisma.toNumber(aggregates._max.pricePerSqm)
          },
          byColony: byColony.map(item => ({
            colony: item.colony,
            municipality: item.municipality,
            count: item._count.id,
            avgPrice: this.prisma.toNumber(item._avg.price),
            avgPxm2: this.prisma.toNumber(item._avg.pricePerSqm)
          }))
        },
        listings: filters.includeListings ? listings : undefined
      };
    } catch (error) {
      this.logger.error('Error generating filtered stats', error);
      throw error;
    }
  }

  async getHistogram(request: HistogramRequestDto): Promise<HistogramResponseDto> {
    // Intentar obtener bins pre-calculados
    const cachedBins = await this.prisma.histogramBins.findUnique({
      where: {
        variable_geoLevel_geoId_propertyType_operation: {
          variable: request.variable,
          geoLevel: request.geoLevel,
          geoId: request.geoId || 'all',
          propertyType: request.propertyType?.[0] || null,
          operation: request.operation?.[0] || null
        }
      }
    });

    if (cachedBins) {
      const bins = this.processCachedBins(cachedBins);
      return {
        bins,
        meta: {
          variable: request.variable,
          totalCount: cachedBins.totalCount,
          method: cachedBins.method,
          calculatedAt: cachedBins.calculatedAt.toISOString(),
          geoLevel: request.geoLevel,
          geoId: request.geoId,
          filters: request
        }
      };
    }

    // Si no hay cache, calcular en tiempo real (fallback)
    return this.calculateHistogramRealTime(request);
  }

  async searchColonies(query: string, limit: number = 10) {
    const colonies = await this.prisma.listingProcessed.findMany({
      where: {
        colony: {
          contains: query,
          mode: 'insensitive'
        },
        isOutlier: false
      },
      select: {
        colony: true,
        municipality: true,
        city: true
      },
      distinct: ['colony', 'municipality'],
      take: limit
    });

    // Agregar conteos
    const coloniesWithCounts = await Promise.all(
      colonies.map(async (colony) => {
        const count = await this.prisma.listingProcessed.count({
          where: {
            colony: colony.colony,
            municipality: colony.municipality,
            isOutlier: false
          }
        });

        return {
          ...colony,
          count,
          label: `${colony.colony}, ${colony.municipality}`,
          value: `${colony.colony}|${colony.municipality}`
        };
      })
    );

    return coloniesWithCounts.sort((a, b) => b.count - a.count);
  }

  async getPropertyTypes() {
    const types = await this.prisma.listingProcessed.groupBy({
      by: ['propertyType'],
      where: { isOutlier: false },
      _count: { id: true },
      orderBy: { _count: { id: 'desc' } }
    });

    return types.map(type => ({
      type: type.propertyType,
      count: type._count.id,
      label: type.propertyType
    }));
  }

  async getOperations() {
    const operations = await this.prisma.listingProcessed.groupBy({
      by: ['operation'],
      where: { isOutlier: false },
      _count: { id: true },
      orderBy: { _count: { id: 'desc' } }
    });

    return operations.map(op => ({
      operation: op.operation,
      count: op._count.id,
      label: op.operation
    }));
  }

  async getMunicipalities() {
    const municipalities = await this.prisma.listingProcessed.groupBy({
      by: ['municipality', 'city'],
      where: { isOutlier: false },
      _count: { id: true },
      _avg: { price: true, pricePerSqm: true },
      orderBy: { _count: { id: 'desc' } }
    });

    return municipalities.map(muni => ({
      municipality: muni.municipality,
      city: muni.city,
      count: muni._count.id,
      avgPrice: this.prisma.toNumber(muni._avg.price),
      avgPxm2: this.prisma.toNumber(muni._avg.pricePerSqm),
      label: muni.municipality
    }));
  }

  async getPriceRanges(filters: FilterDto) {
    const whereClause = this.prisma.buildWhereClause(filters);
    
    // Usar percentiles para rangos sugeridos
    const prices = await this.prisma.listingProcessed.findMany({
      where: whereClause,
      select: { price: true },
      orderBy: { price: 'asc' }
    });

    const priceValues = prices.map(p => this.prisma.toNumber(p.price));
    
    return {
      min: Math.min(...priceValues),
      max: Math.max(...priceValues),
      p25: this.percentile(priceValues, 0.25),
      p50: this.percentile(priceValues, 0.50),
      p75: this.percentile(priceValues, 0.75),
      p90: this.percentile(priceValues, 0.90),
      suggested: [
        [priceValues[0], this.percentile(priceValues, 0.25)],
        [this.percentile(priceValues, 0.25), this.percentile(priceValues, 0.75)],
        [this.percentile(priceValues, 0.75), priceValues[priceValues.length - 1]]
      ]
    };
  }

  async getSurfaceRanges(filters: FilterDto) {
    const whereClause = this.prisma.buildWhereClause(filters);
    
    const surfaces = await this.prisma.listingProcessed.findMany({
      where: {
        ...whereClause,
        surfaceBuiltM2: { not: null }
      },
      select: { surfaceBuiltM2: true },
      orderBy: { surfaceBuiltM2: 'asc' }
    });

    const surfaceValues = surfaces.map(s => this.prisma.toNumber(s.surfaceBuiltM2));
    
    return {
      min: Math.min(...surfaceValues),
      max: Math.max(...surfaceValues),
      p25: this.percentile(surfaceValues, 0.25),
      p50: this.percentile(surfaceValues, 0.50),
      p75: this.percentile(surfaceValues, 0.75),
      p90: this.percentile(surfaceValues, 0.90),
      suggested: [
        [surfaceValues[0], this.percentile(surfaceValues, 0.25)],
        [this.percentile(surfaceValues, 0.25), this.percentile(surfaceValues, 0.75)],
        [this.percentile(surfaceValues, 0.75), surfaceValues[surfaceValues.length - 1]]
      ]
    };
  }

  async compareSegments(segments: { name: string; filters: FilterDto }[]) {
    const results = await Promise.all(
      segments.map(async (segment) => {
        const stats = await this.getFilteredStats({
          ...segment.filters,
          includeListings: false
        });
        
        return {
          name: segment.name,
          filters: segment.filters,
          stats: stats.stats
        };
      })
    );

    return {
      segments: results,
      comparison: this.generateSegmentComparison(results)
    };
  }

  async getMarketHealth() {
    // Métricas de salud del mercado
    const totalProperties = await this.prisma.listingProcessed.count({
      where: { isOutlier: false }
    });

    const outlierRate = await this.prisma.listingProcessed.count({
      where: { isOutlier: true }
    }) / totalProperties;

    const dataQuality = await this.prisma.listingProcessed.aggregate({
      where: { isOutlier: false },
      _avg: { dataQualityScore: true }
    });

    const coloniesWithData = await this.prisma.listingProcessed.groupBy({
      by: ['colony'],
      where: { isOutlier: false, colony: { not: null } },
      _count: { id: true }
    });

    return {
      totalProperties,
      outlierRate: Math.round(outlierRate * 1000) / 10, // Porcentaje con 1 decimal
      avgDataQuality: this.prisma.toNumber(dataQuality._avg.dataQualityScore),
      coloniesCovered: coloniesWithData.length,
      avgPropertiesPerColony: Math.round(totalProperties / coloniesWithData.length),
      healthScore: this.calculateHealthScore(totalProperties, outlierRate, coloniesWithData.length)
    };
  }

  // Métodos auxiliares privados
  private async getTopColonies(): Promise<TopColony[]> {
    const topColonies = await this.prisma.listingProcessed.groupBy({
      by: ['colony', 'municipality'],
      where: { 
        isOutlier: false,
        colony: { not: null },
        pricePerSqm: { not: null }
      },
      _count: { id: true },
      _avg: { price: true, pricePerSqm: true },
      orderBy: { _avg: { pricePerSqm: 'desc' } },
      take: 10
    });

    return topColonies.map(colony => ({
      name: colony.colony,
      municipality: colony.municipality,
      count: colony._count.id,
      avgPrice: this.prisma.toNumber(colony._avg.price),
      avgPxm2: this.prisma.toNumber(colony._avg.pricePerSqm),
      change30d: 0, // TODO: Calcular cambio real
      trend: 'stable' as const
    }));
  }

  private async getPropertyTypeDistribution() {
    const distribution = await this.prisma.listingProcessed.groupBy({
      by: ['propertyType'],
      where: { isOutlier: false },
      _count: { id: true },
      _avg: { price: true, pricePerSqm: true }
    });

    const total = distribution.reduce((sum, item) => sum + item._count.id, 0);

    return distribution.map(item => ({
      type: item.propertyType,
      count: item._count.id,
      percentage: Math.round((item._count.id / total) * 1000) / 10,
      avgPrice: this.prisma.toNumber(item._avg.price),
      avgPxm2: this.prisma.toNumber(item._avg.pricePerSqm)
    }));
  }

  private async generateInsights(): Promise<MarketInsight[]> {
    // Insights automáticos básicos
    const insights: MarketInsight[] = [];

    // TODO: Implementar lógica de insights más sofisticada
    insights.push({
      type: 'trend',
      title: 'Mercado Estable',
      description: 'El mercado inmobiliario de la ZMG mantiene estabilidad en precios.',
      impact: 'medium'
    });

    return insights;
  }

  private async getQuickStats() {
    const municipalities = await this.prisma.listingProcessed.groupBy({
      by: ['municipality'],
      where: { isOutlier: false }
    });

    const colonies = await this.prisma.listingProcessed.groupBy({
      by: ['colony'],
      where: { isOutlier: false, colony: { not: null } }
    });

    const surfaceAvg = await this.prisma.listingProcessed.aggregate({
      where: { isOutlier: false, surfaceBuiltM2: { not: null } },
      _avg: { surfaceBuiltM2: true }
    });

    const bedroomsMode = await this.prisma.listingProcessed.groupBy({
      by: ['bedrooms'],
      where: { isOutlier: false, bedrooms: { not: null } },
      _count: { id: true },
      orderBy: { _count: { id: 'desc' } },
      take: 1
    });

    const bathroomsMode = await this.prisma.listingProcessed.groupBy({
      by: ['bathrooms'],
      where: { isOutlier: false, bathrooms: { not: null } },
      _count: { id: true },
      orderBy: { _count: { id: 'desc' } },
      take: 1
    });

    return {
      totalMunicipalities: municipalities.length,
      totalColonies: colonies.length,
      avgSurface: Math.round(this.prisma.toNumber(surfaceAvg._avg.surfaceBuiltM2)),
      mostCommonBedrooms: bedroomsMode[0]?.bedrooms || 2,
      mostCommonBathrooms: this.prisma.toNumber(bathroomsMode[0]?.bathrooms) || 2
    };
  }

  private processCachedBins(cachedBins: any): HistogramBin[] {
    const edges = cachedBins.binEdges as number[];
    const counts = cachedBins.binCounts as number[];
    const labels = cachedBins.binLabels as string[];
    const totalCount = cachedBins.totalCount;

    return edges.slice(0, -1).map((edge, i) => ({
      min: edge,
      max: edges[i + 1],
      count: counts[i],
      label: labels[i],
      percentage: Math.round((counts[i] / totalCount) * 1000) / 10
    }));
  }

  private async calculateHistogramRealTime(request: HistogramRequestDto): Promise<HistogramResponseDto> {
    // Fallback para calcular histograma en tiempo real
    // TODO: Implementar cálculo dinámico
    return {
      bins: [],
      meta: {
        variable: request.variable,
        totalCount: 0,
        method: 'realtime',
        calculatedAt: new Date().toISOString(),
        geoLevel: request.geoLevel,
        geoId: request.geoId,
        filters: request
      }
    };
  }

  private generateSegmentComparison(segments: any[]) {
    // TODO: Implementar comparación inteligente entre segmentos
    return {
      summary: 'Comparación generada',
      differences: [],
      recommendations: []
    };
  }

  private calculateHealthScore(total: number, outlierRate: number, colonies: number): number {
    // Fórmula simple de health score
    const completeness = Math.min(total / 25000, 1) * 40; // 40% por completitud
    const quality = (1 - outlierRate) * 30; // 30% por calidad
    const coverage = Math.min(colonies / 1000, 1) * 30; // 30% por cobertura

    return Math.round(completeness + quality + coverage);
  }

  private percentile(arr: number[], p: number): number {
    const sorted = arr.sort((a, b) => a - b);
    const index = p * (sorted.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index % 1;

    if (upper >= sorted.length) return sorted[sorted.length - 1];
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
  }

  private formatCurrency(value: number): string {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }
}
