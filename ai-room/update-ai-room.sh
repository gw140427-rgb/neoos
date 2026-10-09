#!/usr/bin/env bash
set -Eeuo pipefail

REPO_RAW="https://raw.githubusercontent.com/gw140427-rgb/neoos/main/ai-room/ai-room.sh"
TARGET_DIR="${AI_ROOM_DIR:-$HOME/ai-room}"
TARGET="$TARGET_DIR/ai-room.sh"

if ! command -v curl >/dev/null 2>&1; then
  echo "오류: curl이 설치되어 있지 않습니다." >&2
  exit 1
fi
if ! command -v bash >/dev/null 2>&1; then
  echo "오류: bash가 설치되어 있지 않습니다." >&2
  exit 1
fi

# Create the destination first; curl -o cannot create missing parent directories.
mkdir -p "$TARGET_DIR"
TMP="$(mktemp "$TARGET_DIR/.ai-room.sh.tmp.XXXXXX")"
cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

echo "다운로드 대상: $TARGET"
if ! curl -fL --retry 3 --connect-timeout 15 "$REPO_RAW" -o "$TMP"; then
  echo "다운로드 실패. 네트워크와 저장 경로를 확인하세요." >&2
  exit 1
fi
if [[ ! -s "$TMP" ]]; then
  echo "오류: 다운로드된 파일이 비어 있습니다." >&2
  exit 1
fi
if ! bash -n "$TMP"; then
  echo "오류: Bash 문법 검사에 실패했습니다. 기존 파일은 유지합니다." >&2
  exit 1
fi

chmod 700 "$TMP"
mv -f "$TMP" "$TARGET"
trap - EXIT
echo "완료: $TARGET"
echo "Bash 문법 검사 통과."
echo "실행하려면: bash \"$TARGET\""
