"""NeoOS 웹 터미널 서버 (VPS 모드).

브라우저에서 접속해서 NeoOS 셸을 원격으로 제어합니다.
- 실제 계정 저장: SQLite(database.db)
- 세션 토큰: 쿠키 기반 (비밀번호는 평문 저장하지 않음)
- 개인정보 처리방침 / 이용약관 페이지
- 14세 미만은 부모 동의 필요 (가입 시 확인)

실행: PORT=8080 python3 server.py
"""

import json
import os
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs

from Neoos import NeoOS

PORT = int(os.environ.get("PORT", 10000))
DB_PATH = os.environ.get("NEOOS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db"))


class SessionStore:
    """세션 토큰 -> NeoOS 인스턴스 매핑.

    각 세션은 독립된 NeoOS 인스턴스를 유지해 상태(파일 등)가 섞이지 않습니다.
    계정 데이터는 NeoOS 내부 SQLite에 공유 저장됩니다.
    토큰은 secrets.token_hex로 생성하므로 추측/재사용이 어렵습니다.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, NeoOS] = {}

    def create(self) -> tuple[str, NeoOS]:
        token = secrets.token_hex(16)
        neo = NeoOS(db_path=DB_PATH)
        self._sessions[token] = neo
        return token, neo

    def get(self, token: str) -> NeoOS | None:
        return self._sessions.get(token)

    def destroy(self, token: str) -> None:
        neo = self._sessions.pop(token, None)
        if neo is not None:
            neo.close()


SESSIONS = SessionStore()


def _find_token_from_headers(headers) -> str | None:
    cookie = headers.get("Cookie")
    if not cookie:
        return None
    c = SimpleCookie()
    try:
        c.load(cookie)
    except Exception:
        return None
    morsel = c.get("neoos_session")
    return morsel.value if morsel else None


class Handler(BaseHTTPRequestHandler):
    # ------------------------------------------------------------------
    # 유틸
    # ------------------------------------------------------------------
    def _send(self, status: int, content_type: str, body: bytes, extra_headers=None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict, extra_headers=None) -> None:
        self._send(status, "application/json; charset=utf-8",
                   json.dumps(payload, ensure_ascii=False).encode("utf-8"), extra_headers)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def _get_neo(self) -> tuple[NeoOS | None, str | None]:
        """요청의 세션 토큰에 해당하는 NeoOS 인스턴스를 반환."""
        token = _find_token_from_headers(self.headers)
        if token is None:
            return None, None
        neo = SESSIONS.get(token)
        if neo is None:
            return None, token
        return neo, token

    def _session_cookie_header(self, token: str, *, maxage=None) -> dict:
        if maxage:
            return {"Set-Cookie": f"neoos_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={maxage}"}
        # 세션 쿠키 (브라우저 종료 시 소멸)
        return {"Set-Cookie": f"neoos_session={token}; Path=/; HttpOnly; SameSite=Lax"}

    # ------------------------------------------------------------------
    # 페이지
    # ------------------------------------------------------------------
    def _page(self, title: str, body_html: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - NeoOS</title>
<style>
 body {{ margin:0; background:#0d1117; color:#c9d1d9; font-family:-apple-system,'Segoe UI',sans-serif; line-height:1.6; }}
 .wrap {{ max-width:760px; margin:0 auto; padding:32px 20px; }}
 a {{ color:#58a6ff; }}
 h1 {{ color:#58a6ff; }}
 .nav {{ background:#161b22; padding:10px 20px; border-bottom:1px solid #30363d; }}
 .nav a {{ margin-right:16px; text-decoration:none; }}
</style></head>
<body>
<div class="nav"><a href="/">🏠 홈</a><a href="/terms">이용약관</a><a href="/privacy">개인정보 처리방침</a></div>
<div class="wrap"><h1>{title}</h1>{body_html}</div>
</body></html>"""

    def _terms_page(self) -> str:
        return self._page("이용약관", """
<p><strong>최종 수정일: 2026년 8월 30일</strong></p>
<h2>제1조 (목적)</h2>
<p>본 약관은 NeoOS 웹 터미널(이하 "서비스")의 이용 조건 및 절차를 규정합니다.</p>
<h2>제2조 (약관의 동의)</h2>
<p>이용자는 본 약관에 동의해야만 서비스를 이용할 수 있습니다. 서비스 이용 시 약관에 동의한 것으로 간주합니다.</p>
<h2>제3조 (계정)</h2>
<p>① 계정은 본인 명의로 1인 1계정 원칙이며, 타인 명의 사용을 금지합니다.<br>
② 만 14세 미만의 미성년자는 <strong>법정대리인(부모)의 동의</strong>를 받은 경우에만 가입할 수 있습니다.<br>
③ 보안상 비밀번호는 암호화(SHA-256)되어 저장되며, 평문으로 저장되지 않습니다.</p>
<h2>제4조 (이용자의 의무)</h2>
<p>이용자는 서비스를 법령 및 약관에 따라 이용해야 하며, 서비스 운영을 방해하거나 타인의 계정을 침해하는 행위를 해서는 안 됩니다.</p>
<h2>제5조 (서비스 이용의 제한)</h2>
<p>① 이용자가 약관을 위반하거나 타인에게 피해를 주는 경우, 서비스 제공자는 사전 통지 없이 계정 이용을 제한할 수 있습니다.<br>
② 본 서비스는 교육 목적으로 제공되며, 실제 운영 체제의 기능을 완전히 보장하지 않습니다.</p>
<h2>제6조 (약관의 변경)</h2>
<p>서비스 제공자는 관련 법령을 위반하지 않는 범위에서 본 약관을 변경할 수 있으며, 변경 시 공지합니다.</p>
""")

    def _privacy_page(self) -> str:
        return self._page("개인정보 처리방침", """
<p><strong>시행일: 2026년 8월 30일</strong></p>
<h2>1. 수집하는 개인정보 항목</h2>
<p>서비스 가입 및 이용 과정에서 다음의 개인정보를 수집합니다.</p>
<ul>
<li>아이디(사용자명)</li>
<li>비밀번호 (SHA-256 암호화 저장, 원문 미보관)</li>
<li>출생연도 (연령 확인 및 부모 동의 판단 목적)</li>
<li>비밀번호 찾기용 회복 질문 답변</li>
</ul>
<h2>2. 개인정보의 이용 목적</h2>
<ul>
<li>계정 식별 및 로그인 인증</li>
<li>만 14세 미만 미성년자 법정대리인 동의 확인</li>
<li>비밀번호 분실 시 본인 확인</li>
</ul>
<h2>3. 개인정보의 보유 및 이용 기간</h2>
<p>계정이 유지되는 동안 보관하며, 계정 삭제 시 지체 없이 파기합니다.</p>
<h2>4. 개인정보의 제3자 제공</h2>
<p>수집한 개인정보를 제3자에게 제공하지 않습니다. 단, 법령에 따른 경우는 예외로 합니다.</p>
<h2>5. 이용자의 권리</h2>
<p>이용자는 언제든지 자신의 개인정보 열람·정정·삭제를 요청할 수 있습니다.</p>
<h2>6. 미성년자 보호</h2>
<p>만 14세 미만 아동의 개인정보는 <strong>법정대리인 동의가 없으면 수집하지 않습니다</strong>. 부모 동의가 있는 경우에만 처리하며, 아동의 개인정보는 보호를 위해 최소한으로만 처리합니다.</p>
<h2>7. 문의</h2>
<p>개인정보 관련 문의는 서비스 관리자(<code>admin</code>)에게 요청해 주세요.</p>
""")

    def _home_page(self) -> str:
        return """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NeoOS 웹 터미널</title>
<style>
  * { box-sizing: border-box; }
  body { margin:0; background:#0d1117; color:#c9d1d9; font-family:'Menlo','Monaco','Consolas',monospace; }
  #bar { padding:8px 14px; background:#161b22; border-bottom:1px solid #30363d; display:flex; justify-content:space-between; align-items:center; }
  #bar h1 { font-size:15px; margin:0; color:#58a6ff; }
  #user { font-size:13px; color:#8b949e; }
  #screen { height:calc(100vh - 96px); overflow-y:auto; padding:12px 16px; white-space:pre-wrap; word-break:break-all; line-height:1.45; }
  .cmd { color:#7ee787; } .prompt { color:#58a6ff; } .out { color:#c9d1d9; } .err { color:#f85149; }
  #inputrow { display:flex; padding:8px 16px; border-top:1px solid #30363d; }
  #cmd { flex:1; background:transparent; border:none; outline:none; color:#c9d1d9; font-family:inherit; font-size:14px; }
  .hidden { display:none; }
  #login { max-width:380px; margin:80px auto; background:#161b22; padding:28px; border-radius:8px; border:1px solid #30363d; }
  #login h2 { color:#58a6ff; margin-top:0; }
  #login input, #login select { width:100%; padding:10px; margin:8px 0; background:#0d1117; color:#c9d1d9; border:1px solid #30363d; border-radius:6px; font-family:inherit; }
  #login button { width:100%; padding:11px; margin-top:10px; background:#238636; color:#fff; border:none; border-radius:6px; font-size:15px; cursor:pointer; }
  .tabs { display:flex; gap:8px; margin-bottom:14px; }
  .tabs button { flex:1; padding:9px; background:#21262d; color:#c9d1d9; border:1px solid #30363d; border-radius:6px; cursor:pointer; }
  .tabs button.active { background:#1f6feb; color:#fff; }
  .field { font-size:12px; color:#8b949e; margin-top:6px; }
  .links { margin-top:16px; font-size:13px; text-align:center; }
  .links a { color:#58a6ff; text-decoration:none; margin:0 6px; }
  .error { color:#f85149; font-size:13px; margin-top:8px; min-height:18px; }
  .notice { font-size:12px; color:#d29922; margin-top:8px; }
</style></head>
<body>
  <div id="bar"><h1>🖥 NeoOS</h1><div id="user">user: <span id="username">-</span></div></div>

  <div id="login">
    <h2 id="loginTitle">로그인</h2>
    <div class="tabs">
      <button id="tabLogin" class="active" onclick="show('loginF')">로그인</button>
      <button id="tabReg" onclick="show('regF')">회원가입</button>
    </div>

    <form id="loginF" onsubmit="return doLogin(event)">
      <input id="li_user" placeholder="사용자명" autocomplete="username" required>
      <input id="li_pass" type="password" placeholder="비밀번호" autocomplete="current-password" required>
      <button type="submit">로그인</button>
      <div class="links"><a href="#" onclick="show('forgotF');return false;">비밀번호 찾기</a></div>
    </form>

    <form id="regF" class="hidden" onsubmit="return doReg(event)">
      <input id="r_user" placeholder="사용자명 (2자 이상)" required>
      <input id="r_pass" type="password" placeholder="비밀번호 (4자 이상)" required>
      <input id="r_birth" type="number" placeholder="출생연도 (예: 2010)" required>
      <input id="r_consent" type="password" placeholder="부모 동의 확인 (14세 미만: '동의' 입력)">
      <div class="field">만 14세 미만이면 보호자의 동의('동의')를 입력해야 합니다.</div>
      <input id="r_recovery" placeholder="비밀번호 찾기용 답 (예: 내 강아지 이름)">
      <div class="field">비밀번호를 잊었을 때 본인 확인에 사용됩니다.</div>
      <label style="font-size:12px;display:flex;align-items:center;gap:6px;margin-top:8px;">
        <input type="checkbox" id="r_agree" required style="width:auto;">
        <a href="/terms" target="_blank">이용약관</a> 및 <a href="/privacy" target="_blank">개인정보 처리방침</a>에 동의합니다.
      </label>
      <button type="submit">가입하기</button>
    </form>

    <form id="forgotF" class="hidden" onsubmit="return doForgot(event)">
      <input id="fg_user" placeholder="사용자명" required>
      <input id="fg_answer" placeholder="가입 시 설정한 회복 질문 답" required>
      <button type="submit">임시 비밀번호 발급</button>
      <div class="notice">임시 비밀번호가 화면에 표시됩니다.<br>로그인 후 passwd 명령어로 변경하세요.</div>
    </form>
    <div class="error" id="authmsg"></div>
  </div>

  <div id="termWrap" class="hidden">
    <div id="screen"><span class="out">NeoOS 웹 터미널 부팅 완료. 'help'로 명령어를 확인하세요.</span></div>
    <div id="inputrow"><span class="prompt">neo&gt;</span><input id="cmd" autocomplete="off" autofocus placeholder="명령어를 입력..."></div>
  </div>

<script>
  const $ = id => document.getElementById(id);
  let token = null;
  let history = [];
  let histIdx = -1;

  function show(id) {
    ['loginF','regF','forgotF'].forEach(f => $(f).classList.add('hidden'));
    $(id).classList.remove('hidden');
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    if (id === 'loginF') $('tabLogin').classList.add('active');
    else if (id === 'regF') $('tabReg').classList.add('active');
    $('authmsg').textContent = '';
  }
  window.show = show;

  async function api(path, body) {
    const opt = { method: 'POST', headers: { 'Content-Type': 'application/json' } };
    if (body) opt.body = JSON.stringify(body);
    const res = await fetch(path, opt);
    return res.json();
  }

  async function doLogin(e) {
    e.preventDefault();
    const d = await api('/api/login', { username: $('li_user').value, password: $('li_pass').value });
    if (d.ok) { token = d.token; enterTerminal(); }
    else $('authmsg').textContent = d.error || '로그인 실패';
    return false;
  }

  async function doReg(e) {
    e.preventDefault();
    const consent = $('r_consent').value ? '동의' : '';
    const d = await api('/api/register', {
      username: $('r_user').value, password: $('r_pass').value,
      birth_year: $('r_birth').value, consent: consent, recovery: $('r_recovery').value
    });
    $('authmsg').textContent = d.message || d.error || '';
    if (d.ok) {
      $('authmsg').textContent = '가입 완료! 로그인하세요.';
      // 성공 시 로그인 탭으로
      show('loginF');
      $('li_user').value = $('r_user').value;
    }
    return false;
  }

  async function doForgot(e) {
    e.preventDefault();
    const d = await api('/api/forgot', { username: $('fg_user').value, answer: $('fg_answer').value });
    $('authmsg').textContent = d.message || d.error || '';
    return false;
  }

  async function enterTerminal() {
    $('login').classList.add('hidden');
    $('termWrap').classList.remove('hidden');
    $('username').textContent = token ? '세션 활성' : '-';
    refreshStatus();
    scrollBottom();
    $('cmd').focus();
  }

  function scrollBottom() { $('screen').scrollTop = $('screen').scrollHeight; }

  async function refreshStatus() {
    const d = await api('/api/whoami', {});
    $('username').textContent = d.user || '(비로그인)';
  }

  async function run(cmd) {
    if (!cmd.trim()) return;
    line('neo> ' + cmd, 'cmd');
    history.push(cmd); histIdx = history.length;
    const d = await api('/api/command', { command: cmd });
    if (String(cmd.trim()) === 'clear') { $('screen').innerHTML = ''; }
    else if (d.output) line(d.output, isErr(d.output) ? 'err' : 'out');
    if (d.user !== undefined) $('username').textContent = d.user || '(비로그인)';
    scrollBottom();
  }

  function line(t, cls) {
    const div = document.createElement('div');
    div.className = cls || 'out';
    div.textContent = t;
    $('screen').appendChild(div);
    $('screen').appendChild(document.createElement('br'));
    scrollBottom();
  }

  function isErr(o) {
    return /알 수 없는 명령어|오류 발생|로그인 실패/.test(o);
  }

  $('cmd').addEventListener('keydown', e => {
    if (e.key === 'Enter') { const v = $('cmd').value; $('cmd').value = ''; run(v); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); if (histIdx > 0) { histIdx--; $('cmd').value = history[histIdx]; } }
    else if (e.key === 'ArrowDown') { e.preventDefault(); if (histIdx < history.length) { histIdx++; $('cmd').value = history[histIdx] || ''; } }
  });
  $('screen').addEventListener('click', () => $('cmd').focus());
  show('loginF');
</script>
</body></html>"""

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def _api_login(self):
        data = self._read_json()
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        # 새 세션 (로그인 시도용)
        token, neo = SESSIONS.create()
        result = neo.execute_line(f"login {username} {password}")
        if neo.current_user is not None:
            # 성공: 세션 유지
            return self._send_json(200, {"ok": True, "token": token, "user": neo.current_user},
                                   extra_headers=self._session_cookie_header(token))
        # 실패: 세션 폐기
        SESSIONS.destroy(token)
        return self._send_json(401, {"ok": False, "error": result})

    def _api_register(self):
        data = self._read_json()
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        birth_year = data.get("birth_year")
        consent = data.get("consent") or ""
        recovery = data.get("recovery") or ""
        args = [username, password]
        if birth_year:
            args.append(str(birth_year))
            # 위치 안정화: 성인은 자동 동의, 미성년자는 입력값 사용 (동의가 없으면 거부됨)
            args.append("동의" if consent in ("동의", "agree", "yes", "y", "네") else "거부")
        if recovery:
            args.append(recovery)
        # 임시 NeoOS로 가입 처리 (계정은 공유 DB에 저장)
        neo = NeoOS(db_path=DB_PATH)
        result = neo.execute_line("register " + " ".join(args))
        neo.close()
        if "계정이 생성되었습니다" in result:
            return self._send_json(200, {"ok": True, "message": result})
        return self._send_json(400, {"ok": False, "message": result})

    def _api_forgot(self):
        data = self._read_json()
        username = (data.get("username") or "").strip()
        answer = (data.get("answer") or "").strip()
        neo = NeoOS(db_path=DB_PATH)
        result = neo.execute_line(f"forgot {username} {answer}")
        neo.close()
        return self._send_json(200, {"message": result})

    def _api_command(self):
        neo, _ = self._get_neo()
        if neo is None:
            return self._send_json(401, {"error": "로그인이 필요합니다. 새로고침 후 다시 로그인하세요."})
        data = self._read_json()
        cmd = data.get("command", "")
        output = neo.execute_line(cmd)
        return self._send_json(200, {"output": output, "user": neo.current_user})

    def _api_whoami(self):
        neo, _ = self._get_neo()
        return self._send_json(200, {"user": neo.current_user if neo else None})

    def _api_logout(self):
        _, token = self._get_neo()
        if token:
            SESSIONS.destroy(token)
        return self._send_json(200, {"ok": True}, extra_headers={
            "Set-Cookie": "neoos_session=; Path=/; HttpOnly; Max-Age=0"
        })

    # ------------------------------------------------------------------
    # 라우팅
    # ------------------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", self._home_page().encode("utf-8"))
        elif path == "/terms":
            self._send(200, "text/html; charset=utf-8", self._terms_page().encode("utf-8"))
        elif path == "/privacy":
            self._send(200, "text/html; charset=utf-8", self._privacy_page().encode("utf-8"))
        else:
            self._send(404, "text/plain; charset=utf-8", b"Not Found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/login":
            self._api_login()
        elif path == "/api/register":
            self._api_register()
        elif path == "/api/forgot":
            self._api_forgot()
        elif path == "/api/command":
            self._api_command()
        elif path == "/api/whoami":
            self._api_whoami()
        elif path == "/api/logout":
            self._api_logout()
        else:
            self._send(404, "text/plain; charset=utf-8", b"Not Found")

    def log_message(self, fmt, *args):
        pass


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print("=" * 50)
    print("NeoOS 웹 터미널 서버 (VPS 모드)")
    print(f"  접속:   http://localhost:{PORT}")
    print(f"  DB:     {DB_PATH}")
    print(f"  기본:   admin / admin")
    print("  약관:   /terms  / privacy: /privacy")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
