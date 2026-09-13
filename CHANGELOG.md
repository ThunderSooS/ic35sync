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
