#!/data/data/com.termux/files/usr/bin/bash
set -u

HOME_WORK="$HOME/ai-room/chatgpt-workspace"
ANDROID_WORK="/storage/emulated/0/ai전용작업폴더/ai-baby"

pause() {
  read -r -p "Enter를 누르면 메뉴로 돌아갑니다..." _
}

show_status() {
  echo
  command -v node >/dev/null 2>&1 && echo "✅ Node: $(node -v)" || echo "❌ Node 없음"
  command -v python >/dev/null 2>&1 && echo "✅ Python: $(python --version 2>&1 | head -n 1)" || echo "❌ Python 없음"
  command -v git >/dev/null 2>&1 && echo "✅ Git: $(git --version)" || echo "❌ Git 없음"
  command -v codex >/dev/null 2>&1 && echo "✅ Codex: $(codex --version 2>/dev/null | head -n 1)" || echo "❌ Codex 명령을 찾지 못함"
  command -v hermes >/dev/null 2>&1 && echo "✅ Hermes 설치됨" || echo "ℹ️ Hermes 명령 없음"
  command -v openclaw >/dev/null 2>&1 && echo "✅ OpenClaw: $(openclaw --version 2>/dev/null | head -n 1)" || echo "❌ OpenClaw 명령을 찾지 못함"
}

while true; do
  clear
  echo "╔══════════════════════════════════╗"
  echo "║       🤖 YANGYANG AI ROOM        ║"
  echo "╠══════════════════════════════════╣"
  echo "║ 📱 Device : $(getprop ro.product.model 2>/dev/null || echo Android)"
  echo "║ 🧠 Node   : $(node -v 2>/dev/null || echo N/A)"
  echo "║ 🐍 Python : $(python --version 2>&1 | head -n 1 || echo N/A)"
  echo "║ 💾 Disk   : $(df -h "$HOME" 2>/dev/null | awk 'NR==2 {print $5 " used"}')"
  echo "╠══════════════════════════════════╣"
  echo "║ 1. 🤖 AI 도구 상태 확인          ║"
  echo "║ 2. 🦞 OpenClaw 상태              ║"
  echo "║ 3. 🧑‍💻 Codex 상태                ║"
  echo "║ 4. 📁 AI 작업폴더                ║"
  echo "║ 5. 🔧 시스템 진단                ║"
  echo "║ 6. 🧹 패키지 캐시 정리           ║"
  echo "║ 7. 💾 민감정보 제외 백업          ║"
  echo "║ 0. 🚪 종료                       ║"
  echo "╚══════════════════════════════════╝"
  read -r -p "👉 선택: " choice
  case "$choice" in
    1)
      show_status
      pause
      ;;
    2)
      echo
      if command -v openclaw >/dev/null 2>&1; then
        openclaw --version 2>/dev/null || true
        openclaw gateway status 2>/dev/null || echo "게이트웨이 상태를 확인할 수 없습니다."
      else
        echo "❌ OpenClaw 명령을 찾지 못함"
      fi
      pause
      ;;
    3)
      echo
      if command -v codex >/dev/null 2>&1; then
        codex --version 2>/dev/null || true
        printf '경로: '; command -v codex
      elif [ -x /opt/node22/bin/codex ]; then
        /opt/node22/bin/codex --version 2>/dev/null || true
        echo "경로: /opt/node22/bin/codex"
      else
        echo "❌ Codex 명령을 찾지 못함"
      fi
      pause
      ;;
    4)
      echo
      if [ -d "$ANDROID_WORK" ]; then
        echo "📁 Android 공유 저장소 작업폴더: $ANDROID_WORK"
        ls -lah "$ANDROID_WORK" | head -n 30
      elif [ -d "$HOME_WORK" ]; then
        echo "📁 Termux 작업폴더: $HOME_WORK"
        ls -lah "$HOME_WORK" | head -n 30
      else
        echo "작업폴더를 찾지 못했습니다."
        echo "Termux 기본 작업폴더를 만듭니다: $HOME_WORK"
        mkdir -p "$HOME_WORK" && echo "✅ 생성 완료"
        echo "Android 공유 저장소를 쓰려면 먼저 termux-setup-storage를 실행하세요."
      fi
      pause
      ;;
    5)
      echo
      echo "=== 🔧 시스템 진단 ==="
      echo "아키텍처: $(uname -m)"
      echo "CPU 코어: $(nproc 2>/dev/null || echo N/A)"
      echo
      if command -v free >/dev/null 2>&1; then free -h; else echo "RAM 정보: free 명령 없음"; fi
      echo
      df -h "$HOME"
      echo
      if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; then
        echo "🌐 네트워크: ONLINE"
      else
        echo "🌐 네트워크: 확인 실패 (ICMP 차단일 수도 있음)"
      fi
      pause
      ;;
    6)
      echo
      echo "🧹 Termux 패키지 캐시 정리"
      if command -v pkg >/dev/null 2>&1; then
        pkg clean
      else
        echo "pkg 명령을 찾지 못했습니다. Termux에서 실행해야 합니다."
      fi
      if command -v npm >/dev/null 2>&1; then
        npm cache verify || true
      fi
      echo "완료. 사용자 설정과 AI 도구는 삭제하지 않았습니다."
      pause
      ;;
    7)
      echo
      BACKUP="$HOME/ai-room/backup-safe.sh"
      if [ -f "$BACKUP" ]; then
        bash "$BACKUP"
      elif [ -f "$HOME/ai-room/backup-local.sh" ]; then
        echo "⚠️ backup-safe.sh가 없어 기존 백업 스크립트를 실행합니다."
        bash "$HOME/ai-room/backup-local.sh"
      else
        echo "❌ 백업 스크립트가 없습니다."
        echo "설치 스크립트를 다시 실행해 backup-safe.sh를 내려받으세요."
      fi
      pause
      ;;
    0)
      clear
      echo "👋 AI 작업실 종료!"
      exit 0
      ;;
    *)
      echo "❌ 잘못된 선택"
      sleep 1
      ;;
  esac
done
