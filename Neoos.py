"""NeoOS: tiny educational shell-like OS simulator."""

import random
import time
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

CommandHandler = Callable[[list[str]], str]

VERSION = "v0.4.2 Beta"


@dataclass
class Command:
    name: str
    description: str
    handler: CommandHandler


class NeoOS:
    def __init__(self) -> None:
        self._running = True
        self._commands: dict[str, Command] = {}
        self._files: dict[str, str] = {}
        self._packages: set[str] = set()
        self._register_builtin_commands()

    @property
    def running(self) -> bool:
        return self._running

    def _register(self, name: str, description: str, handler: CommandHandler) -> None:
        self._commands[name] = Command(name=name, description=description, handler=handler)

    def _register_builtin_commands(self) -> None:
        self._register("help", "사용 가능한 명령어를 출력합니다.", self._cmd_help)
        self._register("echo", "입력한 텍스트를 출력합니다.", self._cmd_echo)
        self._register("time", "현재 UTC 시간을 출력합니다.", self._cmd_time)
        self._register("clear", "터미널 화면을 정리합니다.", self._cmd_clear)
        self._register("exit", "NeoOS를 종료합니다.", self._cmd_exit)

        # 추가 기능
        self._register("calc", "간단한 계산을 합니다.", self._cmd_calc)
        self._register("ls", "파일 목록 출력 (ls 또는 ls 파일명)", self._cmd_ls)
        self._register("touch", "파일 생성 (touch 파일명)", self._cmd_touch)
        self._register("cat", "파일 내용 보기 (cat 파일명)", self._cmd_cat)

        # v0.4 기능
        self._register("rm", "파일 삭제 (rm 파일명 또는 rm -f 파일명)", self._cmd_rm)
        self._register("write", "파일 내용 덮어쓰기 (write 파일명 내용)", self._cmd_write)
        self._register("append", "파일 내용 추가 (append 파일명 내용)", self._cmd_append)
        self._register("install", "가짜 패키지 설치 (install 패키지명)", self._cmd_install)
        self._register("pkgs", "설치된 패키지 목록", self._cmd_pkgs)
        self._register("version", "NeoOS 버전 정보 출력", self._cmd_version)
        self._register("똥", "???", self._cmd_poop)

    def execute_line(self, line: str) -> str:
        # 입력 정리 (^@ 같은 거 제거)
        line = line.replace("\x00", "").strip()

        parts = line.split()
        if not parts:
            return ""

        name, args = parts[0], parts[1:]
        command = self._commands.get(name)

        if command is None:
            return f"알 수 없는 명령어: {name}. 'help'를 입력하세요."

        try:
            return command.handler(args)
        except Exception as e:
            # 사용자에게 친절한 메시지를 주고, 전체 트레이스는 stderr에 남겨 디버그 가능하게 함
            traceback.print_exc(file=sys.stderr)
            return f"오류 발생: {e}. 자세한 정보는 stderr를 확인하세요."

    def _cmd_help(self, _: list[str]) -> str:
        ordered = sorted(self._commands.values(), key=lambda c: c.name)
        header = [
            f"NeoOS {VERSION}",
            "명령어 목록 (사용 예시 포함):",
            "",
        ]
        body = []
        for cmd in ordered:
            body.append(f"{cmd.name:<8} - {cmd.description}")
        examples = [
            "",
            "예시:",
            "  write hello.txt 안녕하세요  -> hello.txt에 '안녕하세요'로 덮어쓰기",
            "  append hello.txt \", 또 추가\" -> 기존 내용 뒤에 줄바꿈 후 추가",
            "  touch newfile.txt           -> 새 파일 생성",
            "  ls                         -> 파일 목록 (크기 표시)",
            "  ls hello.txt               -> 해당 파일 정보",
            "  rm filename                -> 파일 삭제 (또는 rm -f filename)",
            "  install foo                -> 가짜 패키지 설치 (진행바)",
            "  version                    -> NeoOS 버전 출력",
        ]
        return "\n".join(header + body + examples)

    def _cmd_echo(self, args: list[str]) -> str:
        return " ".join(args)

    def _cmd_time(self, _: list[str]) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M:%S UTC")

    def _cmd_clear(self, _: list[str]) -> str:
        return "\033[2J\033[H"

    def _cmd_exit(self, _: list[str]) -> str:
        self._running = False
        return "NeoOS를 종료합니다."

    def _cmd_calc(self, args):
        try:
            expr = " ".join(args)
            allowed = "0123456789+-*/(). "
            if not all(c in allowed for c in expr):
                return "허용되지 않은 입력"
            return str(eval(expr, {"__builtins__": None}, {}))
        except Exception:
            return "계산 오류"

    def _cmd_ls(self, args):
        # ls 또는 ls 파일명
        if not self._files:
            return "파일 없음"
        if args:
            name = args[0]
            if name not in self._files:
                return "파일 없음"
            size = len(self._files[name].encode('utf-8'))
            preview = self._files[name].splitlines()[0] if self._files[name] else ""
            return f"{name} - {size} bytes\n{preview}"
        lines = []
        for name in sorted(self._files.keys()):
            size = len(self._files[name].encode('utf-8'))
            lines.append(f"{name:<20} {size:6d} bytes")
        return "\n".join(lines)

    def _cmd_touch(self, args):
        if not args:
            return "파일 이름 필요"
        name = args[0]
        if name in self._files:
            return f"{name} 이미 존재함"
        self._files[name] = ""
        return f"{args[0]} 생성됨"

    def _cmd_cat(self, args):
        if not args:
            return "파일 이름 필요"
        return self._files.get(args[0], "파일 없음")

    def _cmd_rm(self, args):
        if not args:
            return "파일 이름 필요"
        force = False
        name = args[0]
        if args[0] == "-f":
            force = True
            if len(args) < 2:
                return "파일 이름 필요"
            name = args[1]
        if name not in self._files:
            if force:
                return f"{name} 없음 (강제)"
            return "파일 없음"
        del self._files[name]
        return f"{name} 삭제됨"

    def _cmd_write(self, args):
        if len(args) < 2:
            return "사용법: write 파일명 내용"
        name, content = args[0], " ".join(args[1:])
        self._files[name] = content
        return f"{name}에 저장됨"

    def _cmd_append(self, args):
        if len(args) < 2:
            return "사용법: append 파일명 내용"
        name, content = args[0], " ".join(args[1:])
        if name not in self._files:
            return "파일 없음. 먼저 touch 하세요."
        # 기존 내용이 비어있지 않으면 줄바꿈을 넣고 추가
        if self._files[name]:
            self._files[name] += "\n" + content
        else:
            self._files[name] = content
        return f"{name}에 추가됨"

    def _cmd_install(self, args):
        if not args:
            return "사용법: install 패키지명"
        pkg = args[0]
        if pkg in self._packages:
            return f"{pkg} 은(는) 이미 설치되어 있습니다."

        print(f"패키지 저장소에서 {pkg} 검색 중...")
        total = 20
        for i in range(total + 1):
            bar = "█" * i + "░" * (total - i)
            print(f"\r다운로드 중 [{bar}] {i * 5:3d}%", end="", flush=True)
            time.sleep(random.uniform(0.02, 0.08))
        print()
        self._packages.add(pkg)
        return f"✅ {pkg} 설치 완료!"

    def _cmd_pkgs(self, args):
        if not self._packages:
            return "설치된 패키지 없음. 'install 패키지명' 으로 설치하세요."
        return "\n".join(f"📦 {p}" for p in sorted(self._packages))

    def _cmd_version(self, args):
        return f"NeoOS {VERSION}"

    def _cmd_poop(self, args):
        return "\n".join(
            [
                "      💩💩💩",
                "    💩💩💩💩💩",
                "  💩💩💩💩💩💩💩",
                "💩💩💩💩💩💩💩💩💩",
                "",
                "NeoOS 커널이 응가를 했습니다... 💩",
            ]
        )


def run_shell() -> None:
    neo = NeoOS()
    print(f"NeoOS {VERSION} 부팅 완료. 'help'로 명령어를 확인하세요.")

    while neo.running:
        try:
            line = input("neo> ")
        except EOFError:
            print()
            break

        output = neo.execute_line(line)
        if output:
            print(output)


if __name__ == "__main__":
    run_shell()
