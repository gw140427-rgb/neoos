# NeoOS

Python으로 만든 교육용 셸 OS 시뮬레이터.

## 개요

NeoOS는 메모리 기반의 가상 파일시스템과 명령어 셸을 제공하는 미니 운영체제 시뮬레이터입니다. 실제 OS 동작 원리를 학습하기 위한 교육 목적으로 개발되었습니다.

## 요구사항

- Python 3.10+
- 외부 패키지 불필요 (표준 라이브러리만 사용)

## 실행 방법

```bash
python3 doc_bf43c1cc2757_Neoos.py
```

부팅 후 `neo>` 프롬프트에서 명령어를 입력합니다.

## 명령어 목록

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `help` | 명령어 목록 출력 | `help` |
| `echo` | 텍스트 출력 | `echo 안녕하세요` |
| `time` | 현재 UTC 시간 | `time` |
| `clear` | 화면 정리 | `clear` |
| `exit` | NeoOS 종료 | `exit` |
| `calc` | 계산기 | `calc 2 + 3` |
| `ls` | 파일 목록 | `ls`, `ls 파일명` |
| `touch` | 파일 생성 | `touch new.txt` |
| `cat` | 파일 내용 보기 | `cat new.txt` |
| `write` | 파일 내용 덮어쓰기 | `write file.txt 내용` |
| `append` | 파일 내용 추가 | `append file.txt 추가내용` |
| `rm` | 파일 삭제 | `rm file.txt`, `rm -f file.txt` |
| `install` | 가짜 패키지 설치 | `install 패키지명` |
| `pkgs` | 설치된 패키지 목록 | `pkgs` |
| `pwd` | 현재 경로 | `pwd` |
| `whoami` | 현재 사용자 | `whoami` |
| `uname` | 시스템 정보 | `uname` |
| `history` | 명령어 기록 | `history`, `history 5` |
| `version` | 버전 정보 | `version` |
| `똥` | ??? | `똥` |

## 테스트

```bash
python3 -m unittest test_neoos -v
```

## 라이선스

educational / personal use
