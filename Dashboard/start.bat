@echo off
echo.
echo ========================================
echo 🚀 INICIANDO DASHBOARD ZMG
echo ========================================
echo.

echo 🔍 Verificando datos...
if not exist "data\metadata.json" (
    echo ❌ No se encontraron datos generados
    echo 💡 Ejecuta primero: python python_sync\generate_dashboard_data.py
    pause
    exit /b 1
)

echo ✅ Datos encontrados
echo.

echo 🌐 Iniciando backend en puerto 3001...
start "Backend ZMG" cmd /k "cd backend_csv && npm start"

echo ⏳ Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo 🎨 Iniciando frontend en puerto 5173...
start "Frontend ZMG" cmd /k "cd frontend && npm run dev"

echo ⏳ Esperando 5 segundos...
timeout /t 5 /nobreak >nul

echo 🌐 Abriendo dashboard en el navegador...
start http://localhost:5173

echo.
echo ========================================
echo ✅ DASHBOARD INICIADO
echo ========================================
echo.
echo 🏠 Frontend: http://localhost:5173
echo 🔌 Backend:  http://localhost:3001
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
