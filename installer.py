#!/usr/bin/env python3
"""NeoOS Installer - 설치 화면 시뮬레이터"""
import time
import os
import sys

def clear():
    print("\033[2J\033[H", end="")

def banner():
    print("="*50)
    print("  ███╗  ██╗███████╗ ██████╗  ██████╗ ███████╗")
    print("  ████╗ ██║██╔════╝██╔═══██╗██╔═══██╗██╔════╝")
    print("  ██╔██╗██║█████╗  ██║   ██║██║   ██║███████╗")
    print("  ██║╚████║██╔══╝  ██║   ██║██║   ██║╚════██║")
    print("  ██║ ╚███║███████╗╚██████╔╝╚██████╔╝███████║")
    print("  ╚═╝  ╚══╝╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝")
    print(f"           NeoOS v0.5.0 Beta Installer")
    print("="*50)

def boot_screen():
    clear()
    banner()
    print("\n[BOOT] NeoOS 커널 로딩 중...")
    steps = [
        ("[OK] Linux 커널 6.8.0-lts 로드", 0.3),
        ("[OK] initramfs 마운트", 0.2),
        ("[OK] 파일시스템 초기화", 0.2),
        ("[OK] NeoOS 셸 준비", 0.3),
    ]
    for msg, t in steps:
        time.sleep(t)
        print(msg)
    time.sleep(0.5)
    print("\n✓ 부팅 완료! 설치를 시작합니다...\n")
    time.sleep(1)

def install_screen():
    clear()
    banner()
    print("\n▶ NeoOS 설치 마법사\n")
    print("1. 언어 선택: 한국어 [선택됨]")
    print("2. 디스크 선택: /dev/sda (20GB) [선택됨]")
    print("3. 사용자 생성")
    try:
        user = input("\n  사용자 이름 (기본: neo): ").strip() or "neo"
        pw = input("  비밀번호 (기본: neo1234): ").strip() or "neo1234"
    except EOFError:
        user, pw = "neo", "neo1234"
    
    print("\n[설치] 파일 복사 중...")
    for i in range(21):
        bar = "█" * i + "░" * (20 - i)
        print(f"\r  [{bar}] {i*5:3d}%", end="", flush=True)
        time.sleep(0.08)
    print()
    print(f"\n[OK] /neoos 에 설치 완료!")
    print(f"[OK] 계정 생성: {user} / {'*'*len(pw)}")
    print(f"\n🎉 NeoOS 설치가 완료되었습니다!")
    print(f"   재부팅 후 'login {user} {pw}' 로 로그인하세요.")
    print(f"\n   ISO 저장 위치: /sdcard/Download/neoos.iso")
    return user

if __name__ == "__main__":
    boot_screen()
    install_screen()
    print("\n[엔터]를 눌러 NeoOS 셸로 이동...")
    try:
        input()
    except:
        pass
    # 셸 시작
    import Neoos
    Neoos.run_shell()
