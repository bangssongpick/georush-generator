# GeoRush v1.2 — 영상 연출 개선

## v1.1에서 바뀐 부분

- 첫 프레임부터 국기와 질문 표시. 국기는 원래 크기의 84%에서 짧게 102.5%까지 커진 뒤 0.65초에 정착합니다. 질문은 8픽셀 이내로 빠르게 정착합니다. 검은 인트로·로고 대기·전역 노출 플래시·화면 흔들림이 없습니다.
- 숫자가 바뀔 때 0.18초 동안 최대 13% 확대하고, 링과 얇은 진행 바를 함께 표시합니다. 마지막 2초는 색상만 따뜻하게 강조합니다.
- 정답 카드는 0.28초 동안 최대 4% 확대하고 테두리를 강조합니다. 초록색 정답·국가 이름·잘못된 선택지는 계속 읽을 수 있으며 다음 문제에서 효과가 초기화됩니다.
- 원래 로컬 합성 엔진에 문제당 1개의 짧은 등장음을 추가했습니다. 정답 음의 게인과 전환 잡음 강도를 낮추고 음의 공격·감쇠를 부드럽게 했습니다. 마지막 BGM 페이드는 0.45초입니다.

## 유지한 부분

문제당 카운트다운 5초, 정답 공개 1.5초, 기본 3문제·21초·630프레임·1080×1920·30fps·H.264/AAC와 BGM 8/10/12%를 유지합니다. Hard에도 같은 5초 제한을 사용합니다.
국기·문제·난이도·정답·이력·중복 방지·메타데이터·출력 처리 코드는 재작성하지 않았습니다. GUI는 버전 표시만 바뀝니다.
사용자 영상 폴더는 여전히 shorts.mp4 / shorts_metadata.txt / shorts_thumbnail.jpg 세 파일입니다. 진단 자료는 내부 데이터 폴더에 보존합니다.

## 검증

기존 40개 테스트를 그대로 유지하고 신규 연출 검사 10개를 추가했습니다.
신규 검사는 첫 프레임 국기·질문, 등장 변화, 객체 경계, 선택지 안정성, 숫자·진행 표시, 정답 유지 시간, 정답 카드 경계, 전환 초기화, 실제 PCM 음향·중복·페이드, 마지막 화면을 확인합니다.

실제 MP4마다 정확한 프레임 0/3/9/21/30/33/75/93/149/151/154/195/629를 추출합니다.
요청한 0·0.3·0.7·1초·중간·종료 직전·정답 직후·다음 문제·끝 직전과 추가 확대 시점을 포함합니다.
인코딩된 프레임을 의도한 프레임과 비교하고, 실제 국기 움직임·정답 초록색 위치·다음 문제의 강조 초기화를 검사합니다. 프레임 시트도 제공합니다.
이 수치 검사는 시청 유지율이나 주관적인 흥미도 합격을 보장하지 않습니다. 실제 음질·모바일 가독성은 사용자가 직접 시청해 확인해야 합니다.

## Windows 배포

압축을 완전히 풀고 START_HERE.cmd 또는 GeoRushGenerator.exe를 실행합니다. Python과 FFmpeg는 포함돼 있으며 _internal 폴더를 함께 보관하세요.
정상 영상 제작에는 Codex·외부 AI 서비스·API·유료 음원이 필요하지 않습니다.
자동 Windows 검증은 EXE GUI에서 3편 배치를 실제 생성하고 영상당 13프레임을 검사합니다. 한글 폴더로 배포본을 옮긴 뒤 1편을 다시 제작합니다.
실제 결과는 동봉 WINDOWS_VALIDATION.json / WINDOWS_RELOCATION_VALIDATION.json과 릴리스 WINDOWS_BUILD_REPORT.json에서 확인하세요.
호스팅 Windows 러너 검증과 Python 미설치 물리 PC·실제 OneDrive 동기화·수동 GUI/음향 검수는 구분합니다.

## 실제 완료 결과

[Windows Actions 성공 실행](https://github.com/bangssongpick/georush-generator/actions/runs/40824517592)에서 기존 40개 및 신규 10개, 총 50개 테스트가 통과했습니다(5.874초).
EXE GUI에서 3편을 배치 생성하고 39개 실제 인코딩 프레임을 검사했습니다. 한글 경로 이동 후 추가 1편·13프레임도 통과했습니다.
3편 모두 21초·630프레임·1080×1920·30fps·H.264/AAC입니다. 내부 SQLite는 서로 다른 4개 성공 기록을 보존했고, 모든 최종 폴더는 정확히 세 파일이며 임시 WAV는 정리됐습니다.
첫 프레임 국기·질문, 등장 움직임, 숫자 확대·진행, 정답 초록색 위치, 다음 문제 초기화를 확인했습니다. Windows 샘플 프레임 시트 3개도 개발자가 시각적으로 검사했습니다.
AAC 디코딩 최대 진폭 -8.574663dBFS, PCM 최대 0.37309·클리핑 0입니다. 8/10/12% 음악 게인·15개 타이머 음·중복 없는 이벤트·페이드는 자동 테스트로 확인했습니다.
인코딩된 프레임과 의도한 프레임의 최소 PSNR은 34.926 / 35.662 / 35.574dB입니다. 이는 영상 정확도 검사이지 시청 유지율 점수가 아닙니다.

[정식 릴리스](https://github.com/bangssongpick/georush-generator/releases/tag/v1.2.0-windows)
[EXE ZIP 다운로드](https://github.com/bangssongpick/georush-generator/releases/download/v1.2.0-windows/GeoRush-v1.2-Windows-EXE.zip)

배포 EXE: 5,326,564 bytes. ZIP: 66,273,444 bytes.
ZIP SHA256: `738ff203495594167d05b0e7f7669defbd6cb0068d0eabc955e5ee026c724be2`.
공개 HTTPS ZIP·샘플3편 다운로드에 성공했고 ZIP SHA256·CRC 및 샘플별 SHA256이 실제 Windows 보고서와 일치했습니다.

연출 변경 파일은 `georush/render.py`, `georush/audio.py`입니다. 신규 `tests/test_presentation_v12.py`, `georush/presentation_review.py`와 기존 distribution_check·build_windows·Actions는 검증·패키징용입니다. GUI와 __init__는 버전 표시만 갱신했습니다.
`quiz.py`, `catalog.py`, `history.py`, `pipeline.py`, `output.py`, `paths.py`, `validation.py`는 v1.1과 바이트 단위로 동일합니다. 기존 40개 테스트 파일도 변경하지 않았습니다.
실행 시 외부 API나 Codex는 사용하지 않습니다. 수동 음질 청취·흥미도·실제 OneDrive 동기화·Python 없는 물리 PC는 추가 검수 대상입니다. 기존 v1.1 릴리스는 보존했습니다.
