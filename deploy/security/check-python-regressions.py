"""Offline regressions for CPython CVE-2025-15367 and CVE-2026-12345.

Adapted from upstream CPython (PSF License):
b234a2b67539f787e191d2ef19a7cbdce32874e7 / test_poplib.py
58ed0259cae509a19138795df302fe60b544dc74 / test_tempfile.py
Run as a non-root user on a system with symlink-safe shutil.rmtree.
"""

import contextlib
import os
import poplib
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class CPythonSecurityRegressions(unittest.TestCase):
    def test_pop3_rejects_control_characters_before_sending(self):
        # No socket is constructed; record the exact commands that would be sent.
        client = object.__new__(poplib.POP3)
        client._debugging = 0
        sent = []
        client._putline = sent.append
        client._getresp = lambda: b"+OK"
        for value in (*range(32), 127):
            for method, command in (
                (client.user, f"user{chr(value)}"),
                (client.pass_, f"{chr(value)}pass"),
            ):
                with self.subTest(control=value, command=method.__name__):
                    sent.clear()
                    with self.assertRaises(ValueError):
                        method(command)
                    self.assertEqual(sent, [], "Rejected input reached the send boundary")
        sent.clear()
        client.user("alice")
        client.pass_("valid-password")
        self.assertEqual(sent, [b"USER alice", b"PASS valid-password"])

    def test_temporary_directory_cleanup_resists_symlink_race(self):
        self.assertNotEqual(os.geteuid(), 0, "Run this regression as non-root")
        self.assertTrue(
            shutil.rmtree.avoids_symlink_attacks, "This regression requires fd-based rmtree"
        )
        # Both the attacked tree and the sentinel are confined to this test's
        # private directory; nothing outside our fixture can be modified.
        outer = Path(tempfile.mkdtemp(prefix="liqvera-cpython-security-"))
        victim = None
        attacked = None
        try:
            target = outer / "target"
            target.mkdir()
            sentinel = target / "file1"
            sentinel.write_bytes(b"must survive")
            original_mode = sentinel.stat().st_mode
            victim = tempfile.TemporaryDirectory(prefix="victim-", dir=outer)
            attacked = Path(victim.name) / "dir1"
            attacked.mkdir()
            (attacked / "file1").write_bytes(b"temporary")
            attacked.chmod(0o500)
            original_unlink = os.unlink
            raced = False

            def race_after_permission_error(path, *, dir_fd=None):
                nonlocal raced
                try:
                    return original_unlink(path, dir_fd=dir_fd)
                except PermissionError:
                    if not attacked.is_symlink():
                        attacked.chmod(0o700)
                        attacked.rename(str(attacked) + "_moved")
                        attacked.symlink_to(target, target_is_directory=True)
                        raced = True
                    raise

            try:
                with mock.patch("os.unlink", race_after_permission_error):
                    with contextlib.suppress(OSError):
                        victim.cleanup()
            finally:
                if attacked.is_symlink():
                    attacked.unlink()
                    Path(str(attacked) + "_moved").rename(attacked)
                if attacked.exists():
                    attacked.chmod(0o700)
                victim.cleanup()
            self.assertTrue(raced, "Permission-error race was not exercised")
            self.assertTrue(sentinel.exists(), "Cleanup deleted a file outside its tree")
            self.assertEqual(sentinel.read_bytes(), b"must survive")
            self.assertEqual(
                sentinel.stat().st_mode,
                original_mode,
                "Cleanup changed permissions outside its tree",
            )
        finally:
            if attacked is not None and attacked.exists() and not attacked.is_symlink():
                attacked.chmod(0o700)
            if victim is not None:
                victim.cleanup()
            shutil.rmtree(outer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
