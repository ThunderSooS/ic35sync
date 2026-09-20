# 3.3.0a8

- Neue persönliche MP3 zum Start der Synchronisation.
- Schritt 2 bestätigt sichtbar den erkannten Dock-Tastendruck nach erfolgreichem
  Verbindungsaufbau; ebenso beim direkten Aufgaben-Sync und manuellen Backup.
- Die bisherige Dock-Aufforderung und der Bestätigungston bleiben erhalten.

# 3.3.0a7 (Windows-Installer-Alpha)

- Einzelne Windows-EXE mit eingebettetem Python, Sounds und Google-Anmeldung.
- Installer für das aktuelle Konto mit Startmenü und optionalem Desktop-Link.
- Radicale als Unterprozess der gebündelten EXE; bestehender Datenordner bleibt.
- Paketprüfung für Tk, Google-API-Definitionen, Ressourcen und lokalen CardDAV-Start.

# 3.3.0a6 (persönliches Audio-Extra)

- Kurzer Bestätigungston nach erfolgreichem Dock-Verbindungsaufbau bei
  Gesamt-Sync, direktem Aufgaben-Sync und manuellem Backup.
- Eine noch laufende Dock-Sprachansage wird beim Bestätigungston beendet.

# 3.3.0a5 (persönliches Audio-Extra)

- MP3-Sprachhinweis bei Aufforderung zum Drücken der Docktaste im Gesamt-Sync,
  direkten Aufgaben-Sync und manuellen Backup.
- Asynchrone Windows-Wiedergabe einmal pro Aufforderung, nicht pro Verbindungsversuch.

# 3.3.0a4

- Google-Tokens mit Windows-DPAPI und kontrollgelesener atomarer Migration.
- Neue Geräte-/Memo-/Tasks-Sicherungen, Rohdatenexporte, Berichte und ausführliche Sync-Protokolle verschlüsselt.
- Exportbutton für eine ausdrücklich angeforderte unverschlüsselte Kopie und Datenschutzlink.
- Bestehende Archive und laufender State werden nicht pauschal migriert; siehe LOCAL_DATA_PROTECTION.md.
- Echte DPAPI-Tests mit künstlichen Daten erfolgreich; Hardware-/Google-Migrationstest noch offen.

# 3.3.0a3

- Aufgaben ohne Datum: die vom IC35 eingesetzten Datumswerte werden beim Kontrolllesen akzeptiert und für verknüpfte undatierte Google-Aufgaben nicht zurückübertragen.
- Nach einem abgebrochenen Anlegevorgang wird eine eindeutig passende Aufgabe anhand des Journals wieder zugeordnet.
- Am Gerät bestätigt: Google-Aufgabe auf IC35, Erledigung vom IC35 nach Google, Löschung von Google zum IC35.
- Google-Anmeldung für Kalender und Tasks ohne Dateiauswahl mit mitgelieferter Desktop-Konfiguration getestet.
- 37 Offline-Tests erfolgreich. Öffentliche Google-Datenzugriffsprüfung noch ausstehend.

# 3.3.0a2

- Google-Anmeldung ohne Dateiauswahl für Kalender und Tasks vorbereitet.
- Bestehende lokale Client-Konfiguration bleibt erhalten.
- Fehlende Herausgeber-Konfiguration wird verständlich gemeldet.
- Beim GitHub-Upload fehlende Git-Regeln und Prüfworkflow wieder ergänzt.

# Änderungen

## 3.3.0a1

- Erste getrennte GitHub-Vorabfassung auf Basis von v3.2.5.
- Legacy-Testaktionen entfernt und Dokumentation zusammengeführt.
- Kalenderauswahl statt persönlichem Kalendernamen; erster Abgleich ohne alte Baseline möglich.
- Preview-Daten getrennt; Kalender-Zuordnungen je Ziel erhalten.
- Quellrelease-Build und automatisierte Prüfungen hinzugefügt.

## Grundlage v3.2.5

- Ein Sync-Button, ein SyncStation-Tastendruck, Vollbackup nur auf Anfrage.
- Kontakte, Kalender, Memos und Google Tasks; Sounds und Konfliktprüfungen.
- IC35-Startdatum-Ergänzung bei Aufgaben berücksichtigt und eindeutige
  Wiederaufnahme unterbrochener Aufgabenimporte ergänzt.
