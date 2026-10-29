@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0"
call "%~dp0INSTALL.cmd" /nopause
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements-build.txt"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto failed
".venv\Scripts\python.exe" "tools\build_windows.py"
if errorlevel 1 goto failed
echo.
echo EXE 및 실제 GUI 영상 검사 성공. dist\GeoRush-v1.1-Windows-EXE.zip 생성 완료.
echo 배포 시 ZIP을 완전히 풀고 START_HERE.cmd를 실행하세요. Python 설치는 필요 없습니다.
pause
popd
exit /b 0
:failed
echo 빌드 또는 검증 실패. 성공 배포로 판정하지 않습니다.
echo 위 오류와 build_validation\WINDOWS_VALIDATION.json을 확인하세요.
pause
popd
exit /b 1
