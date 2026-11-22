# GeoRush v1.6.0 — 국기 찾기(Find)·시청자 국가·도전형 제목

근거: Studio 2026-11 (시청 국가 인도네시아·한국·필리핀·우즈베키스탄·미국 순, Shorts 피드 94.9%, 신규 시청자 98%), 조사 탭의 "Find Your Flag", "Only 1% …" 계열 고성과 영상.

- **새 주제 Find (국기 찾기):** 나라 이름을 보여 주고 국기 4개(2x2) 중 맞는 것을 고른다. 오답은 닮은 국기 → 같은 대륙 순. 첫 문제는 우리 시청자 상위 국가(id, kr, ph, in, us, vn, br, my, mx, th) 중 최근에 덜 쓴 것. 한 영상 안의 다른 정답은 오답으로 나오지 않는다. 정답 때 나머지 국기는 어둡게, 정답 칸은 초록 테두리·색종이.
  - GUI "시리즈 주제"에서 Find, CLI `--theme Find`.
- **Mixed(기본) 쇼츠:** 첫 국기 후보에 인도네시아 추가, 중간(Normal) 문제는 절반 확률로 필리핀·베트남·말레이시아·태국(최근에 안 쓴 것).
- **제목:** Mixed 쇼츠는 도전형 제목 — "Only 1 of These 3 Flags Is Hard 😈", "Most People Miss the Last Flag! Can You Get 3/3?" (둘 다 Mixed 구성상 사실). Find 전용 제목 4종.
- **마지막 화면:** "COMMENT YOUR SCORE + WHERE YOU'RE FROM!" (나라 댓글 유도).
- 보류: 순위 공개형(인구 순위 등은 사실 확인용 데이터 출처 필요), Kokoro 영어 음성(Python 3.12 별도 환경이라 EXE 묶기 별도 작업).
- 운영 방침(2026-11-12 사용자): 롱폼 새 업로드 중단, 쇼츠 하루 2편 KST 13:00·19:00, 기존 예약분 이후(11/29~)부터 v1.6.0 영상.

## v1.6.1 — 끝 화면 제거(반복 재생)
- 마지막 3초 "TIME'S UP" 화면 삭제. 쇼츠는 마지막 정답에서 끝나고 첫 국기로 바로 이어진다(16.5초 → 13.5초).
- 점수·나라 댓글 요청("COMMENT YOUR SCORE + WHERE YOU'RE FROM!")은 마지막 정답 화면 아래 노란 띠로 옮김.
- 근거: 28일 통계에서 평균 시청 시간이 영상 길이보다 긴(반복 시청) 유일한 쇼츠가 시청 시간 1위.

## v1.6.2 — 인구 비교 쇼츠, Kokoro 영어 음성, 구독 멘트
- **새 주제 Population:** 국기 4개(나라 이름 표시) 중 인구가 가장 많은 나라 고르기. 정답 때 네 나라 인구(예: 286M)를 보여 줌. 데이터는 세계은행 WDI SP.POP.TOTL(2025, CC BY 4.0)을 assets/country_population.json에 고정해 넣음(실행 중 인터넷 안 씀). 화면 아래 출처 "Population: World Bank (2025)". 1위가 2위보다 쉬움 3배↑, 보통 1.6~3배, 어려움 1.25~1.6배 차이 나는 조합만. 면적은 원본 값(캐나다 등)이 일반 통계와 달라 쓰지 않음.
- **영어 음성:** Kokoro-82M(Apache-2.0, 목소리 af_heart)로 미리 만든 클립 384개(assets/voice, 15MB)를 영상에 섞음 — 문제 시작 멘트(Guess the flag / Find Indonesia / Final flag / Which has the most people?), 정답 국가명, 마지막 "Comment your score, and subscribe for more!". EXE는 Kokoro를 실행하지 않고 파일만 재생. 클립 다시 만들기: Kokoro venv로 tools/make_voice.py.
- **마지막 정답 2.5초 연장(총 16초):** 구독 멘트 자리. 노란 띠 문구 "COMMENT YOUR SCORE + COUNTRY! / LIKE & SUBSCRIBE FOR MORE!". 별도 끝 화면은 여전히 없음(반복 재생 유지).

