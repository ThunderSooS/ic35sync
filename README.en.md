# IC35 Sync Beta · 3.4.0a11

**a9 requires both the app and add-on update.** Install the new setup and `IC35-Thunderbird-Bridge-3.4.0a9.xpi` using Thunderbird's Install Add-on From File menu, then restart Thunderbird. Pairing is preserved. Confirmed uncached CalDAV notifications can recover a missing write callback, followed by readback. Unconfirmed operations time out without retrying and the calendar list remains available. Keep all sync state files.

**a8:** Prevents the observed delete/recreate loop. Unique matching events are linked even when their reminders differ; both initial reminder values are preserved. Cleanup requires an existing original and an unchanged journal-identified copy, never just IC35 markers. Keep state files and the same calendar selection. This does not generally resolve CalDAV acknowledgement timeouts for necessary writes.

**a3 update:** Recognizes observed IC35 firmware defaults after event creation: an empty zero-valued control field and an unused repeat-end date on non-recurring events. This fixes a false readback failure and lets the existing recovery journal associate the already-created event. Keep state/journal files and use the same calendar selection. The a2 Thunderbird add-on remains compatible; reinstalling it is unnecessary.

**Thunderbird alpha for 64-bit Windows 10/11.** Two-way synchronization of contacts, individual calendar events and tasks with a Siemens IC35. The sync app needs no cloud login or credential JSON files. The bundled add-on connects existing Thunderbird calendars, including a Google CalDAV calendar already configured there. Thunderbird continues handling the account connection. The application interface is currently German.

[Deutsch](README.md) · [Privacy](PRIVACY.md) · [License](LICENSE)

## Use an existing calendar

Keep your existing calendar and phone configuration. The path is `IC35 ↔ sync app ↔ Thunderbird add-on ↔ existing calendar service ↔ phone`.

1. Install the new setup and install `IC35-Thunderbird-Bridge-3.4.0a9.xpi` in Thunderbird using **Add-ons and Themes → gear menu → Install Add-on From File**. The installer places this file beside the EXE; it is also a separate release asset.
2. In the sync app, click **Thunderbird-Add-on koppeln**. Paste the copied pairing code into the add-on's settings and click **Verbinden**.
3. Click **Kalender aus Thunderbird laden** in the app and choose the existing calendar you want under **Termine aus**. It is shown with the suffix **· Thunderbird**.
4. Choose a task-capable calendar separately under **Aufgaben aus**, or keep **Lokale IC35-Sammlung**. Google Tasks is not available through Google's CalDAV calendar connection.

The add-on currently supports **Thunderbird 153.x**, tested on 153.0.1. It uses an Experiment API for calendar access, which causes Thunderbird to show a broad permission prompt. Its implementation uses calendar functions and does not access email or account passwords.

Keep both applications open. Network calendars must be online; errors or pending offline changes stop the reconciliation. Existing calendar entries do not need to be copied. Read-only or disabled calendars are not selectable. Contacts still use the local CardDAV address book below. Recurrence and other limitations listed below still apply.

## Setup

1. Run `IC35-Sync-Beta-3.4.0a11-Setup.exe`. Python is bundled; installation is per user without administrator rights.
2. Open **IC35 Sync Beta**, select the dock's COM port and check the IC35 time zone (default `Europe/Berlin`).
3. Install the bundled `IC35-Thunderbird-Bridge-3.4.0a9.xpi` add-on in Thunderbird and restart Thunderbird.
4. In the app, click **Thunderbird-Add-on koppeln**, paste the pairing code into the add-on settings and click **Verbinden**.
5. Click **Kalender aus Thunderbird laden** and select the existing calendar and task collection shown with **· Thunderbird**.

The add-on method uses the calendars and task collections already configured in Thunderbird. Thunderbird continues to handle account login and server synchronization; the IC35 app does not need Google credentials or JSON files.

## Daily use

Synchronize the address book/calendar in Thunderbird, then click **Alles mit Thunderbird synchronisieren** in this app. Press the dock button when prompted. The UI and a sound confirm the connection. Wait for completion, then synchronize Thunderbird again to receive the changes. Avoid editing either side during the operation.

