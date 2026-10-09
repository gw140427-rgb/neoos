#!/usr/bin/env bash
set -u
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

BASE="$HOME/ai-room"
mkdir -p "$BASE"

echo "🤖 NeoOS AI 통합 설치"
echo "환경: $(uname -s) / $(uname -m)"
echo "⚠️ 기존 Node/OpenClaw/Hermes/Codex 설정은 삭제하지 않습니다."
echo "⚠️ 설치 과정은 네트워크와 저장 공간을 사용하며 일부 도구는 별도 로그인/설정이 필요합니다."

install_base_packages() {
  # Use Termux pkg only inside the real Termux host. Debian PRoot can inherit
  # a "pkg" command from PATH, but Termux refuses to run it as root.
  if [[ "${PREFIX:-}" == *"/com.termux/files/usr" ]] && command -v pkg >/dev/null 2>&1; then
    echo "패키지 관리자: Termux pkg"
    pkg update && pkg install -y git curl python nodejs openssl
  elif command -v apt-get >/dev/null 2>&1; then
    echo "패키지 관리자: Debian/Ubuntu apt-get"
    if [ "$(id -u)" -eq 0 ]; then
      APT=(apt-get)
    elif command -v sudo >/dev/null 2>&1; then
      APT=(sudo apt-get)
    else
      echo "오류: Debian/Ubuntu에서 패키지를 설치하려면 root 또는 sudo 권한이 필요합니다." >&2
      return 1
    fi
    "${APT[@]}" update &&
      DEBIAN_FRONTEND=noninteractive "${APT[@]}" install -y \
        git curl python3 python-is-python3 python3-venv python3-pip \
        nodejs npm openssl ca-certificates unzip
  elif command -v pkg >/dev/null 2>&1; then
    echo "오류: 'pkg' 명령은 있지만 현재 환경이 실제 Termux가 아닙니다." >&2
    echo "Debian/Ubuntu에서는 apt-get이 필요합니다." >&2
    return 1
  else
    echo "오류: 지원되는 패키지 관리자를 찾지 못했습니다 (Termux pkg / apt-get)." >&2
    return 1
  fi
}

# Download to a temporary file first, so failed downloads never leave a partial script.
download_file() {
  local url="$1" dest="$2" tmp
  mkdir -p "$(dirname "$dest")" || return 1
  tmp="$(mktemp "${dest}.tmp.XXXXXX")" || return 1
  if curl -fL --retry 3 --connect-timeout 15 "$url" -o "$tmp"; then
    if [ ! -s "$tmp" ]; then
      echo "⚠️ 빈 파일 다운로드: $url" >&2
      rm -f "$tmp"
      return 1
    fi
    if mv -f "$tmp" "$dest"; then
      return 0
    fi
  fi
  echo "⚠️ 다운로드/저장 실패: $dest (저장 공간과 권한을 확인하세요)" >&2
  rm -f "$tmp"
  return 1
}

echo "== 기본 도구 =="
if ! install_base_packages; then
  echo "❌ 기본 도구 설치에 실패했습니다. 위의 오류를 확인하세요." >&2
  exit 1
fi

echo "== ai-room =="
download_file https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/ai-room.sh "$BASE/ai-room.sh" || echo "⚠️ ai-room 다운로드 실패"
chmod +x "$BASE/ai-room.sh" 2>/dev/null || true

echo "== 안전 백업 기능 =="
download_file https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/backup-safe.sh "$BASE/backup-safe.sh" || echo "⚠️ backup-safe 다운로드 실패"
chmod +x "$BASE/backup-safe.sh" 2>/dev/null || true

mkdir -p "$HOME/bin"
cat > "$HOME/bin/ai-room" <<'WRAP'
#!/usr/bin/env bash
exec "$HOME/ai-room/ai-room.sh" "$@"
WRAP
chmod +x "$HOME/bin/ai-room"

cat > "$HOME/bin/ai-backup" <<'WRAP'
#!/usr/bin/env bash
exec "$HOME/ai-room/backup-safe.sh" "$@"
WRAP
chmod +x "$HOME/bin/ai-backup"

echo "== Codex =="
if command -v npm >/dev/null 2>&1; then
  npm install -g @openai/codex@latest || echo "⚠️ Codex 설치 실패"
else
  echo "⚠️ npm 없음"
fi

echo "== Hermes =="
if command -v hermes >/dev/null 2>&1; then
  echo "✅ Hermes 이미 설치됨"
else
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash || echo "⚠️ Hermes 설치 실패"
fi

echo "== OpenClaw =="
if command -v openclaw >/dev/null 2>&1; then
  echo "✅ OpenClaw 이미 설치됨"
