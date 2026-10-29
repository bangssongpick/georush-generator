@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0"
echo GeoRush 무료 Python 라이브러리를 설치합니다. 첫 설치에는 인터넷이 필요합니다.
if exist ".venv\Scripts\python.exe" goto packages
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m venv ".venv"
) else (
  python -m venv ".venv"
)
if not exist ".venv\Scripts\python.exe" goto failed
:packages
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements.txt"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import tkinter,PIL,numpy,imageio_ffmpeg; print('GeoRush dependencies OK')"
if errorlevel 1 goto failed
echo 설치 완료. START_HERE.cmd를 실행하세요.
if /I not "%~1"=="/nopause" pause
popd
exit /b 0
:failed
echo 설치 실패. Python 3.11 이상과 인터넷 연결을 확인하세요. Python 3.12를 권장합니다.
echo Python 공식 설치: https://www.python.org/downloads/windows/
if /I not "%~1"=="/nopause" pause
popd
exit /b 1
