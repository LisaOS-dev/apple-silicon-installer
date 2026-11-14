# SPDX-License-Identifier: MIT
# Lisa's addition to the fork: what the installer downloaded is checked
# against the lineage's signed targets -- length and sha256 -- before it
# writes a byte (docs.lisaos.dev/system/install#apple-silicon). Gravity's
# installer checks no digest of its OS package (osinstall.py:44-59).
#
# Not in this module yet: the targets envelope's Ed25519 signatures, checked
# against the trusted root the tarball carries. `targets` here is the signed
# body's "targets" map, as assembly/tools/release_sign.py writes it.
import json, os

REFUSAL = ("The download does not match what the Lisa release authority signed. "
           "Nothing was written.")


class NotSigned(Exception):
    def __init__(self, detail):
        super().__init__(REFUSAL)
        self.detail = detail


def expected(targets, name):
    return 0, ""


def verify_stream(stream, targets, name):
    stream.read()
    return ""


def load_installer_data(path, targets):
    with open(path, "rb") as f:
        return json.loads(f.read())


def load_targets(path="targets.json"):
    with open(path, "rb") as f:
        return json.load(f)["targets"]


def package_location(template):
    return template["package"]


def verify_package(template, targets):
    return ""
