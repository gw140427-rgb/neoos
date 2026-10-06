# AI Room for NeoOS

Termux용 YANGYANG AI 작업실입니다.

## 구성

- `ai-room.sh`: AI 상태/작업실 메뉴
- `install-ai.sh`: Codex + Hermes + OpenClaw 설치
- `backup-safe.sh`: AI 설정/작업 데이터 백업
- `backup-local.sh`: 기존 로컬 백업
- `README.md`: 사용 설명

## 설치

Termux에서:

```bash
bash ~/ai-room/install-ai.sh
```

설치 스크립트는 기존 Node 프로젝트를 삭제하지 않습니다. OpenClaw는 현재 공식 지원 Node 런타임을 자체 설치/관리할 수 있으며, Codex와 Hermes도 공식 설치 경로를 사용합니다.

## 안전 백업

```bash
bash ~/ai-room/backup-safe.sh
```

백업에서 다음과 같은 민감정보는 제외합니다.

- API 키/환경변수 파일
- OAuth/access/refresh token
- 비밀번호/credentials
- 쿠키
- SSH 개인키
- private key/pem
- 명시적인 secret 파일
- 일반적인 session JSON

따라서 복구 후 OpenClaw/Hermes/Codex의 로그인은 다시 해야 할 수 있습니다.

> GitHub 저장소에는 실제 백업 아카이브나 인증정보를 올리지 않습니다.
