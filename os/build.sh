#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="/tmp/neoos-archiso"
PROFILE="$WORK/profile"
OUT="$ROOT/out"
rm -rf "$WORK" "$OUT"
mkdir -p "$WORK" "$OUT"
pacman -Sy --noconfirm archiso
cp -a /usr/share/archiso/configs/releng "$PROFILE"
cat >> "$PROFILE/packages.x86_64" <<'PACKAGES'
plasma-meta
sddm
konsole
dolphin
kate
firefox
networkmanager
mesa
vulkan-radeon
vulkan-intel
vulkan-tools
libva
libva-utils
nvidia-open
nvidia-utils
linux-headers
htop
fastfetch
git
curl
wget
python
PACKAGES
mkdir -p "$PROFILE/airootfs/usr/local/bin"
cat > "$PROFILE/airootfs/usr/local/bin/neoos-hardware" <<'EOF'
#!/usr/bin/env bash
set -u
echo "=== NeoOS Hardware ==="
echo
echo "[CPU]"
lscpu | grep -E 'Model name|CPU\\(s\\)|Architecture' || true
echo
echo "[GPU]"
lspci | grep -Ei 'vga|3d|display' || true
echo
echo "[Memory]"
free -h
echo
echo "[Storage]"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS 2>/dev/null || true
echo
echo "[Kernel]"
uname -a
echo
echo "[OpenGL]"
if command -v glxinfo >/dev/null 2>&1; then
  glxinfo -B 2>/dev/null | grep -E 'OpenGL vendor|OpenGL renderer|OpenGL version' || true
else
  echo "glxinfo not installed"
fi
EOF
chmod +x "$PROFILE/airootfs/usr/local/bin/neoos-hardware"
cat > "$PROFILE/airootfs/root/customize_airootfs.sh" <<'EOF'
#!/usr/bin/env bash
set -e
systemctl enable NetworkManager.service
systemctl enable sddm.service
mkdir -p /etc/xdg/autostart
cat > /etc/xdg/autostart/neoos-welcome.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=NeoOS Welcome
Exec=konsole --hold -e bash -lc 'clear; echo "Welcome to NeoOS PC Edition"; echo; echo "Run: neoos-hardware"; exec bash'
Terminal=false
X-KDE-autostart-after=panel
DESKTOP
cat > /etc/os-release <<'OSREL'
NAME="NeoOS"
PRETTY_NAME="NeoOS PC Edition"
ID=neoos
ID_LIKE=arch
BUILD_ID=rolling
HOME_URL="https://github.com/gw140427-rgb/neoos"
OSREL
echo "NeoOS PC Edition" > /etc/issue
EOF
chmod +x "$PROFILE/airootfs/root/customize_airootfs.sh"
sed -i 's/^iso_name=.*/iso_name="neoos-pc"/' "$PROFILE/profiledef.sh"
sed -i 's/^iso_label=.*/iso_label="NEOOS_PC"/' "$PROFILE/profiledef.sh"
sed -i 's/^iso_application=.*/iso_application="NeoOS PC Edition"/' "$PROFILE/profiledef.sh"
sed -i 's/^iso_publisher=.*/iso_publisher="NeoOS Project"/' "$PROFILE/profiledef.sh"
mkarchiso -v -r -w "$WORK/work" -o "$OUT" "$PROFILE"
ls -lh "$OUT"