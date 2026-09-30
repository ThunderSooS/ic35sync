# Verification · 3.4.0b6

## Deutsch
- 82 automatisierte Tests, davon 17 für den Notizabgleich: Erstabgleich, Wiederholung ohne Änderungen, Bearbeiten und Umbenennen auf beiden Seiten, Löschen in beide Richtungen, Neuanlage am PC, Konflikte, gleiche Änderung auf beiden Seiten, keine Kürzung, CRLF-Längenprüfung, Sicherheitsstopps (Ordner fehlt, alle Dateien fehlen, IC35 leer), Wiederaufnahme einer unterbrochenen Neuanlage, Verknüpfung vorhandener Dateien und das Schreibformat an den IC35 (Befehle 01 08/01 09/01 02, Memo-Magic 60 16 99 laut ic35link 1.18, Blöcke zu 80 Byte).
- Unter Wine gebaut; dort schlägt der Radicale-Integrationstest wegen des Wine-Dateisystems fehl, `smoke_windows.py` und die Installer-Prüfung liefen nicht.
- **Noch nicht an echter IC35-Hardware geprüft:** Schreiben, Ändern und Löschen von Notizen. Vor dem ersten Test ein Vollbackup erstellen und mit einer Testnotiz beginnen.

## English
- 82 automated tests, 17 of them for note sync: initial sync, repeat without changes, editing and renaming on both sides, deletion both ways, creation on the PC, conflicts, identical change on both sides, no truncation, CRLF length check, safety stops (folder missing, all files missing, IC35 empty), resuming an interrupted creation, linking existing files and the IC35 write format (commands 01 08/01 09/01 02, memo magic 60 16 99 per ic35link 1.18, 80-byte blocks).
- Built under Wine; there the Radicale integration test fails due to the Wine file system, `smoke_windows.py` and the installer check were not run.
- **Not yet verified on real IC35 hardware:** writing, updating and deleting notes. Make a full backup before the first test and start with a test note.

# Verification · 3.4.0b5

## Deutsch
- Nur Textänderungen in App und Add-on; 67 automatisierte Tests wie in 3.4.0b4 (unter Wine: Radicale-Integrationstest schlägt wegen des Wine-Dateisystems fehl; `smoke_windows.py` und die Installer-Prüfung liefen dort nicht).
- Die gebaute XPI enthält Version 3.4.0.13 und keine persönlichen Beispielnamen.

## English
- Text-only changes in app and add-on; 67 automated tests as in 3.4.0b4 (under Wine the Radicale integration test fails due to the Wine file system; `smoke_windows.py` and the installer check were not run there).
- The built XPI contains version 3.4.0.13 and no personal example names.

# Verification · 3.4.0b4

## Deutsch

- 67 automatisierte Tests, davon 2 neue für die Notizablage (sichere Dateinamen, reservierte Windows-Namen, Anlegen, Aktualisieren, Umbenennen bei geändertem Betreff, keine Löschung, fremde Dateien bleiben unberührt, UTF-8 mit Windows-Zeilenumbrüchen).
- Die Notizen werden nur lesend über die bestehenden IC35-Lesefunktionen (Datenbank öffnen, zählen, per Index lesen, schließen) abgerufen; es werden keine Records oder Change-Flags geschrieben.
- Der Build dieser Ausgabe wurde unter Wine erstellt. Dort schlägt der Radicale-Integrationstest wegen des Wine-Dateisystems fehl; `smoke_windows.py` und die isolierte Installer-Prüfung liefen dort nicht. Beides sollte unter echtem Windows wiederholt werden.
- Noch nicht an echter IC35-Hardware geprüft: Auslesen der Notizen nach dem Abgleich innerhalb derselben Dock-Verbindung.

## English

- 67 automated tests, including 2 new ones for note export (safe file names, reserved Windows names, create, update, rename on subject change, no deletion, unrelated files untouched, UTF-8 with Windows line endings).
- Notes are read read-only using the existing IC35 read functions (open database, count, read by index, close); no records or change flags are written.
- This release was built under Wine. There, the Radicale integration test fails due to the Wine file system; `smoke_windows.py` and the isolated installer check were not run. Both should be repeated on real Windows.
- Not yet verified on real IC35 hardware: reading notes after reconciliation within the same dock connection.

# Verification · 3.4.0b1

## Google Tasks adapter

The real Thunderbird 153.0.1 extension API was exercised with a synthetic Google-provider wrapper backed by Thunderbird storage. The wrapper assigns new server IDs and normalizes due dates to UTC timestamps. End-to-end reconciliation covers IC35-side creation, server-side creation, bidirectional edits and completion/reopening, deletion from either side, stable ID mapping and repeated runs without duplicates. Durable uncertain-create state blocks synchronization. Subtask hierarchies are rejected. Existing real CalDAV integration checks also pass. The physical IC35 and live Google provider/account are not exercised by this automated test; a live test is still required before claiming full provider compatibility.

## a9 write acknowledgement checks

