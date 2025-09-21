#!/bin/bash

echo "🏗️  Configurando Dashboard ZMG..."

# Crear directorios principales
mkdir -p backend frontend python_sync testing

# Copiar archivo de entorno
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Archivo .env creado. Por favor, configura las variables necesarias."
fi

# Backend setup
echo "📦 Configurando Backend (NestJS)..."
cd backend

# Crear package.json si no existe
if [ ! -f package.json ]; then
    cat > package.json << 'EOF'
{
  "name": "dashboard-zmg-backend",
  "version": "1.0.0",
  "description": "Backend API para Dashboard Inmobiliario ZMG",
  "main": "dist/main.js",
  "scripts": {
    "build": "nest build",
    "format": "prettier --write \"src/**/*.ts\" \"test/**/*.ts\"",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "start:debug": "nest start --debug --watch",
    "start:prod": "node dist/main",
    "lint": "eslint \"{src,apps,libs,test}/**/*.ts\" --fix",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:cov": "jest --coverage",
    "prisma:generate": "prisma generate",
    "prisma:migrate": "prisma migrate dev",
    "prisma:seed": "ts-node prisma/seed.ts"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/platform-express": "^10.0.0",
    "@nestjs/cache-manager": "^2.1.0",
    "@nestjs/throttler": "^5.0.0",
    "@prisma/client": "^5.0.0",
    "cache-manager": "^5.2.3",
    "cache-manager-redis-store": "^3.0.1",
    "class-transformer": "^0.5.1",
    "class-validator": "^0.14.0",
    "prisma": "^5.0.0",
    "redis": "^4.6.7",
    "reflect-metadata": "^0.1.13",
    "rxjs": "^7.8.1"
  },
  "devDependencies": {
    "@nestjs/cli": "^10.0.0",
    "@nestjs/schematics": "^10.0.0",
    "@nestjs/testing": "^10.0.0",
    "@types/express": "^4.17.17",
    "@types/jest": "^29.5.2",
    "@types/node": "^20.3.1",
    "@types/supertest": "^2.0.12",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.42.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-prettier": "^5.0.0",
    "jest": "^29.5.0",
    "prettier": "^3.0.0",
    "source-map-support": "^0.5.21",
    "supertest": "^6.3.3",
    "ts-jest": "^29.1.0",
    "ts-loader": "^9.4.3",
    "ts-node": "^10.9.1",
    "tsconfig-paths": "^4.2.0",
    "typescript": "^5.1.3"
  }
}
EOF
fi

# Instalar dependencias del backend
npm install

# Crear estructura de directorios del backend
mkdir -p src/{prisma,stats,geo,analysis,cache,common}
mkdir -p src/common/{decorators,filters,guards,interceptors}
mkdir -p src/analysis/services
mkdir -p src/stats/dto

cd ../

# Frontend setup
echo "🎨 Configurando Frontend (React + Vite)..."
cd frontend

# Crear package.json si no existe
if [ ! -f package.json ]; then
    cat > package.json << 'EOF'
{
  "name": "dashboard-zmg-frontend",
  "version": "1.0.0",
  "type": "module",
  "description": "Frontend para Dashboard Inmobiliario ZMG",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "@tanstack/react-query": "^4.32.6",
    "zustand": "^4.4.1",
    "recharts": "^2.8.0",
    "mapbox-gl": "^2.15.0",
    "react-map-gl": "^7.1.6",
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-select": "^1.2.2",
    "@radix-ui/react-dialog": "^1.0.4",
    "@radix-ui/react-tabs": "^1.0.4",
    "react-hook-form": "^7.45.4",
    "@hookform/resolvers": "^3.3.1",
    "zod": "^3.22.2",
    "lucide-react": "^0.263.1",
    "clsx": "^2.0.0",
    "tailwind-merge": "^1.14.0",
    "framer-motion": "^10.16.4",
    "react-window": "^1.8.8"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@types/react-window": "^1.8.5",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "postcss": "^8.4.27",
    "tailwindcss": "^3.3.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5",
    "vitest": "^0.34.6",
    "jsdom": "^22.1.0"
  }
}
EOF
fi

# Instalar dependencias del frontend
npm install

# Crear estructura de directorios del frontend
mkdir -p src/{components,pages,hooks,store,services,utils,types,styles}
mkdir -p src/components/{ui,layout,charts,maps,filters,cards,segments}
mkdir -p public/{icons,images}

cd ../

# Python sync setup
echo "🐍 Configurando Python Sync..."
cd python_sync

# Crear requirements.txt si no existe
if [ ! -f requirements.txt ]; then
    cat > requirements.txt << 'EOF'
pandas>=2.0.0
numpy>=1.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
scikit-learn>=1.3.0
scipy>=1.10.0
python-dotenv>=1.0.0
geopandas>=0.13.0
shapely>=2.0.0
redis>=4.6.0
requests>=2.31.0
EOF
fi

# Crear entorno virtual de Python
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "🐍 Entorno virtual de Python creado."
fi

# Activar entorno virtual e instalar dependencias
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

pip install -r requirements.txt

cd ../

# Crear directorios de testing
mkdir -p testing/{backend,frontend,python}
mkdir -p testing/backend/{unit,integration,e2e}
mkdir -p testing/frontend/{components,pages,utils}

echo "✅ Setup completado!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configurar variables de entorno en .env"
echo "2. Obtener token de Mapbox y agregarlo a .env"
echo "3. Ejecutar: docker-compose up -d"
echo "4. Ejecutar migraciones: cd backend && npm run prisma:migrate"
echo "5. Sincronizar datos: cd python_sync && python sync_data.py"
echo ""
echo "🚀 Para desarrollo:"
echo "   Backend:  cd backend && npm run start:dev"
echo "   Frontend: cd frontend && npm run dev"