elif command -v pkg >/dev/null 2>&1 && [[ "${PREFIX:-}" == *com.termux* ]]; then
  echo "⚠️ Android Termux 호스트에서는 공식 OpenClaw Gateway 설치를 시도하지 않습니다."
  echo "   OpenClaw 공식 설치 경로는 macOS/Linux/WSL이며, Android는 동반 앱(Node) 역할입니다."
  echo "   Gateway를 설치하려면 Debian PRoot에 로그인한 뒤 이 설치 스크립트를 실행하세요."
else
  curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash -s -- --no-onboard || echo "⚠️ OpenClaw 설치 실패"
fi

echo "== ChatGPT Termux MCP Workbench =="
mkdir -p "$BASE/chatgpt-workspace"
if python -m venv "$BASE/.venv"; then
  "$BASE/.venv/bin/python" -m pip install --upgrade pip fastmcp || echo "⚠️ FastMCP 설치 실패"
else
  echo "⚠️ Python venv 생성 실패. FastMCP 설치를 건너뜁니다."
fi
download_file https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/chatgpt-mcp.py "$BASE/chatgpt-mcp.py" || echo "⚠️ ChatGPT MCP 다운로드 실패"
chmod +x "$BASE/chatgpt-mcp.py" 2>/dev/null || true

cat > "$HOME/bin/chatgpt-mcp" <<'WRAP'
#!/usr/bin/env bash
export CHATGPT_WORKSPACE="$HOME/ai-room/chatgpt-workspace"
if [ -x "$HOME/ai-room/.venv/bin/python" ]; then
  exec "$HOME/ai-room/.venv/bin/python" "$HOME/ai-room/chatgpt-mcp.py" "$@"
fi
exec python "$HOME/ai-room/chatgpt-mcp.py" "$@"
WRAP
chmod +x "$HOME/bin/chatgpt-mcp"

cat > "$HOME/bin/chatgpt-mcp-check" <<'WRAP'
#!/usr/bin/env bash
set -u
export CHATGPT_WORKSPACE="$HOME/ai-room/chatgpt-workspace"
printf 'workspace: %s\\n' "$CHATGPT_WORKSPACE"
if [ -x "$HOME/ai-room/.venv/bin/python" ] && "$HOME/ai-room/.venv/bin/python" -c 'import fastmcp' >/dev/null 2>&1; then
  echo "fastmcp: OK (venv)"
elif python -c 'import fastmcp' >/dev/null 2>&1; then
  echo "fastmcp: OK (system)"
else
  echo "fastmcp: ERROR"
fi
if [ -f "$HOME/ai-room/chatgpt-mcp.py" ]; then
  echo "server-file: OK"
else
  echo "server-file: MISSING"
fi
echo "endpoint: http://127.0.0.1:8765/mcp"
WRAP
chmod +x "$HOME/bin/chatgpt-mcp-check"

echo
echo "== 확인 =="
printf 'ai-room: '; [ -x "$HOME/bin/ai-room" ] && echo "✅ $HOME/bin/ai-room" || echo "⚠️ 확인 필요"
printf 'ai-backup: '; [ -x "$HOME/bin/ai-backup" ] && echo "✅ $HOME/bin/ai-backup" || echo "⚠️ 확인 필요"
printf 'codex: '; command -v codex || echo "⚠️ 확인 필요"
printf 'hermes: '; command -v hermes || echo "⚠️ 확인 필요"
printf 'openclaw: '; command -v openclaw || echo "⚠️ 확인 필요"
printf 'chatgpt-mcp: '; [ -x "$HOME/bin/chatgpt-mcp" ] && echo "✅ $HOME/bin/chatgpt-mcp" || echo "⚠️ 확인 필요"

echo
echo "✅ 통합 설치 단계 완료"
echo "명령: ai-room"
echo "백업: ai-backup"
echo "MCP 확인: chatgpt-mcp-check"
echo "MCP 실행: chatgpt-mcp"
echo "MCP 서버는 기본적으로 localhost에서만 실행됩니다."
echo "로그인/Provider 설정은 각 도구에서 직접 진행하세요."

# OpenAI Secure MCP Tunnel helper. Installs the official ARM64 release on demand.
cat > "$HOME/bin/chatgpt-tunnel-setup" <<'TUNNEL'
#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

VERSION="v0.0.16"
RELEASE_BASE="https://github.com/openai/tunnel-client/releases/download/$VERSION"
ASSET="tunnel-client-${VERSION}-linux-arm64.zip"
BIN_DIR="$HOME/.local/bin"
TMP_DIR=""

cleanup() {
  if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then rm -rf "$TMP_DIR"; fi
}
trap cleanup EXIT

