import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  constructor() {
    super({
      log: ['query', 'info', 'warn', 'error'],
    });
  }

  async onModuleInit() {
    await this.$connect();
    console.log('🗄️  Database connected successfully');
  }

  async onModuleDestroy() {
    await this.$disconnect();
    console.log('🗄️  Database disconnected');
  }

  // Helper method for safe decimal conversion
  toNumber(decimal: any): number {
    return decimal ? parseFloat(decimal.toString()) : 0;
  }

  // Helper method for pagination
  getPaginationParams(page: number = 1, limit: number = 20) {
    const skip = (page - 1) * limit;
    return { skip, take: limit };
  }

  // Helper method for building where clauses
  buildWhereClause(filters: any) {
    const where: any = {};

    if (filters.propertyType?.length) {
      where.propertyType = { in: filters.propertyType };
    }

    if (filters.operation?.length) {
      where.operation = { in: filters.operation };
    }

    if (filters.city?.length) {
      where.city = { in: filters.city };
    }

    if (filters.municipality?.length) {
      where.municipality = { in: filters.municipality };
    }

    if (filters.colonies?.length) {
      where.colony = { in: filters.colonies };
    }

    if (filters.priceRange?.length === 2) {
      where.price = {
        gte: filters.priceRange[0],
        lte: filters.priceRange[1],
      };
    }

    if (filters.surfaceRange?.length === 2) {
      where.surfaceBuiltM2 = {
        gte: filters.surfaceRange[0],
        lte: filters.surfaceRange[1],
      };
    }

    if (filters.pxm2Range?.length === 2) {
      where.pricePerSqm = {
        gte: filters.pxm2Range[0],
        lte: filters.pxm2Range[1],
      };
    }

    if (filters.bedrooms?.length) {
      where.bedrooms = { in: filters.bedrooms };
    }

    if (filters.bathrooms?.length) {
      where.bathrooms = { in: filters.bathrooms };
    }

    if (filters.amenitiesRequired?.length) {
      where.amenities = {
        path: '$',
        array_contains: filters.amenitiesRequired,
      };
    }

    if (!filters.includeOutliers) {
      where.isOutlier = false;
    }

    return where;
  }
}
