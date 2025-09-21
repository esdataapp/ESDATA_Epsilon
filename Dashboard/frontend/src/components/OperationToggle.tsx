import { useOperationStore, type Operation } from '@/store/operationStore';
import { cn } from '@/lib/utils';
import { Home, Key } from 'lucide-react';

const operationConfig = {
  venta: {
    label: 'Venta',
    icon: Home,
    color: 'bg-primary-500 text-white',
    hoverColor: 'hover:bg-primary-600',
    inactiveColor: 'text-gray-600 hover:text-gray-800 hover:bg-gray-100',
  },
  renta: {
    label: 'Renta',
    icon: Key,
    color: 'bg-secondary-500 text-white',
    hoverColor: 'hover:bg-secondary-600',
    inactiveColor: 'text-gray-600 hover:text-gray-800 hover:bg-gray-100',
  },
};

export function OperationToggle() {
  const { currentOperation, setOperation } = useOperationStore();

  const handleOperationChange = (operation: Operation) => {
    setOperation(operation);
  };

  return (
    <div className="flex bg-gray-100 rounded-lg p-1 shadow-sm">
      {(Object.keys(operationConfig) as Operation[]).map((operation) => {
        const config = operationConfig[operation];
        const Icon = config.icon;
        const isActive = currentOperation === operation;

        return (
          <button
            key={operation}
            onClick={() => handleOperationChange(operation)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 font-medium text-sm min-w-[100px] justify-center',
              isActive 
                ? cn(config.color, config.hoverColor, 'shadow-sm')
                : cn(config.inactiveColor)
            )}
          >
            <Icon size={16} />
            {config.label}
          </button>
        );
      })}
    </div>
  );
}

// Versión compacta para mobile
export function OperationToggleCompact() {
  const { currentOperation, setOperation } = useOperationStore();

  const handleOperationChange = (operation: Operation) => {
    setOperation(operation);
  };

  return (
    <div className="flex bg-gray-100 rounded-lg p-1">
      {(Object.keys(operationConfig) as Operation[]).map((operation) => {
        const config = operationConfig[operation];
        const Icon = config.icon;
        const isActive = currentOperation === operation;

        return (
          <button
            key={operation}
            onClick={() => handleOperationChange(operation)}
            className={cn(
              'flex items-center justify-center p-2 rounded-md transition-all duration-200 min-w-[44px]',
              isActive 
                ? cn(config.color, config.hoverColor)
                : cn(config.inactiveColor)
            )}
            title={config.label}
          >
            <Icon size={18} />
          </button>
        );
      })}
    </div>
  );
}
