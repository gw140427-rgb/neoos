"""Vercel WSGI entrypoint for NeoOS.

Render continues to use server.py. This module only adapts the same
application to Vercel's Python function runtime.
"""
import json
from http.cookies import SimpleCookie

from Neoos import NeoOS
from server import DB_PATH, SESSIONS, Handler


def _json(start_response, status, payload, extra=None):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("X-Content-Type-Options", "nosniff"),
    ]
    if extra:
        headers.extend(extra)
    start_response(status, headers)
    return [body]


def _html(start_response, body):
    body = body.encode("utf-8")
    start_response("200 OK", [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("X-Content-Type-Options", "nosniff"),
    ])
    return [body]


def _read_json(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
        raw = environ["wsgi.input"].read(length) if length else b"{}"
        value = json.loads(raw.decode("utf-8"))
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _token(environ):
    cookie = SimpleCookie()
    try:
        cookie.load(environ.get("HTTP_COOKIE", ""))
    except Exception:
        return None
    morsel = cookie.get("neoos_session")
    return morsel.value if morsel else None


def _page(method):
    obj = Handler.__new__(Handler)
    return getattr(obj, method)()


def _cookie(token, clear=False):
    value = (
        "neoos_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
        if clear
        else f"neoos_session={token}; Path=/; HttpOnly; SameSite=Lax"
    )
    return [("Set-Cookie", value)]


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if method == "GET":
        pages = {
            "/": "_home_page",
            "/index.html": "_home_page",
            "/terms": "_terms_page",
            "/privacy": "_privacy_page",
        }
        page = pages.get(path)
        if page:
            return _html(start_response, _page(page))
        return _json(start_response, "404 Not Found", {"error": "Not Found"})

    if method != "POST":
        return _json(start_response, "405 Method Not Allowed", {"error": "Method Not Allowed"})

    data = _read_json(environ)

    if path == "/api/login":
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")
        token, neo = SESSIONS.create()
        try:
            result = neo.execute_line("login " + username + " " + password)
        except Exception:
            SESSIONS.destroy(token)
            return _json(start_response, "500 Internal Server Error", {"ok": False, "error": "로그인 처리 중 오류가 발생했습니다."})
        if neo.current_user is not None:
            return _json(start_response, "200 OK",
                         {"ok": True, "token": token, "user": neo.current_user},
                         _cookie(token))
        SESSIONS.destroy(token)
        return _json(start_response, "401 Unauthorized", {"ok": False, "error": result})

    if path == "/api/register":
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")
        birth_year = data.get("birth_year")
        consent = str(data.get("consent") or "")
        recovery = str(data.get("recovery") or "")
        args = [username, password]
        if birth_year:
            args.extend([
                str(birth_year),
                "동의" if consent in ("동의", "agree", "yes", "y", "네") else "거부",
            ])
        if recovery:
            args.append(recovery)
        neo = NeoOS(db_path=DB_PATH)
        try:
            result = neo.execute_line("register " + " ".join(args))
        finally:
            neo.close()
        ok = "계정이 생성되었습니다" in result
        return _json(start_response, "200 OK" if ok else "400 Bad Request",
                     {"ok": ok, "message": result})

    if path == "/api/forgot":
        username = str(data.get("username") or "").strip()
        answer = str(data.get("answer") or "").strip()
        neo = NeoOS(db_path=DB_PATH)
        try:
            result = neo.execute_line("forgot " + username + " " + answer)
        finally:
            neo.close()
        return _json(start_response, "200 OK", {"message": result})

    if path == "/api/command":
        token = _token(environ)
        neo = SESSIONS.get(token) if token else None
        if neo is None:
            return _json(start_response, "401 Unauthorized",
                         {"error": "로그인이 필요합니다. 새로고침 후 다시 로그인하세요."})
        command = str(data.get("command") or "")
        output = neo.execute_line(command)
        return _json(start_response, "200 OK",
                     {"output": output, "user": neo.current_user})

    if path == "/api/whoami":
        token = _token(environ)
        neo = SESSIONS.get(token) if token else None
        return _json(start_response, "200 OK",
                     {"user": neo.current_user if neo else None})

    if path == "/api/logout":
        token = _token(environ)
        if token:
            SESSIONS.destroy(token)
        return _json(start_response, "200 OK", {"ok": True}, _cookie(None, clear=True))

    return _json(start_response, "404 Not Found", {"error": "Not Found"})


handler = app
