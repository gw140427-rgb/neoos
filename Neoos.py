"""NeoOS: tiny educational shell-like OS simulator."""

import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


VERSION = "v0.4.1-beta"

CommandHandler = Callable[[list[str]], str]


@dataclass
class Command:
    name: str
    description: str
    handler: CommandHandler


class NeoOS:
    def __init__(self) -> None:
        self._running = True
        self._commands: dict[str, Command] = {}
        self._files = {}
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
        self._register("ls", "파일 목록 출력", self._cmd_ls)
        self._register("touch", "파일 생성", self._cmd_touch)
        self._register("cat", "파일 내용 보기", self._cmd_cat)

        # v0.4 기능
        self._register("rm", "파일 삭제", self._cmd_rm)
        self._register("write", "파일 내용 덮어쓰기 (write 파일명 내용)", self._cmd_write)
        self._register("append", "파일 내용 추가 (append 파일명 내용)", self._cmd_append)
        self._register("install", "가짜 패키지 설치 (install 패키지명)", self._cmd_install)
        self._register("pkgs", "설치된 패키지 목록", self._cmd_pkgs)
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

        return command.handler(args)

    def _cmd_help(self, _: list[str]) -> str:
        ordered = sorted(self._commands.values(), key=lambda c: c.name)
        return "\n".join(f"{cmd.name:<8} - {cmd.description}" for cmd in ordered)

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
        except:
            return "계산 오류"

    def _cmd_ls(self, args):
        if not self._files:
            return "파일 없음"
        return "\n".join(self._files.keys())

    def _cmd_touch(self, args):
        if not args:
            return "파일 이름 필요"
        self._files[args[0]] = ""
        return f"{args[0]} 생성됨"

    def _cmd_cat(self, args):
        if not args:
            return "파일 이름 필요"
        return self._files.get(args[0], "파일 없음")

    def _cmd_rm(self, args):
        if not args:
            return "파일 이름 필요"
        if args[0] not in self._files:
            return "파일 없음"
        del self._files[args[0]]
        return f"{args[0]} 삭제됨"

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
        self._files[name] += content
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
    os = NeoOS()
    print(f"NeoOS {VERSION} 부팅 완료. 'help'로 명령어를 확인하세요.")

    while os.running:
        try:
            line = input("neo> ")
        except EOFError:
            print()
            break

        output = os.execute_line(line)
        if output:
            print(output)


if __name__ == "__main__":
    run_shell()
