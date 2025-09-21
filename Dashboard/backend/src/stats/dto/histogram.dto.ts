import { IsString, IsOptional, IsEnum } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';
import { FilterDto } from './filter.dto';

export enum HistogramVariable {
  PRICE = 'price',
  SURFACE = 'surface',
  PXM2 = 'pxm2'
}

export enum GeoLevel {
  ZMG = 'zmg',
  CITY = 'city',
  MUNICIPALITY = 'municipality',
  COLONY = 'colony'
}

export class HistogramRequestDto extends FilterDto {
  @ApiProperty({ 
    description: 'Variable para el histograma',
    enum: HistogramVariable,
    example: HistogramVariable.PRICE
  })
  @IsEnum(HistogramVariable)
  variable: HistogramVariable;

  @ApiProperty({ 
    description: 'Nivel geográfico',
    enum: GeoLevel,
    example: GeoLevel.ZMG,
    required: false
  })
  @IsOptional()
  @IsEnum(GeoLevel)
  geoLevel?: GeoLevel = GeoLevel.ZMG;

  @ApiProperty({ 
    description: 'ID geográfico específico',
    example: 'guadalajara',
    required: false
  })
  @IsOptional()
  @IsString()
  geoId?: string;
}

export interface HistogramBin {
  min: number;
  max: number;
  count: number;
  label: string;
  percentage: number;
}

export interface HistogramResponseDto {
  bins: HistogramBin[];
  meta: {
    variable: string;
    totalCount: number;
    method: string;
    calculatedAt: string;
    geoLevel: string;
    geoId?: string;
    filters: any;
  };
}
