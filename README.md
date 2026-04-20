# NeoOS

NeoOS는 교육용으로 만든 **미니 터미널 운영체제 시뮬레이터**입니다.

## 목표
- 간단한 커맨드 인터프리터 구조 이해
- 명령어 레지스트리 기반 확장
- 테스트 가능한 구조 유지

## 빠른 시작
```bash
python3 neoos.py
```

## 지원 명령어
- `help`: 명령어 목록 표시
- `echo <text>`: 텍스트 출력
- `time`: 현재 UTC 시간 출력
- `clear`: 화면 정리(ANSI clear)
- `exit`: 셸 종료

## 테스트
```bash
python3 -m unittest -v
```
