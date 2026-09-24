# 3.4.0a10 · Kopplung nach Add-on-Neuinstallation

- Gültiger Kopplungscode darf eine veraltete Thunderbird-Profilkennung ersetzen, wenn keine andere aktive Sitzung verbunden ist. Dadurch funktioniert eine Neuinstallation des Add-ons ohne manuelles Zurücksetzen versteckter Browserdaten.
- Eine aktive andere Sitzung bleibt geschützt und kann nicht durch einen zweiten Client übernommen werden.
- 65 Tests einschließlich Stale-Profile-Reparatur und aktiver Sitzungsablehnung.

# 3.4.0a9 · Thunderbird-Schreibbestätigung

- Neues Add-on 3.4.0.9: begrenzte Auftragslaufzeit (85 s), Schreibbestätigung spätestens nach 60 s oder verständlicher Abbruch. Die Auftragsannahme bleibt anschließend verfügbar.
- Bei CalDAV ohne Offline-Cache dienen zusätzlich die providerseitigen Meldungen über dieselbe UID als Bestätigung; anschließend wird der aktuelle Inhalt erneut gelesen. Neuanlagen können intern als Änderungen gemeldet werden. Bei aktivem Offline-Cache genügt eine solche Meldung ausdrücklich nicht.
- Unbestätigte laufende Schreibvorgänge bleiben gegen Wiederholung gesperrt. Keine automatische Wiederholung eines Schreibbefehls. Bei dauerhaft hängendem Provider ist ein Thunderbird-Neustart mit anschließender Journalprüfung nötig.
- Eine vom Provider ergänzte Standard-Erinnerung darf bei einer Neuanlage als eigene Ausgangsbasis gespeichert werden. Explizite spätere Änderungen bleiben streng geprüft. Erfolgreiche Neuanlagen mit verlorener Rückmeldung werden wieder zugeordnet.
- 64 Python-Tests sowie tatsächliches Thunderbird 153.0.1 mit lokalen, zwischengespeicherten und nicht zwischengespeicherten CalDAV-Testkalendern geprüft. CREATE/MODIFY mit absichtlich unterdrückter Rückmeldung, falsche UID, ausbleibende Bestätigung ohne Wiederholung und anschließendes Kalenderlisten-Laden getestet.
- Installer allein aktualisiert das Thunderbird-Add-on nicht: XPI über Thunderbird-Erweiterungen installieren und Thunderbird neu starten. Bestehende Kopplung und Sync-Dateien behalten.
- Persönlicher Google-CalDAV-Kalender und Hardware wurden nicht für Entwickler-Schreibtests verwendet.

# 3.4.0a8 · Lösch-/Neuanlage-Schleife beenden

- Eindeutig gleiche Einzeltermine werden beim Erstabgleich trotz abweichender Erinnerung verknüpft. Beide Erinnerungswerte bleiben als getrennte Ausgangswerte erhalten; spätere Änderungen werden weiterhin erkannt.
- Eine unterbrochene Neuanlage wird nur bereinigt, wenn ein passendes Original oder ein exakt passendes Serienvorkommen vorhanden ist. UID-Präfixe und IC35-Markierungen allein erlauben keine Löschung. Geänderte Inhalte und zusätzliche Nutzdaten blockieren die Bereinigung.
- Regulär erfolgreich angelegte Termine werden bei verlorener Bestätigung wieder zugeordnet, statt gelöscht und neu angelegt zu werden.
- Entfernt die vereinfachte Wochenberechnung aus a5: COUNT, INTERVAL und Zeitzonen werden wieder durch die vollständige Wiederholungsregel ausgewertet.
- 62 Tests, darunter drei unveränderte Folgesynchronisationen nach Bereinigung. Build stoppt bei fehlgeschlagenen Tests oder EXE-Paketprüfung.
- Die fehlende CalDAV-Schreibbestätigung ist damit nicht allgemein behoben. Diese Version verhindert insbesondere unnötige Schreibvorgänge bei bereits vorhandenen Terminen. Kein neuer Test an persönlichen Kalendern oder IC35 durch den Entwickler.

# 3.4.0a6 · Journal-Reparatur eindeutig abschließen

- Reparatur eines abgebrochenen Thunderbird-CREATE verwendet jetzt die eindeutige IC35-UID aus dem Journal und den unveränderten Datensatz. Die zusätzliche Serienberechnung kann diese sichere Wiederaufnahme nicht mehr fälschlich blockieren.
- Fremde Kalenderänderungen, eine andere UID oder zusätzliche unbekannte Inhalte blockieren weiterhin jede automatische Löschung.

# 3.4.0a5 · Wöchentliche Serien korrekt erkennen

- Korrigiert die Berechnung wöchentlicher Wiederholungen. Lokale IC35-Zeit wird direkt als Kalender-Wandzeit verglichen; dadurch wird ein passender Termin wie 20.09.2027 in einer Serie korrekt erkannt.
- EXDATE wird berücksichtigt. Die Serie wird weiterhin niemals verändert.

