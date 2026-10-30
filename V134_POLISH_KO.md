# GeoRush v1.3.4 — 마무리 다듬기

영상 디자인·문제 구성·롱폼·이력 구조는 그대로이고, 아래 네 가지만 바뀌었습니다.

1. **쇼츠 CTA 3초.** 마지막 "점수를 댓글로 남겨 주세요" 화면이 1.5초에서 3초로 늘었습니다. 쇼츠는 21초에서 **22.5초**(675프레임)가 됩니다. 문제당 6.5초(카운트다운 5초 + 정답 1.5초)는 그대로입니다.
2. **쇼츠 설명·태그·고정 댓글 다양화.** 영상마다 소개 문장, 안내 문장, 구독 문구, 태그(기본 5개 + 무작위 4개 + Shorts), 고정 댓글이 달라집니다. 같은 영상은 항상 같은 문구가 나옵니다. `#GeoRush #GuessTheFlag #FlagQuiz #GeographyQuiz #Shorts` 해시태그, `@GeoRushGames` 언급, 점수를 묻는 문장은 모든 변형에 들어 있고 국가 이름·정답은 들어가지 않습니다. 롱폼 설명(챕터 포함 형식)은 그대로입니다.
3. **화면에 보이는 국가명.** 문제 선택지와 정답 화면에서만 더 익숙한 이름을 씁니다: United States, Czechia, Brunei, Micronesia, DR Congo, Ivory Coast, Cape Verde, Turkey. 국가 데이터·정답 검증·이력은 검증된 원본 이름(예: United States of America, Türkiye)을 그대로 씁니다.
4. **논란이 있는 국기 제외.** 아프가니스탄(공화국 국기와 현 집권 세력 국기가 경쟁)과 시리아(2024~25년 국기 변경, 여전히 논란)는 문제와 선택지에서 빠집니다. 국기 파일과 데이터는 보존합니다. 문제 풀은 188개국(Easy 40 / Normal 59 / Hard 89, 롱폼 Hard 44 / Expert 45)입니다.

변경 파일: `georush/audio.py`, `georush/pipeline.py`, `georush/render.py`, `georush/longform/render.py`, `georush/catalog.py`, `georush/names.py`(신규), `georush/distribution_check.py`. 테스트: `tests/test_polish_v134.py`(신규), `tests/test_catalog_v133.py`, `tests/test_media.py`.