install_tunnel_client() {
  if command -v tunnel-client >/dev/null 2>&1; then
    echo "tunnel-client: $(tunnel-client --version 2>&1 | head -n 1)"
    return 0
  fi

  case "$(uname -m)" in
    aarch64|arm64) ;;
    *)
      echo "이 설치 스크립트는 ARM64/aarch64 전용 릴리스를 지원합니다. 현재 아키텍처: $(uname -m)" >&2
      return 1
      ;;
  esac

  command -v curl >/dev/null 2>&1 || { echo "curl이 없습니다. 먼저 pkg install curl을 실행하세요." >&2; return 1; }
  command -v unzip >/dev/null 2>&1 || {
    if command -v pkg >/dev/null 2>&1; then
      pkg install -y unzip coreutils
    else
      echo "unzip이 없습니다. unzip과 sha256sum을 설치한 뒤 다시 실행하세요." >&2
      return 1
    fi
  }
  command -v sha256sum >/dev/null 2>&1 || { echo "sha256sum이 없습니다." >&2; return 1; }

  TMP_DIR="$(mktemp -d "${TMPDIR:-$HOME}/tunnel-client-install.XXXXXX")"
  echo "OpenAI 공식 tunnel-client ${VERSION} ARM64 릴리스를 다운로드합니다..."
  curl --fail --location --silent --show-error "$RELEASE_BASE/$ASSET" -o "$TMP_DIR/$ASSET"
  curl --fail --location --silent --show-error "$RELEASE_BASE/SHA256SUMS.txt" -o "$TMP_DIR/SHA256SUMS.txt"

  (
    cd "$TMP_DIR"
    grep -E "[[:space:]]${ASSET//./\\.}$" SHA256SUMS.txt > expected.sha256 || {
      echo "공식 SHA256SUMS에서 ${ASSET} 체크섬을 찾지 못했습니다." >&2
      exit 1
    }
    sha256sum -c expected.sha256
  )

  mkdir -p "$BIN_DIR"
  unzip -q "$TMP_DIR/$ASSET" -d "$TMP_DIR/unpacked"
  CLIENT_PATH="$(find "$TMP_DIR/unpacked" -type f -name tunnel-client -print -quit)"
  [ -n "$CLIENT_PATH" ] || { echo "압축 파일에 tunnel-client 실행 파일이 없습니다." >&2; return 1; }
  install -m 0755 "$CLIENT_PATH" "$BIN_DIR/tunnel-client"

  CLOUDFLARED_PATH="$(find "$TMP_DIR/unpacked" -type f -name cloudflared -print -quit)"
  if [ -n "$CLOUDFLARED_PATH" ]; then
    install -m 0755 "$CLOUDFLARED_PATH" "$BIN_DIR/cloudflared"
  fi

  hash="$(sha256sum "$BIN_DIR/tunnel-client" | awk '{print $1}')"
  echo "설치된 tunnel-client SHA256: $hash"
  "$BIN_DIR/tunnel-client" --version
}

install_tunnel_client
export PATH="$BIN_DIR:$PATH"

read -r -p "OpenAI Tunnel ID (tunnel_...): " TUNNEL_ID
[ -n "$TUNNEL_ID" ] || { echo "Tunnel ID가 비어 있습니다."; exit 1; }
case "$TUNNEL_ID" in
  tunnel_*) ;;
  *) echo "Tunnel ID는 tunnel_ 접두사로 시작해야 합니다."; exit 1 ;;
esac

read -r -p "MCP URL [http://127.0.0.1:8765/mcp]: " MCP_URL
MCP_URL="${MCP_URL:-http://127.0.0.1:8765/mcp}"

if [ -z "${CONTROL_PLANE_API_KEY:-}" ]; then
  echo "런타임 API 키를 채팅이나 파일에 붙여 넣지 마세요."
  echo "현재 셸에서 다음처럼 환경변수로 설정한 뒤 다시 실행하세요:"
  echo '  export CONTROL_PLANE_API_KEY="YOUR_RUNTIME_API_KEY"'
  echo "이 키에는 필요한 Tunnels Read/Use 권한만 부여하세요."
  exit 1
fi

tunnel-client init \
  --sample sample_mcp_remote_no_auth \
  --profile neoos-ai-room \
  --tunnel-id "$TUNNEL_ID" \
  --mcp-server-url "$MCP_URL"

echo
echo "프로필 생성 요청이 완료되었습니다. MCP 서버를 먼저 실행한 뒤 터널을 실행하세요:"
echo "  tunnel-client run --profile neoos-ai-room"
echo "터널 연결 후 ChatGPT의 MCP 커넥터에서 연결 상태를 확인하세요."
TUNNEL
chmod +x "$HOME/bin/chatgpt-tunnel-setup"

echo "OpenAI Secure MCP Tunnel 설치/설정 도우미: chatgpt-tunnel-setup"
