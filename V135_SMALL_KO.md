# GeoRush v1.3.5 — 작은 다듬기

v1.3.4와 영상 구성·문제·국기·쇼츠 결과는 같고, 아래만 바뀌었습니다.

1. **GUI 창 제목.** 이제 실제 버전(`GeoRush Generator v1.3.5`)이 표시됩니다. 이전에는 "v1.3"으로 고정돼 있었습니다. "첫 설치 시 라이브러리 다운로드가 필요합니다"라는 오래된 안내는 "Python과 FFmpeg가 포함돼 있어 별도 설치가 필요 없습니다"로 바꿨습니다.
2. **롱폼 설명·태그·고정 댓글 다양화.** 영상마다 소개 문장, 본문, 규칙 설명, 마무리 문구, 구독 문구, 태그(기본 4개 + 무작위 4개), 고정 댓글이 달라집니다(같은 영상은 항상 같은 문구).
   - 한 번에 복사하는 `[설명]` 구조는 그대로입니다: 소개 → 구독 문구 → `CHAPTERS`(실제 타임라인 시각) → 해시태그 `#GeoRush #FlagQuiz #GeographyQuiz #GuessTheFlag`.
   - 규칙의 실제 시간(질문당 8초 카운트다운, 2초 정답 공개)과 "난이도는 편집 기준" 안내는 모든 변형에 들어 있고, 국가 이름·정답은 들어가지 않습니다.
   - 문구 풀은 `georush/textvariants.py`에 모았습니다. 쇼츠 문구는 기존과 한 바이트도 다르지 않습니다(480개 파일 비교).

변경 파일: `georush/gui.py`, `georush/longform/output.py`, `georush/pipeline.py`(문구를 새 모듈로 옮김), `georush/textvariants.py`(신규), `georush/__init__.py`. 테스트: `tests/test_small_v135.py`(신규), `tests/test_longform_metadata_v131.py`(정확한 문장 비교 → 구조 검사).
