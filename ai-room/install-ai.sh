#!/data/data/com.termux/files/usr/bin/bash
set -e
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

echo "🤖 NeoOS AI 설치"
echo "⚠️ 기존 Node/OpenClaw/Hermes 설정은 삭제하지 않습니다."

pkg_install() {
  command -v pkg >/dev/null 2>&1 && pkg install -y "$@" >/dev/null
}

echo "== 기본 도구 =="
pkg_install git curl python nodejs openssl || true

echo "== Codex =="
if command -v npm >/dev/null 2>&1; then
  npm install -g @openai/codex@latest
fi

echo "== Hermes =="
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

echo "== OpenClaw =="
# OpenClaw requires a supported Node runtime. Its installer manages its own runtime
# when necessary, so it is kept separate from the user's existing Node projects.
curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash -s -- --no-onboard

echo
echo "== 확인 =="
command -v codex && codex --version || echo "⚠️ Codex 확인 필요"
command -v hermes && hermes --version 2>/dev/null || echo "⚠️ Hermes 확인 필요"
command -v openclaw && openclaw --version 2>/dev/null || echo "⚠️ OpenClaw 확인 필요"
echo
echo "✅ 설치 단계 완료. 로그인/Provider 설정은 각 도구에서 직접 진행하세요."
