<a id="windows-1.9.2.1-signed-candidate"></a>

# Townlight Windows 1.9.2.1 signed public beta

Windows 1.9.2.1 is the current signed public beta. The release adds revisioned council packets, shared Meetings and Records work between a city host and workstation, and unattended portal delivery for materials staff have explicitly approved.

[Download the signed Windows x64 MSI](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/Townlight-Windows-x64-1.9.2.1.msi) · [Release catalog](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.2.1) · [SHA-256 checksums](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/SHA256SUMS-Windows-1.9.2.1.txt) · [Acceptance and limits](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/ACCEPTANCE-Windows-1.9.2.1.md)

MSI SHA-256: `3242792ad6c825a5057d96c5e1d9d45fb5726ccbfba7ab24a2b428a54e63b0bf`. The corresponding-source archive is [available from the release](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/Townlight-Windows-1.9.2.1-Corresponding-Source.zip); its SHA-256 is `1b9cebd0fec34b06118f9b07cd85c4de3b5af69fba6ab9301cbf402ab67e0a88`. The desktop source commit is `1bc45be5a14aa969e53b87b1cef1f278dadc79a4`.

<a id="what-the-candidate-adds"></a>

## What Windows 1.9.2.1 adds

The release adds shared Windows staff work across a city host and workstation. The host owns the database, managed files, staff accounts and Station recording hardware. Workstations use the same signed installer and connect through a private, certificate-validated HTTPS endpoint. Existing Townlight roles control access; staff sessions are named, revocable and attributable. Shared mode requires explicit configuration and does not change the ordinary stand-alone installation.

In Meetings, a clerk can prepare and revise a council packet on one Windows session, then review the same saved packet from another. Source files selected at a workstation are copied to the host and verified. Staff can download verified preview and approved files to a workstation. A changed response must be reviewed and approved again. The public packet contains only the selected public revision; restricted material remains in the staff packet.

Records staff can attach the host's private Station recording to the shared request by its identity and verified SHA-256, prepare original and release copies, and approve the reviewed response. Station capture and Records release finalization stay on the host.

## Approved portal publishing

The Windows host can deliver an explicitly approved council packet or eligible Records release copy to a separately deployed Townlight resident portal. Staff select the public revision or release copy and explicitly approve publication. Approved jobs can finish after staff sign out and resume after an outage or host restart. Retries are idempotent. A corrected packet uses the same meeting identity after the revised content is reviewed and approved. Withdrawing a recording removes that recording; a packet remains public until it is separately withdrawn.

This does not make the Townlight documentation website the resident portal. The portal is separately deployed and configured. See the [portal guide](https://townlight.github.io/manuals/portal.html) and the maintained [portal source guide at the signed commit](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/docs/portal/guide.md).

<a id="for-the-candidate-implementation"></a>
<a id="setup-and-technical-references"></a>

## Source pins and implementation

Follow the [shared Windows staff guide at the signed commit](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/docs/installer/windows-shared-staff.md) for host and workstation configuration, roles, TLS, restart behavior and recovery. It covers the supported `/staff/v1/*` path and the environment settings. Do not expose the staff service or place its credentials on the public portal.

The [versioned source-pin record](../reference/windows-1.9.2.1-source-pins.json) lists the release's exact repository commits, component archive hashes and installer identity. The [native shared-staff client](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/src-tauri/src/shared_staff.rs), [council packet client](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/src-tauri/src/council_packet_client.rs), [staff gateway](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/runtime/python-services/townlight_runtime/shared_staff.py), [packet contract](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/runtime/python-services/townlight_runtime/council_packet.py), and [portal publication contract](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/runtime/python-services/townlight_runtime/portal_publication.py) are pinned to the canonical source commit.

## Acceptance scope

The exact signed MSI was administratively extracted and run on a physical Windows host with an isolated profile, then installed in a separate clean Windows Sandbox guest on the same machine. The host and guest verified the MSI and contained executable signatures. The guest used the existing named staff roles over private HTTPS. Synthetic checks covered council packet revision approvals, preview and approved downloads, exclusion of restricted material from public PDF and HTML, Station-to-Records file identity, stale-approval rejection, account revocation, queued publication after an outage and host restart, idempotent retry, packet correction, independent withdrawal, and cold recovery into a fresh profile at the same paths on the original host and account.

Acceptance used synthetic data and a test portal. It does not establish deployment on two physical PCs, recovery onto a different physical computer or Windows account, testing against a production portal or city network, direct MSI upgrade from an earlier version, or new hardware and broadcast acceptance. The public council packet PDF was printable and searchable; PDF/UA tagging and a full assistive-technology review of that packet PDF were not verified. See the [release acceptance summary](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/ACCEPTANCE-Windows-1.9.2.1.md) for exact results and limits.

The earlier [Windows 1.9.1.1 release](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.1.1) remains available with its own checksums and version-specific acceptance evidence.
