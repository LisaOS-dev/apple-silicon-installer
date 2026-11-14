# SPDX-License-Identifier: MIT
# Lisa's addition to the fork (docs.lisaos.dev/system/install#apple-silicon):
# installer_data.json and the OS package are checked against the lineage's
# signed targets, length and sha256, before the installer writes a byte.
# Gravity's installer checks no digest of its package (osinstall.py:44-59).
import hashlib, io, json, os, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import lisa_verify

REFUSAL = ("The download does not match what the Lisa release authority signed. "
           "Nothing was written.")


def fake_package():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("boot.img", b"\0" * 4096)
        z.writestr("root.img", b"\1" * 8192)
        z.writestr("esp/m1n1/boot.bin", b"m1n1 stage2 + u-boot")
    return data.getvalue()


def target(name, body, kind):
    return {name: {"length": len(body),
                   "hashes": {"sha256": hashlib.sha256(body).hexdigest()},
                   "custom": {"kind": kind}}}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.package = fake_package()
        self.data = json.dumps({"os_list": [{
            "name": "Lisa Server", "default_os_name": "Lisa",
            "package": "lisa-server-test.zip", "partitions": []}]}).encode()
        (self.dir / "os").mkdir()
        (self.dir / "os" / "lisa-server-test.zip").write_bytes(self.package)
        (self.dir / "installer_data.json").write_bytes(self.data)
        self.targets = {}
        self.targets.update(target("lisa-server-test.zip", self.package, "installer-package"))
        self.targets.update(target("installer_data.json", self.data, "installer-data"))

    def tearDown(self):
        self.tmp.cleanup()


class VerifyStream(Fixture):
    def test_the_signed_package_passes(self):
        with open(self.dir / "os" / "lisa-server-test.zip", "rb") as f:
            got = lisa_verify.verify_stream(f, self.targets, "lisa-server-test.zip")
        self.assertEqual(got, hashlib.sha256(self.package).hexdigest())

    def test_one_changed_byte_is_refused_with_the_sentence(self):
        bad = bytearray(self.package); bad[100] ^= 1
        with self.assertRaises(lisa_verify.NotSigned) as e:
            lisa_verify.verify_stream(io.BytesIO(bytes(bad)), self.targets, "lisa-server-test.zip")
        self.assertEqual(str(e.exception), REFUSAL)

    def test_a_short_download_is_refused(self):
        with self.assertRaises(lisa_verify.NotSigned) as e:
            lisa_verify.verify_stream(io.BytesIO(self.package[:-1]), self.targets, "lisa-server-test.zip")
        self.assertEqual(str(e.exception), REFUSAL)

    def test_a_long_download_is_refused_without_reading_it_all(self):
        endless = io.BytesIO(self.package + b"x" * (1 << 20))
        with self.assertRaises(lisa_verify.NotSigned):
            lisa_verify.verify_stream(endless, self.targets, "lisa-server-test.zip")
        self.assertLessEqual(endless.tell(), len(self.package) + lisa_verify.CHUNK)

    def test_a_name_the_targets_do_not_sign_is_refused(self):
        with self.assertRaises(lisa_verify.NotSigned) as e:
            lisa_verify.verify_stream(io.BytesIO(self.package), self.targets, "other.zip")
        self.assertEqual(str(e.exception), REFUSAL)


class InstallerData(Fixture):
    def test_signed_installer_data_is_returned_parsed(self):
        got = lisa_verify.load_installer_data(self.dir / "installer_data.json", self.targets)
        self.assertEqual(got["os_list"][0]["package"], "lisa-server-test.zip")

    def test_changed_installer_data_is_refused(self):
        (self.dir / "installer_data.json").write_bytes(self.data.replace(b"Lisa", b"Evil"))
        with self.assertRaises(lisa_verify.NotSigned):
            lisa_verify.load_installer_data(self.dir / "installer_data.json", self.targets)


class BeforeAnyWrite(Fixture):
    """The check runs first in InstallerMain.main: nothing about the disks is
    read or written, and no question is asked, when the package does not match."""

    def make_main(self):
        import main as gmain
        (self.dir / "targets.json").write_text(json.dumps({"targets": self.targets}))
        (self.dir / "boot").mkdir()
        (self.dir / "boot" / "m1n1.bin").write_bytes(b"\0" * 64)
        cwd = os.getcwd(); os.chdir(self.dir)
        self.addCleanup(os.chdir, cwd)
        env = mock.patch.dict(os.environ, {"REPO_BASE": str(self.dir)})
        env.start(); self.addCleanup(env.stop)
        with mock.patch.object(gmain.m1n1, "get_version", return_value="test"):
            return gmain, gmain.InstallerMain("test")

    def test_a_tampered_package_stops_before_the_disks_are_touched(self):
        bad = bytearray(self.package); bad[-30] ^= 1
        (self.dir / "os" / "lisa-server-test.zip").write_bytes(bytes(bad))
        gmain, ins = self.make_main()
        touched = mock.Mock(side_effect=AssertionError("touched before the check"))
        with mock.patch.object(gmain.system, "SystemInfo", touched), \
             mock.patch.object(gmain.diskutil, "DiskUtil", touched), \
             mock.patch.object(ins, "input", touched), \
             mock.patch.object(ins, "main_loop", touched):
            with self.assertRaises(lisa_verify.NotSigned) as e:
                ins.main()
        self.assertEqual(str(e.exception), REFUSAL)
        touched.assert_not_called()

    def test_a_tampered_installer_data_stops_at_startup(self):
        (self.dir / "installer_data.json").write_bytes(self.data + b" ")
        import main as gmain
        (self.dir / "targets.json").write_text(json.dumps({"targets": self.targets}))
        cwd = os.getcwd(); os.chdir(self.dir); self.addCleanup(os.chdir, cwd)
        with mock.patch.object(gmain.m1n1, "get_version", return_value="test"):
            with self.assertRaises(lisa_verify.NotSigned):
                gmain.InstallerMain("test")


if __name__ == "__main__":
    unittest.main()
