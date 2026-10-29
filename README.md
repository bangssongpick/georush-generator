# GeoRush Generator v1.0

`@GeoRushGames`용 **국기 맞히기 쇼츠**를 만드는 독립 Python 프로그램입니다.
국가 선택 → 국기·4지선다 검증 → 카운트다운·정답 공개 → 로컬 합성 BGM/효과음 → MP4 → 영어 게시 문구 저장까지 연결했습니다.
제작 중 인터넷, Codex, AI API, TTS, API 키가 필요하지 않습니다.

## Windows에서 실행

1. 무료 **Python 3.12 64비트**를 설치합니다. 최소 3.11이며 공식 설치판의 Tkinter를 사용합니다.
   https://www.python.org/downloads/windows/
2. ZIP을 새 `GeoRush-Generator` 폴더에 풉니다. Brain Blink·왜일까? 설치 폴더에 덮어쓰지 않습니다.
3. `START_HERE.cmd`를 더블클릭합니다. 첫 실행에는 `INSTALL.cmd`가 프로젝트 전용 `.venv`에 의존성을 설치합니다.
   **첫 설치에는 인터넷이 필요합니다. 설치 후 영상 제작은 오프라인입니다.**
4. 한국어 GUI에서 **1 / 3 / 5 / 10편**, 난이도, 문제 수, BGM 볼륨을 선택하고 **영상 제작 시작**을 누릅니다.
5. **출력 폴더 열기**로 영상과 영어 게시 문구를 확인합니다. 기본 위치는 Windows 실제 바탕화면의 `GeoRush_Output`입니다.
   Windows 셸 바탕화면 경로를 사용하므로 OneDrive로 이동한 바탕화면도 탐지합니다.

Windows GUI·CMD·EXE 직접 실행은 **미검증**입니다. Linux 실제 GUI 버튼→MP4→SQLite 통합 테스트를 통과했으며 이 결과를 Windows 성공으로 보고하지 않습니다.
Linux 개발 환경의 Tk9에는 한글 글꼴 외관 문제가 있습니다. 한글 문자열과 GUI 동작은 검사했지만 Linux 화면의 한글 외관은 완성 판정하지 않았습니다.

## 기본 영상

- **1080×1920 원본 프레임**, 30fps, H.264/yuv420p, AAC 스테레오. 저해상도 업스케일을 사용하지 않습니다.
- 기본 **3문제 / 21초 / 630프레임**. 문제당 5초 카운트다운 + 1.5초 정답 공개, 마지막 CTA 1.5초입니다.
- 첫 프레임부터 국기·질문·A/B/C/D 선택지가 표시됩니다.
- 파란색·노란색 GeoRush 디자인, 움직이는 카운트다운, 정답 강조, 짧은 전환, 점수 질문을 사용합니다.
- BGM은 **8% / 10% / 12%** 중 선택하며 기본 10%입니다. 이 수치는 합성 음악 성분의 게인입니다.
  효과음과 합친 뒤 클리핑을 막습니다. 외부 음원이나 저작권 불명 음악을 포함하지 않습니다.
- 1~5문제 선택도 가능하지만 **18~25초 기준은 기본 3문제에 해당**합니다. 각각 8 / 14.5 / 21 / 27.5 / 34초입니다.
- CPU `libx264` 2스레드 인코딩을 사용하며 RTX/CUDA나 Blender는 요구하지 않습니다. RTX 성능을 측정한 것은 아닙니다.

## 국가·정답·중복 검증

MIT `flag-icons`의 고정 커밋에서 가져온 국기 아이콘 **60개**와 동일 코드의 영어 국가명을 포함합니다.
Easy / Normal / Hard 각 20개이며 Mixed는 전체 풀에서 선택합니다. 난이도는 친숙도를 기준으로 나눈 편집 분류입니다.
국기는 원본의 표준 **4:3 아이콘 변형**으로 국가별 공식 제작 비율을 재현한다는 의미가 아닙니다.
자세한 출처·상업적 사용·재배포 조건은 [에셋 라이선스](assets/ASSET_LICENSES.md)를 확인하세요.

