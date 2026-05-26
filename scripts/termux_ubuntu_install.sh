#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

log() {
  printf '\n[+] %s\n' "$1"
}

warn() {
  printf '\n[!] %s\n' "$1"
}

if [[ "${PREFIX:-}" != "/data/data/com.termux/files/usr" ]]; then
  warn "이 스크립트는 Termux 환경에서 실행해야 합니다."
  exit 1
fi

log "패키지 목록 업데이트"
pkg update -y && pkg upgrade -y

log "필수 패키지 설치"
pkg install -y proot-distro curl git

if ! command -v proot-distro >/dev/null 2>&1; then
  warn "proot-distro 설치에 실패했습니다."
  exit 1
fi

if proot-distro list | grep -q '^ubuntu$'; then
  log "Ubuntu 배포판이 이미 설치되어 있습니다."
else
  log "Ubuntu 배포판 설치"
  proot-distro install ubuntu
fi

log "Ubuntu 초기 설정 스크립트 생성"
cat > "$HOME/.termux-ubuntu-init.sh" <<'INITEOF'
#!/bin/bash
set -euo pipefail

apt update -y
DEBIAN_FRONTEND=noninteractive apt upgrade -y
DEBIAN_FRONTEND=noninteractive apt install -y \
  sudo curl wget git vim nano ca-certificates locales tzdata

if ! id -u ubuntu >/dev/null 2>&1; then
  useradd -m -s /bin/bash ubuntu
  echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ubuntu
  chmod 0440 /etc/sudoers.d/ubuntu
fi

if ! locale -a | grep -q 'en_US.utf8'; then
  sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
  locale-gen
fi

ln -sf /usr/share/zoneinfo/UTC /etc/localtime

echo "Ubuntu 설정 완료"
INITEOF

chmod +x "$HOME/.termux-ubuntu-init.sh"

log "Ubuntu 내부 초기 설정 실행"
proot-distro login ubuntu -- bash /root/.termux-ubuntu-init.sh || {
  warn "초기 설정 실행 중 오류가 발생했습니다. 수동 실행: proot-distro login ubuntu -- bash /root/.termux-ubuntu-init.sh"
  exit 1
}

log "Termux에서 Ubuntu를 바로 실행하는 alias 추가"
if ! grep -q "alias ubuntu='proot-distro login ubuntu'" "$HOME/.bashrc"; then
  echo "alias ubuntu='proot-distro login ubuntu'" >> "$HOME/.bashrc"
fi

log "설치 완료! 다음 명령으로 Ubuntu에 접속하세요:"
echo "  ubuntu"
