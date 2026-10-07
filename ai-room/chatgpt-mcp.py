#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
import os
import subprocess
from fastmcp import FastMCP

ROOT = Path(os.environ.get("CHATGPT_WORKSPACE", Path.home() / "ai-room" / "chatgpt-workspace")).expanduser().resolve()
ROOT.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("YangYang Termux Workbench")

def safe_path(path: str = ".") -> Path:
    p = (ROOT / path).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError("workspace 밖의 경로는 사용할 수 없습니다.")
    return p

@mcp.tool
def workspace_info() -> str:
    """작업공간 경로와 기본 상태를 확인합니다."""
    return f"workspace={ROOT}\nfiles={len(list(ROOT.rglob('*')))}"

@mcp.tool
def list_files(path: str = ".") -> str:
    """작업공간 안의 파일/폴더 목록을 보여줍니다."""
    p = safe_path(path)
    if not p.is_dir():
        raise ValueError("디렉터리가 아닙니다.")
    return "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir()))

@mcp.tool
def read_file(path: str) -> str:
    """작업공간 안의 텍스트 파일을 읽습니다."""
    p = safe_path(path)
    if not p.is_file():
        raise ValueError("파일이 없습니다.")
    if p.stat().st_size > 1_000_000:
        raise ValueError("1 MB보다 큰 파일은 읽지 않습니다.")
    return p.read_text(encoding="utf-8")

@mcp.tool
def write_file(path: str, content: str) -> str:
    """작업공간 안에 텍스트 파일을 생성하거나 수정합니다."""
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"saved: {p.relative_to(ROOT)}"

@mcp.tool
def run_safe(command: str) -> str:
    """작업공간에서 허용된 개발 명령만 실행합니다."""
    allowed = ("git ", "git", "python ", "python3 ", "pytest", "npm ", "node ", "bash -n ", "sh -n ")
    if not command.strip().startswith(allowed):
        raise ValueError("허용되지 않은 명령입니다. git/python/pytest/npm/node 및 셸 문법검사만 허용합니다.")
    result = subprocess.run(command, shell=True, cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    return result.stdout[-12000:]

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
