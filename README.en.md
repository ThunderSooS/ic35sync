# IC35 Sync 3.4.0

Synchronize a Siemens IC35 with Thunderbird on Windows: contacts, individual events, tasks and notes. [Deutsche Dokumentation](README.md).

## Downloads

[Release 3.4.0](https://github.com/ThunderSooS/ic35sync/releases/tag/v3.4.0)

| File | Purpose |
| --- | --- |
| IC35-Sync-3.4.0-Setup.exe | Recommended installer |
| IC35-Sync-3.4.0-Windows.zip | Complete application folder for manual use |
| IC35-Sync-3.4.0-Source.zip | Matching build source and scripts |
| IC35-Thunderbird-Bridge-3.4.0.13.xpi | Thunderbird extension |
| SHA256SUMS.txt | SHA-256 checksums |
| BUILD-MANIFEST.json | Source revision and recorded build checks |

The bridge uses an independent version number. Its manifest permits Thunderbird 153.x; compatibility with other Thunderbird versions is not implied.

## Installation and upgrades

1. Back up IC35 and Thunderbird data. Initially retain the previous installation and its data.
2. Close all IC35 Sync windows and run the installer.
3. Keep existing settings, pairing and sync state. Historical internal directory names remain for compatibility.
4. When needed, install the XPI separately through Thunderbird's Add-ons and Themes → gear menu → Install Add-on From File. The Windows installer does not install it into Thunderbird automatically.

For manual use, fully extract the Windows ZIP. Keep IC35Thunderbird.exe and _internal together in the application folder. Do not copy only the executable. Folder packaging avoids repeated extraction at startup; it does not guarantee a particular launch time or eliminate every possible Windows access restriction.

## First synchronization

1. Keep Thunderbird open. Select the dock COM port and IC35 time zone in the app.
2. Pair the Thunderbird bridge using the code supplied by the app. Do not publish this code.
3. Load calendars and task lists, then choose the intended targets. Existing network calendars are accessed through Thunderbird; account credentials stay there.
4. Configure the local CardDAV address book in Thunderbird for contacts. The app's setup help provides the addresses.
5. Synchronize Thunderbird before the device operation. Start synchronization in IC35 Sync and press the SyncStation button only when prompted.
6. Review the result and log, then synchronize Thunderbird again. Begin with disposable test entries.

Local collections use port 5233 and the paired bridge uses port 5234 on 127.0.0.1. The application must be running for these services. Do not configure router port forwarding.

## Notes as text files

Choose a dedicated notes folder, not a folder of unrelated text files. New .txt files without an IC35 tag are treated as new notes. Bound files carry a suffix such as [IC35-000012]. Do not remove it to resolve a conflict unless creating a new device note is intended.

Creation, editing, renaming and deletion are reconciled both ways when a baseline mapping exists. Deletion on one side combined with an edit on the other remains a conflict. Tagged files without a saved mapping are not automatically deleted or recreated on the device. After confirming an intentional device deletion, orphaned files can be moved to a backup folder outside the synchronization folder.

The IC35 note limits are 60 bytes for the subject and 255 bytes for the body in Windows-1252, including CRLF line breaks. Unsupported or oversized text is skipped rather than truncated. Synchronized note files are plaintext.

## Protection and limitations

- Baselines, conflict checks, readback and recovery journals protect reconciliation; they are not a substitute for backups.
- For task deletion, only valid DTSTAMP and LAST-MODIFIED value differences receive special treatment. Other properties remain protected.
- Recurrence, exceptions, all-day events and meeting invitations do not have general bidirectional synchronization. Protected or unsupported entries may be skipped.
- A successful overall operation can still contain note conflicts or skipped entries. Review the summary and log.
- Lost note mappings and all possible Windows launch failures have not been generally resolved.

When troubleshooting, first inspect the exact message, file path and security logs. Do not disable antivirus globally or delete state/pairing files speculatively. Logs can contain personal data; share only necessary, preferably anonymized excerpts.

## Development and evidence

For a normal Windows build, run scripts/build_final_release.py without arguments. --publish is reserved for explicitly authorized publication and can modify main, a tag and a public release. Normal documentation commits on GitHub build packages but do not publish releases.

The fixed v3.4.0 source and downloads can be older than this documentation on main. Documentation updates do not automatically replace published assets.

[Changes](RELEASE-NOTES.md) · [History](CHANGELOG.md) · [Validation](VALIDATION.md) · [Privacy](PRIVACY.md) · [Third-party notices](THIRD_PARTY_NOTICES.md) · [License](LICENSE)
