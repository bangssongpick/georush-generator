# GeoRush Windows 배포 안정화 상태

현재 상태: **Windows 러너 미실행 / EXE·Python 불필요 배포 ZIP 미생성 / 사이트 다운로드 링크 없음**.
GitHub API 요청은 현재 실행 환경에서 `Forbidden`입니다. 기존 저장소의 Git 읽기는 성공했지만,
새 GeoRush 저장소 생성·Actions 실행·릴리스 업로드 권한을 의미하지 않습니다.
이전의 소스 ZIP은 Python 불필요 Windows 배포본이 아닙니다.

## 준비한 실제 코드

- `.github/workflows/windows-release.yml`: Windows x64/Python 3.12에서 기존 테스트 실행 → PyInstaller → 실제 EXE GUI 버튼 렌더 → 검증 PASS 후 ZIP. 태그 실행은 PASS한 ZIP만 GitHub Release에 올립니다.
- `tools/build_windows.py`: 내장 Python·Tk·Pillow·NumPy·국기·글꼴·로컬 FFmpeg가 포함되는 폴더형 EXE 빌드. FFmpeg는 `_internal/bin/ffmpeg.exe`로 포함합니다.
- `main.py --distribution-check REPORT --output OUTPUT`: 소스와 EXE에서 같은 실제 GUI 제작 진입점을 호출합니다. 모의 렌더러를 사용하지 않습니다.
- `georush/distribution_check.py`: 60개 에셋·동봉 FFmpeg·글꼴·실제 셸 바탕화면 쓰기/읽기·한글 OneDrive 유사 경로·GUI 응답·3문제 21초 MP4·오디오·정답·성공 DB를 검사합니다.
- Windows 기본 Tk 글꼴을 Malgun Gothic으로 설정합니다. 폰트 이름 검사와 별도로 사람이 외관을 검수해야 합니다.

워크플로는 EXE 테스트 중 PATH에서 Python·시스템 FFmpeg를 제외합니다. FFprobe가 없어도 내장 FFmpeg로 실제 전체 디코딩 검사를 수행합니다.
Windows 호스팅 러너의 GUI 세션이 부족하면 검사 실패로 처리하며 ZIP을 성공 배포하지 않습니다.

## 실제 실행과 미검증 구분

- Linux 기존 테스트: **32개 통과**, 실패·건너뜀 0개 (`reports/windows_stabilization_tests.log`).
- Linux 새 배포 검사 진입점: `reports/distribution_check_linux.json`에 실제 실행 결과를 기록합니다. Linux 소스 검사는 Windows frozen EXE 검사가 아닙니다.
- Windows Actions, Windows EXE, 실제 Windows 한글 글꼴·바탕화면: **미검증**.
- OneDrive 유사 한글 로컬 경로와 실제 OneDrive 클라우드 동기화는 다릅니다. 후자는 사용자 로그인된 PC에서만 검수할 수 있습니다.
- Brain Blink 및 왜일까? 소스·설정·자료는 수정하지 않았습니다.

## 남은 외부 조건

환경 설정 초안에 기존 허용 도메인을 유지하고 `api.github.com`, `uploads.github.com`을 추가했습니다.
이 초안은 검토·저장·게시 후 적용해야 합니다. API가 열리면 기존 인증으로 새 GeoRush 전용 저장소 생성·Actions 실행 권한부터 다시 확인합니다.
새 접근 권한이 실제로 검증되기 전에는 인증이나 배포 성공을 주장하지 않습니다. API 키·토큰을 채팅에 입력할 필요는 없습니다.

새 전용 저장소의 Actions가 PASS한 후에만 Windows EXE와 ZIP의 실제 HTTPS 릴리스 링크를 제공합니다.
기존 Brain Blink·왜일까? 저장소에 워크플로나 GeoRush 배포 파일을 추가하지 않습니다.
