# IC35 Sync Beta · 3.4.0b4

**IC35 Sync Beta for 64-bit Windows 10/11.** Two-way synchronization of contacts, individual calendar events and tasks with a Siemens IC35; IC35 notes are saved as text files in a folder of your choice during each sync. The sync app needs no cloud login or credential JSON files. The bundled add-on connects existing Thunderbird calendars, including Google CalDAV and other network calendars. Thunderbird continues handling the account connection. The application interface is currently German.

[Deutsch](README.md) · [Privacy](PRIVACY.md) · [Changes](CHANGELOG.md) · [License](LICENSE)

## Use an existing calendar

Keep your existing calendar and phone configuration. The path is `IC35 ↔ sync app ↔ Thunderbird add-on ↔ existing calendar service ↔ phone`.

1. Install the new setup and install `IC35-Thunderbird-Bridge-3.4.0b1.xpi` in Thunderbird using **Add-ons and Themes → gear menu → Install Add-on From File**. The installer places this file beside the EXE; it is also a separate release asset.
2. In the sync app, click **Thunderbird-Add-on koppeln**. Paste the copied pairing code into the add-on's settings and click **Verbinden**.
3. Click **Kalender und Aufgabenlisten laden** in the app and choose the existing calendar you want under **Termine aus**. It is shown with the suffix **· Thunderbird**.
4. Choose a task-capable calendar separately under **Aufgaben aus**, or keep **Lokale IC35-Sammlung**. Google Tasks lists are available through Thunderbird’s Provider for Google Calendar add-on.

The add-on currently supports **Thunderbird 153.x**, tested on 153.0.1. It uses an Experiment API for calendar access, which causes Thunderbird to show a broad permission prompt. Its implementation uses calendar functions and does not access email or account passwords.

Keep both applications open. Network calendars must be online; errors or pending offline changes stop the reconciliation. Existing calendar entries do not need to be copied. Read-only or disabled calendars are not selectable. Contacts still use the local CardDAV address book below. Recurrence and other limitations listed below still apply.

## Setup

1. Run `IC35-Sync-Beta-3.4.0b4-Setup.exe`. Python is bundled; installation is per user without administrator rights.
2. Open **IC35 Sync Beta**, select the dock's COM port and check the IC35 time zone (default `Europe/Berlin`).
3. Install the bundled `IC35-Thunderbird-Bridge-3.4.0b1.xpi` add-on in Thunderbird and restart Thunderbird.
4. In the app, click **Thunderbird-Add-on koppeln**, paste the pairing code into the add-on settings and click **Verbinden**.
5. Calendars and task lists load automatically after pairing (manually via **Kalender und Aufgabenlisten laden**). Select the existing calendar and task collection shown with **· Thunderbird**.
6. Optionally choose a folder for IC35 notes under **Notizen nach:** (notes to) using **Ordner wählen …** (choose folder).

The add-on method uses the calendars and task collections already configured in Thunderbird. Thunderbird continues to handle account login and server synchronization; the IC35 app does not need Google credentials or JSON files.

## Daily use

Synchronize the address book/calendar in Thunderbird, then click **Alles mit Thunderbird synchronisieren** in this app. Press the dock button when prompted. The UI and a sound confirm the connection. Wait for completion; at the end, IC35 notes are saved to the chosen folder. Then synchronize Thunderbird again to receive the changes. The log to the right of the controls shows every step, and the completion message summarizes all changes including notes. Avoid editing either side during the operation.

The regular workflow uses one dock connection, without a confirmation dialog or an automatic full-device backup. The supplied start and dock voice prompts and connection/completion sounds are retained.

## Supported data and limits

- Contacts: first/last name, company, home/work/mobile/fax numbers, one postal address, two email addresses, URL, birthday and note.
- Calendar: individual timed events, title, note, start/end and one supported display reminder. Zoned events are converted to the configured device time zone; device events use local floating times. Set Thunderbird to the same time zone.
- Tasks: title, note, start/due dates without time, open/completed and high/normal/low priority.
- Creation, editing and deletion propagate both ways after the first successful association.
- Notes: IC35 → folder only, one text file per note (subject and content); nothing is written back to the IC35.

Unsupported items are skipped with a reason in the log: recurring/all-day events, exceptions, invitations, task times/reminders/intermediate progress, complex contacts with additional names/addresses or duplicate phone slots, and text exceeding IC35 field sizes or Windows-1252. Photos and other Thunderbird-only properties are not copied to the IC35; properties without a device equivalent are retained when updating an existing resource. Categories are not synchronized bidirectionally. IC35 memos are not synchronized, but every sync exports them read-only as text files into the folder chosen under “Notizen nach:” (notes to) (one file per note, named after subject and IC35 ID; existing files are updated, nothing is deleted).

