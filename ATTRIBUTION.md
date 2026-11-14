# Attribution

Lisa's Apple-silicon installer is a fork of the Gravity Linux installer,
https://github.com/GravityLinux/installer, imported at commit
`f54140ea4957363c6fcdd8f1699b2e38730603ab` (branch `air-j713`, 2026-11-11),
the commit Gravity's published installer
`gravity-20261111-f54140ea4957-stage1-950e6b7-4838f2c0` was built from.
That installer is itself of the Asahi Linux installer's lineage.

- The MIT licence text in `LICENSE` (Copyright (c) 2021 The Asahi Linux
  contributors) and every `SPDX-License-Identifier: MIT` header are kept.
- `gravity_firmware/asn1.py` is Python-ASN1's, under its MIT notice, kept.
- Lisa's additions are under the same MIT licence.

This installer is based on Gravity Linux's installer. It is not Gravity Linux,
and neither Gravity Linux nor the Asahi Linux project endorses it. It may not
be distributed until Gravity's name, logos and artwork have left it
(TRADEMARKS.md: modified distributions "should use their own name and logos");
as imported on 2026-11-14 they have not: `util.py` DISTRO, `main.py` and
`reporting.py` strings, and `build.sh`'s logo and m1n1 boot-logo payload are
still Gravity's. Identifiers Gravity's boot chain
reads (`chosen.gravity,efi-system-partition`, the `gravity` directory on the
EFI partition, the `gravity_firmware` module) are interfaces, not branding.
