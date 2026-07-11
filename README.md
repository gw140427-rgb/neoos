# NeoOS 🖥️

> 🇰🇷 Python으로 만든 간단한 쉘(OS) 시뮬레이터 — 터미널에서 돌아가는 미니 가상 OS!
>
> 🇺🇸 A tiny shell-like OS simulator written in Python. A mini virtual OS that runs in your terminal!

![Python](https://img.shields.io/badge/python-3.9+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/dependencies-zero-brightgreen)
![Release](https://img.shields.io/github/v/release/gw140427-rgb/neoos)

```
NeoOS v0.4.1 부팅 완료. 'help'로 명령어를 확인하세요.
neo> install neofetch
패키지 저장소에서 neofetch 검색 중...
다운로드 중 [████████████████████] 100%
✅ neofetch 설치 완료!
neo> 똥
      💩💩💩
    💩💩💩💩💩
  💩💩💩💩💩💩💩
💩💩💩💩💩💩💩💩💩
```

## 🚀 실행 방법 / Usage

```bash
python Neoos.py
```

설치 필요 없음! 파이썬만 있으면 됩니다. (No dependencies — pure Python!)

## ⌨️ 명령어 / Commands

### ⚙️ 기본 명령어 / Basic

| 명령어 | 설명 |
|--------|------|
| `help` | 사용 가능한 명령어 전체 보기 |
| `echo 글` | 입력한 텍스트 그대로 출력 |
| `time` | 현재 UTC 시간 출력 |
| `clear` | 화면 초기화 |
| `exit` | NeoOS 종료 |

### 📁 파일 시스템 / File system

| 명령어 | 설명 |
|--------|------|
| `ls` | 파일 목록 보기 |
| `touch 파일명` | 파일 생성 |
| `cat 파일명` | 파일 내용 보기 |
| `write 파일명 내용` | 파일 내용 덮어쓰기 |
| `append 파일명 내용` | 파일 내용 추가 |
| `rm 파일명` | 파일 삭제 |

### 📦 패키지 매니저 / Package manager

| 명령어 | 설명 |
|--------|------|
| `install 패키지명` | 가짜 패키지 설치 (진행바 애니메이션 ✨) |
| `pkgs` | 설치된 패키지 목록 |

### 🧮 기타 / Etc

| 명령어 | 설명 |
|--------|------|
| `calc 수식` | 간단한 계산기 (예: `calc 1+2*3`) |
| `똥` | ??? 직접 쳐보세요 💩 |

## 📥 다운로드 / Download

최신 릴리즈는 GitHub Releases에서 받을 수 있습니다.
Termux 설치 스크립트는 `scripts/termux_ubuntu_install.sh`를 사용하세요.

## 🤝 기여 / Contributing

이슈와 PR 환영합니다! Issues and PRs are welcome!

---

**Keywords**: python shell simulator, os simulator, terminal, cli, 파이썬 쉘, 미니 OS, toy os, educational
