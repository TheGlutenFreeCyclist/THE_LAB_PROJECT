# NOVA INC132 R153 — deterministic QA on TEST only

The branch TEST root runtime was integrated at commit `ae1e603765c0c54e6b3a0d10fbf189388e0a2547`. This directory contains the 51-test regression suite, three real-Chromium synthetic UI tests (3 viewport widths each), and source-reconstruction patches.

`bootstrap_from_R150.py` is **read-only toward the repository root**. It accepts either the original R150 root or the byte-identical R153 dual root. For a R153 root it reverses both patches *in a temporary directory*, recovers the exact original R150 for regression, then applies the patches forward and verifies the three pinned SHA256 values. Unknown root versions fail closed; no production code is silently modified.

Pinned source hashes:
- R150: `6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73`
- R153+FTP: `6e7e70e033d1a9e53105cfe0d3660c3f3366f91d8ed9ce09423dc1ae9a8fede9`
- R153+FTP+duale: `d37840512624592eaf867730e93156ca50eb99e864bdf171f6379823d93291c1`

The workflow `.github/workflows/nova-inc132-r153-commit-qa.yml` runs on this TEST branch with **no deploy**. This post-integration documentation commit intentionally triggers the workflow against the now-integrated R153 root, not just against the earlier R150 baseline.

**Do not infer PRODUCT_GO from synthetic tests.** Authenticated Intervals/RAW FIT and issuer proof, scientific review for `POWER_1`, `SPRINTER`, `ENDURANCE_BASE`, Q01–Q31 and safe production release control remain separate. No private DTM content or raw athlete data is committed.
