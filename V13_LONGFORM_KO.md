# GeoRush v1.3 — Shorts + Longform

ZIP을 완전히 풀고 `START_HERE.cmd` 또는 `GeoRushGenerator.exe`를 실행하세요.
Python, FFmpeg, API 키, 유료 서비스는 필요하지 않습니다. `_internal` 폴더를 함께 보관하세요.
기존 v1.2를 덮어쓰기보다 별도 폴더에 압축을 풀어 이전 실행본을 보관하세요.

## 사용 방법

1. **영상 종류**에서 Shorts 또는 Longform을 선택합니다. 기본 모드는 기존 Shorts입니다.
2. Shorts는 기존 설정을 사용합니다. Longform은 1/2/3편, 20/30/40문제 중 선택합니다. 기본값은 40문제, Mixed입니다.
3. BGM 8/10/12%와 출력 폴더를 확인하고 **영상 제작 시작**을 누릅니다.
4. 작업 중에는 진행률이 표시됩니다. 완료 후 **출력 폴더 열기**를 누릅니다.

Shorts 설정과 Longform 설정은 별도로 유지되며 모드 전환은 기존 설정을 덮어쓰지 않습니다.
업로드는 직접 진행합니다. 자동 업로드·예약 게시 기능은 없습니다.
권장 채널 운영(KST): Shorts 매일 09:00 / Longform 수·토 21:00.

## 롱폼 길이·화질

기본 1920×1080, 30fps, H.264/AAC. 세로 영상의 확대가 아닌 별도 가로 레이아웃입니다.
5초 인트로 + 문제당 8초 카운트다운·2초 정답 + 난이도 전환 3회×3초 + 10초 엔딩입니다.

| 문제 수 | 난이도별 문제 수 Easy/Normal/Hard/Expert | 실제 계획 길이 |
|---|---|---|
|20|5/5/5/5|3분 44초|
|30|8/8/7/7|5분 24초|
|40 (기본)|10/10/10/10|7분 04초|

목표 6~8분은 기본 40문제에 해당합니다. 20/30문제를 억지로 늘리지 않습니다.
각 문제 국기와 4개 선택지가 처음부터 보이며 카운트다운 8초를 온전히 제공합니다.
정답 위치는 A/B/C/D별로 최대 1개 차이로 균형을 맞춥니다.

## 난이도 기준

원본 60개 국기·국가 데이터는 변경하지 않았습니다. 기존 Easy 20 / Normal 20 / Hard 20입니다.
롱폼에서만 Hard 20개를 다음 편집 그룹으로 구분합니다.

- Hard: Ecuador, Bolivia, Peru, Chile, Colombia, Costa Rica, Panama, Cuba, Jamaica, Uruguay.
- Expert: Kazakhstan, Uzbekistan, Georgia, Armenia, Azerbaijan, Albania, Croatia, Serbia, Bosnia and Herzegovina, Slovakia.

Easy/Normal은 기존 분류를 그대로 사용합니다. Hard/Expert는 지역별 친숙도·문양·유사 삼색기 등을 고려한 **편집상 진행 단계**입니다.
실제 플레이어 정답률로 검증한 객관적 난이도가 아니며 시청자에 따라 체감이 다릅니다. 설명문에도 명시합니다.
국기 부족·해시 불일치·선택지 오류·중복 국가 발생 시 제작을 차단합니다.

## 출력과 이력

Shorts 영상 폴더는 기존과 동일하게 `shorts.mp4`, `shorts_metadata.txt`, `shorts_thumbnail.jpg`만 포함합니다.
Longform 영상 폴더에는 `longform.mp4`, `longform_metadata.txt`, `longform_thumbnail.jpg`만 포함합니다.
썸네일은 실제 영상에 등장하는 국기 5개로 만듭니다. 국가명과 정답 위치는 썸네일·메타데이터에 미리 노출하지 않습니다.
문제 수·설명·점수·챕터는 실제 타임라인으로 계산합니다. YouTube에서 챕터가 표시되는지는 플랫폼 조건에 따릅니다.

기본 출력은 Windows 실제 바탕화면의 `GeoRush_Output`이며 Windows 셸이 반환하는 OneDrive 바탕화면 경로도 사용합니다.
기존 SQLite의 테이블이나 레코드를 변경하는 마이그레이션은 없습니다. 신규 롱폼은 같은 이력에 `mode=Longform`과 별도 순서 서명을 기록합니다.
기존 쇼츠 이력은 보존됩니다. 동일한 롱폼 국가 순서는 정답 위치만 바꿔 재생성할 수 없습니다.
기존 실패·실행 중 예약도 건너뛰므로 강제 종료 후 재실행은 새 작업으로 진행합니다. 중단 지점 이어 렌더링 기능은 없습니다.

내부 이력·로그·실패 진단: `%LOCALAPPDATA%\GeoRush`.
성공 후 임시 WAV·중간 MP4·PNG를 정리합니다. 실패 자료는 내부 `debug`에 보존하고 최종 영상 폴더로 공개하지 않습니다.
출력 드라이브와 내부 데이터 드라이브에 최소 1GB 여유 공간을 확보하세요. 여러 편 제작 시 추가 공간이 필요합니다.
영상 전체를 메모리에 저장하지 않고 문제별 PNG 키프레임/영상과 1초 PCM 청크를 처리합니다.

## 검증과 한계

`WINDOWS_BUILD_REPORT.json` 및 동봉된 Windows 검증 JSON에 실제 실행 결과를 기록합니다.
배포 워크플로는 기존 50개 회귀 테스트와 신규 Longform 테스트, 동결 EXE의 Shorts GUI 제작,
20문제·40문제 Longform GUI 제작, 전체 MP4 디코딩·음향·실제 프레임 대응 검사, 한글 경로 이동 후 Shorts 재실행을 수행합니다.
모두 통과해야 새 ZIP과 릴리스를 게시합니다. 실패 시 성공한 배포로 표시하지 않습니다.

Windows 호스팅 러너는 Windows 11 실물 PC와 다릅니다. 실제 OneDrive 동기화, 수동 청취, 모바일 가독성·시청 지속률,
사용자 PC의 보안 프로그램/SmartScreen 동작은 별도 확인이 필요합니다. EXE는 코드 서명되지 않았습니다.
오디오는 기존 GeoRush의 직접 합성한 음계·효과음 방식을 재사용하며 외부 음악·TTS를 사용하지 않습니다.

## 소스와 빌드

`BUILD_EXE.cmd`는 Windows Python 3.12 환경에서 기존 무료 의존성/PyInstaller로 EXE를 만들고 실제 검증 후 ZIP을 생성합니다.
소스 실행: `START_HERE.cmd`. 개발자 CLI 예: `python main.py --mode Longform --generate 1 --questions 40`.
릴리스 EXE를 사용하는 일반 사용자는 Python을 설치하지 않습니다.

변경 파일: `georush/longform/` 독립 모듈, `gui.py` 모드 연결, `main.py` 실행 분기,
`validation.py`의 선택적 해상도/검증 제한 인자(기본 Shorts 값 동일), 버전 표시, Windows 빌드/배포와 신규 테스트·안내 문서.
기존 Shorts `quiz.py`, `catalog.py`, `history.py`, `pipeline.py`, `render.py`, `audio.py`, `output.py`, `paths.py`와 원본 에셋은 보존합니다.
