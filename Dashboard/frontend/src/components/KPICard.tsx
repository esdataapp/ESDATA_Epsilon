import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  className?: string;
  loading?: boolean;
}

export function KPICard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  className,
  loading = false,
}: KPICardProps) {
  if (loading) {
    return (
      <div className={cn('bg-white rounded-lg shadow-sm border p-6', className)}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  const trendIcons = {
    up: <TrendingUp size={16} className="text-green-500" />,
    down: <TrendingDown size={16} className="text-red-500" />,
    neutral: <Minus size={16} className="text-gray-400" />,
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500',
  };

  return (
    <div className={cn('bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {icon && <div className="text-gray-400">{icon}</div>}
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
          </div>
          
          <div className="mb-1">
            <span className="text-2xl font-bold text-gray-900">
              {typeof value === 'number' ? value.toLocaleString('es-MX') : value}
            </span>
          </div>
          
          {subtitle && (
            <p className="text-sm text-gray-500 mb-2">{subtitle}</p>
          )}
          
          {trend && trendValue && (
            <div className="flex items-center gap-1">
              {trendIcons[trend]}
              <span className={cn('text-sm font-medium', trendColors[trend])}>
                {trendValue}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Variante compacta para mobile
export function KPICardCompact({
  title,
  value,
  icon,
  className,
  loading = false,
}: Pick<KPICardProps, 'title' | 'value' | 'icon' | 'className' | 'loading'>) {
  if (loading) {
    return (
      <div className={cn('bg-white rounded-lg shadow-sm border p-4', className)}>
        <div className="animate-pulse">
          <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-6 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('bg-white rounded-lg shadow-sm border p-4', className)}>
      <div className="flex items-center gap-2 mb-1">
        {icon && <div className="text-gray-400 text-sm">{icon}</div>}
        <h3 className="text-xs font-medium text-gray-600 truncate">{title}</h3>
      </div>
      <div className="text-lg font-bold text-gray-900">
        {typeof value === 'number' ? value.toLocaleString('es-MX') : value}
      </div>
    </div>
  );
}
