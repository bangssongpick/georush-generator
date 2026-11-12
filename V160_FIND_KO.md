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
