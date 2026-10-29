# GeoRush v1.3.1 — 롱폼 메타데이터 최소 패치

새로 제작하는 `longform_metadata.txt`에서 `[설명]`만 복사하면 영상 소개·구독 유도·챕터·해시태그가 모두 포함됩니다.

출력 순서:

1. `[제목]`
2. `[설명]` — 본문, 구독 유도, `CHAPTERS`, 실제 타임스탬프, 해시태그
3. `[고정 댓글]`
4. `[태그]`
5. `[카테고리]`

별도의 `[챕터]` 항목을 생성하지 않습니다. 타임스탬프는 기존 영상 타임라인에서 계산합니다.
기존 Shorts 메타데이터·렌더링·국기 데이터·GUI·SQLite·최종 파일 3개 구조는 변경하지 않았습니다.
기존에 생성한 영상 폴더와 메타데이터 파일은 자동 수정하지 않습니다.

ZIP 전체를 별도 폴더에 풀고 `START_HERE.cmd` 또는 `GeoRushGenerator.exe`를 실행하세요.
Python·FFmpeg 별도 설치는 필요 없습니다. `_internal` 폴더를 함께 보관하세요.
기본 GUI와 화면 제목은 기존 v1.3 그대로 유지합니다. 상세 사용 방법은 `V13_LONGFORM_KO.md`를 참고하세요.

20·30·40문제의 필드 순서·설명 전체 복사·챕터 시간 및 타임라인 변경 반영을 자동 검사합니다.
Windows 빌드는 기존 EXE GUI 제작·전체 디코딩·한글 경로 이동 검증을 그대로 수행합니다.
실제 결과는 릴리스에 첨부한 `WINDOWS_BUILD_REPORT.json`과 ZIP에 동봉된 Windows 검증 JSON을 확인하세요.
Windows 11 실물 PC·실제 OneDrive 동기화·수동 청취는 사용자 환경에서 확인해야 합니다.

## 실제 검증·배포 결과

- Linux·Windows 자동 테스트 각각 72개 통과. 20·30·40문제 설명/챕터, 필드 순서, 타임라인 변경 반영 검사 통과.
- 실제 Windows EXE GUI에서 Shorts 및 20·40문제 Longform 생성·전체 디코딩·최종 파일 3개 검사 통과.
- Windows에서 생성한 20·40문제 메타데이터를 공개 HTTPS로 다시 받아 `[설명]` 안의 챕터가 실제 타임라인과 일치하고, 별도 `[챕터]`가 없음을 확인.
- GUI·Shorts 메타데이터·렌더링·국기·SQLite 관련 기존 코드 보존. 한글 경로 이동 후 Shorts 재제작 통과.
- ZIP 66,328,776 bytes / EXE 5,365,822 bytes. 공개 다운로드 HTTP 200, ZIP CRC 및 SHA256 일치.
- 기존 v1.3.0-windows 릴리스 보존.

[Windows EXE ZIP 다운로드](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.1-windows/GeoRush-v1.3.1-Windows-EXE.zip)

[릴리스](https://github.com/bangssongpick/georush-generator/releases/tag/v1.3.1-windows) · [Windows Actions](https://github.com/bangssongpick/georush-generator/actions/runs/40833796301) · [실제 Windows 메타데이터 예시](https://github.com/bangssongpick/georush-generator/releases/download/v1.3.1-windows/GeoRush-v1.3.1-Longform-20-metadata.txt) · [검증 보고서](reports/V131_RELEASE_VERIFICATION.json)

SHA256: `1c78a0390add56c0612eaa5baa10ea04178bfa88b1bf7aa72993abf11bcf3718`

실제 동작 패치는 `georush/longform/output.py`의 메타데이터 문자열 구성뿐입니다.
그 외 변경은 버전/배포 파일명·검사·사용 안내입니다. 기존 GUI 화면 제목은 그대로 유지합니다.
Windows 11 실물 PC는 직접 검증하지 않았습니다. 30문제는 메타데이터 단위 테스트를 수행했고 새 MP4를 렌더하지 않았습니다.
