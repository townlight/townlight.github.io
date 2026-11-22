# Windows 1.9.2.1 signed candidate

**Status: not publicly distributed.** The signed Windows 1.9.2.1 candidate passed its identified installed acceptance. No 1.9.2.1 installer download is published. The current public Windows download remains [Townlight Windows 1.9.1.1](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.1.1).

The candidate MSI SHA-256 is `3242792ad6c825a5057d96c5e1d9d45fb5726ccbfba7ab24a2b428a54e63b0bf`. The signature and Microsoft timestamp were independently verified. The code is merged in [Suite main](https://github.com/townlight/townlight/tree/main) through [PR #339](https://github.com/townlight/townlight/pull/339). See the [candidate acceptance summary](https://github.com/townlight/townlight/blob/main/release/CANDIDATE-Windows-1.9.2.1.md) for exact identity, evidence and limits.

## What the candidate adds

The candidate adds shared Windows staff work across a city host and workstation. The host owns the database, managed files, staff accounts and Station recording hardware. Workstations use the same signed installer and connect through a private, certificate-validated HTTPS endpoint. Existing Townlight roles control access; staff sessions are named, revocable and attributable. Shared mode requires explicit configuration and does not change the ordinary stand-alone installation.

In Meetings, a clerk can prepare and revise a council packet on one Windows session, then review the same saved packet from another. Source files selected at a workstation are copied to the host and verified. Staff can download verified preview and approved files to a workstation. A changed response must be reviewed and approved again. The public packet contains only the selected public revision; restricted material remains in the staff packet.

Records staff can attach the host's private Station recording to the shared request by its identity and verified SHA-256, prepare original and release copies, and approve the reviewed response. Station capture and Records release finalization stay on the host.

## Approved portal publishing

The Windows host can deliver an explicitly approved council packet or eligible Records release copy to a separately deployed Townlight resident portal. Staff select the public revision or release copy and explicitly approve publication. Approved jobs can finish after staff sign out and resume after an outage or host restart. Retries are idempotent. A corrected packet uses the same meeting identity after the revised content is reviewed and approved. Withdrawing a recording removes that recording; a packet remains public until it is separately withdrawn.

This does not make the Townlight documentation website the resident portal. The portal is separately deployed and configured. See the [portal guide](https://townlight.github.io/manuals/portal.html) and the maintained [portal source guide at the signed commit](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/docs/portal/guide.md).

## Setup and technical references

Follow the [shared Windows staff guide at the signed commit](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/docs/installer/windows-shared-staff.md) for host and workstation configuration, roles, TLS, restart behavior and recovery. It covers the supported `/staff/v1/*` path and the environment settings. Do not expose the staff service or place its credentials on the public portal.

For the candidate implementation, see the [native shared-staff client](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/src-tauri/src/shared_staff.rs), [council packet client](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/src-tauri/src/council_packet_client.rs), [staff gateway](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/runtime/python-services/townlight_runtime/shared_staff.py), [packet contract](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/runtime/python-services/townlight_runtime/council_packet.py), and [portal publication contract](https://github.com/townlight/townlight/blob/1bc45be5a14aa969e53b87b1cef1f278dadc79a4/desktop/runtime/python-services/townlight_runtime/portal_publication.py). Existing released API snapshots and source pins retain their historical identities.

## Acceptance scope

On the physical Windows host, the exact signed MSI was administratively extracted to verify the embedded executable and signatures. The MSI was installed in the isolated Windows Sandbox guest. Synthetic tests checked named-role access, shared packet readback, verified preview and approved downloads, exclusion of a restricted file from public PDF and HTML, stale-approval rejection, Station-to-Records file identity, queued publication after outage and restart, idempotent retry, correction and separate withdrawal. Cold recovery used a fresh Townlight profile at the same absolute paths under the original Windows host account; it did not exercise a physically separate replacement computer.

This evidence covers separate Windows environments on one physical machine; it does not establish a two-physical-PC installation or acceptance in a live city network or portal. The portal and staff workflow checks used synthetic data. City IT must configure its own host, trusted TLS certificate, staff accounts, backups and separately deployed portal before operational use.

The signed candidate is not an available public download. Use the [Windows 1.9.1.1 release](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.1.1) for the current public installer and its version-specific acceptance evidence.
