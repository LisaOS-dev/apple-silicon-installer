# SPDX-License-Identifier: MIT
# Lisa's addition to the fork: what the installer downloaded is checked
# against the lineage's signed targets -- length and sha256 -- before it
# writes a byte (docs.lisaos.dev/system/install#apple-silicon). Gravity's
# installer checks no digest of its OS package (osinstall.py:44-59).
#
# Not in this module yet: the targets envelope's Ed25519 signatures, checked
# against the trusted root the tarball carries. `targets` here is the signed
# body's "targets" map, as assembly/tools/release_sign.py writes it.
import hashlib, json, logging, os, urllib.request

CHUNK = 1 << 20
REFUSAL = ("The download does not match what the Lisa release authority signed. "
           "Nothing was written.")


class NotSigned(Exception):
    def __init__(self, detail):
        super().__init__(REFUSAL)
        self.detail = detail


def expected(targets, name):
    entry = targets.get(name) if isinstance(targets, dict) else None
    try:
        length = entry["length"]
        digest = entry["hashes"]["sha256"]
    except (TypeError, KeyError):
        raise NotSigned(f"{name} is not named in the signed targets")
    if not isinstance(length, int) or isinstance(length, bool) or length < 0 \
            or not isinstance(digest, str) or len(digest) != 64:
        raise NotSigned(f"{name} has a malformed target entry")
    return length, digest


def verify_stream(stream, targets, name):
    """Read stream to its end (never more than the signed length plus one
    chunk) and return its sha256 when length and digest are the signed ones."""
    length, digest = expected(targets, name)
    h = hashlib.sha256()
    seen = 0
    while True:
        block = stream.read(min(CHUNK, length + 1 - seen) or 1)
        if not block:
            break
        seen += len(block)
        if seen > length:
            raise NotSigned(f"{name}: more than the signed {length} bytes")
        h.update(block)
    got = h.hexdigest()
    if seen != length or got != digest:
        logging.error(f"lisa_verify: {name}: {seen} bytes sha256 {got}; "
                      f"signed {length} bytes sha256 {digest}")
        raise NotSigned(f"{name}: {seen} bytes sha256 {got}, signed {length} sha256 {digest}")
    logging.info(f"lisa_verify: {name}: {length} bytes sha256 {got} as signed")
    return got


def load_installer_data(path, targets):
    with open(path, "rb") as f:
        raw = f.read()
    import io
    verify_stream(io.BytesIO(raw), targets, os.path.basename(str(path)))
    return json.loads(raw)


def load_targets(path="targets.json"):
    with open(path, "rb") as f:
        return json.load(f)["targets"]


def package_location(template):
    package = template["package"]
    if package.startswith("http"):
        return package
    return os.environ.get("REPO_BASE", ".") + "/os/" + package


def verify_package(template, targets):
    """The whole OS package, read once from where the install will read it."""
    location = package_location(template)
    name = template["package"].rsplit("/", 1)[-1]
    if location.startswith("http"):
        with urllib.request.urlopen(location, timeout=60) as f:
            return verify_stream(f, targets, name)
    with open(location, "rb") as f:
        return verify_stream(f, targets, name)
