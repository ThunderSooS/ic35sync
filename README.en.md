# Siemens IC35 Sync

## Windows installer alpha 3.3.0a8

Install `IC35-Sync-3.3.0a8-Alpha-Setup.exe`, then launch **Siemens IC35 Sync Alpha**
from the Start menu. Python and dependencies are included. Existing data in
`%APPDATA%\IC35SyncPreview` is preserved, including during uninstall.
Hardware tests of the previous Python version still need repeating with the
bundled executable. Google verification remains pending. The installer is unsigned.
The Python setup instructions below apply to running from source.

[Deutsch](README.md) · **English**

> 🚧 **Pre-release – Google verification in progress**
>
> Google branding has been verified. Verification of Calendar and Tasks
> permissions is being prepared; the demo video is available.
> Bug reports are welcome through GitHub Issues.

A Windows desktop client for the Siemens IC35: synchronize contacts with
Thunderbird/CardDAV, calendars and tasks with Google, and memos with a local
notes folder.

**Current version: 3.3.0a8 (installer alpha).** Google sign-in and selected task
synchronization workflows have been tested with a real IC35. Google's public
verification of Calendar and Tasks permissions has not yet been completed.
This is an independent project, not an official Siemens, Google, or Thunderbird
application.

The application interface is currently in German. This documentation is
available in German and English. Instructions below retain the German button
labels so you can find them in the application.

[Project website](https://ic35.thundersoos.cc/) ·
[Downloads and releases](https://github.com/ThunderSooS/ic35thunderbird/releases) ·
[Changelog (German)](CHANGELOG.md)

## Features

- One button for the full sync and one press of the SyncStation button.
- Bidirectional synchronization with conflict notices and separate record mappings.
- Selection of a writable Google calendar and a Google Tasks list.
- Memo files in UTF-8 TXT or Markdown format, optionally in a locally synchronized cloud folder.
- Full backups only on request using **Nur Backup**; sounds at sync start and completion.

## Installation and startup

Requirements: Windows, Python **3.12** including Tcl/Tk and the Python Launcher,
an IC35 SyncStation, and a working serial connection or USB-to-serial driver.

1. Download the **application package with Google sign-in** from the release
   attachments and extract it completely into its own folder. For v3.3.0a4,
   the filename is `IC35-Sync-3.3.0a4-Google-Login-Test.zip`.
2. Run `install.bat`. Dependencies are installed in a local `.venv`.
3. Run `start.bat` and select the COM port.
4. Configure the Google destinations and, if needed, the notes folder.
5. Click **ALLES SYNCHRONISIEREN** (sync everything) and press the SyncStation
   button when prompted.

### Connecting to Google

Click **Google verbinden** to open sign-in in your browser. Sign in with your
own Google account, grant the calendar permissions, and select a calendar.
Under **Aufgaben-Ziel**, connect Google Tasks, select a task list, and enable
its participation in the full sync. Calendar and Tasks currently use separate
authorization flows; use the same Google account for both.

The application package includes `google_oauth_client.json` next to `start.bat`.
Users do not need to select this file or set up their own Cloud project.
GitHub's automatically generated **Source code** archives contain only the
repository contents and may lack this configuration. If the application reports
that the publisher's configuration is missing, use the application package from
the release attachments and extract it completely.

Google branding has been verified. The additional data access verification is
still pending, so sign-in may display **“Google hasn't verified this app.”**
This pre-release has not yet completed Google's verification process.

### Data folder and updates

The pre-release uses `%APPDATA%\IC35SyncPreview`, separate from the old
`IC35ThunderbirdSync` folder. There is **no automatic migration**. Do not run
both applications at the same time: both use port 5232 for Radicale.
The new initial sync merges existing records; deletion history from the old
installation is not imported automatically. Before testing with real data,
create a manual full backup and save the old state files.

Updates within the 3.3 pre-release series use the same preview data folder,
preserving saved sign-ins and mappings. Close the application, extract the new
package separately, and run its `install.bat` and `start.bat`. Do not delete the
data folder or pending operation journals as part of an update.

Full backups are created only on request using **Nur Backup** and stored in
`%APPDATA%\IC35SyncPreview\backups`. Small backups of individual sync operations
and operation journals remain part of synchronization. Restoring device full
backups is not yet implemented.

## Thunderbird contacts

The local Radicale service listens only on `127.0.0.1:5232`.
For a Thunderbird CardDAV address book, use
`http://127.0.0.1:5232/ic35/addressbook/`, username `ic35`, and no password.
The service starts during the first full sync. It is not exposed to the LAN.
Contact synchronization currently runs alongside a configured calendar.
Google Tasks alone can run through the same sync button without a calendar.

## Behavior and limitations

- An initial sync links matching content and copies missing counterparts.
  Later deletions are propagated using the last shared synchronization baseline.
- Memos/tasks support titles up to 60 bytes and text up to 255 bytes in
  Windows-1252. Oversized or unrepresentable content is not silently truncated.
- Google Tasks: title, notes, date, and completion status. No time-of-day or
  recurrence support; subtasks, parent tasks, and assigned tasks are skipped.
- Recurring Google Calendar events are represented as individual occurrences
  within a limited time window. The client's calendar time zone is currently
  **Europe/Berlin**. IC35 alarms and recurrence have limited support in the
  reverse direction.
- Sync is not a single transaction across all systems. An error can leave a
  partially completed run. Do not delete journals without investigating.
- Device locks/passwords are not currently supported.
- **Restoring full backups is not yet implemented.**

## Development and validation

Starting with 3.3.0a4, tokens are migrated on load to Windows DPAPI protection.
New backups, raw exports, reports and sync logs are encrypted. Protected files
normally require the same Windows account and computer; the new export button
creates an explicit plaintext copy when needed. Older versions cannot read
migrated tokens. Existing archives, live sync state, Radicale storage and notes
are not all encrypted. See [scope and limitations (German)](docs/LOCAL_DATA_PROTECTION.md).
The hardware results below refer to 3.3.0a3. Hardware testing and a real Google
sign-in after token migration are still pending for 3.3.0a4.

For v3.3.0a3, **37 offline tests** passed. Testing with a real device confirmed
browser sign-in for Calendar and Tasks, transferring a Google task to the IC35,
propagating completion from the IC35 to Google, and propagating deletion from
Google to the IC35. The full sync completed successfully. This does not cover
every calendar, contact, or memo edge case.

Undated tasks: the IC35 may automatically insert dates from the year 2000.
Version 3.3.0a3 handles the observed case during read-back verification and
prevents an invented due date from being sent to Google for the corresponding
linked tasks. See the [fix details (German)](docs/TASKS_UNDATED_FIX.md).

```text
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/check_release.py
python scripts/build_release.py
```

Offline tests use simulated device data. GUI and Google tests require the
normal dependencies. Set `IC35_SYNC_DATA_DIR` to use a separate data folder for
isolated tests. Never use another person's user or Google tokens.

`scripts/build_release.py` creates a source package without OAuth configuration.
To build an application package with a Desktop client explicitly intended for
that purpose:

```text
python scripts/build_login_test.py PATH_TO_DESKTOP_CLIENT_JSON
```

Personal tokens (`google_token.json`, `google_tasks_token.json`), sync state,
logs, and backups must not be included in the repository or release downloads.

The following supporting documents are currently in German:
[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) ·
[Privacy](docs/PRIVACY.md) · [Release readiness](docs/RELEASE_READINESS.md)

## License

GNU GPL version 2. See [LICENSE](LICENSE) and
[third-party notices (German)](THIRD_PARTY_NOTICES.md). Provided without warranty.
