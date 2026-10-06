#!/data/data/com.termux/files/usr/bin/bash
set -u
BACKUP_DIR="$HOME/ai-room/backups"
ANDROID_BACKUP_DIR="$HOME/storage/shared/ai-backups"
DATE="$(date +%Y%m%d-%H%M%S)"
STAGE="$TMPDIR/yangyang-ai-$DATE"
FILE="$BACKUP_DIR/yangyang-ai-$DATE.tar.gz"
mkdir -p "$STAGE" "$BACKUP_DIR" "$ANDROID_BACKUP_DIR"
add_path() { local src="$1" name="$2"; if [ -e "$src" ]; then echo "  ✅ $name"; mkdir -p "$STAGE/$(dirname "$name")"; cp -a "$src" "$STAGE/$name" 2>/dev/null || true; fi; }
echo "📦 YANGYANG AI 로컬 백업"
add_path "$HOME/ai-room" "ai-room"
add_path "/storage/emulated/0/ai전용작업폴더/ai-baby" "ai-baby"
add_path "$HOME/.openclaw" "termux-openclaw"
add_path "$HOME/.hermes" "termux-hermes"
add_path "$HOME/.codex" "termux-codex"
ROOTFS="$PREFIX/var/lib/proot-distro/installed-rootfs/debian"
add_path "$ROOTFS/root/.openclaw" "debian-openclaw"
add_path "$ROOTFS/root/.hermes" "debian-hermes"
add_path "$ROOTFS/usr/local/lib/hermes-agent" "debian-hermes-agent"
add_path "$ROOTFS/opt/node22" "debian-node22"
add_path "$ROOTFS/root/.config" "debian-root-config"
echo "📦 압축 중..."
tar -czf "$FILE" -C "$STAGE" . 2>/dev/null
rm -rf "$STAGE"
if [ ! -f "$FILE" ]; then echo "❌ 백업 생성 실패"; read -r -p "Enter..."; exit 1; fi
echo "✅ Termux 백업: $FILE"
if cp -f "$FILE" "$ANDROID_BACKUP_DIR/"; then echo "✅ Android: /storage/emulated/0/ai-backups/"; else echo "❌ Android 저장공간 복사 실패"; fi
echo; ls -lh "$ANDROID_BACKUP_DIR"/*.tar.gz 2>/dev/null || true
echo; echo "🔒 백업에는 AI 설정/인증정보가 포함될 수 있습니다."
read -r -p "Enter..."