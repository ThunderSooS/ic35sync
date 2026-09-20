# Siemens IC35 Sync

**Deutsch** · [English](README.en.md)

> 🚧 **Vorabversion – Google-Verifizierung in Arbeit**
>
> Das Google-Branding ist bestätigt. Die Prüfung der Kalender- und
> Aufgabenberechtigungen wird vorbereitet; das Demo-Video steht noch aus.
> Fehlerberichte sind über die GitHub-Issues willkommen.

Windows-Desktop-Client für den Siemens IC35: Kontakte mit Thunderbird/CardDAV,
Kalender und Aufgaben mit Google, Memos mit einem lokalen Notizordner synchronisieren.

**Aktuelle Version: 3.3.0a8 (Installer-Alpha).** Google-Anmeldung und ausgewählte
Aufgaben-Sync-Abläufe wurden mit einem echten IC35 getestet. Die öffentliche
Google-Prüfung für Kalender- und Aufgabenberechtigungen ist noch nicht abgeschlossen.
Dies ist ein unabhängiges Projekt, keine offizielle Siemens-, Google- oder
Thunderbird-Anwendung.

Die Programmoberfläche ist derzeit deutschsprachig. Diese Dokumentation ist
auf Deutsch und Englisch verfügbar.

## Windows-Installer (Alpha)

`IC35-Sync-3.3.0a8-Alpha-Setup.exe` installieren und anschließend **Siemens IC35
Sync Alpha** über das Startmenü öffnen. Python und Abhängigkeiten sind enthalten.
Bestehende Daten unter `%APPDATA%\IC35SyncPreview` bleiben erhalten, auch bei
Deinstallation. Die Geräteprüfungen der Python-Vorversion müssen noch mit der
gebündelten EXE wiederholt werden. [Installation und Grenzen](docs/WINDOWS_ALPHA.md).
Die nachfolgende Python-Installation ist für die Ausführung aus dem Quellcode.

