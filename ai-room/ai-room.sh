#!/data/data/com.termux/files/usr/bin/bash

while true; do
  clear
  echo "╔══════════════════════════════════╗"
  echo "║       🤖 YANGYANG AI ROOM        ║"
  echo "╠══════════════════════════════════╣"
  echo "║ 📱 Device : $(getprop ro.product.model)"
  echo "║ 🧠 Node   : $(node -v 2>/dev/null || echo N/A)"
  echo "║ 🐍 Python : $(python --version 2>&1 | head -1 || echo N/A)"
  echo "║ 💾 Disk   : $(df -h /data/data/com.termux/files/home | awk 'NR==2 {print $5 " used"}')"
  echo "╠══════════════════════════════════╣"
  echo "║ 1. 🤖 AI 상태 확인               ║"
  echo "║ 2. 🦞 OpenClaw 상태              ║"
  echo "║ 3. 🧑‍💻 Codex 상태                ║"
  echo "║ 4. 📁 AI 작업폴더                ║"
  echo "║ 5. 🔧 시스템 진단                ║"
  echo "║ 6. 🧹 캐시 정리                  ║"
  echo "║ 7. 💾 작업실 백업                ║"
  echo "║ 0. 🚪 종료                       ║"
  echo "╚══════════════════════════════════╝"
  read -r -p "👉 선택: " choice
  case "$choice" in
    1) echo; command -v node >/dev/null && echo "✅ Node: $(node -v)" || echo "❌ Node 없음"; command -v python >/dev/null && echo "✅ Python: $(python --version 2>&1)" || echo "❌ Python 없음"; command -v git >/dev/null && echo "✅ Git: $(git --version)" || echo "❌ Git 없음"; read -r -p "Enter..." ;;
    2) echo; if command -v openclaw >/dev/null; then echo "✅ OpenClaw: $(openclaw --version 2>/dev/null)"; openclaw gateway status 2>/dev/null || true; else echo "❌ OpenClaw 명령을 찾지 못함"; fi; read -r -p "Enter..." ;;
    3) echo; if [ -x /opt/node22/bin/codex ]; then echo "✅ Codex: $(/opt/node22/bin/codex --version 2>/dev/null)"; echo "📍 /opt/node22/bin/codex"; elif command -v codex >/dev/null; then echo "✅ Codex: $(codex --version 2>/dev/null)"; echo "📍 $(command -v codex)"; else echo "❌ Codex 명령을 찾지 못함"; fi; read -r -p "Enter..." ;;
    4) WORK="/storage/emulated/0/ai전용작업폴더/ai-baby"; echo; if [ -d "$WORK" ]; then echo "📁 $WORK"; cd "$WORK" || true; printf '\n현재 위치: %s\n' "$PWD"; ls -lah | head -30; else echo "⚠️ 작업폴더 없음: $WORK"; fi; read -r -p "Enter..." ;;
    5) echo; echo "=== 🔧 시스템 진단 ==="; echo "CPU: $(nproc)"; echo; free -h; echo; df -h /data/data/com.termux/files/home; echo; if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; then echo "🌐 네트워크: ONLINE"; else echo "🌐 네트워크: OFFLINE"; fi; read -r -p "Enter..." ;;
    6) echo; echo "🧹 안전한 캐시 정리"; apt clean 2>/dev/null || true; npm cache verify 2>/dev/null || true; echo "✅ 완료"; read -r -p "Enter..." ;;
    7) echo; "$HOME/ai-room/backup-local.sh" ;;
    0) clear; echo "👋 AI 작업실 종료!"; exit 0 ;;
    *) echo "❌ 잘못된 선택"; sleep 1 ;;
  esac
done