64 Python regression tests pass. An isolated Thunderbird 153.0.1 profile and local Radicale server exercise the production add-on with local storage, cached CalDAV and uncached CalDAV. The test-only wrapper deliberately drops CREATE and MODIFY promise completion after dispatching the real operation; the add-on confirms the uncached provider notification and reads back the stored result. The server retains one record, then reflects the edit and deletion. Additional tests reject a different UID, keep uncertain mutations locked against retries, remove observers on timeout, reject unconfirmed cached writes, and verify that the next calendar-list call succeeds. Test fixtures are injected only into the disposable test XPI, never the release XPI. The personal Google calendar and IC35 hardware were not used for write tests.

The installer ships add-on 3.4.0.9, which must also be installed in Thunderbird. A timeout does not cancel an already dispatched provider request; unresolved operations remain locked until completion or Thunderbird restart, then Python's durable journal checks the actual state before further writes.

## a3 regression checks

Four additional tests reproduce the supplied hardware log's event-field defaults, reject actual content/time/alarm changes, reject recurrence flags including reserved low-nibble values, and resume an interrupted successful CREATE without duplicates. The a2 add-on is unchanged. The correction itself still requires a real-device retry; the supplied log proves that the earlier CREATE reached the device before readback validation failed.

## Completed

- 43 automated tests: contact/event/task mapping, low task priority and completion, device date defaults, time-zone conversion, unsupported data rejection, preservation of unmapped properties, initial matching, bidirectional edits/deletions, conflicts, ambiguous duplicates and incomplete reads; add-on pairing authentication, website-origin/Host/profile rejection, timeout behavior, calendar routing and state separation.
- Recovery tests simulate lost acknowledgements after creating records on either side and ensure no duplicates are created when resuming.
- Source-change guards cover concurrent device edits/reappearance and deletion conflicts involving otherwise unmapped remote properties or local categories.
- Real Radicale integration test on a temporary local port: create, read, update and delete all three resource types; stale ETag deletion is rejected.
- Actual Thunderbird 153.0.1 in a separate headless profile: add-on reads, creates, updates and deletes synthetic events/tasks; rejects stale versions; handles a cached CalDAV calendar; app-side changes reach the local CalDAV server, server-side changes reach Thunderbird, and a server outage stops the operation. The test-only XPI adds a fixture initializer to the production API/background code; this initializer is absent from the release XPI.
- Full production reconciliation engine and calendar adapter tested together with the real Thunderbird add-on and CalDAV server: simulated IC35 event creation reaches the server, a server edit reaches the simulated IC35, and a device-side deletion removes the server entry. DPAPI-backed state is used. Only the physical IC35 is simulated in this integration check.
- Frozen EXE check: Tk application constructed in isolation, current-user Windows DPAPI write/read round-trip, time-zone data and all configured audio files present; local add-on broker starts with protected pairing storage.
- Frozen Radicale subprocess: synthetic task PUT/GET/DELETE through the bundled service.
- Inno Setup 6.7.3: successful isolated per-user install; installed executable passes package/DAV checks; successful uninstall.
- Source ZIP: complete file CRC check, fixed source allowlist; no runtime state, credentials or personal organizer data included.

## Not yet verified

- Real Siemens IC35 read/write/delete using this new combined Thunderbird edition.
- Interactive add-on installation/pairing in the user's existing Thunderbird profile and end-to-end edits in the actual personal Google calendar. No personal Google calendar was accessed during these tests.
- Listening to the audio prompts on the user's output device; checks verify file inclusion, not audibility.

The reconciliation tests use a simulated IC35 adapter. The actual serial transport is carried over from the previous edition. These tests do not establish hardware compatibility on every dock/firmware version. This release remains a beta.

## Suggested hardware acceptance test

1. Create a manual full backup; retain the existing installation and its data.
2. Add the new local CardDAV/CalDAV collections in Thunderbird.
3. Create one simple test contact, timed event and date-only task in Thunderbird; sync to IC35 and inspect them there.
4. Change these entries on IC35, including completing the task; sync and refresh Thunderbird.
5. Delete one test entry on either side, sync, and verify the matching deletion. Repeat in the opposite direction with a separate test entry.
6. Run a second unchanged sync; no new duplicates or content writes should occur.

## a4 Serien-Duplikatschutz

56 automatisierte Tests erfolgreich. Neue Tests: Serienvorkommen trotz unterschiedlicher Erinnerung, anderer Tag, EXDATE, unveränderte Aufgaben, gezielte Journal-Bereinigung, geänderte Notiz und zusätzlicher Ort verhindern Löschung, Wiederaufnahme nach verlorener Löschbestätigung. Konservative Erkennung hochfrequenter Regeln berechtigt niemals zur automatischen Bereinigung. Tatsächliche gespeicherte Nutzer-Serie nur lesend gegen den betroffenen IC35-Datensatz geprüft. Kein Live-Kalender und kein IC35 durch den Entwickler verändert; der nächste Hardwarelauf steht aus.
