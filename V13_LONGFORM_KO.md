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

## 실제 배포 검증 결과 — 2026-10-29 KST

[Windows EXE ZIP 다운로드](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.0-windows/GeoRush-v1.3-Windows-EXE.zip)

[릴리스](https://github.com/bangssongpick/georush-generator/releases/tag/v1.3.0-windows) · [Windows Actions](https://github.com/bangssongpick/georush-generator/actions/runs/40829705207) · [전체 Windows 검증 JSON](reports/V13_WINDOWS_BUILD_REPORT.json) · [공개 다운로드 재검증](reports/V13_RELEASE_VERIFICATION.json)

| 항목 | 실제 결과 |
|---|---|
|Windows 자동 테스트|68개 통과, 실패/건너뜀 0개. 기존 50개 테스트 파일 원본 유지 + 신규 18개|
|Shorts GUI 버튼 → MP4|21초, 630프레임, 1080×1920/30fps/H.264/AAC, 전체 디코딩 통과|
|20문제 Longform GUI 버튼 → MP4|224초(3:44), 6,720프레임, 1920×1080/30fps/H.264/AAC|
|40문제 Longform GUI 버튼 → MP4|424초(7:04), 12,720프레임, 1920×1080/30fps/H.264/AAC|
|20문제 실제 프레임 대응 검사|66프레임, 모든 국기 등장·정답 공개 포함, 최소 PSNR 33.319dB|
|40문제 실제 프레임 대응 검사|126프레임, 모든 국기 등장·정답 공개 포함, 최소 PSNR 33.315dB|
|국가·정답|영상 내 국가 중복 0개. 20문제 정답 위치 A/B/C/D 각 5개, 40문제 각 10개|
|카운트다운·공개|각 문제 8초/2초. 음향 이벤트와 화면이 같은 타임라인 사용|
|음향|20문제 AAC 피크 −11.616dBFS, 40문제 −11.609dBFS. 원본 PCM 클리핑 0개, 비무음·종료 페이드 검사|
|최종 출력|모든 성공 영상 폴더에 지정된 MP4/TXT/JPG 3개만 존재|
|SQLite|이전 Shorts 및 앞선 Longform 이력 보존 검사 통과|
|응답성|실제 Tk 이벤트 루프 동작. 20문제 983회, 40문제 1,831회 heartbeat 기록|
|한글 경로|한글 OneDrive 유사 출력 경로와 앱 폴더 이동 후 Shorts 재제작 통과|
|Windows 렌더 소요|20문제 렌더 97.812초 / GUI+검증 114.203초. 40문제 렌더 182.578초 / GUI+검증 212.438초. 호스팅 러너 결과이며 사용자 PC 성능 보장은 아님|
|공개 다운로드|ZIP·샘플 HTTP 200. 다운로드한 MP4 3개 전체 영상/오디오 재디코딩 통과|
|ZIP|66,326,451 bytes, CRC 통과, Windows 빌드 SHA256과 일치|
|EXE|5,365,820 bytes. Python/FFmpeg 경로 제외 후 번들 리소스 사용 확인|

ZIP SHA256:

`74261912e1a3cef9c1ef15cfbaa1e98fd843eb9bc0c69bfb2428ac23c6588cdf`

실제 Windows EXE 샘플:

- [20문제 영상](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.0-windows/GeoRush-v1.3-Longform-20.mp4) · [프레임 검수 이미지](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.0-windows/GeoRush-v1.3-Longform-20-frames.jpg)
- [40문제 영상](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.0-windows/GeoRush-v1.3-Longform-40.mp4) · [프레임 검수 이미지](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.0-windows/GeoRush-v1.3-Longform-40-frames.jpg)
- [Shorts 회귀 검증 영상](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.0-windows/GeoRush-v1.3-Shorts-sample.mp4)

Linux에서도 별도의 실제 20문제 영상 1편을 생성해 224초/6,720프레임, 전체 디코딩 및 66프레임 검사를 통과했습니다.
기존 왜일까? 보호 대상 파일 163개 해시가 일치했습니다. Brain Blink·Oddly Sharp 등 타 저장소 수정 없음.
기존 v1.2/v1.1/v1.0 릴리스는 보존했습니다.

남은 미검증: 30문제 실제 MP4(문제 생성/배분/타임라인 단위 테스트는 통과), Windows 11 실물 PC,
실제 OneDrive 클라우드 동기화, 수동 GUI 마우스 조작·수동 청취·시청 지속률.
러너 GUI 검증은 실제 Tk 제작 버튼을 프로그램으로 invoke하고 실제 워커·인코더를 실행한 것입니다. 렌더러를 모의 객체로 대체하지 않았습니다.
현재 자동 검사에서 발견된 미해결 오류는 없습니다.
