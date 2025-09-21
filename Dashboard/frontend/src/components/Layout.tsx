import { ReactNode } from 'react';
import { useOperationStore } from '@/store/operationStore';
import EsdataLogo from './ui/EsdataLogo';
import Breadcrumb from './navigation/Breadcrumb';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Barra superior solo con breadcrumb */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-12">
            {/* Breadcrumb izquierda */}
            <div className="flex items-center gap-4">
              <EsdataLogo size="sm" variant="color" />
              <Breadcrumb />
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
            <div className="text-sm text-neutral-500">
              © 2025 Esdata - Inteligencia Inmobiliaria ZMG
            </div>
            <div className="text-xs text-neutral-400">
              Datos actualizados: {new Date().toLocaleDateString('es-MX')}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
