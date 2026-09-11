"""NeoOS: tiny educational shell-like OS simulator."""

import ast
import hashlib
import operator
import os
import random
import secrets
import sqlite3
import time
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

CommandHandler = Callable[[list[str]], str]

VERSION = "v0.5.0 Beta"

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("허용되지 않는 식입니다.")


@dataclass
class Command:
    name: str
    description: str
    handler: CommandHandler


class NeoOS:
    def __init__(self, db_path: str | None = None) -> None:
        self._running = True
        self._commands: dict[str, Command] = {}
        self._files: dict[str, str] = {}
        self._packages: set[str] = set()
        self._current_user: str | None = None
        self._history: list[str] = []
        # 실제 계정 저장 (SQLite). db_path가 없으면 메모리 전용 (테스트/교육용).
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._users: dict[str, dict] = {}
        self._init_db()
        self._ensure_admin()
        self._register_builtin_commands()

    # ------------------------------------------------------------------
    # 데이터베이스 (계정 실제 저장)
    # ------------------------------------------------------------------
    def _init_db(self) -> None:
        if self._db_path is None:
            return  # 메모리 모드: _users dict에 저장
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username   TEXT PRIMARY KEY,
                password   TEXT NOT NULL,
                birth_year INTEGER,
                parent_consent INTEGER DEFAULT 0,
                recovery   TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()
        self._load_users_from_db()

    def _load_users_from_db(self) -> None:
        if self._conn is None:
            return
        for row in self._conn.execute("SELECT username, password, birth_year, parent_consent, recovery FROM users"):
            username, password, birth_year, parent_consent, recovery = row
            self._users[username] = {
                "password": password,
                "birth_year": birth_year,
                "parent_consent": bool(parent_consent),
                "recovery": recovery,
            }

    def _save_user_to_db(self, username: str) -> None:
        if self._conn is None:
            return
        u = self._users[username]
        self._conn.execute(
            "INSERT OR REPLACE INTO users (username, password, birth_year, parent_consent, recovery, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                username,
                u["password"],
                u["birth_year"],
                int(u["parent_consent"]),
                u["recovery"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def _remove_user_from_db(self, username: str) -> None:
        if self._conn is None:
            return
        self._conn.execute("DELETE FROM users WHERE username = ?", (username,))
        self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()

    @staticmethod
    def _hash_password(password: str) -> str:
        # 보안 강화: SHA-256 해시 (평문은 절대 저장하지 않음)
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _ensure_admin(self) -> None:
        # 기본 관리자 계정 (첫 실행 시에만 생성)
        if "admin" not in self._users:
            self._users["admin"] = {
                "password": self._hash_password("admin"),
                "birth_year": None,
                "parent_consent": True,
                "recovery": None,
            }
            if self._conn is not None:
                self._save_user_to_db("admin")

    @property
    def current_user(self) -> str | None:
        return self._current_user

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
        self._register("pwd", "현재 경로 출력", self._cmd_pwd)
        self._register("uname", "시스템 정보 출력", self._cmd_uname)
        self._register("history", "명령어 기록 출력", self._cmd_history)
        self._register("version", "NeoOS 버전 정보 출력", self._cmd_version)
        self._register("똥", "???", self._cmd_poop)

        # 계정/로그인 기능
        self._register("register", "새 계정 생성 (register 사용자명 비밀번호 [출생연도] [회복질문답])", self._cmd_register)
        self._register("login", "로그인 (login 사용자명 비밀번호)", self._cmd_login)
        self._register("logout", "로그아웃", self._cmd_logout)
        self._register("whoami", "현재 로그인한 사용자 출력", self._cmd_whoami)
        self._register("passwd", "비밀번호 변경 (passwd 새비밀번호)", self._cmd_passwd)
        self._register("users", "등록된 사용자 목록", self._cmd_users)
        self._register("forgot", "비밀번호 찾기 (forgot 사용자명 응답)", self._cmd_forgot)
        self._register("resetpw", "비밀번호 초기화 (관리자 전용)", self._cmd_resetpw)

    def execute_line(self, line: str) -> str:
        # 입력 정리 (^@ 같은 거 제거)
        line = line.replace("\x00", "").strip()
        if line:
            self._history.append(line)

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

    def _cmd_calc(self, args: list[str]) -> str:
        try:
            expr = " ".join(args)
            if not expr:
                return "사용법: calc 2 + 3"
            tree = ast.parse(expr, mode="eval")
            return str(_safe_eval(tree))
        except ZeroDivisionError:
            return "0으로 나눌 수 없습니다."
        except Exception:
            return "계산 오류"

    def _cmd_ls(self, args: list[str]) -> str:
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

    def _cmd_touch(self, args: list[str]) -> str:
        if not args:
            return "파일 이름 필요"
        name = args[0]
        if name in self._files:
            return f"{name} 이미 존재함"
        self._files[name] = ""
        return f"{args[0]} 생성됨"

    def _cmd_cat(self, args: list[str]) -> str:
        if not args:
            return "파일 이름 필요"
        if args[0] not in self._files:
            return f"{args[0]} 파일 없음"
        return self._files[args[0]]

    def _cmd_rm(self, args: list[str]) -> str:
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

    def _cmd_write(self, args: list[str]) -> str:
        if len(args) < 2:
            return "사용법: write 파일명 내용"
        name, content = args[0], " ".join(args[1:])
        self._files[name] = content
        return f"{name}에 저장됨"

    def _cmd_append(self, args: list[str]) -> str:
        if len(args) < 2:
            return "사용법: append 파일명 내용"
        name, content = args[0], " ".join(args[1:])
        if name not in self._files:
            self._files[name] = content
            return f"{name}에 추가됨"
        # 기존 내용이 비어있지 않으면 줄바꿈을 넣고 추가
        if self._files[name]:
            self._files[name] += "\n" + content
        else:
            self._files[name] = content
        return f"{name}에 추가됨"

    def _cmd_install(self, args: list[str]) -> str:
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

    def _cmd_pkgs(self, _: list[str]) -> str:
        if not self._packages:
            return "설치된 패키지 없음. 'install 패키지명' 으로 설치하세요."
        return "\n".join(f"📦 {p}" for p in sorted(self._packages))

    def _cmd_version(self, _: list[str]) -> str:
        return f"NeoOS {VERSION}"

    def _cmd_pwd(self, _: list[str]) -> str:
        if self._current_user:
            return f"/home/{self._current_user}"
        return "/"

    def _cmd_uname(self, args: list[str]) -> str:
        if args and args[0] == "-a":
            return f"NeoOS {VERSION} neoos {self._current_user or 'guest'} x86_64 Python"
        return f"NeoOS {VERSION}"

    def _cmd_history(self, args: list[str]) -> str:
        if not self._history:
            return "기록 없음"
        n = len(self._history)
        if args and args[0].isdigit():
            n = min(int(args[0]), len(self._history))
            hist = self._history[-n:]
            start = len(self._history) - n + 1
        else:
            hist = self._history
            start = 1
        lines = []
        for i, cmd in enumerate(hist, start=start):
            lines.append(f"{i:4d}  {cmd}")
        return "\n".join(lines)

    def _cmd_poop(self, _: list[str]) -> str:
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

    def _cmd_register(self, args: list[str]) -> str:
        """register 사용자명 비밀번호 [출생연도] [회복질문답]

        14세 미만(2013년 이후 출생)은 부모 동의가 필요합니다.
        출생연도를 생략하면 자동으로 14세 이상으로 간주합니다.
        """
        if len(args) < 2:
            return "사용법: register 사용자명 비밀번호 [출생연도] [회복질문답]"
        name, password = args[0], args[1]
        if len(name) < 2:
            return "사용자명은 2자 이상이어야 합니다."
        if len(password) < 4:
            return "비밀번호는 4자 이상이어야 합니다."
        if name in self._users:
            return f"{name} 계정이 이미 존재합니다."
        if any(ch.isspace() for ch in name):
            return "사용자명에 공백을 포함할 수 없습니다."

        # 부모 동의 처리
        current_year = datetime.now(timezone.utc).year
        birth_year = None
        parent_consent = None
        recovery = None

        if len(args) >= 3:
            try:
                birth_year = int(args[2])
            except ValueError:
                return "출생연도는 숫자(예: 2012)여야 합니다."
            age = current_year - birth_year
            if age < 14:
                if len(args) < 4:
                    return (
                        f"{age}세는 만 14세 미만입니다.\n"
                        "부모 동의가 필요합니다.\n"
                        "사용법: register 사용자명 비밀번호 출생연도 부모동의(예: 동의)"
                    )
                if args[3] in ("동의", "agree", "yes", "y", "네"):
                    parent_consent = True
                else:
                    parent_consent = False
                    return "부모 동의가 거부되었습니다. 만 14세 미만은 부모 동의가 있어야 가입할 수 있습니다."
            else:
                parent_consent = True
            # 회복 질문 답
            if len(args) >= 5:
                recovery = " ".join(args[4:])

        if parent_consent is None:
            parent_consent = True

        self._users[name] = {
            "password": self._hash_password(password),
            "birth_year": birth_year,
            "parent_consent": parent_consent,
            "recovery": recovery,
        }
        self._save_user_to_db(name)
        note = ""
        if parent_consent is False:
            note = "\n(부모 동의 대기 중: 아직 로그인할 수 없습니다.)"
        return f"{name} 계정이 생성되었습니다.{note}"

    def _cmd_login(self, args: list[str]) -> str:
        if len(args) < 2:
            return "사용법: login 사용자명 비밀번호"
        name, password = args[0], args[1]
        user = self._users.get(name)
        if user is None or user["password"] != self._hash_password(password):
            return "로그인 실패: 사용자명 또는 비밀번호가 올바르지 않습니다."
        if user.get("parent_consent") is False:
            return "부모 동의가 완료되지 않은 계정입니다. 관리자에게 문의하세요."
        if user.get("parent_consent") is None and name != "admin":
            return "부모 동의 상태를 확인할 수 없습니다. 관리자에게 문의하세요."
        self._current_user = name
        return f"{name} 님, 환영합니다! NeoOS에 로그인했습니다."

    def _cmd_logout(self, _: list[str]) -> str:
        if self._current_user is None:
            return "로그인 상태가 아닙니다."
        name = self._current_user
        self._current_user = None
        return f"{name} 님이 로그아웃했습니다."

    def _cmd_whoami(self, _: list[str]) -> str:
        if self._current_user is None:
            return "로그인하지 않았습니다."
        return self._current_user

    def _cmd_passwd(self, args: list[str]) -> str:
        if self._current_user is None:
            return "로그인한 상태에서만 비밀번호를 변경할 수 있습니다."
        if len(args) < 1:
            return "사용법: passwd 새비밀번호"
        if len(args[0]) < 4:
            return "비밀번호는 4자 이상이어야 합니다."
        self._users[self._current_user]["password"] = self._hash_password(args[0])
        if self._conn is not None:
            self._save_user_to_db(self._current_user)
        return "비밀번호가 변경되었습니다."

    def _cmd_users(self, args: list[str]) -> str:
        # users [전체] : 전체 보기는 관리자와 서버 소유자만
        if not self._users:
            return "등록된 사용자 없음"
        if args and args[0] == "--all" and self._current_user == "admin":
            lines = []
            for name in sorted(self._users):
                u = self._users[name]
                age_txt = f"출생 {u['birth_year']}" if u["birth_year"] else "연령 미확인"
                consent_txt = "부모동의" if u["parent_consent"] else "미동의"
                lines.append(f"👤 {name} | {age_txt} | {consent_txt}")
            return "\n".join(lines)
        return "\n".join(f"👤 {name}" for name in sorted(self._users))

    def _cmd_forgot(self, args: list[str]) -> str:
        """forgot 사용자명 회복질문답
        가입 시 설정한 회복 질문 답을 맞히면 새 비밀번호를 발급합니다.
        """
        if len(args) < 2:
            return "사용법: forgot 사용자명 회복질문답\n(가입 시 설정한 회복 질문 답을 입력하세요)"
        name, answer = args[0], " ".join(args[1:])
        user = self._users.get(name)
        if user is None:
            return "존재하지 않는 사용자입니다."
        if not user.get("recovery"):
            return "이 계정에는 비밀번호 찾기(회복 질문)가 설정되지 않았습니다."
        if user["recovery"] != answer:
            return "회복 질문 답이 올바르지 않습니다."

        # 임시 비밀번호 발급 (재로그인용)
        temp = secrets.token_hex(4)
        user["password"] = self._hash_password(temp)
        if self._conn is not None:
            self._save_user_to_db(name)
        return f"임시 비밀번호가 발급되었습니다: {temp}\n'login {name} {temp}' 로 로그인 후 'passwd' 로 변경하세요."

    def _cmd_resetpw(self, args: list[str]) -> str:
        """resetpw 사용자명 새비밀번호 (관리자 전용)"""
        if self._current_user != "admin":
            return "관리자(admin)만 사용할 수 있습니다."
        if len(args) < 2:
            return "사용법: resetpw 사용자명 새비밀번호"
        name, newpw = args[0], args[1]
        user = self._users.get(name)
        if user is None:
            return "존재하지 않는 사용자입니다."
        if len(newpw) < 4:
            return "비밀번호는 4자 이상이어야 합니다."
        user["password"] = self._hash_password(newpw)
        if self._conn is not None:
            self._save_user_to_db(name)
        return f"{name} 의 비밀번호가 관리자에 의해 초기화되었습니다."


def run_shell(db_path: str | None = None) -> None:
    neo = NeoOS(db_path=db_path)
    print(f"NeoOS {VERSION} 부팅 완료. 'help'로 명령어를 확인하세요.")
    try:
        while neo.running:
            try:
                line = input("neo> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            output = neo.execute_line(line)
            if output:
                print(output)
    finally:
        neo.close()


if __name__ == "__main__":
    # 웹 서버(server.py)는 DB 파일 경로를 넘겨 실제 계정 저장을 켭니다.
    run_shell(db_path=os.environ.get("NEOOS_DB") if "os" in globals() else None)
