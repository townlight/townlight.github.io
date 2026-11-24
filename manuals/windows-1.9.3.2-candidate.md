# Townlight Windows 1.9.3.2 release notes

Windows 1.9.3.2 is the current signed public beta, published 2026-11-24T05:50:39Z. The signed MSI passed direct-upgrade, lifecycle, and fresh exact-artifact acceptance checks.

Candidate changes include private managed Records attachment downloads for authorized staff, with byte-count and SHA-256 verification before the workstation copy is saved, and a Station fix for an operator-control race during session renewal and polling.

Candidate component evidence used synthetic test data. R7 downloaded the same private Records attachment from R9: 2,174,280,536 bytes with SHA-256 `d7285a6c7d5fdc647ce8aada943e6a668ca63a1e5137db07b673250fa8bff775`. The saved copy matched the expected size and hash; audio and video decoded near the end. In a separate short physical Station candidate run, four operator polls succeeded during a delayed renewal response, Stop returned HTTP 202, and the recording completed normally.

These physical checks are candidate component evidence. In signing/build run 45321294952, direct-upgrade and lifecycle jobs passed but the first fresh-maintenance job failed because of fixture setup. A fixture-only correction was made without rebuilding the signed MSI; fresh exact-artifact run 45328280431 then passed.

## Published release links

- Signed MSI: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/Townlight-Windows-x64-1.9.3.2.msi>
- Release catalog: <https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.3.2>
- Checksums: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/SHA256SUMS-Windows-1.9.3.2.txt>
- Acceptance: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/ACCEPTANCE-Windows-1.9.3.2.md>
- Maintainer handoff: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/HANDOFF-Windows-1.9.3.2.md>
- Signing evidence: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/Signing-Evidence-Windows-1.9.3.2.txt>
- Corresponding source: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/Townlight-Windows-1.9.3.2-Corresponding-Source.zip>
- Installed evidence: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/Townlight-Windows-1.9.3.2-Installed-Evidence.zip>
- Signing receipt: <https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.3.2/Townlight-Windows-1.9.3.2-signing-receipt.json>

Verified signed MSI metadata: Suite source `67d56f24c12be4f2a409d1940ca4199a226adcfc`; MSI SHA-256 `b00510e0649552b5efd9744513bf9fcaf59cbee5755fd864eb922a5151c96b77`; size 1,866,072,064 bytes. [Signing/build run 45321294952](https://github.com/townlight/townlight/actions/runs/45321294952) included passing upgrade and lifecycle jobs and an initial fresh-maintenance fixture failure. A fixture-only correction without rebuilding was followed by the passing exact-artifact [fresh run 45328280431](https://github.com/townlight/townlight/actions/runs/45328280431). Published 2026-11-24T05:50:39Z.
