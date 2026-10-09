# Pair your phone with a Unio session

Owner-requested on 2026-10-09. **Planned; not implemented or assigned a release.**

Check progress and talk to the lead from a phone while Unio keeps working on
the home PC. Pair with one selected project and lead session through a mobile
browser. A dedicated Android app is optional, not a requirement.

## Proposed pairing flow

1. In the PC dashboard, select the running session and choose **Connect phone**.
   Unio shows a short-lived, single-use QR invitation.
2. Scan the QR code to open the mobile session page in a browser.
3. Confirm the phone on the PC and choose its permissions. Scanning alone must
   not authorize access. The invitation must not contain PC credentials or a
   permanent session access key.
4. The phone shows that session's progress and messages. If permitted, send a
   message to the same lead that is already working on the PC.
5. Revoke the phone from the PC or end the session to close its access. Show
   connected devices and their permission/expiry information clearly.

Pairing must not launch another AI workflow or consume another lead slot.
Viewing local activity makes no model call; messages processed by the lead use
its normal allowance. Keep the current work mode, budget tier and owner controls.

## Access belongs to the selected session

| Permission | What the phone may do |
| --- | --- |
| View | Read this session's approved activity and conversation views. |
| Message | Send an instruction to this lead session, with visible delivery status. |
| Approve | Separately granted: approve a specific action and its exact revision. |

Start with view access; messaging and approvals require explicit grants.
Do not expose a general terminal, remote desktop, arbitrary file browser,
host paths, provider credentials or other projects through these controls.
Apply the existing output/file access rules to anything shown on the phone.

This is an application access boundary. Unio currently runs agents with
`trusted_host` access, not an OS sandbox. A permitted message can still cause
the lead to use its existing tools and permissions. Pairing must not expand
those permissions or bypass STOP, account admission or action approvals.

## Connecting away from home

The proposed default is an outbound connection from Unio to a relay, with the
phone joining the paired session through its browser. Avoid router port
forwarding and device-wide network access. The relay must not be able to read
session message contents; authentication and encryption need a defined protocol.

Relay hosting, protocol, operating cost and any optional private-network route
remain undecided. No service has been deployed or purchased. Keep existing
Host/Origin, authentication and capability checks; placing a relay in front
of today's loopback dashboard does not implement this feature by itself.

## Deliver in bounded steps

1. **Attach to a supported lead.** Define a managed session identity and an
   adapter that can deliver messages to that actual live lead. The current
   dashboard does not have this adapter. Do not guess a session from a PID or
   write arbitrary keystrokes into a terminal. Start with one supported CLI.
2. **Pair and authorize locally.** Add the mobile view, PC confirmation,
   permission grants, expiry, connected-device list and immediate revocation.
3. **Connect remotely.** Select the relay/authentication/encryption protocol
   and implement remote transport without widening the session's capabilities.
   Notifications and an installable web-app shortcut can follow.

Before shipping, check successful pairing and delivery to the intended session,
expired/reused invitations, missing grants, cross-session requests, disconnects,
revocation and duplicate delivery after reconnect. A reconnect must not replay
a message or an approval. Bind approvals to the exact action/revision shown.
Make offline, stopped and cooldown states visible. A restarted lead must have
an explicit identity transition; never silently attach the phone to another
session or deliver its pending instructions there.

See the [roadmap](ROADMAP.md), existing
[browser execution boundaries](../BROWSER-EXECUTION-CONTRACT.md) and
[console access contract](../BROWSER-CONSOLE-CONTRACT.md).
