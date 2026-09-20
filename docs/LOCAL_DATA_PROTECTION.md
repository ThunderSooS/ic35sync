# Lokaler Datenschutz ab 3.3.0a4

Windows DPAPI schützt Daten für das aktuelle Windows-Benutzerkonto. Die App
verwendet keine maschinenweite Freigabe und keinen Klartext-Fallback. Ein Fehler
beim Schützen oder Entschlüsseln stoppt den betroffenen Vorgang.

## Geschützt

- Google-Kalender- und Tasks-Tokens: vorhandenes Token-JSON wird beim Laden
  eingelesen und atomar durch eine kontrollgelesene verschlüsselte Datei ersetzt.
  Der Dateiname bleibt gleich. Keine zusätzliche Klartextkopie wird angelegt.
- Neue manuelle Geräte-Vollbackups: `.org.dpapi`, intern unveränderte Gerätebytes.
- Neue automatische Memo-/Tasks-Sicherungen, einschließlich Memo-Dateikopien.
- Neue Rohdatenexporte und Berichte des Gesamt- und direkten Tasks-Abgleichs
  sowie Google-Ereignissicherungen vor Löschungen.
- Neue ausführliche Sync-/Backup-Protokolle: `.log.dpapi`. Die Live-Anzeige
  der App bleibt lesbar und kann persönliche Inhalte enthalten.

Einige geschützte JSON-Dateien behalten `.json` im Namen, enthalten aber ein
binäres Format. Die App erkennt es beim Lesen. Ältere Programmversionen können
die migrierten Tokens und geschützten Dateien nicht lesen: nach dem Wechsel
nicht parallel mit einer älteren Version denselben Datenordner verwenden.

## Grenzen und vorhandene Dateien

Es erfolgt keine pauschale Umschreibung älterer Archive. Bestehende Backups,
Exporte und Protokolle bleiben in ihrem bisherigen Format erhalten. Nur Tokens
und tatsächlich erneut eingelesene ältere JSON-Sicherungen werden automatisch
migriert. Das ist keine sichere Löschung früherer Dateiversionen auf dem Datenträger.

Live-Sync-State, Operationsjournale, Konflikt-/Planungsdateien, Einstellungen,
Radicale-Daten und dessen eigenes Startprotokoll bleiben in dieser Version
unverschlüsselt. Auch der ausgewählte Notizordner und der IC35 sind nicht durch
diese Änderung verschlüsselt. DPAPI schützt nicht vor anderen Programmen, die
unter demselben Windows-Konto laufen. Es gibt weiterhin keine automatische
Aufbewahrungsfrist und keine Geräte-Restore-Funktion.

## Export und Rechnerwechsel

DPAPI-Dateien sind grundsätzlich an Windows-Konto und Rechner gebunden.
Vor einem Rechnerwechsel oder Verlust des Windows-Profils benötigte Sicherungen
über **Geschützte Datei entschlüsselt exportieren …** ausgeben und die ausgegebene
Kopie an einem selbst gewählten geschützten Ort sichern. Eine verschlüsselte
Dateikopie allein ist kein garantiert portables Wiederherstellungsmedium.

Der Export legt absichtlich eine unverschlüsselte Kopie an, überschreibt keine
vorhandene Datei und ändert das Original nicht. Für ein `.org`-Backup kann im
Speicherdialog ein Dateiname mit `.org` gewählt werden. Dies entschlüsselt die
Sicherung; es stellt noch keine Daten auf dem Gerät wieder her.

Auch per Kommando möglich:

```text
python scripts/decrypt_local_file.py QUELLE ZIEL
```

Tokens nicht für Support exportieren oder teilen. Auf einem neuen Rechner neu
bei Google anmelden. Diagnoseprotokolle vor Weitergabe auf persönliche Inhalte
prüfen; Verschlüsselung ist keine Anonymisierung.

## Prüfung

Mit künstlichen Daten unter echtem Windows DPAPI getestet: Roundtrip,
Manipulationserkennung, fehlgeschlagener atomarer Austausch mit unverändertem
Original, Tokenmigration, kein Klartext-Fallback und verschlüsselte Logeinträge.
Ein Hardwarelauf und der Test der echten Google-Anmeldung nach Migration stehen
für 3.3.0a4 noch aus. Persönliche Runtime-Dateien wurden beim Entwickeln nicht migriert.

Am 16.09.2026 bestanden alle 43 automatisierten Tests, einschließlich
Tokenmigration mit simulierter Google-Aktualisierung und geschütztem Gerätebackup
mit simuliertem Geräteprotokoll.

Quelle: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
