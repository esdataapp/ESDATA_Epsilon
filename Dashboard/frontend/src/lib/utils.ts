import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number, type?: string): string {
  if (type === 'currency' || type?.includes('precio')) {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }
  
  if (type?.includes('pxm2') || type?.includes('por_m2')) {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value) + '/m²';
  }
  
  if (type?.includes('superficie') || type?.includes('area')) {
    return new Intl.NumberFormat('es-MX', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(value) + ' m²';
  }
  
  return new Intl.NumberFormat('es-MX').format(value);
}

export function formatPercentage(value: number): string {
  return new Intl.NumberFormat('es-MX', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
}
