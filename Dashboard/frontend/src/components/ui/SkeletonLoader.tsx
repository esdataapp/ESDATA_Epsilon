import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular' | 'rounded';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
  animation = 'pulse'
}) => {
  const getVariantClasses = () => {
    switch (variant) {
      case 'circular':
        return 'rounded-full';
      case 'rounded':
        return 'rounded-lg';
      case 'rectangular':
        return 'rounded-none';
      default:
        return 'rounded';
    }
  };

  const getAnimationClasses = () => {
    switch (animation) {
      case 'wave':
        return 'animate-pulse bg-gradient-to-r from-neutral-200 via-neutral-300 to-neutral-200 bg-[length:200%_100%] animate-[wave_1.5s_ease-in-out_infinite]';
      case 'pulse':
        return 'animate-pulse bg-neutral-200';
      default:
        return 'bg-neutral-200';
    }
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`${getVariantClasses()} ${getAnimationClasses()} ${className}`}
      style={style}
    />
  );
};

// Componentes de skeleton predefinidos
export const KPICardSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg p-6 border shadow-sm">
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton width="60%" height="16px" />
        <Skeleton variant="circular" width="20px" height="20px" />
      </div>
      <Skeleton width="40%" height="32px" />
      <Skeleton width="50%" height="12px" />
      <Skeleton width="100%" height="32px" variant="rounded" />
    </div>
  </div>
);

export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 300 }) => (
  <div className="bg-white rounded-lg p-6 border shadow-sm">
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton width="40%" height="20px" />
        <Skeleton width="20%" height="16px" />
      </div>
      <Skeleton width="100%" height={`${height}px`} variant="rounded" />
      <div className="flex justify-between">
        <Skeleton width="15%" height="12px" />
        <Skeleton width="15%" height="12px" />
        <Skeleton width="15%" height="12px" />
        <Skeleton width="15%" height="12px" />
      </div>
    </div>
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 4 
}) => (
  <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
    {/* Header */}
    <div className="bg-neutral-50 p-4 border-b">
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {[...Array(columns)].map((_, i) => (
          <Skeleton key={i} width="80%" height="16px" />
        ))}
      </div>
    </div>
    
    {/* Rows */}
    <div className="divide-y">
      {[...Array(rows)].map((_, rowIndex) => (
        <div key={rowIndex} className="p-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {[...Array(columns)].map((_, colIndex) => (
              <Skeleton 
                key={colIndex} 
                width={colIndex === 0 ? "90%" : "70%"} 
                height="14px" 
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const ListSkeleton: React.FC<{ items?: number }> = ({ items = 6 }) => (
  <div className="space-y-4">
    {[...Array(items)].map((_, i) => (
      <div key={i} className="bg-white rounded-lg p-4 border shadow-sm">
        <div className="flex items-start space-x-4">
          <Skeleton variant="circular" width="48px" height="48px" />
          <div className="flex-1 space-y-2">
            <Skeleton width="60%" height="16px" />
            <Skeleton width="40%" height="14px" />
            <Skeleton width="80%" height="12px" />
          </div>
          <Skeleton width="80px" height="32px" variant="rounded" />
        </div>
      </div>
    ))}
  </div>
);

export const FilterSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg border p-4">
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton width="30%" height="20px" />
        <Skeleton variant="circular" width="24px" height="24px" />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Skeleton width="40%" height="14px" />
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-2">
                <Skeleton variant="rectangular" width="16px" height="16px" />
                <Skeleton width="60%" height="14px" />
              </div>
            ))}
          </div>
        </div>
        
        <div className="space-y-2">
          <Skeleton width="40%" height="14px" />
          <Skeleton width="100%" height="40px" variant="rounded" />
        </div>
      </div>
      
      <div className="flex justify-end">
        <Skeleton width="120px" height="36px" variant="rounded" />
      </div>
    </div>
  </div>
);

export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* Header */}
    <div className="bg-white rounded-lg p-6 border shadow-sm">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton width="300px" height="28px" />
          <Skeleton width="400px" height="16px" />
        </div>
        <Skeleton width="100px" height="60px" variant="rounded" />
      </div>
    </div>

    {/* KPIs */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <KPICardSkeleton key={i} />
      ))}
    </div>

    {/* Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ChartSkeleton height={350} />
      <ChartSkeleton height={350} />
    </div>

    {/* Table */}
    <TableSkeleton rows={8} columns={6} />
  </div>
);

export default Skeleton;
