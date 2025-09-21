import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { CacheModule } from '@nestjs/cache-manager';
import { ThrottlerModule } from '@nestjs/throttler';
import { redisStore } from 'cache-manager-redis-store';

import { PrismaModule } from './prisma/prisma.module';
import { StatsModule } from './stats/stats.module';
import { GeoModule } from './geo/geo.module';
import { AnalysisModule } from './analysis/analysis.module';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '../.env',
    }),

    // Rate limiting
    ThrottlerModule.forRoot([
      {
        ttl: 60000, // 1 minute
        limit: 100, // 100 requests per minute
      },
    ]),

    // Cache with Redis
    CacheModule.register({
      isGlobal: true,
      store: redisStore as any,
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT) || 6379,
      ttl: 300, // 5 minutes default
      max: 1000, // maximum number of items in cache
    }),

    // Application modules
    PrismaModule,
    StatsModule,
    GeoModule,
    AnalysisModule,
  ],
})
export class AppModule {}
