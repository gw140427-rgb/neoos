# NeoOS

NeoOS 저장소는 현재 **Podroid의 Alpine Linux에서 Docker로 Debian Linux 컨테이너를 실행하는 용도**로 정리되어 있습니다.

## 현재 구조

    Podroid Alpine Linux
    └── Docker
        └── neoos-linux
            └── Debian Linux

- Podroid Alpine Linux: Docker를 실행하는 호스트
- neoos-linux: Debian Bookworm 기반 Linux 컨테이너
- 현재 구성에서는 NeoOS 웹 서버, Vercel 배포, Windows 컨테이너를 사용하지 않습니다.
- Debian은 Podroid에 직접 설치하지 않고 Docker 컨테이너로 실행합니다.

## Podroid에서 실행하는 방법

### 1. 저장소 받기

    git clone https://github.com/gw140427-rgb/neoos.git
    cd neoos

이미 클론해 둔 경우에는 최신 변경사항을 먼저 받습니다.

    cd ~/neoos
    git pull

### 2. Debian Linux 컨테이너 빌드 및 실행

    docker compose up -d --build

### 3. 실행 상태 확인

    docker compose ps

neoos-linux 컨테이너가 실행 중이면 정상입니다.

### 4. Debian Linux 접속

    docker exec -it neoos-linux /bin/bash

접속하면 Debian Linux 셸에서 명령어를 사용할 수 있습니다.

    cat /etc/os-release
    uname -a
    pwd
    ls

나가려면:

    exit

## 중요한 점

현재 compose.yaml은 **Debian Linux 컨테이너만 실행하도록 구성**되어 있습니다.

따라서 다음과 같은 예전 방식은 현재 사용하지 않습니다.

- NeoOS 웹 터미널
- Vercel 배포
- Windows 컨테이너
- docker compose up neoos
- http://127.0.0.1:10000 웹 접속

현재 필요한 명령은 아래 4개입니다.

    cd ~/neoos
    git pull
    docker compose up -d --build
    docker exec -it neoos-linux /bin/bash

## 컨테이너 구성

현재 Debian 컨테이너에는 다음과 같은 제한이 적용되어 있습니다.

- Debian Bookworm Slim
- Bash
- Python 3
- 홈 디렉터리 영속 볼륨
- 읽기 전용 루트 파일시스템
- 임시 /tmp, /run
- CPU 제한
- 메모리 제한
- 프로세스 수 제한
- 추가 Linux capability 제거
- no-new-privileges 적용

따라서 일반적인 Docker 컨테이너보다 제한된 환경입니다.

## 저장소의 주요 파일

- compose.yaml — Podroid용 Debian Linux 컨테이너 구성
- linux/Dockerfile — Debian 컨테이너 이미지 구성
- linux/bridge.py — 내부 Linux 브리지
- Neoos.py — 기존 NeoOS CLI 코드
- installer.py — 기존 NeoOS 설치 관련 코드
- test_neoos.py — 기존 NeoOS 테스트
- scripts/ — 관련 설치 스크립트

현재 Podroid에서 실제로 사용하는 핵심 구성은 compose.yaml과 linux/입니다.

## 라이선스

MIT License - [LICENSE](LICENSE) 참고
