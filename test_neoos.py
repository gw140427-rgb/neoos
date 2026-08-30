"""NeoOS 유닛 테스트.

실행: python3 -m unittest test_neoos -v
"""

import tempfile
import unittest
from pathlib import Path

from Neoos import NeoOS, VERSION


class NeoOSTestCase(unittest.TestCase):
    def setUp(self):
        self.os = NeoOS()

    def test_echo(self):
        self.assertEqual(self.os.execute_line("echo 안녕하세요"), "안녕하세요")

    def test_empty_line(self):
        self.assertEqual(self.os.execute_line(""), "")
        self.assertEqual(self.os.execute_line("   "), "")

    def test_unknown_command(self):
        result = self.os.execute_line("없는명령어")
        self.assertIn("알 수 없는 명령어", result)
        # 셸은 계속 실행 중이어야 한다
        self.assertTrue(self.os.running)

    def test_calc_basic(self):
        self.assertEqual(self.os.execute_line("calc 2 + 3 * 4"), "14")
        self.assertEqual(self.os.execute_line("calc (2 + 3) * 4"), "20")
        self.assertEqual(self.os.execute_line("calc 10 / 4"), "2.5")

    def test_calc_rejects_non_arithmetic(self):
        self.assertIn("계산 오류", self.os.execute_line("calc __import__('os')"))
        self.assertIn("계산 오류", self.os.execute_line("calc 'a'"))

    def test_calc_division_by_zero(self):
        self.assertEqual(self.os.execute_line("calc 1 / 0"), "0으로 나눌 수 없습니다.")

    def test_calc_no_args(self):
        self.assertIn("사용법", self.os.execute_line("calc"))

    def test_version_command(self):
        self.assertEqual(self.os.execute_line("version"), f"NeoOS {VERSION}")

    def test_file_lifecycle(self):
        self.assertEqual(self.os.execute_line("touch a.txt"), "a.txt 생성됨")
        # 이미 존재하는 파일을 다시 touch 하면 덮어쓰지 않음
        self.assertIn("이미 존재함", self.os.execute_line("touch a.txt"))

        self.assertEqual(self.os.execute_line("write a.txt 반가워요"), "a.txt에 저장됨")
        self.assertEqual(self.os.execute_line("cat a.txt"), "반가워요")

        ls = self.os.execute_line("ls")
        self.assertIn("a.txt", ls)

    def test_cat_missing_file(self):
        self.assertIn("파일 없음", self.os.execute_line("cat ghost.txt"))

    def test_write_requires_args(self):
        self.assertIn("사용법", self.os.execute_line("write"))

    def test_append_creates_missing_file(self):
        self.assertEqual(self.os.execute_line("append new.txt 첫줄"), "new.txt에 추가됨")
        self.assertEqual(self.os.execute_line("cat new.txt"), "첫줄")

    def test_append_joins_with_newline(self):
        self.os.execute_line("touch b.txt")
        self.os.execute_line("write b.txt 첫째줄")
        self.os.execute_line("append b.txt 둘째줄")
        self.assertEqual(self.os.execute_line("cat b.txt"), "첫째줄\n둘째줄")

    def test_rm(self):
        self.os.execute_line("touch c.txt")
        self.assertEqual(self.os.execute_line("rm c.txt"), "c.txt 삭제됨")
        self.assertIn("파일 없음", self.os.execute_line("cat c.txt"))

    def test_rm_force_missing(self):
        result = self.os.execute_line("rm -f ghost.txt")
        self.assertIn("ghost.txt 없음", result)

    def test_exit(self):
        self.assertEqual(self.os.execute_line("exit"), "NeoOS를 종료합니다.")
        self.assertFalse(self.os.running)

    def test_time_output_format(self):
        import re

        pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC"
        self.assertRegex(self.os.execute_line("time"), pattern)

    def test_null_bytes_are_stripped(self):
        self.assertEqual(self.os.execute_line("\x00echo 하이\x00"), "하이")

    def test_register_new_account(self):
        self.assertEqual(self.os.execute_line("register bob secret"), "bob 계정이 생성되었습니다.")

    def test_register_requires_args(self):
        self.assertIn("사용법", self.os.execute_line("register"))

    def test_register_duplicate(self):
        self.os.execute_line("register bob secret")
        self.assertIn("이미 존재", self.os.execute_line("register bob other"))

    def test_login_success(self):
        self.os.execute_line("register bob secret")
        self.assertEqual(self.os.execute_line("login bob secret"), "bob 님, 환영합니다! NeoOS에 로그인했습니다.")
        self.assertEqual(self.os.current_user, "bob")

    def test_login_wrong_password(self):
        self.os.execute_line("register bob secret")
        self.assertIn("로그인 실패", self.os.execute_line("login bob wrong"))
        self.assertIsNone(self.os.current_user)

    def test_login_unknown_user(self):
        self.assertIn("로그인 실패", self.os.execute_line("login ghost x"))

    def test_whoami_when_not_logged_in(self):
        self.assertEqual(self.os.execute_line("whoami"), "로그인하지 않았습니다.")

    def test_whoami_when_logged_in(self):
        self.os.execute_line("login admin admin")
        self.assertEqual(self.os.execute_line("whoami"), "admin")

    def test_logout(self):
        self.os.execute_line("login admin admin")
        self.assertEqual(self.os.execute_line("logout"), "admin 님이 로그아웃했습니다.")
        self.assertEqual(self.os.execute_line("whoami"), "로그인하지 않았습니다.")

    def test_logout_when_not_logged_in(self):
        self.assertEqual(self.os.execute_line("logout"), "로그인 상태가 아닙니다.")

    def test_passwd_requires_login(self):
        self.assertIn("로그인한 상태에서만", self.os.execute_line("passwd newpass"))

    def test_passwd_changes_password(self):
        self.os.execute_line("login admin admin")
        self.assertEqual(self.os.execute_line("passwd admin123"), "비밀번호가 변경되었습니다.")
        self.os.execute_line("logout")
        self.assertIn("로그인 실패", self.os.execute_line("login admin admin"))
        self.assertIn("환영합니다", self.os.execute_line("login admin admin123"))

    def test_users_lists_accounts(self):
        result = self.os.execute_line("users")
        self.assertIn("admin", result)

    def test_register_short_password_rejected(self):
        self.assertIn("4자 이상", self.os.execute_line("register bob ab"))

    def test_register_username_with_space_rejected(self):
        # 셸은 공백으로 인자를 나누므로, 사용자명에 공백이 들어가면 2+개 인자로 분리됨.
        result = self.os.execute_line("register 'bob name' secret")
        # 출생연도 자리에 'name'이 들어가 숫자 파싱에서 걸림 -> 가입 실패
        self.assertNotIn("계정이 생성되었습니다", result)

    def test_register_adult_no_parent_consent_needed(self):
        self.os.execute_line("register adult1 secret 1990")
        self.assertEqual(self.os.execute_line("login adult1 secret"), "adult1 님, 환영합니다! NeoOS에 로그인했습니다.")

    def test_register_minor_requires_consent(self):
        result = self.os.execute_line("register kid secret 2016")
        self.assertIn("부모 동의", result)
        self.assertIn("만 14세", result)

    def test_register_minor_with_consent(self):
        self.os.execute_line("register kid2 secret 2016 동의")
        self.assertEqual(self.os.execute_line("login kid2 secret"), "kid2 님, 환영합니다! NeoOS에 로그인했습니다.")

    def test_register_minor_consent_denied(self):
        result = self.os.execute_line("register kid3 secret 2016 아니")
        self.assertIn("부모 동의가 거부", result)
        # 아직 로그인 불가
        self.assertIsNone(self.os.current_user)

    def test_forgot_requires_args(self):
        self.assertIn("사용법", self.os.execute_line("forgot bob"))

    def test_forgot_unknown_user(self):
        self.assertIn("존재하지 않는 사용자", self.os.execute_line("forgot ghost x"))

    def test_forgot_wrong_answer(self):
        self.os.execute_line("register bob secret 1995 동의 내강아지")
        self.assertIn("올바르지 않습니다", self.os.execute_line("forgot bob 엉뚱한답"))

    def test_forgot_issues_temp_password(self):
        self.os.execute_line("register bob secret 1995 동의 내강아지")
        result = self.os.execute_line("forgot bob 내강아지")
        self.assertIn("임시 비밀번호가 발급되었습니다", result)
        # 기존 비밀번호로는 로그인 불가
        self.assertIn("로그인 실패", self.os.execute_line("login bob secret"))

    def test_resetpw_requires_admin(self):
        self.assertEqual(self.os.execute_line("resetpw bob xxxx"), "관리자(admin)만 사용할 수 있습니다.")

    def test_resetpw_as_admin(self):
        self.os.execute_line("login admin admin")
        self.os.execute_line("register bob secret")
        self.assertEqual(self.os.execute_line("resetpw bob newpass"), "bob 의 비밀번호가 관리자에 의해 초기화되었습니다.")
        self.assertIn("로그인 실패", self.os.execute_line("login bob secret"))
        self.assertIn("환영합니다", self.os.execute_line("login bob newpass"))

    def test_accounts_persist_in_database(self):
        # 실제 DB 파일에 계정이 저장되고, 재시작 후에도 유지되는지 확인
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "neoos.db")
            neo1 = NeoOS(db_path=db_path)
            self.assertIn("계정이 생성되었습니다", neo1.execute_line("register bob secret"))
            neo1.close()

            # 새 인스턴스로 재오픈: 계정이 DB에서 복원되어야 함
            neo2 = NeoOS(db_path=db_path)
            self.assertIn("로그인 실패", neo2.execute_line("login bob wrong"))
            self.assertIn("환영합니다", neo2.execute_line("login bob secret"))
            neo2.close()

    def test_password_never_stored_in_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "neoos.db")
            neo = NeoOS(db_path=db_path)
            neo.execute_line("register bob secret")
            neo.close()
            raw = Path(db_path).read_bytes()
            self.assertNotIn(b"secret", raw, "비밀번호 평문이 DB에 저장되면 안 됩니다.")


if __name__ == "__main__":
    unittest.main()
