# Lisa's Apple-silicon installer

Installs Lisa next to macOS on an Apple-silicon Mac, from macOS, with no USB
stick. Today it targets the Mac mini (M4, 2024) and Lisa Server first; the law
is <https://docs.lisaos.dev/system/install#apple-silicon>.

It is a fork of the Gravity Linux installer
(<https://github.com/GravityLinux/installer>, itself of the Asahi Linux
installer's lineage), under the same MIT licence — see `ATTRIBUTION.md`. It is
not Gravity Linux, and neither Gravity Linux nor the Asahi Linux project
endorses it.

## What Lisa adds

- **Nothing is written for an unsigned download.** `installer_data.json` and
  every OS package are read whole and checked against the Lisa release's
  signed targets (length and sha256) before the first question is asked or a
  disk is read (`src/lisa_verify.py`, `tests/test_lisa_verify.py`).
- Lisa's name, documentation links and artwork; Gravity's name and logos are
  never shipped (their `TRADEMARKS.md`).

## Running the tests

```sh
PYTHONPATH=src:. python3 -m unittest discover -s tests -p "test_*.py"
```

`test.sh` is not the test suite: it builds m1n1 and runs the installer as root.

## Not yet

- The signed targets' Ed25519 signatures are not checked yet; only length and
  sha256 against the targets body.
- The bootstrap line (`curl -fsSL https://releases.lisaos.dev/install | sh`),
  Lisa's `installer_data.json` and the Lisa package are not published.
- Lisa's own artwork is not in this repository yet.
