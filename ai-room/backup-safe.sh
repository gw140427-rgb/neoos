#!/data/data/com.termux/files/usr/bin/bash
set -u

BACKUP_DIR="$HOME/ai-room/backups"
ANDROID_BACKUP_DIR="$HOME/storage/shared/ai-backups"
DATE="$(date +%Y%m%d-%H%M%S)"
STAGE="$TMPDIR/yangyang-safe-$DATE"
FILE="$BACKUP_DIR/yangyang-safe-$DATE.tar.gz"

mkdir -p "$STAGE" "$BACKUP_DIR" "$ANDROID_BACKUP_DIR"

copy_filtered() {
  src="$1"
  dst="$2"
  [ -e "$src" ] || return 0
  mkdir -p "$STAGE/$dst"
  tar -C "$(dirname "$src")" -cf - "$(basename "$src")" \
    --exclude='*/.env' --exclude='*/.env.*' \
    --exclude='*/auth.json' --exclude='*/credentials*' \
    --exclude='*/token*' --exclude='*/secret*' --exclude='*/secrets*' \
    --exclude='*/cookies*' --exclude='*/session*.json' \
    --exclude='*/id_rsa' --exclude='*/id_ed25519' --exclude='*/id_ecdsa' \
    --exclude='*/private*.key' --exclude='*/private*.pem' \
    --exclude='*/access_token*' --exclude='*/refresh_token*' \
    2>/dev/null | tar -C "$STAGE/$dst" -xf - 2>/dev/null || true
}

echo "📦 민감정보 제외 AI 백업"
copy_filtered "$HOME/ai-room" "ai-room"
copy_filtered "/storage/emulated/0/ai전용작업폴더/ai-baby" "ai-baby"
copy_filtered "$HOME/.openclaw" "termux-openclaw"
copy_filtered "$HOME/.hermes" "termux-hermes"
copy_filtered "$HOME/.codex" "termux-codex"

ROOTFS="$PREFIX/var/lib/proot-distro/installed-rootfs/debian"
copy_filtered "$ROOTFS/root/.openclaw" "debian-openclaw"
copy_filtered "$ROOTFS/root/.hermes" "debian-hermes"
copy_filtered "$ROOTFS/usr/local/lib/hermes-agent" "debian-hermes-agent"

tar -czf "$FILE" -C "$STAGE" . 2>/dev/null
rm -rf "$STAGE"

if [ -f "$FILE" ]; then
  cp -f "$FILE" "$ANDROID_BACKUP_DIR/"
  echo "✅ 저장: $FILE"
  echo "✅ Android: /storage/emulated/0/ai-backups/"
else
  echo "❌ 백업 실패"
  exit 1
fi
