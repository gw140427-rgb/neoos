#!/usr/bin/env bash
set -Eeuo pipefail

REPO_RAW="https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/ai-room.sh"
TARGET_DIR="${AI_ROOM_DIR:-$HOME/ai-room}"
TARGET="$TARGET_DIR/ai-room.sh"

for cmd in curl bash mktemp; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "오류: 필요한 명령이 없습니다: $cmd" >&2
    exit 1
  }
done

# Download into /tmp first so the destination directory can be created/repaired
# without curl failing while trying to open ~/ai-room/ai-room.sh.
TMP="$(mktemp "${TMPDIR:-/tmp}/ai-room-update.XXXXXX")"
cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

echo "1/4: 임시 위치에 다운로드합니다."
if ! curl -fL --retry 3 --connect-timeout 15 "$REPO_RAW" -o "$TMP"; then
  echo "오류: 다운로드 실패. 네트워크 연결을 확인하세요." >&2
  exit 1
fi
if [[ ! -s "$TMP" ]]; then
  echo "오류: 다운로드 파일이 비어 있습니다." >&2
  exit 1
fi

echo "2/4: Bash 문법을 검사합니다."
if ! bash -n "$TMP"; then
  echo "오류: 문법 검사 실패. 기존 파일은 변경하지 않았습니다." >&2
  exit 1
fi

echo "3/4: 저장 폴더를 준비합니다: $TARGET_DIR"
if ! mkdir -p "$TARGET_DIR"; then
  echo "오류: 저장 폴더를 만들 수 없습니다: $TARGET_DIR" >&2
  echo "HOME=$HOME" >&2
  df -h "$HOME" 2>/dev/null || true
  ls -ld "$HOME" "$TARGET_DIR" 2>/dev/null || true
  exit 1
fi

DEST_TMP="$(mktemp "$TARGET_DIR/.ai-room.sh.tmp.XXXXXX")" || {
  echo "오류: $TARGET_DIR 에 임시 파일을 만들 수 없습니다." >&2
  echo "HOME=$HOME" >&2
  df -h "$TARGET_DIR" 2>/dev/null || true
  ls -ld "$TARGET_DIR" 2>/dev/null || true
  exit 1
}
trap 'rm -f "$TMP" "${DEST_TMP:-}"' EXIT

if ! cat "$TMP" > "$DEST_TMP"; then
  echo "오류: 대상 파일시스템에 쓸 수 없습니다: $TARGET_DIR" >&2
  df -h "$TARGET_DIR" 2>/dev/null || true
  ls -ld "$TARGET_DIR" 2>/dev/null || true
  exit 1
fi
chmod 700 "$DEST_TMP"
mv -f "$DEST_TMP" "$TARGET"
DEST_TMP=""

echo "4/4: 업데이트 완료"
echo "파일: $TARGET"
echo "Bash 문법 검사: 통과"
echo "실행 명령: bash \"$TARGET\""
