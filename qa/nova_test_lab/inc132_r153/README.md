# NOVA INC132 R153 — verified QA thin source (branch TEST only)

Complete 51 test suite and 9 Chromium synthetic checks. Monoliths are rebuilt at CI runtime from the **byte-identical R150** repository root by two reviewable UTF-8 patches under `patches/`, then checked for exact SHA256. `bootstrap_from_R150.py` changes only QA staging files, **never the runtime root**. No private DTM, raw FIT, secrets, deployment, or main modification.

Verified hashes:
- root R150 `6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73`
- R153 FTP `6e7e70e033d1a9e53105cfe0d3660c3f3366f91d8ed9ce09423dc1ae9a8fede9`
- R153 duale `d37840512624592eaf867730e93156ca50eb99e864bdf171f6379823d93291c1`

Use `python qa/nova_test_lab/inc132_r153/bootstrap_from_R150.py` from repo root before `verify_commit_candidate.py`, unit tests and Chromium. Workflow runs on TEST branch and never deploys.