- 국가 데이터·출처 해시, ISO 코드↔원본 영어 이름, 국기 파일명·SHA256·이미지 디코딩을 검사합니다.
- 누락·변조된 국기는 선택하지 않습니다. 국가 데이터의 연결 자체가 틀리면 오류로 중단합니다.
- 선택지는 검증된 서로 다른 국가 4개이며 정답은 하나입니다. 정답 위치를 섞습니다.
- 한 영상에서 국가 중복을 막고, SQLite에 기록된 동일 국가 조합은 순서를 바꿔도 재사용하지 않습니다.
- 최근 20개 제작의 국가를 가능하면 피합니다. 풀을 소진하면 국가 재등장은 가능하지만 동일 조합은 계속 차단합니다.
- 이력은 출력 루트의 **`georush_history.sqlite3`**에 독립 저장합니다. 출력 루트를 바꾸거나 이력을 지우면 그 이전 이력과 비교할 수 없습니다.
- FFmpeg·디코딩·오디오·메타데이터 검사가 끝난 뒤에만 성공으로 기록합니다. 한 편 실패 시 다른 편을 계속 제작합니다.

## 저장 파일

```text
바탕화면/GeoRush_Output/
  georush_history.sqlite3
  georush.log
  GeoRush_시각_고유번호/
    video.mp4
    title.txt
    description.txt
    tags.txt
    pinned_comment.txt
    quiz_data.json
    MEDIA_REPORT.json / RENDER_REPORT.json
    original_audio.wav / ffmpeg.log
    inspection/                 # 인코딩 전 검사 이미지
    encoded_inspection/         # 실제 MP4에서 추출한 검사 이미지
```

파일명 충돌을 막기 위해 매번 새 하위 폴더를 만듭니다. 실패 시 `ERROR.txt`와 로그를 남깁니다.
남은 디스크가 256MB 미만이면 제작을 시작하지 않습니다. 외부 BGM 파일을 읽지 않으므로 BGM 누락 문제는 없으며,
내장 합성·오디오 저장에 실패하면 해당 영상은 실패 처리합니다.

## 실제 결과와 테스트

- `samples/GeoRush_Output/`에 서로 다른 **실제 쇼츠 3편**과 필수 게시 문구를 포함합니다.
- `reports/ACTUAL_SAMPLE_QA.json`, `ENCODED_ANSWER_CHECK.json`: 9문제·정답·국기·인코딩 결과.
- `reports/GUI_E2E_REPORT.json`: 모의 객체 없이 GUI 실제 버튼으로 추가 1편을 생성한 Linux 통합 검사.
- `reports/unit_tests_final.log`: 자동 테스트 **32개 통과**, 실패·건너뜀 0개.
- [상세 검증 보고서](TEST_REPORT_KO.md): 실제 검증과 Windows 미검증을 구분합니다.

명령 실행을 원하는 개발자는 다음을 사용할 수 있습니다. 일반 사용자는 GUI만 사용하면 됩니다.

```bat
.venv\Scripts\python main.py --generate 3 --difficulty Mixed --questions 3 --bgm 0.10 --output "D:\GeoRush_Output"
.venv\Scripts\python -m unittest discover -s tests -v
```

FFmpeg는 `GEORUSH_FFMPEG` 직접 지정 → `bin/ffmpeg.exe` → PATH → 설치된 `imageio-ffmpeg`의 로컬 바이너리 순으로 찾습니다.
FFprobe가 없어도 FFmpeg 헤더·전체 프레임 디코딩·오디오 통계로 검사합니다. 제작 중 다운로드하지 않습니다.

## Windows EXE

**이 배포본은 소스+CMD 실행본이며 Windows EXE는 생성·실행하지 못했습니다.** Linux에서 Windows PyInstaller EXE를 검증할 수 없습니다.
Windows에서 `BUILD_EXE.cmd`를 실행하면 무료 PyInstaller를 설치하고 다음 폴더형 EXE 빌드를 시도합니다.

```text
dist/GeoRushGenerator/GeoRushGenerator.exe
```

위 경로는 **빌드 후 예상 위치**이며 이 ZIP에 존재하는 EXE 경로가 아닙니다. 배포 시 해당 폴더 전체가 필요합니다.
빌드 후 GUI에서 3편 제작, 한글·OneDrive 경로, BGM, 실제 MP4 재생을 확인해야 합니다.

## 기존 프로그램 보존

현재 접근 가능한 작업 공간에 Brain Blink·기존 GeoRush 소스가 없어 재사용한 Brain Blink 모듈은 **0개**입니다.
실행 파일 역공학은 하지 않았습니다. GeoRush의 `catalog / quiz / history / audio / render / validation / pipeline / gui / paths`를 새로 구현했습니다.
왜일까? 기존 프로젝트는 수정하지 않았으며, 작업 전후 파일 163개의 해시와 Git 작업 상태가 동일합니다.
기존 프로그램·API 설정·채널 자료를 복사하거나 삭제하지 않습니다. 지도·수도 퀴즈·자동 업로드 기능은 포함하지 않습니다.
