#!/bin/bash

# 🚀 Samsung Galaxy Note 20 (Snapdragon 865) 전용 
# Windows 7 최적화 실행 스크립트

echo "Starting Windows 7 on Termux..."

qemu-system-x86_64 \
  -m 2048M \
  -cpu max,hv_relaxed,hv_spinlocks=0x1fff,hv_vapic,hv_time \
  -smp 4,cores=4 \
  -vga std \
  -display sdl \
  -device e1000,netdev=n0 \
  -netdev user,id=n0 \
  -device qemu-xhci,id=usb \
  -device usb-tablet \
  -drive file=win7.qcow2,format=qcow2 \
  -boot c