# 3.4.0a4 · Schutz vor Einzelkopien vorhandener Serien

- Vorhandene Serienvorkommen werden anhand von Titel, Beginn, Ende und Wiederholungsregel erkannt. Passende IC35-Einzeltermine bleiben ausgenommen und werden nicht erneut hochgeladen. Abweichende Erinnerungen verhindern diesen Schutz nicht.
- EXDATE und vorhandene Serienausnahmen werden bei der Erkennung berücksichtigt. Hochfrequente Regeln werden vorsichtig anhand von Titel und Dauer geschützt.
- Ein unterbrochenes CREATE kann seine eigene Einzelkopie bereinigen, wenn Journal, UID, unveränderter IC35-Termin und vorhandenes Serienvorkommen zusammenpassen. Nur eine nachträglich ergänzte Erinnerung darf abweichen; zusätzliche unbekannte Nutzdaten verhindern die Löschung.
- Die Bereinigung sichert Journal und Kalenderdaten verschlüsselt, prüft den aktuellen Datensatz vor der Löschung und kann nach einer verlorenen Löschbestätigung fortgesetzt werden. Keine pauschale Duplikatbereinigung.
- Protokoll zeigt jetzt vor jeder Übertragung an, dass die Bestätigung aussteht.
- Add-on a2 bleibt unverändert. Bestehende State-Dateien müssen erhalten bleiben.
- Serien werden weiterhin nicht bidirektional bearbeitet. Diese Version verhindert Doppelanlagen; sie ersetzt keine vollständige Serien-Synchronisation.

# 3.4.0a3 · IC35-Termin-Kontrolllesen

- Behebt den im Geräteprotokoll beobachteten falschen Abbruch nach erfolgreichem Termin-CREATE: Firmware speichert AlrmRep=0 als leeres Feld und ergänzt bei fehlender Wiederholung EndRepeat.
- Kontrolllesen akzeptiert nur diese Vorgaben; Betreff, Zeiten, Notiz, Erinnerung und übrige Steuerwerte bleiben exakt geprüft.
- Wiederholungserkennung verwendet die dokumentierte Maske 0x0F. Ein unbenutztes EndRepeat-Datum allein macht einen Termin nicht zur Serie.
- Regressionstest für Wiederaufnahme eines bestehenden CREATE-Journals ohne doppelte Anlage.
- Keine State-Migration und kein Zurücksetzen erforderlich. Add-on a2 unverändert kompatibel.

# 3.4.0a2 · Vorhandene Thunderbird-Kalender

- Neues Add-on für Thunderbird 153.x: vorhandene lokale und CalDAV-Kalender direkt auswählen, einschließlich bereits eingebundener Google-Kalender.
- Kalender und Aufgaben getrennt in der Sync-App auswählbar; Kontakte bleiben beim lokalen CardDAV-Adressbuch.
- Lokale Kopplung mit zufälligem Code und Profilbindung; keine Weitergabe von Thunderbird-Kontozugangsdaten an die App.
- Aktualisierungs-, Offline-, Versions- und Rückleseprüfungen vor dem Übernehmen von Änderungen.
- Getrennte Sync-Zuordnungen je Kalenderauswahl. Fremde unvollständige Vorgänge blockieren einen Zielwechsel.
- Add-on in einem isolierten echten Thunderbird mit lokalem und zwischengespeichertem CalDAV-Kalender geprüft; Netzwerkausfall führt zum Stopp.
- Serien, ganztägige Termine und Besprechungseinladungen bleiben vorerst ausgenommen. Kein direkter Google-Tasks-Zugriff.

# 3.4.0a1 · Thunderbird-only Alpha

- Lokaler Zweiwegeabgleich für Kontakte, Einzeltermine und Aufgaben über CardDAV/CalDAV.
- Cloud-Anmeldung, Cloud-Synchronisation und OAuth-Dateien aus dieser Ausgabe entfernt.
- Eigener Port 5233 und Datenordner IC35ThunderbirdAlpha; keine automatische Migration alter Zuordnungen.
- Dreifachvergleich mit gespeichertem Ausgangsstand, Konfliktstopp, Versionsprüfung und verschlüsseltem Wiederaufnahmejournal.
- Dock-Erkennung, Sprachansagen, Töne und rotierende Halbkreis-Pfeile enthalten.
- Vollbackup auf Anfrage; normale Synchronisation mit einer Dock-Verbindung.
- Windows-EXE, Benutzer-Installer, deutsche und englische Dokumentation sowie reproduzierbare Build-Skripte.
- Noch keine Bestätigung des neuen Gesamtablaufs an echter IC35-Hardware. Einschränkungen siehe README.
# 3.4.0a11 · Umbenennung in IC35 Sync Beta

Die Anwendung heißt jetzt **IC35 Sync Beta**. Fenstertitel, Installer, Startmenü und Desktop-Verknüpfung verwenden den neuen Namen. Installationsordner, EXE-Dateiname und AppId bleiben unverändert, damit vorhandene Einstellungen, Kopplung und State-Dateien erhalten bleiben.
