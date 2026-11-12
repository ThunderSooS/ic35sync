# IC35 Sync 3.4.0

Synchronisation des Siemens IC35 mit Thunderbird unter Windows.

## Änderungen
- Aufgabenlöschungen vom IC35 nach Thunderbird berücksichtigen reine Änderungen der gültigen DTSTAMP- und LAST-MODIFIED-Zeitstempel. Andere Eigenschaften und die Prüfungen vor dem Löschen bleiben geschützt.
- Das installierte Programm verwendet ein vollständiges Ordnerpaket. Das erneute Entpacken einer Einzel-EXE beim Start entfällt.
- Der Installer liefert alle Laufzeitdateien mit. Das Paket enthält den passenden Quellcode und SHA-256-Prüfsummen.

## Installation
Alle IC35-Sync-Fenster schließen, Daten sichern und IC35-Sync-3.4.0-Setup.exe ausführen. Vorhandene interne Datenpfade und Zuordnungen werden nicht umbenannt. Für den manuellen Start muss der gesamte Programmordner einschließlich _internal zusammenbleiben.

## Hinweise
Die Bridge trägt ihre unabhängige Versionsnummer 3.4.0.13. Die unterstützte Thunderbird-Version ergibt sich aus dem Add-on-Manifest.
Dateien mit IC35-ID ohne gespeicherte Notizzuordnung werden weiterhin nicht automatisch gelöscht. Die Ursache einer verlorenen Zuordnung ist mit dieser Version nicht allgemein behoben.
Die Windows-Zugriffsmeldung ist nicht als generell behoben nachgewiesen; die Umstellung beseitigt den Entpackschritt, nicht sämtliche möglichen Startprobleme.
