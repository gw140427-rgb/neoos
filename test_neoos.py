"""NeoOS 유닛 테스트.

실행: python3 -m unittest test_neoos -v
"""

import unittest

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


if __name__ == "__main__":
    unittest.main()