## Safety and storage

Conflicting edits or delete/edit conflicts stop the planned batch. Set both entries to the desired identical content, then retry; do not delete the sync state. Writes are read back, DAV changes use ETags, and a persistent journal supports recovery after interruption. An ambiguous interrupted operation stops for investigation. An error can occur after some changes have succeeded; there is no automatic rollback of the entire batch.

The app saves an encrypted record snapshot before reconciliation. This is not a full-device backup and does not require another dock press. **Nur Vollbackup** creates a separate complete `database_….org.dpapi`. No full-backup restore-to-device feature is included. **Geschützte Datei exportieren** decrypts a file to a plaintext copy; it does not restore it to the IC35.

Data directory: `%APPDATA%\IC35ThunderbirdAlpha`. State, journals, exports, operation snapshots and application logs use current-user Windows DPAPI. Add-on state/snapshots are separated by calendar selection under `sync_states`; `addon_pairing.dpapi` stores the protected pairing code. An interrupted operation must be resolved using its previous calendar selection before changing targets. The DAV collection files and Thunderbird caches remain ordinary local files. Files are retained until manually removed. DPAPI files depend on the originating Windows account.

Previous versions' data/settings are neither migrated nor removed. This edition has its own installer, directory and port (the folder name `IC35ThunderbirdAlpha` is kept for compatibility). Use only one IC35 per data directory: the model identifier is not a guaranteed unique serial number. After resetting or replacing the device, plan a separate initialization with backed-up data instead of reusing the previous state. Uninstalling keeps personal data.

## Verification and source build

67 automated tests cover mappings, two-way changes/deletions, conflicts, recovery, pairing security, calendar selection and note export. A real isolated Thunderbird 153.0.1 profile tests add-on creation/updates/deletion with local and cached CalDAV calendars, changes from both sides and unavailable-server rejection. No personal Google calendar is used in these tests. Windows executable checks cover the UI, DPAPI and bundled DAV service.

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

The setup and add-on are available under [Releases](https://github.com/ThunderSooS/ic35sync/releases). GPL-2.0; see `THIRD_PARTY_NOTICES.md` for provenance and bundled license notices.

## Recurring events and interrupted writes

IC35 events matching an existing Thunderbird recurrence are skipped even if reminders differ. Series are not modified. An interrupted CREATE may roll back only its journal-identified duplicate after an encrypted backup and fresh checks. Unrelated or subsequently edited duplicates are not deleted automatically. Keep all state and pending files and select the same calendar. The add-on does not need to be reinstalled for this.

## Google Tasks through Thunderbird

Google Tasks lists are supported since 3.4.0b1. This requires the add-on `IC35-Thunderbird-Bridge-3.4.0b1.xpi` (internal add-on version 3.4.0.12); restart Thunderbird after installing it. Existing pairing is retained. Configure your Google Tasks list in Thunderbird using Provider for Google Calendar. Click **Kalender und Aufgabenlisten laden** and select the list under **Aufgaben aus**.

Supports title, notes, due date, completion, creation, editing and deletion in both directions. Server-assigned IDs are mapped persistently in the Thunderbird profile. Keep this profile and the app’s sync state. An uncertain creation blocks synchronization rather than retrying; provide the log for investigation instead of deleting state files.

Only normal priority is supported. A separate start date is unsupported unless equal to the due date. Lists containing subtasks are blocked. Recurring Google tasks are not reliably exposed as recurring by the provider and are unsupported. Use simple tasks for the first test.

Tests use a simulated Google provider inside real isolated Thunderbird. An actual Google account and physical IC35 still require a practical verification run.

The app automatically starts Thunderbird if it is not already running. If its installation cannot be found, open Thunderbird manually. Closing the sync app leaves Thunderbird running.

## IC35 notes (since 3.4.0b4)

Choose a target folder under **Notizen nach:** (notes to) with **Ordner wählen …** (choose folder); the choice is remembered. Every regular sync then reads all IC35 notes read-only and stores them there:

- one file per note, named after subject and IC35 ID, e.g. `Einkauf [IC35-000012].txt` (UTF-8, Windows line endings),
- changed notes are overwritten; if the subject changes, the file is renamed,
- no files are deleted, not even when a note was removed on the IC35; your own files in the folder are left alone,
- edits to the text files are not transferred to the IC35.

Without a folder, notes are skipped. An error while saving notes is reported in the log and does not abort the sync. **Nur Vollbackup** (full backup only) does not write note files. Note files are not encrypted (see [Privacy](PRIVACY.md)).
