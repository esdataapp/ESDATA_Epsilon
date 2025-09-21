import { ReactNode } from 'react';
import { OperationToggle, OperationToggleCompact } from './OperationToggle';
import { useOperationStore } from '@/store/operationStore';
import { BarChart3, MapPin } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { currentOperation } = useOperationStore();
  
  const operationColors = {
    venta: 'from-blue-500 to-blue-600',
    renta: 'from-green-500 to-green-600',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo y título */}
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-gradient-to-r ${operationColors[currentOperation]} text-white`}>
                <BarChart3 size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Dashboard ZMG
                </h1>
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <MapPin size={12} />
                  Zona Metropolitana de Guadalajara
                </p>
              </div>
            </div>
            
            {/* Toggle de operación - Desktop */}
            <div className="hidden sm:block">
              <OperationToggle />
            </div>
            
            {/* Toggle de operación - Mobile */}
            <div className="sm:hidden">
              <OperationToggleCompact />
            </div>
          </div>
        </div>
      </header>
      
      {/* Breadcrumb con operación actual */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-2">
            <div className="flex items-center text-sm text-gray-500">
              <span>Inicio</span>
              <span className="mx-2">›</span>
              <span className={`font-medium ${
                currentOperation === 'venta' ? 'text-blue-600' : 'text-green-600'
              }`}>
                {currentOperation === 'venta' ? '🏠 Venta' : '🔑 Renta'}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Contenido principal */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="text-sm text-gray-500">
              © 2024 Dashboard ZMG - Inteligencia Inmobiliaria
            </div>
            <div className="text-xs text-gray-400">
              Datos actualizados: {new Date().toLocaleDateString('es-MX')}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
