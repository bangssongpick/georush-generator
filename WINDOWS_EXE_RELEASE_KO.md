# GeoRush Windows EXE 정식 배포 검증

- [다운로드](https://github.com/bangssongpick/georush-generator/releases/download/v1.0.0-windows/GeoRush-v1.0-Windows-EXE.zip)
- [릴리스](https://github.com/bangssongpick/georush-generator/releases/tag/v1.0.0-windows)
- [성공한 Windows 실행](https://github.com/bangssongpick/georush-generator/actions/runs/40800479659)
- [실제 빌드 JSON](https://github.com/bangssongpick/georush-generator/releases/download/v1.0.0-windows/WINDOWS_BUILD_REPORT.json)

## 실제 결과

Windows 3.12에서 기존 32개 테스트가 3.208초에 통과했습니다. 첫 실행에서 확인한 SQLite 미종료 파일 잠금과 Git 줄바꿈 변환의 에셋 해시 오류를 수정했으며 테스트나 에셋 해시를 우회하지 않았습니다.

실제 EXE는 GUI 버튼을 통해 21초·630프레임·1080×1920·30fps·H.264/AAC 영상을 만들었습니다. 메타데이터 4종·정답·국기·SQLite 이력·한글 경로·내장 FFmpeg·내장 Python을 검사했습니다.
폴더를 한글 임시 경로로 복사한 뒤 같은 데이터베이스를 사용해 다시 제작했고 통과했습니다. GUI heartbeat는 각각 96/104회였고 실제 기본 글꼴은 Malgun Gothic입니다.
두 실행의 MP4 전체 디코딩·스테레오·무음 아님·최대 진폭 0dBFS 미만 검사를 통과했습니다. 자동 검사는 사람이 음질을 듣고 판단한 결과가 아닙니다.

| 파일 | 크기 |
| --- | ---: |
| GeoRushGenerator.exe | 5,313,462 bytes |
| GeoRush-v1.0-Windows-EXE.zip | 66,253,876 bytes |

ZIP SHA256:

```text
1080d5be12a2a237de143d4205a17979081039093f30ba5445e9948d1e9b1b91
```

공개 HTTPS에서 ZIP을 실제로 다시 다운로드했고 HTTP 200·SHA256 일치·CRC 통과와 EXE의 PE 헤더, Python DLL·FFmpeg·국기·글꼴·검증 JSON 포함을 확인했습니다. Release Assets에 직접 첨부됐습니다.

## 추가 확인할 한계

Windows 호스팅 러너에는 Python이 설치되어 있지만 EXE 검증은 Python·시스템 FFmpeg를 PATH에서 제외한 상태로 수행했습니다. Python 미설치 물리 PC 실행과 OS별 권한·GUI 외관·사람이 듣는 음질은 사용자 PC 검수 항목입니다. 실제 OneDrive 클라우드 동기화는 검사하지 않았습니다.

압축을 완전히 풀고 전체 GeoRushGenerator 폴더를 보관한 뒤 START_HERE.cmd 또는 EXE를 실행하세요. _internal 폴더가 필수입니다. 최초 테스트는 1편·Mixed·3문제·BGM10%를 권장합니다.
