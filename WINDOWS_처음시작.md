> 이 문서는 이전 개발 단계의 기록입니다. 최신 Windows EXE와 검증은 [정식 배포 보고서](WINDOWS_EXE_RELEASE_KO.md)를 확인하세요.

# GeoRush v1.0 — Windows 11 처음 실행·EXE 만들기

이 ZIP은 **소스 배포본**입니다. 이미 완성된 Windows EXE를 포함하지 않습니다.
Windows 실기 빌드·실행은 개발 환경에서 미검증입니다. GitHub, GitHub Actions, Codex 클라우드 게시, API 키는 필요 없습니다.
실제로 생성한 예제 영상 3편은 `samples/sample_01`, `sample_02`, `sample_03`의 `video.mp4`입니다.

## 1. Python 준비

1. https://www.python.org/downloads/windows/ 에서 **Python 3.12 64비트** 공식 설치 프로그램을 받습니다.
2. 설치 화면의 **Add python.exe to PATH**와 Python Launcher를 선택하고 설치합니다. Tkinter는 공식 기본 설치에 포함됩니다.
3. 이 ZIP을 오른쪽 클릭 → **압축 풀기**로 새 독립 폴더에 풉니다. 예: `C:\GeoRush`.
   ZIP 안에서 바로 실행하지 마세요. Brain Blink나 왜일까? 폴더에 덮어쓰지 마세요.

## 2. 소스로 먼저 실행

1. `START_HERE.cmd`를 더블클릭합니다.
2. 첫 실행에는 `INSTALL.cmd`가 GeoRush 안에만 `.venv`를 만들고 무료 라이브러리를 설치합니다. **처음에는 인터넷 연결이 필요**합니다.
3. 한국어 GeoRush Generator 창에서 제작 편수 1, Mixed, 문제 수 3, BGM 10%로 둡니다.
4. **영상 제작 시작**을 누릅니다. 기본 21초 영상이며 제작 중 창에서 진행 상태를 볼 수 있습니다.
5. **출력 폴더 열기**로 `video.mp4`, 영어 제목·설명·태그·고정댓글과 정답 JSON을 확인합니다.
6. 영상을 실제 재생해 카운트다운, 초록색 정답, BGM·효과음과 한글 UI를 확인합니다.

기본 출력은 Windows가 지정한 실제 바탕화면의 `GeoRush_Output`입니다. OneDrive로 옮긴 바탕화면도 Windows 셸 경로로 탐지합니다.
원하면 GUI에서 다른 폴더를 지정하세요. 실제 OneDrive 동기화·권한과 Windows 한글 외관은 사용자 PC 검수 항목입니다.

## 3. 내 PC에서 EXE 만들기

1. GUI를 닫고 **`BUILD_EXE.cmd`**를 더블클릭합니다.
2. 빌드 전용 의존성을 설치하고 기존 32개 테스트를 실행합니다.
3. PyInstaller로 Python·Tk·NumPy·Pillow·국기·영어 글꼴·FFmpeg를 포함한 폴더형 EXE를 만듭니다.
4. 만들어진 **EXE 자체**가 자동으로 GUI 버튼을 눌러 3문제 MP4를 만드는 검사를 합니다. 잠깐 자동 검증 창이 나타날 수 있습니다.
5. 정답·자원 경로·실제 MP4 디코딩·음향·한글 경로·제작 이력이 통과한 경우에만 아래 ZIP을 만듭니다.

```text
dist\GeoRush-v1.0-Windows-x64.zip          검증 통과 후 생성되는 배포 ZIP
dist\GeoRushGenerator\GeoRushGenerator.exe
dist\GeoRushGenerator\WINDOWS_VALIDATION.json
build_validation\                        검증 영상과 결과
```

위 파일들은 **사용자 Windows에서 성공적으로 빌드한 뒤 생기는 파일**입니다. 현재 소스 ZIP에 EXE가 들어 있다는 뜻이 아닙니다.
빌드가 실패하면 위 오류와 `build_validation\WINDOWS_VALIDATION.json`을 확인하세요.
이전 빌드 ZIP이 남아 있을 수 있으므로 실패 후에는 기존 ZIP을 새 성공 결과로 사용하지 마세요.

## 4. Python 없는 PC에 옮기기

성공한 `dist\GeoRush-v1.0-Windows-x64.zip`을 다른 Windows 11 64비트 PC로 복사합니다.
그 PC에서 압축을 완전히 풀고 폴더 안의 `START_HERE.cmd` 또는 `GeoRushGenerator.exe`를 실행합니다.
**그 배포본의 실행에는 Python 별도 설치가 필요 없습니다.** `.exe`만 따로 복사하면 안 됩니다. `_internal` 폴더 전체가 필요합니다.
이 동작은 빌드 코드가 목표로 하는 구성이고, 개발 환경에서는 Windows 무설치 PC 실기 검증을 수행하지 못했습니다.

## 포함 리소스와 의존성

| 항목 | 소스 실행 / EXE 경로 |
| --- | --- |
| Python | 소스는 공식 3.12 64비트 필요 / EXE는 PyInstaller가 포함 |
| Pillow 12.3.0 | PNG·영어 텍스트·프레임 렌더 |
| NumPy 2.3.5 | 내장 BGM·효과음 합성 |
| imageio-ffmpeg 0.6.0 | 무료 로컬 FFmpeg 바이너리 제공 |
| PyInstaller 6.16.0 | EXE를 만드는 PC에만 필요 |
| Tkinter/SQLite | 공식 Python 기본 구성 / EXE에 포함 |
| 국기·국가 | `assets` / `_internal\assets` |
| FFmpeg | 로컬 탐지 / `_internal\bin\ffmpeg.exe` |
| 영어 글꼴 | `assets\fonts\DejaVuSans-Bold.ttf` / `_internal\assets\fonts` |
| 한국어 GUI | Windows 기본 맑은 고딕 사용, OS 글꼴 파일 재배포 안 함 |
| BGM·효과음 | 별도 파일 다운로드 없이 프로그램에서 합성, 실행 시 출력 폴더에 WAV 저장 |

실행 의존성은 `requirements.txt`, 빌드 의존성은 `requirements-build.txt`에 고정했습니다.
유료 API·TTS·음원·AI 서비스가 필요 없습니다. 첫 설치/빌드 이후 영상 생성은 오프라인입니다.
FFprobe는 필수 설치 항목이 아니며 없어도 내장 FFmpeg로 전체 디코딩 검사를 수행합니다.
출처·라이선스는 `assets/ASSET_LICENSES.md`, `THIRD_PARTY_NOTICES.md`에 있습니다.

## 확인한 범위

- 기존 32개 테스트 유지 및 Linux 재실행 통과.
- 실제 국기 60개 해시·디코딩 검사 통과. EXE 형태의 자원 경로 선택은 **모의 검사** 통과.
- 이전 Linux 실제 GUI→MP4 제작과 실제 쇼츠 3편의 전체 디코딩은 통과했습니다.
- 새 로컬 배포 검사 결과는 `reports/local_source_gui_check.json`을 확인하세요. Linux 검사는 Windows EXE 검사가 아닙니다.
- **Windows CMD, EXE 빌드, Windows 한국어 외관, 실제 OneDrive 동기화는 미검증**입니다.
- 기존 Brain Blink·왜일까? 설치 파일·설정·채널 자료는 변경하거나 삭제하지 않습니다.
