import React from 'react';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';

interface SparkLineData {
  value: number;
  timestamp: string;
}

interface EnhancedKPICardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  sparkData?: SparkLineData[];
  loading?: boolean;
  trend?: 'up' | 'down' | 'stable';
  variant?: 'default' | 'premium' | 'warning' | 'success';
  tooltip?: string;
}

const SparkLine: React.FC<{ data: SparkLineData[]; className?: string }> = ({ data, className = '' }) => {
  if (!data || data.length === 0) return null;

  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((d.value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  const lastValue = values[values.length - 1];
  const prevValue = values[values.length - 2];
  const isPositive = lastValue >= prevValue;

  return (
    <div className={`relative ${className}`}>
      <svg
        width="100%"
        height="32"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="overflow-visible"
      >
        <defs>
          <linearGradient id="sparkGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity="0.3" />
            <stop offset="100%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity="0.1" />
          </linearGradient>
        </defs>
        
        {/* Área bajo la curva */}
        <polygon
          points={`0,100 ${points} 100,100`}
          fill="url(#sparkGradient)"
        />
        
        {/* Línea principal */}
        <polyline
          points={points}
          fill="none"
          stroke={isPositive ? "#10b981" : "#ef4444"}
          strokeWidth="2"
          className="drop-shadow-sm"
        />
        
        {/* Punto final */}
        <circle
          cx={data.length > 1 ? ((data.length - 1) / (data.length - 1)) * 100 : 50}
          cy={data.length > 1 ? 100 - ((lastValue - min) / range) * 100 : 50}
          r="2"
          fill={isPositive ? "#10b981" : "#ef4444"}
          className="animate-pulse-soft"
        />
      </svg>
    </div>
  );
};

const EnhancedKPICard: React.FC<EnhancedKPICardProps> = ({
  title,
  value,
  change,
  changeLabel,
  subtitle,
  icon,
  sparkData,
  loading = false,
  trend = 'stable',
  variant = 'default',
  tooltip
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp size={16} className="text-accent-500" />;
      case 'down':
        return <TrendingDown size={16} className="text-danger-500" />;
      default:
        return <Minus size={16} className="text-neutral-500" />;
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'premium':
        return 'bg-gradient-to-br from-premium-50 to-premium-100 border-premium-200';
      case 'warning':
        return 'bg-gradient-to-br from-warning-50 to-warning-100 border-warning-200';
      case 'success':
        return 'bg-gradient-to-br from-accent-50 to-accent-100 border-accent-200';
      default:
        return 'bg-white border-neutral-200';
    }
  };

  const getChangeColor = () => {
    if (change === undefined) return 'text-neutral-500';
    return change > 0 ? 'text-accent-600' : change < 0 ? 'text-danger-600' : 'text-neutral-500';
  };

  if (loading) {
    return (
      <div className={`rounded-lg p-6 border shadow-sm animate-pulse ${getVariantStyles()}`}>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="h-4 bg-neutral-200 rounded w-24"></div>
            <div className="h-5 w-5 bg-neutral-200 rounded"></div>
          </div>
          <div className="h-8 bg-neutral-200 rounded w-32"></div>
          <div className="h-3 bg-neutral-200 rounded w-20"></div>
          <div className="h-8 bg-neutral-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg p-6 border shadow-sm hover:shadow-md transition-all duration-300 animate-fade-in ${getVariantStyles()}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-neutral-600">{title}</p>
          {tooltip && (
            <div className="group relative">
              <Info size={14} className="text-neutral-400 cursor-help" />
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-neutral-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                {tooltip}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-neutral-800"></div>
              </div>
            </div>
          )}
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-primary-50 text-primary-600">
            {icon}
          </div>
        )}
      </div>

      {/* Valor principal */}
      <div className="flex items-baseline gap-3 mb-2">
        <h3 className="text-3xl font-bold text-neutral-900 animate-slide-up">
          {typeof value === 'number' ? value.toLocaleString('es-MX') : value}
        </h3>
        
        {change !== undefined && (
          <div className={`flex items-center gap-1 ${getChangeColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-semibold">
              {change > 0 ? '+' : ''}{change.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Subtítulo */}
      {subtitle && (
        <p className="text-sm text-neutral-500 mb-3">{subtitle}</p>
      )}

      {/* Etiqueta de cambio */}
      {changeLabel && (
        <p className="text-xs text-neutral-400 mb-3">{changeLabel}</p>
      )}

      {/* Sparkline */}
      {sparkData && sparkData.length > 0 && (
        <div className="mt-4">
          <SparkLine data={sparkData} className="h-8" />
        </div>
      )}

      {/* Indicador de tendencia visual */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex space-x-1">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={`h-1 w-6 rounded-full transition-all duration-300 ${
                trend === 'up' && i < 4 ? 'bg-accent-400' :
                trend === 'down' && i > 0 ? 'bg-danger-400' :
                trend === 'stable' && i === 2 ? 'bg-warning-400' :
                'bg-neutral-200'
              }`}
            />
          ))}
        </div>
        
        {/* Badge de estado */}
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          trend === 'up' ? 'bg-accent-100 text-accent-700' :
          trend === 'down' ? 'bg-danger-100 text-danger-700' :
          'bg-neutral-100 text-neutral-700'
        }`}>
          {trend === 'up' ? 'Creciendo' : trend === 'down' ? 'Bajando' : 'Estable'}
        </span>
      </div>
    </div>
  );
};

export default EnhancedKPICard;
