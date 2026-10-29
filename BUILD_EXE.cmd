@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  call "%~dp0INSTALL.cmd" /nopause
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check "pyinstaller>=6.11,<7"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name GeoRushGenerator --add-data "assets;assets" --collect-all imageio_ffmpeg --collect-all PIL --hidden-import tkinter "main.py"
if errorlevel 1 goto failed
echo.
echo 빌드 완료: dist\GeoRushGenerator\GeoRushGenerator.exe
echo 배포할 때 dist\GeoRushGenerator 폴더 전체를 함께 복사하세요.
echo Windows GUI, 한글 경로, 실제 MP4 생성은 이 PC에서 검증하세요.
pause
popd
exit /b 0
:failed
echo EXE 빌드 실패. 위 오류 로그를 확인하세요.
pause
popd
exit /b 1