The regular workflow uses one dock connection, without a confirmation dialog or an automatic full-device backup. The supplied start and dock voice prompts and connection/completion sounds are retained.

## Supported data and limits

- Contacts: first/last name, company, home/work/mobile/fax numbers, one postal address, two email addresses, URL, birthday and note.
- Calendar: individual timed events, title, note, start/end and one supported display reminder. Zoned events are converted to the configured device time zone; device events use local floating times. Set Thunderbird to the same time zone.
- Tasks: title, note, start/due dates without time, open/completed and high/normal/low priority.
- Creation, editing and deletion propagate both ways after the first successful association.

Unsupported items are skipped with a reason in the log: recurring/all-day events, exceptions, invitations, task times/reminders/intermediate progress, complex contacts with additional names/addresses or duplicate phone slots, and text exceeding IC35 field sizes or Windows-1252. Photos and other Thunderbird-only properties are not copied to the IC35; properties without a device equivalent are retained when updating an existing resource. Categories are not synchronized bidirectionally. IC35 memos are outside this edition's scope.

## Safety and storage

Conflicting edits or delete/edit conflicts stop the planned batch. Set both entries to the desired identical content, then retry; do not delete the sync state. Writes are read back, DAV changes use ETags, and a persistent journal supports recovery after interruption. An ambiguous interrupted operation stops for investigation. An error can occur after some changes have succeeded; there is no automatic rollback of the entire batch.

The app saves an encrypted record snapshot before reconciliation. This is not a full-device backup and does not require another dock press. **Nur Vollbackup** creates a separate complete `database_….org.dpapi`. No full-backup restore-to-device feature is included. **Geschützte Datei exportieren** decrypts a file to a plaintext copy; it does not restore it to the IC35.

Data directory: `%APPDATA%\IC35ThunderbirdAlpha`. State, journals, exports, operation snapshots and application logs use current-user Windows DPAPI. Add-on state/snapshots are separated by calendar selection under `sync_states`; `addon_pairing.dpapi` stores the protected pairing code. An interrupted operation must be resolved using its previous calendar selection before changing targets. The DAV collection files and Thunderbird caches remain ordinary local files. Files are retained until manually removed. DPAPI files depend on the originating Windows account.

Previous versions' data/settings are neither migrated nor removed. The new edition has its own installer, directory and port. Use only one IC35 per data directory: the model identifier is not a guaranteed unique serial number. After resetting or replacing the device, plan a separate initialization with backed-up data instead of reusing the previous state. Uninstalling keeps personal data.

## Alpha verification and source build

43 automated tests cover mappings, two-way changes/deletions, conflicts, recovery, pairing security and calendar selection. A real isolated Thunderbird 153.0.1 profile tests add-on creation/updates/deletion with local and cached CalDAV calendars, changes from both sides and unavailable-server rejection. No personal Google calendar is used in these tests. Windows executable checks cover the UI, DPAPI and bundled DAV service.

**The new combined Thunderbird workflow has not yet been verified on real IC35 hardware.** Its serial transport comes from the previous edition. Make a manual full backup before the first hardware test, then test a contact, individual event and task in both directions, including deletion.

Use Python **3.12** on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe desktop_entry.py
.\.venv\Scripts\python.exe scripts/build_windows.py
```

The build also packages the XPI from `addon/`. Compile `installer.iss` with Inno Setup 6. `scripts/package_source.py` creates and validates the source ZIP using an explicit allowlist. `scripts/smoke_windows.py` checks the executable and embedded DAV service without accessing a device. `scripts/test_thunderbird.py` uses a separate synthetic Thunderbird profile. `build-requirements.txt` records the concrete build versions. No personal data or credentials are packaged.

Use this source as a complete new repository revision, removing the previous cloud modules and build configuration instead of overlaying files. Publish the installer as a release asset. GPL-2.0; see `THIRD_PARTY_NOTICES.md` for provenance and bundled license notices.

## Recurring events and interrupted writes (a4)

IC35 events matching an existing Thunderbird recurrence are skipped even if reminders differ. Series are not modified. An interrupted CREATE may roll back only its journal-identified duplicate after an encrypted backup and fresh checks. Unrelated or subsequently edited duplicates are not deleted automatically. Keep all state and pending files and select the same calendar. The a2 add-on remains compatible.
