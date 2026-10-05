# NeoOS PC Edition

NeoOS PC Edition is the real-hardware Linux distribution track of NeoOS.

## Target

- x86_64 PCs
- Intel Core / AMD Ryzen CPUs
- Intel / AMD / NVIDIA GPUs
- UEFI and legacy BIOS boot through the Archiso releng profile
- KDE Plasma desktop
- NetworkManager
- Vulkan/Mesa graphics stack
- NVIDIA open kernel module package
- NeoOS hardware inspection command

## Build

On an Arch Linux build host:

    bash os/build.sh

The resulting ISO is written to `out/`.

GitHub Actions also builds the ISO automatically when `os/**` changes.

## Hardware

After booting the live system:

    neoos-hardware

This reports the CPU, PCI GPU, memory, storage, kernel and available OpenGL renderer information.

## Important

This first PC Edition is a live ISO prototype. It is the foundation for a future installable NeoOS system. It uses the Linux kernel and Linux hardware drivers, so CPU/GPU work is performed by the actual machine hardware rather than a browser simulation.

NVIDIA support depends on GPU generation and Linux driver support. The image includes the open NVIDIA kernel module packages.
