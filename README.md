# NeoOS

Python으로 만든 교육용 셸 OS 시뮬레이터 (+ 웹 터미널 VPS).

## 개요

NeoOS는 메모리 기반의 가상 파일시스템과 명령어 셸을 제공하는 미니 운영체제 시뮬레이터입니다. 실제 OS 동작 원리를 학습하기 위한 교육 목적으로 개발되었습니다.

계정은 SQLite(`database.db`)에 **암호화(SHA-256)**로 실제 저장되며, 14세 미만은 부모 동의 후 가입할 수 있습니다. 브라우저에서 접속할 수 있는 웹 터미널(VPS 모드)도 포함되어 있습니다.

## 요구사항

- Python 3.10+
- 외부 패키지 불필요 (표준 라이브러리만 사용: `sqlite3`, `http.server`, `hashlib`)

## 실행 방법

### 1. 로컬 셸 (CLI)

```bash
python3 Neoos.py
```

부팅 후 `neo>` 프롬프트에서 명령어를 입력합니다. (기본 관리자: `admin` / `admin`)

### 2. 웹 터미널 (VPS 모드)

```bash
python3 server.py
```

브라우저에서 `http://localhost:10000` 에 접속합니다.
`PORT` 환경변수로 포트 변경, `NEOOS_DB`로 DB 파일 경로를 바꿀 수 있습니다.

```bash
PORT=8080 NEOOS_DB=/path/to/db.sqlite python3 server.py
```

### 3. Docker

```bash
docker compose up neoos
```

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
| `append` | 파일 내용 추가 (없으면 생성) | `append file.txt 추가내용` |
| `rm` | 파일 삭제 | `rm file.txt`, `rm -f file.txt` |
| `install` | 가짜 패키지 설치 (진행바) | `install 패키지명` |
| `pkgs` | 설치된 패키지 목록 | `pkgs` |
| `pwd` | 현재 경로 | `pwd` |
| `whoami` | 현재 사용자 | `whoami` |
| `uname` | 시스템 정보 | `uname` |
| `history` | 명령어 기록 | `history`, `history 5` |
| `version` | 버전 정보 | `version` |
| `똥` | ??? | `똥` |

### 계정 / 로그인 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `register` | 새 계정 생성 (14세 미만은 부모 동의 필요) | `register user pass 2005 동의 답변` |
| `login` | 로그인 | `login user pass` |
| `logout` | 로그아웃 | `logout` |
| `whoami` | 현재 사용자 | `whoami` |
| `passwd` | 비밀번호 변경 (로그인 중) | `passwd 새비번` |
| `forgot` | 비밀번호 찾기 (회복 질문 답으로 임시 비번 발급) | `forgot user 답변` |
| `resetpw` | 비밀번호 초기화 (관리자 전용) | `resetpw user 새비번` |
| `users` | 사용자 목록 | `users`, `users --all` (admin) |

### 계정 규칙

- 비밀번호는 **평문 저장 금지** — SHA-256 해시로만 저장합니다.
- **만 14세 미만**은 법정대리인(부모) 동의 후 가입할 수 있습니다.
- 웹 터미널은 **세션 토큰(쿠키)** 기반으로, 세션마다 독립된 상태를 유지합니다.

## 웹 터미널 페이지

| 경로 | 내용 |
|------|------|
| `/` | 로그인 / 회원가입 / 웹 터미널 |
| `/terms` | 이용약관 |
| `/privacy` | 개인정보 처리방침 |

## 보안

- 비밀번호 해시 저장 (SHA-256, 솔트 없음 — 교육용 단순화)
- 세션 토큰은 `secrets.token_hex`로 생성
- 쿠키에 `HttpOnly`, `SameSite=Lax` 적용
- `calc`는 AST 기반 안전 계산기 (`eval` 사용 안 함)

## 테스트

```bash
python3 -m unittest test_neoos -v
```

## 라이선스

MIT License - [LICENSE](LICENSE) 참고
