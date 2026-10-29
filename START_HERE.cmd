@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0"
if exist "dist\GeoRushGenerator\GeoRushGenerator.exe" (
  start "GeoRush Generator" "dist\GeoRushGenerator\GeoRushGenerator.exe"
  popd
  exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
  call "%~dp0INSTALL.cmd" /nopause
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" "main.py"
if errorlevel 1 goto failed
popd
exit /b 0
:failed
echo.
echo [GeoRush] 실행하지 못했습니다. 위 오류와 출력 폴더의 georush.log를 확인하세요.
pause
popd
exit /b 1
