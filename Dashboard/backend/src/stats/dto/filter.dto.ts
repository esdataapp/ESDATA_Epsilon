import { IsOptional, IsArray, IsNumber, IsString, IsBoolean, Min, Max } from 'class-validator';
import { Type, Transform } from 'class-transformer';
import { ApiProperty } from '@nestjs/swagger';

export class FilterDto {
  @ApiProperty({ 
    description: 'Tipos de propiedad', 
    example: ['Departamento', 'Casa'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  propertyType?: string[];

  @ApiProperty({ 
    description: 'Tipos de operación', 
    example: ['Venta', 'Renta'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  operation?: string[];

  @ApiProperty({ 
    description: 'Ciudades', 
    example: ['Guadalajara', 'Zapopan'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  city?: string[];

  @ApiProperty({ 
    description: 'Municipios', 
    example: ['Guadalajara', 'Zapopan'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  municipality?: string[];

  @ApiProperty({ 
    description: 'Colonias específicas', 
    example: ['Providencia', 'Americana'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  colonies?: string[];

  @ApiProperty({ 
    description: 'Rango de precio [min, max]', 
    example: [1000000, 5000000],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsNumber({}, { each: true })
  @Type(() => Number)
  priceRange?: [number, number];

  @ApiProperty({ 
    description: 'Rango de superficie [min, max]', 
    example: [50, 200],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsNumber({}, { each: true })
  @Type(() => Number)
  surfaceRange?: [number, number];

  @ApiProperty({ 
    description: 'Rango de precio por m² [min, max]', 
    example: [20000, 50000],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsNumber({}, { each: true })
  @Type(() => Number)
  pxm2Range?: [number, number];

  @ApiProperty({ 
    description: 'Número de recámaras', 
    example: [1, 2, 3],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsNumber({}, { each: true })
  @Type(() => Number)
  bedrooms?: number[];

  @ApiProperty({ 
    description: 'Número de baños', 
    example: [1, 1.5, 2],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsNumber({}, { each: true })
  @Type(() => Number)
  bathrooms?: number[];

  @ApiProperty({ 
    description: 'Amenidades requeridas (TODAS deben estar presentes)', 
    example: ['piscina', 'gym'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  amenitiesRequired?: string[];

  @ApiProperty({ 
    description: 'Amenidades opcionales (CUALQUIERA puede estar presente)', 
    example: ['terraza', 'jardin'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  amenitiesAny?: string[];

  @ApiProperty({ 
    description: 'Incluir propiedades outliers', 
    example: false,
    required: false 
  })
  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  includeOutliers?: boolean = false;

  @ApiProperty({ 
    description: 'Estratos de precio', 
    example: ['medio', 'premium'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  priceStratum?: string[];

  @ApiProperty({ 
    description: 'Estratos de superficie', 
    example: ['standard', 'amplio'],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  surfaceStratum?: string[];

  @ApiProperty({ 
    description: 'Rango de antigüedad en años [min, max]', 
    example: [0, 10],
    required: false 
  })
  @IsOptional()
  @IsArray()
  @IsNumber({}, { each: true })
  @Type(() => Number)
  ageRange?: [number, number];
}

export class PaginationDto {
  @ApiProperty({ 
    description: 'Número de página', 
    example: 1,
    minimum: 1,
    required: false 
  })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Type(() => Number)
  page?: number = 1;

  @ApiProperty({ 
    description: 'Elementos por página', 
    example: 20,
    minimum: 1,
    maximum: 100,
    required: false 
  })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(100)
  @Type(() => Number)
  limit?: number = 20;

  @ApiProperty({ 
    description: 'Campo para ordenar', 
    example: 'price',
    required: false 
  })
  @IsOptional()
  @IsString()
  sortBy?: string = 'createdAt';

  @ApiProperty({ 
    description: 'Orden ascendente o descendente', 
    example: 'desc',
    required: false 
  })
  @IsOptional()
  @IsString()
  sortOrder?: 'asc' | 'desc' = 'desc';
}

export class FilteredStatsDto extends FilterDto {
  @ApiProperty({ 
    description: 'Incluir listado de propiedades', 
    example: false,
    required: false 
  })
  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  includeListings?: boolean = false;

  @ApiProperty({ 
    description: 'Máximo número de propiedades a incluir', 
    example: 50,
    required: false 
  })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(1000)
  @Type(() => Number)
  maxListings?: number = 50;
}