## v1.6.4 — 첫 화면 도전 문구 돌리기, 나라 묻는 댓글
- Mixed 3문제 쇼츠의 첫 화면 문구가 5종에서 영상마다(국기 조합 기준) 정해짐: CAN YOU GET ALL 3? / 99% MISS THE LAST ONE! / THE LAST FLAG IS HARD! / ONLY EXPERTS GET 3/3! / MOST PEOPLE FAIL #3! — 모두 Mixed 구성(마지막만 Hard)에서 사실. 음성도 같은 문장(Kokoro 클립 4개 추가).
- 고정 댓글 후보에 "점수 + 어느 나라에서 보는지" 묻는 문구 4개 추가(총 12개).
- 개발: tools/make_voice.py 기본 Kokoro 경로 = 바탕화면\뱅으니\Inkmap History\도구_Kokoro, 키를 주면 그 클립만 다시 만듦.

## v1.6.5 — 승인된 디자인(지구본 로고·노란 배너·빨간 배지), 안전 여백, 정답 반짝임
- **새 화면:** 사용자가 고른 시안 그대로 — 위에 지구본 로고·세계지도·비행기, 노란 배너(안 글씨만 바뀜: `FIND MALAYSIA!`, `CAN YOU GET ALL 3?`, `FINAL FLAG!`, `WHICH HAS THE MOST PEOPLE?`), 그 아래 빨간 배지(Find 첫 문제 `90% FAIL!`, 그 외 `ROUND 2 / 3`, 마지막 `FINAL ROUND!`), 파란 네온 흰 카드. 배경은 시안에서 로고·지도 부분만 떼어 `assets/bg_v165.jpg`로 만들었다(`tools/make_bg.py`, 원본 `assets/design/find_mock_v165.webp`). 배너·배지·카드는 코드로 그려 글씨를 마음대로 바꿀 수 있다. 헤더 "QUESTION 1/3" 칸은 배지로 대체.
- **안전 여백(쇼츠 화면 버튼·설명이 덮는 곳):** 보기 카드를 오른쪽 끝 930px 안으로(전엔 1004px), 아래쪽 1580px 위로. 화면 맨 아래 `@GeoRushGames / 3 rounds. One challenge.`는 유튜브 설명에 가려 보이지 않아 삭제. 마지막 정답의 노란 "COMMENT YOUR SCORE + COUNTRY! / LIKE & SUBSCRIBE" 띠를 1620~1820px에서 위로 올림(전엔 아래 절반이 가려짐). 인구 퀴즈의 출처 한 줄은 1590px로 옮김(보이도록 유지).
- **Find는 정답 카드(FLAG A~D)를 없앰:** 글자가 이미 국기 칸에 있고 정답은 "CORRECT ANSWER D · Malaysia"로 보여 준다. 그 자리를 4국기 칸을 키우는 데 씀. 1문제 국기·Population은 보기 카드(국가 이름)가 필요해서 유지(카드 높이 130→104).
- **정답 순간:** 맞는 칸/카드가 0.3초 동안 5%(2.5%) 커지며 흰빛이 퍼졌다 사라짐(국소 효과, 화면 전체 번쩍임 아님). 기존 상승 화음·색종이·초록 테두리 유지.
- 1문제 국기 크기: 83%→73% 화면 너비(로고 자리를 위해). 시간(4.5초/문제, 16초)과 음성은 그대로.

## v1.6.6 — 마지막 문구 시험(친구 태그·좋아요), 단 한 가지 변경
- 근거(2026-11-22, 쇼츠 41편): 거의 모든 영상이 조회수 1,000~1,500에서 멈추고(중간값 1,100), 끝까지 보는 정도는 이미 좋은데(계속 시청함 53~61%, 평균 조회율 75~140%) **공유는 영상당 0~4회, 좋아요는 조회수의 약 1%**. 그래서 마지막 정답의 노란 띠를 반으로 나눠 시험한다.
  - A(기존): `COMMENT YOUR SCORE + COUNTRY!` / `LIKE & SUBSCRIBE FOR MORE!` + 음성 "Comment your score, and subscribe for more!"
  - B(시험): `TAG A FRIEND WHO CAN'T GET 3/3!` / `LIKE & SUBSCRIBE IF YOU GOT 3/3!` + 음성 "Tag a friend who can't get three!"(Kokoro, assets/voice/outro_tag.wav 1.47초)
- 어느 쪽인지는 퀴즈의 국가 코드로 정해진다(`georush/cta.py`, 순서와 무관·항상 같은 결과). 그래서 **올린 뒤에도 업로드 기록의 `countries`로 A/B를 다시 계산**할 수 있다: `cta.variant(codes)` = sha256(정렬한 코드를 ','로 이음) 둘째 바이트가 홀수면 B. B는 3문제 쇼츠에만(음성이 "three"라서).
- 비교 지표: 영상별 공유·좋아요·댓글·구독을 조회수로 나눈 비율(분석 API). 영상 수가 적어 큰 차이만 보인다(주 14편이면 한쪽 7편).
