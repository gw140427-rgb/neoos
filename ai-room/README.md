# AI Room for NeoOS

Termux용 YANGYANG AI 작업실입니다.

## 처음 설치 (Termux)

아래 명령은 **Termux 터미널에서** 실행하세요. 먼저 폴더를 만들고 다운로드한 뒤 실행합니다.

```bash
pkg install -y curl
mkdir -p "$HOME/ai-room"
curl -fL --retry 3 --connect-timeout 15 \
  "https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/ai-room.sh" \
  -o "$HOME/ai-room/ai-room.sh"
bash -n "$HOME/ai-room/ai-room.sh" &&
  bash "$HOME/ai-room/ai-room.sh"
```

위 명령은 작업실 메뉴를 실행합니다. 메뉴에서 `8`을 선택하면 AI 도구 설치/복구를 시작합니다.

## AI 도구만 설치

작업실 메뉴 없이 설치 스크립트를 직접 실행하려면 **Termux에서**:

```bash
mkdir -p "$HOME/ai-room"
curl -fL --retry 3 --connect-timeout 15 \
  "https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/install-ai.sh" \
  -o "$HOME/ai-room/install-ai.sh"
bash -n "$HOME/ai-room/install-ai.sh" &&
  bash "$HOME/ai-room/install-ai.sh"
```

이 저장소에는 `install-all.sh`라는 파일이 없습니다. 실제 AI 도구 설치 파일 이름은 `install-ai.sh`입니다.

## 구성

- `ai-room.sh`: AI 상태/작업실 메뉴
- `install-ai.sh`: Codex + Hermes + OpenClaw 설치
- `backup-safe.sh`: AI 설정/작업 데이터 백업
- `backup-local.sh`: 기존 로컬 백업
- `README.md`: 사용 설명

## NeoOS Super MCP 설치 (Debian/PRoot)

아래 명령은 **Debian 세션 안에서** 실행하세요. 주소 중간에 공백을 넣지 마세요.

```bash
curl -fL --retry 3 --connect-timeout 15 \
  "https://raw.githubusercontent.com/gw140427-rgb/neoos/main/scripts/setup-neoos-super-mcp.sh" \
  -o "$HOME/setup-neoos-super-mcp.sh"
bash -n "$HOME/setup-neoos-super-mcp.sh" &&
  bash "$HOME/setup-neoos-super-mcp.sh"
```

설치 스크립트는 `~/neoos-super-mcp`에 프로젝트가 있거나, Android Download 또는 홈 폴더에 `neoos-super-mcp.zip`이 있는지 확인합니다. 둘 다 없으면 프로젝트를 찾지 못했다는 오류를 냅니다.

## 안전 백업

```bash
bash "$HOME/ai-room/backup-safe.sh"
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
