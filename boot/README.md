# NeoOS Bootable ISO (prototype)

This repository currently contains a Python shell/web-terminal simulator, not a bootable operating system. This folder adds a reproducible path toward a bootable x86_64 ISO using Debian's Linux kernel, GRUB, and a tiny NeoOS userspace launcher.

## Build target

- Architecture: x86_64 UEFI/BIOS in QEMU (not Android hardware)
- Kernel: Debian-packaged Linux kernel
- Bootloader: GRUB
- Root filesystem: Debian live system, launching the existing NeoOS Python shell
- This is a Linux-based NeoOS prototype, not a new kernel.

## Safe first milestone

Use Debian Live Build to create a live ISO, then add NeoOS as the first-run application. The ISO boots the Linux kernel and initramfs; NeoOS starts after the live system initializes.

## Build on a Debian/Ubuntu machine

Install prerequisites:

```sh
sudo apt update
sudo apt install -y live-build debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools
```

From the repository root, configure and build a Debian live image:

```sh
mkdir -p boot/live-config
cd boot/live-config
lb config --distribution stable --architectures amd64 --binary-images iso-hybrid --bootappend-live "boot=live components quiet"
mkdir -p config/package-lists
printf '%s\\n' python3 python3-venv ca-certificates > config/package-lists/neoos.list.chroot
mkdir -p config/includes.chroot/opt/neoos
cp ../../Neoos.py config/includes.chroot/opt/neoos/Neoos.py
cat > config/includes.chroot/etc/skel/.profile <<'EOF'
if [ -t 0 ] && [ -f /opt/neoos/Neoos.py ]; then
  python3 /opt/neoos/Neoos.py
fi
EOF
sudo lb build
```

The resulting ISO is produced in the live-config directory (typically `live-image-amd64.hybrid.iso`). Test it in QEMU first; do not write it to a real device until it has been tested and you have backed up important data.

## Important

- This is a prototype recipe and may need small adjustments to match the repository's actual Python entrypoint and the Debian Live Build version.
- The current NeoOS shell is not a Linux kernel and cannot manage hardware by itself.
- Do not replace a phone's boot image or attempt to boot this ISO directly on the Galaxy A16. The ISO is for a PC/virtual machine.
