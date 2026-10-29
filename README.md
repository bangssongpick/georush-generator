# GeoRush Generator v1.0 — Windows EXE 정식 배포

[**Python 설치 없이 실행하는 EXE ZIP 다운로드**](https://github.com/bangssongpick/georush-generator/releases/download/v1.0.0-windows/GeoRush-v1.0-Windows-EXE.zip)

[릴리스 페이지](https://github.com/bangssongpick/georush-generator/releases/tag/v1.0.0-windows) · [Windows Actions 실행](https://github.com/bangssongpick/georush-generator/actions/runs/40800479659) · [상세 검증 결과](WINDOWS_EXE_RELEASE_KO.md)

## 일반 사용자 실행

1. 위 ZIP을 다운로드하고 **압축을 완전히 풉니다**.
2. `GeoRushGenerator` 폴더의 `START_HERE.cmd` 또는 `GeoRushGenerator.exe`를 실행합니다.
3. 제작 편수 1, Mixed, 문제 수 3, BGM 10%로 첫 영상을 만듭니다.
4. **출력 폴더 열기**로 `video.mp4`와 영어 제목·설명·태그·고정댓글을 확인합니다.

Python·FFmpeg를 별도 설치할 필요가 없습니다. `_internal` 폴더를 포함한 전체 폴더를 함께 보관하세요. EXE만 따로 옮기면 안 됩니다.
기본 출력은 Windows 실제 바탕화면의 `GeoRush_Output`입니다. GUI에서 다른 출력 폴더를 선택할 수 있습니다.
설치 후 영상 제작은 무료·로컬·오프라인이며 Codex·유료 API·TTS가 필요 없습니다.

## 프로그램 범위

- 국기 맞히기 한 종류: 검증된 국가·국기 60개, 영어 4지선다, 정답 1개, 선택지와 정답 위치 무작위 배치.
- Easy/Normal/Hard 각 20개, Mixed 전체. 난이도는 친숙도 편집 분류입니다.
- 기본 3문제, 21초, 원본 1080×1920, 30fps, H.264/AAC.
- 첫 프레임부터 문제 표시, 5초 카운트다운·1.5초 정답 공개, 마지막 CTA 1.5초.
- 내장 로컬 BGM·효과음 합성, BGM 8/10/12%, 클리핑 방지.
- SQLite 독립 이력, 한 영상의 국가 중복 및 이전 동일 국가 조합 차단.
- 백그라운드 제작, GUI 진행률·성공/실패·오류·제작 이력.
- 각 출력에 영상·게시 문구·정답 JSON·검증 로그 저장. 한 편 실패 시 다른 편은 계속 처리합니다.

국기는 `flag-icons`의 표준 4:3 아이콘 변형이며 국가별 공식 제작 비율 전체를 재현하지 않습니다.
[국기·글꼴 출처 및 라이선스](assets/ASSET_LICENSES.md) · [의존성 안내](THIRD_PARTY_NOTICES.md).

## 실제 Windows 검증

`windows-latest`에서 기존 **32개 테스트 통과**, 실제 EXE GUI 버튼으로 3문제 MP4 제작과 전체 디코딩·정답·메타데이터·이력 검사를 통과했습니다.
Python·시스템 FFmpeg를 PATH에서 제외했고, 한글 경로로 배포 폴더를 복사한 뒤 다시 제작했습니다. 두 영상 모두 21초·630프레임·1080×1920·30fps·H.264/AAC입니다.

Windows 호스팅 러너 검증이므로 Python이 전혀 설치되지 않은 물리 PC 검증과는 구분합니다.
실제 PC의 GUI 외관·한국어 가독성·음향 듣기·OneDrive 클라우드 동기화는 추가 확인이 필요합니다.

## 개발자: 소스 실행·직접 빌드

소스 실행은 Python 3.12 64비트 설치 후 루트 `START_HERE.cmd`를 실행합니다.
프로젝트 전용 `.venv`의 무료 의존성 다운로드는 첫 설치에만 필요합니다.
`BUILD_EXE.cmd`는 테스트 → EXE 빌드 → 실제 GUI MP4 → 폴더 이동 후 재검사 → 성공 ZIP 순서로 동작합니다.
현재 출력 이름은 `dist/GeoRush-v1.0-Windows-EXE.zip`입니다.

```text
requirements.txt          실행 의존성
requirements-build.txt    PyInstaller 포함 빌드 의존성
georush/                  독립 제작 엔진
assets/                   국기·폰트·출처·라이선스
tests/                    기존 32개 테스트
tools/build_windows.py    실제 EXE 빌드·GUI·재배치 검사
```

기존 Brain Blink 모듈을 복사하거나 역공학하지 않았고 왜일까? 프로그램은 수정하지 않았습니다.
이전 소스 릴리스와 과거 보고서는 해당 시점의 기록이며, 최신 Windows 배포 검증은 위 정식 릴리스 보고서를 기준으로 보세요.
