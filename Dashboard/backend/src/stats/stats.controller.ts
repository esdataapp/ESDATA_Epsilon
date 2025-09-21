import { Controller, Get, Post, Body, Query, UseInterceptors, CacheInterceptor, CacheTTL } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { StatsService } from './stats.service';
import { FilterDto, FilteredStatsDto, PaginationDto } from './dto/filter.dto';
import { HistogramRequestDto, HistogramResponseDto } from './dto/histogram.dto';
import { OverviewResponseDto } from './dto/overview.dto';

@ApiTags('stats')
@Controller('stats')
@UseInterceptors(CacheInterceptor)
export class StatsController {
  constructor(private readonly statsService: StatsService) {}

  @Get('overview')
  @ApiOperation({ 
    summary: 'Obtener KPIs y métricas principales',
    description: 'Endpoint principal para la vista de Inicio. Devuelve KPIs, top colonias e insights automáticos.'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'KPIs y métricas principales',
    type: OverviewResponseDto
  })
  @CacheTTL(6 * 60 * 60) // 6 horas según recomendación
  async getOverview(): Promise<OverviewResponseDto> {
    return this.statsService.getOverview();
  }

  @Post('filtered')
  @ApiOperation({ 
    summary: 'Obtener estadísticas con filtros aplicados',
    description: 'Aplica filtros y devuelve estadísticas agregadas. Usado por todas las vistas con filtros.'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Estadísticas filtradas'
  })
  @CacheTTL(30 * 60) // 30 minutos según recomendación
  async getFilteredStats(@Body() filters: FilteredStatsDto) {
    return this.statsService.getFilteredStats(filters);
  }

  @Get('histogram')
  @ApiOperation({ 
    summary: 'Obtener histograma pre-calculado',
    description: 'Devuelve bins pre-calculados para histogramas de precio, superficie o precio por m².'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Datos del histograma',
    type: HistogramResponseDto
  })
  @CacheTTL(12 * 60 * 60) // 12 horas
  async getHistogram(@Query() request: HistogramRequestDto): Promise<HistogramResponseDto> {
    return this.statsService.getHistogram(request);
  }

  @Get('colonies/search')
  @ApiOperation({ 
    summary: 'Búsqueda de colonias con autocompletar',
    description: 'Búsqueda rápida de colonias usando índice trigram para autocompletar.'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Lista de colonias que coinciden'
  })
  @CacheTTL(60 * 60) // 1 hora
  async searchColonies(
    @Query('q') query: string,
    @Query('limit') limit: number = 10
  ) {
    return this.statsService.searchColonies(query, limit);
  }

  @Get('property-types')
  @ApiOperation({ 
    summary: 'Obtener tipos de propiedad disponibles',
    description: 'Lista todos los tipos de propiedad únicos en la base de datos.'
  })
  @CacheTTL(24 * 60 * 60) // 24 horas
  async getPropertyTypes() {
    return this.statsService.getPropertyTypes();
  }

  @Get('operations')
  @ApiOperation({ 
    summary: 'Obtener tipos de operación disponibles',
    description: 'Lista todos los tipos de operación únicos (venta, renta, etc.).'
  })
  @CacheTTL(24 * 60 * 60) // 24 horas
  async getOperations() {
    return this.statsService.getOperations();
  }

  @Get('municipalities')
  @ApiOperation({ 
    summary: 'Obtener municipios disponibles',
    description: 'Lista todos los municipios con conteo de propiedades.'
  })
  @CacheTTL(6 * 60 * 60) // 6 horas
  async getMunicipalities() {
    return this.statsService.getMunicipalities();
  }

  @Get('price-ranges')
  @ApiOperation({ 
    summary: 'Obtener rangos de precio sugeridos',
    description: 'Devuelve rangos de precio basados en percentiles para filtros.'
  })
  @CacheTTL(6 * 60 * 60) // 6 horas
  async getPriceRanges(@Query() filters: FilterDto) {
    return this.statsService.getPriceRanges(filters);
  }

  @Get('surface-ranges')
  @ApiOperation({ 
    summary: 'Obtener rangos de superficie sugeridos',
    description: 'Devuelve rangos de superficie basados en percentiles para filtros.'
  })
  @CacheTTL(6 * 60 * 60) // 6 horas
  async getSurfaceRanges(@Query() filters: FilterDto) {
    return this.statsService.getSurfaceRanges(filters);
  }

  @Post('compare-segments')
  @ApiOperation({ 
    summary: 'Comparar múltiples segmentos',
    description: 'Compara estadísticas entre diferentes segmentaciones de mercado.'
  })
  @CacheTTL(30 * 60) // 30 minutos
  async compareSegments(@Body() segments: { name: string; filters: FilterDto }[]) {
    return this.statsService.compareSegments(segments);
  }

  @Get('market-health')
  @ApiOperation({ 
    summary: 'Indicadores de salud del mercado',
    description: 'Métricas agregadas sobre la salud y actividad del mercado inmobiliario.'
  })
  @CacheTTL(6 * 60 * 60) // 6 horas
  async getMarketHealth() {
    return this.statsService.getMarketHealth();
  }
}
