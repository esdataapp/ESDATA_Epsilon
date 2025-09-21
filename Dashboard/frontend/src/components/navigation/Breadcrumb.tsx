import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { useOperationStore } from '@/store/operationStore';

interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
}

interface BreadcrumbProps {
  className?: string;
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ className = '' }) => {
  const { currentOperation } = useOperationStore();

  const operationLabels = {
    venta: 'Venta',
    renta: 'Renta'
  };

  const breadcrumbItems: BreadcrumbItem[] = [
    {
      label: 'Inicio',
      href: '/',
    },
    {
      label: operationLabels[currentOperation],
      active: true
    }
  ];

  return (
    <nav className={`flex items-center space-x-2 text-sm ${className}`} aria-label="Breadcrumb">
      <div className="flex items-center space-x-2">
        {breadcrumbItems.map((item, index) => (
          <React.Fragment key={index}>
            {index > 0 && (
              <ChevronRight size={14} className="text-neutral-400" />
            )}
            
            {item.href && !item.active ? (
              <a
                href={item.href}
                className="flex items-center gap-1 text-neutral-600 hover:text-neutral-900 transition-colors"
              >
                {index === 0 && <Home size={14} />}
                {item.label}
              </a>
            ) : (
              <span 
                className={`flex items-center gap-1 ${
                  item.active 
                    ? 'text-primary-600 font-medium' 
                    : 'text-neutral-600'
                }`}
              >
                {index === 0 && <Home size={14} />}
                {item.label}
              </span>
            )}
          </React.Fragment>
        ))}
      </div>
    </nav>
  );
};

export default Breadcrumb;