[Projektwebsite](https://ic35.thundersoos.cc/) ·
[Downloads und Releases](https://github.com/ThunderSooS/ic35thunderbird/releases) ·
[Änderungen](CHANGELOG.md)

## Funktionen

- Ein Button für den Gesamtabgleich, ein SyncStation-Tastendruck.
- Bidirektionaler Abgleich mit Konflikthinweisen und getrennten Zuordnungen.
- Auswahl eines beschreibbaren Google-Kalenders und einer Google-Aufgabenliste.
- Memo-Dateien als UTF-8 TXT oder Markdown; optional im lokal synchronisierten Cloud-Ordner.
- Vollbackup ausschließlich über **Nur Backup**; Start- und Abschlusssounds.

## Installieren und starten

Voraussetzungen: Windows, Python **3.12** inklusive Tcl/Tk und Python Launcher,
IC35-SyncStation sowie ein funktionierender serieller Anschluss/USB-Seriell-Treiber.

1. Das **Programmpaket mit Google-Anmeldung** aus den Release-Anhängen herunterladen
   und vollständig in einen eigenen Ordner entpacken. Für v3.3.0a4 heißt es
   `IC35-Sync-3.3.0a4-Google-Login-Test.zip`.
2. `install.bat` starten. Abhängigkeiten werden in eine lokale `.venv` installiert.
3. `start.bat` starten und den COM-Port auswählen.
4. Google-Ziele und gegebenenfalls den Notizordner einrichten.
5. **ALLES SYNCHRONISIEREN** anklicken und bei Aufforderung die SyncStation drücken.

### Google verbinden

Über **Google verbinden** öffnet sich die Anmeldung im Browser. Mit dem eigenen
Google-Konto anmelden, die Kalenderberechtigungen freigeben und einen Kalender
auswählen. Unter **Aufgaben-Ziel** Google Tasks verbinden, die Aufgabenliste
auswählen und die Teilnahme am Gesamtabgleich aktivieren. Kalender und Tasks
verwenden derzeit getrennte Freigaben; für beide dasselbe Google-Konto verwenden.

Das Programmpaket enthält `google_oauth_client.json` neben `start.bat`. Nutzer
müssen diese Datei nicht auswählen und kein eigenes Cloud-Projekt einrichten.
Die automatisch von GitHub angebotenen **Source code**-Archive enthalten nur
den Repository-Stand und können diese Konfiguration nicht enthalten. Falls die
App eine fehlende Herausgeber-Konfiguration meldet, das Programmpaket aus den
Release-Anhängen verwenden und vollständig entpacken.

Das Google-Branding ist bestätigt. Die zusätzliche Datenzugriffsprüfung steht
noch aus; bei der Anmeldung kann daher **„Google hat diese App nicht überprüft“**
erscheinen. Diese Vorabversion ist noch keine vollständig von Google überprüfte
Veröffentlichung.

### Datenordner und Updates

Die Vorabversion verwendet `%APPDATA%\IC35SyncPreview`, getrennt vom alten
`IC35ThunderbirdSync`-Ordner. Es gibt **keine automatische Migration**. Nicht
beide Programme gleichzeitig starten: Radicale nutzt auf beiden Seiten Port 5232.
Beim neuen Erstabgleich werden Bestände vereinigt; vorhandene Löschhistorie der
alten Installation wird nicht automatisch übernommen. Vor einem Test mit echten
Daten ein manuelles Vollbackup erstellen und die alten State-Dateien sichern.

Updates innerhalb der 3.3-Vorabversion nutzen denselben Preview-Datenordner und
behalten dort gespeicherte Anmeldungen und Zuordnungen. Dazu die App schließen,
das neue Paket separat entpacken und dessen `install.bat` sowie `start.bat` verwenden.
Den Datenordner und offene Operationsjournale nicht für ein Update löschen.

Vollbackups werden nur auf Anforderung über **Nur Backup** erstellt und liegen
in `%APPDATA%\IC35SyncPreview\backups`. Kleine Sicherungen einzelner
Sync-Vorgänge und Operationsjournale bleiben Teil des Abgleichs.
Eine Wiederherstellungsfunktion für Geräte-Vollbackups ist noch nicht vorhanden.

## Thunderbird-Kontakte

Der lokale Radicale-Dienst lauscht ausschließlich auf `127.0.0.1:5232`.
Für ein Thunderbird-CardDAV-Adressbuch die Adresse
`http://127.0.0.1:5232/ic35/addressbook/` verwenden; Benutzer `ic35`, kein Passwort.
Im ersten Gesamtlauf wird der Dienst gestartet. Es gibt keine LAN-Freigabe.
Derzeit läuft der Kontakte-Abgleich zusammen mit einem eingerichteten Kalender.
Nur Google Tasks kann über denselben Button ohne Kalender laufen.

## Verhalten und Grenzen

- Ein Erstabgleich verbindet gleiche Inhalte und übernimmt fehlende Gegenstücke.
  Spätere Löschungen werden anhand der letzten gemeinsamen Baseline übertragen.
- Memos/Aufgaben: maximal 60 Byte Titel und 255 Byte Text in Windows-1252.
  Zu große oder nicht darstellbare Inhalte werden nicht still gekürzt.
- Google Tasks: Titel, Text, Datum und Status. Keine Uhrzeit-/Serienlogik;
  Unteraufgaben, Elternaufgaben und zugewiesene Aufgaben werden ausgelassen.
- Google-Kalenderserien werden in einem begrenzten Zeitfenster als Einzeltermine
  abgebildet. Die Kalenderzeitzone im Client ist derzeit **Europe/Berlin**.
  IC35-Alarme/-Wiederholungen sind in der Gegenrichtung eingeschränkt.
- Der Sync ist keine Transaktion über alle Systeme. Fehler können einen teilweise
  abgeschlossenen Lauf hinterlassen. Journale nicht blind löschen.
- Gerätesperren/Passwörter werden derzeit nicht unterstützt.
- **Wiederherstellen von Vollbackups ist noch nicht implementiert.**

## Entwickeln und prüfen

Ab 3.3.0a4 werden Tokens beim Laden mit Windows DPAPI geschützt; neue Backups,
Rohdatenexporte, Berichte und Sync-Protokolle werden verschlüsselt gespeichert.
Geschützte Dateien benötigen in der Regel dasselbe Windows-Konto auf demselben
Rechner. Der neue Exportbutton erstellt bei Bedarf eine unverschlüsselte Kopie.
Ältere Programmversionen können migrierte Tokens nicht lesen. Bestehende Archive,
laufender Sync-State, Radicale-Daten und Notizdateien sind nicht pauschal
verschlüsselt. [Umfang, Migration und Grenzen](docs/LOCAL_DATA_PROTECTION.md).
Die folgenden Hardwareergebnisse beziehen sich auf 3.3.0a3; der Hardwaretest
und die echte Anmeldung nach Tokenmigration stehen für 3.3.0a4 noch aus.

Für v3.3.0a3 sind **37 Offline-Tests** erfolgreich. Im Test am Gerät wurden
die Browser-Anmeldung für Kalender und Tasks, die Übernahme einer Google-Aufgabe
auf den IC35, die Erledigung vom IC35 nach Google und die Löschung von Google
zum IC35 bestätigt. Der Gesamtlauf wurde erfolgreich abgeschlossen. Das ist
keine vollständige Prüfung aller Kalender-, Kontakt- und Memo-Sonderfälle.

Aufgaben ohne Datum: Der IC35 kann automatisch Datumswerte aus dem Jahr 2000
einsetzen. v3.3.0a3 berücksichtigt den beobachteten Fall beim Kontrolllesen und
verhindert für entsprechend verknüpfte Google-Aufgaben die Übertragung eines
erfundenen Fälligkeitsdatums. Siehe [Details zur Korrektur](docs/TASKS_UNDATED_FIX.md).

```text
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/check_release.py
python scripts/build_release.py
```

Die Offline-Tests verwenden simulierte Gerätedaten. Für GUI-/Google-Tests werden
die normalen Abhängigkeiten benötigt. `IC35_SYNC_DATA_DIR` kann für isolierte Tests
einen eigenen Datenordner vorgeben. Niemals fremde Benutzer- oder Google-Tokens verwenden.

`scripts/build_release.py` erstellt ein Quellpaket ohne OAuth-Konfiguration.
Für ein Programmpaket mit einem ausdrücklich dafür vorgesehenen Desktop-Client:

```text
python scripts/build_login_test.py PFAD_ZUR_DESKTOP_CLIENT_JSON
```

Persönliche Tokens (`google_token.json`, `google_tasks_token.json`), Sync-State,
Protokolle und Backups gehören weder ins Repository noch in Release-Downloads.

[Beitragen](CONTRIBUTING.md) · [Sicherheit](SECURITY.md) ·
[Datenschutz](docs/PRIVACY.md) · [Veröffentlichungsstand](docs/RELEASE_READINESS.md)

## Lizenz

GNU GPL Version 2, siehe [LICENSE](LICENSE) und
[Herkunftshinweise](THIRD_PARTY_NOTICES.md). Bereitstellung ohne Gewährleistung.

