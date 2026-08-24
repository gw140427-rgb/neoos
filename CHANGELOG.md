# Changelog

## v0.4.3 Beta - 2026-08-24
- 보안: `calc`의 `eval` 제거 → AST 기반 안전 계산기로 교체 (지수 연산으로 인한 DoS 차단)
- 개선: Ctrl+C(KeyboardInterrupt) 입력 시 트레이스백 없이 깔끔하게 종료
- 개선: `append`가 파일이 없으면 새로 생성 (셸 관례에 맞게 통일)
- 수정: `cat`이 파일 내용과 "파일 없음" 오류 메시지를 구분하도록 변경
- 정리: 레포에서 다른 프로젝트 유물 제거 (`Dockerfile1`, `agent.yaml`, `Md`)
- 정리: dockurr/windows compose 파일을 `docker-compose.yml`로 분리, RDP 포트 로컬 바인딩
- CI: 실제 Dockerfile 추가로 Docker Image CI 복구, 유닛 테스트 워크플로우 추가
- 테스트: `test_neoos.py` 유닛 테스트 추가
- 문서: README 실행 명령 정정, MIT LICENSE 추가

## v0.4.2 Beta - 2026-07-30
- 개선: help 출력 개선 (버전, 사용 예시 추가)
- 추가: `version` 명령 추가 (NeoOS v0.4.2 Beta)
- 개선: 전역 예외 처리 추가 — 명령 실행 중 예외가 발생해도 셸이 종료되지 않음
- 개선: 파일 관련 명령 개선
  - `ls`: 정렬된 목록, 파일 크기 표시, 파일 미리보기
  - `touch`: 기존 파일을 덮어쓰지 않고 존재 알림
  - `write`: 기존 동작(덮어쓰기) 유지
  - `append`: 기존 내용이 있을 경우 줄바꿈을 삽입하여 추가
  - `rm`: `-f` 간단 옵션 지원
- 문서: README.md 업데이트
- 버그 수정: 일부 명령 실행 중 발생할 수 있는 셸 크래시 방지
