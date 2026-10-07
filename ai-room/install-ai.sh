#!/data/data/com.termux/files/usr/bin/bash
set -u
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

BASE="$HOME/ai-room"
mkdir -p "$BASE"

echo "🤖 NeoOS AI 통합 설치"
echo "⚠️ 기존 Node/OpenClaw/Hermes/Codex 설정은 삭제하지 않습니다."

pkg_install() {
  if command -v pkg >/dev/null 2>&1; then
    pkg install -y "$@" >/dev/null 2>&1 || true
  fi
}

echo "== 기본 도구 =="
pkg_install git curl python nodejs openssl

echo "== ai-room =="
curl -fsSL https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/ai-room.sh -o "$BASE/ai-room.sh" || echo "⚠️ ai-room 다운로드 실패"
chmod +x "$BASE/ai-room.sh" 2>/dev/null || true

echo "== 안전 백업 기능 =="
curl -fsSL https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/backup-safe.sh -o "$BASE/backup-safe.sh" || echo "⚠️ backup-safe 다운로드 실패"
chmod +x "$BASE/backup-safe.sh" 2>/dev/null || true

mkdir -p "$HOME/bin"
cat > "$HOME/bin/ai-room" <<'WRAP'
#!/data/data/com.termux/files/usr/bin/bash
exec "$HOME/ai-room/ai-room.sh" "$@"
WRAP
chmod +x "$HOME/bin/ai-room"

cat > "$HOME/bin/ai-backup" <<'WRAP'
#!/data/data/com.termux/files/usr/bin/bash
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
else
  curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash -s -- --no-onboard || echo "⚠️ OpenClaw 설치 실패"
fi

echo "== ChatGPT Termux MCP Workbench =="
mkdir -p "$BASE/chatgpt-workspace"
python -m pip install --user --upgrade fastmcp || echo "⚠️ FastMCP 설치 실패"
curl -fsSL https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/chatgpt-mcp.py -o "$BASE/chatgpt-mcp.py" || echo "⚠️ ChatGPT MCP 다운로드 실패"
chmod +x "$BASE/chatgpt-mcp.py" 2>/dev/null || true

cat > "$HOME/bin/chatgpt-mcp" <<'WRAP'
#!/data/data/com.termux/files/usr/bin/bash
export CHATGPT_WORKSPACE="$HOME/ai-room/chatgpt-workspace"
exec python "$HOME/ai-room/chatgpt-mcp.py" "$@"
WRAP
chmod +x "$HOME/bin/chatgpt-mcp"

cat > "$HOME/bin/chatgpt-mcp-check" <<'WRAP'
#!/data/data/com.termux/files/usr/bin/bash
set -u
export CHATGPT_WORKSPACE="$HOME/ai-room/chatgpt-workspace"
printf 'workspace: %s\n' "$CHATGPT_WORKSPACE"
if python -c 'import fastmcp' >/dev/null 2>&1; then
  echo "fastmcp: OK"
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
