@echo off
echo.
echo ========================================
echo 🚀 INSTALACION DASHBOARD ZMG
echo ========================================
echo.

echo 📦 Instalando dependencias del backend...
cd backend_csv
if exist package.json (
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Error instalando backend
        pause
        exit /b 1
    )
    echo ✅ Backend instalado correctamente
) else (
    echo ❌ No se encontró package.json del backend
    pause
    exit /b 1
)

echo.
echo 📦 Instalando dependencias del frontend...
cd ..\frontend
if exist package.json (
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Error instalando frontend
        pause
        exit /b 1
    )
    echo ✅ Frontend instalado correctamente
) else (
    echo ❌ No se encontró package.json del frontend
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ INSTALACION COMPLETADA
echo ========================================
echo.
echo Para iniciar el dashboard:
echo.
echo 1. Backend:  cd backend_csv  ^&^& npm start
echo 2. Frontend: cd frontend     ^&^& npm run dev
echo 3. Abrir:    http://localhost:5173
echo.
pause
