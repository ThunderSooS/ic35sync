# 3.4.0b6 · Notizen in beide Richtungen / Two-way notes

## Deutsch

### Neu
- IC35-Notizen werden jetzt in **beide Richtungen** mit den Textdateien im Notizordner abgeglichen: Anlegen, Bearbeiten, Umbenennen (= Betreff) und Löschen wirken jeweils auf die andere Seite.
- Neue Notizen am PC: `.txt`-Datei ohne Zusatz „[IC35-…]“ anlegen; sie wird übertragen und danach mit IC35-ID umbenannt.
- Konflikte (auf beiden Seiten unterschiedlich geändert oder gelöscht und geändert) werden gemeldet; für diese Notiz wird nichts geschrieben.
- Die Beschriftung in der App heißt jetzt **Notizordner:**.

### Sicherheit
- Jeder Schreibvorgang wird vom IC35 zurückgelesen; vor dem Abgleich wird eine geschützte Sicherung aller Notizen angelegt.
- Kein Kürzen: zu lange Texte (Betreff 60, Text 255 Byte) oder Zeichen außerhalb Windows-1252 werden mit Grund übersprungen.
- Fehlender Ordner, verschwundene Notizdateien oder ein plötzlich leerer IC35 halten den Notizabgleich an, ohne etwas zu löschen.
- Unterbrochene Neuanlagen werden beim nächsten Lauf erkannt statt doppelt angelegt.

### Hinweis
Beim ersten Abgleich werden vorhandene Dateien aus 3.4.0b4/b5 mit den Notizen verknüpft. Eine vorher am PC gelöschte Datei wird dabei neu angelegt, weil es noch keinen gemeinsamen Stand gibt; erst danach wirkt Löschen am PC auch auf dem IC35. Im Notizordner keine anderen Textdateien ablegen, da jede `.txt`-Datei als neue Notiz gilt. Das Add-on ist unverändert (`IC35-Thunderbird-Bridge-3.4.0b5.xpi`). Das Setup ist nicht signiert. Falls Windows SmartScreen erscheint, bitte über **Weitere Informationen → Trotzdem ausführen** bestätigen.

---

## English

### New
- IC35 notes are now synchronized **both ways** with the text files in the notes folder: creating, editing, renaming (= subject) and deleting each apply to the other side.
- New notes on the PC: create a `.txt` file without the “[IC35-…]” suffix; it is transferred and then renamed with its IC35 ID.
- Conflicts (changed differently on both sides, or deleted and changed) are reported; nothing is written for that note.
- The label in the app is now **Notizordner:** (notes folder).

### Safety
- Every write is read back from the IC35; a protected backup of all notes is saved before syncing.
- No truncation: texts that are too long (subject 60, text 255 bytes) or characters outside Windows-1252 are skipped with a reason.
- A missing folder, vanished note files or a suddenly empty IC35 stop the note sync without deleting anything.
- Interrupted creations are detected on the next run instead of being created twice.

### Note
On the first sync, existing files from 3.4.0b4/b5 are linked to the notes. A file deleted on the PC before that is created again, because there is no common state yet; afterwards, deleting on the PC also deletes on the IC35. Do not keep other text files in the notes folder, as every `.txt` file counts as a new note. The add-on is unchanged (`IC35-Thunderbird-Bridge-3.4.0b5.xpi`). The setup is not signed. If Windows SmartScreen appears, please confirm via **More info → Run anyway**.

# 3.4.0b5 · Texte aufgeräumt / Text cleanup

## Deutsch

### Geändert
- Hilfetexte in der App und die Einstellungsseite des Add-ons nennen keine persönlichen Kalendernamen mehr als Beispiel.
- Die Bezeichnung „Alpha“ in Meldungen der App und des Add-ons wurde entfernt.
- Die Kopplungsanleitung nennt jetzt den richtigen Button **Kalender und Aufgabenlisten laden**.
- Neues Thunderbird-Add-on `IC35-Thunderbird-Bridge-3.4.0b5.xpi` (intern 3.4.0.13) mit den geänderten Texten; die Funktion ist unverändert.

### Hinweis
Das Add-on kann über die vorhandene Version installiert werden, die Kopplung bleibt erhalten. Das Setup ist nicht signiert. Falls Windows SmartScreen erscheint, bitte über **Weitere Informationen → Trotzdem ausführen** bestätigen.

---

## English

### Changed
- Help texts in the app and the add-on settings page no longer use personal calendar names as examples.
- The term “Alpha” was removed from app and add-on messages.
- The pairing instructions now name the correct button **Kalender und Aufgabenlisten laden** (load calendars and task lists).
- New Thunderbird add-on `IC35-Thunderbird-Bridge-3.4.0b5.xpi` (internal 3.4.0.13) with the updated texts; functionality is unchanged.

### Note
The add-on can be installed over the existing version; pairing is retained. The setup is not signed. If Windows SmartScreen appears, please confirm via **More info → Run anyway**.

# 3.4.0b4 · IC35-Notizen beim Sync speichern / Save IC35 notes during sync

## Deutsch

### Neu
- Bei jeder Synchronisation werden alle IC35-Notizen (Memos) nur lesend mit ausgelesen und als Textdateien gespeichert.
- Der Zielordner wird in der App unter **Notizen nach:** über **Ordner wählen …** festgelegt und dauerhaft gespeichert. Ohne Ordner werden Notizen übersprungen.
- Eine Datei pro Notiz, benannt nach Betreff und IC35-ID, z. B. `Einkauf [IC35-000012].txt`.
- Geänderte Notizen werden aktualisiert, bei geändertem Betreff wird die Datei umbenannt. Es werden keine Dateien gelöscht.
- Das Protokoll wird rechts neben der Bedienung angezeigt (mit Scrollleiste, volle Fensterhöhe).
- Die Abschlussmeldung nennt zusätzlich neue, aktualisierte und umbenannte Notizen.

### Behoben
- Die Einrichtungshilfe nennt jetzt den richtigen Dateinamen des Thunderbird-Add-ons (`IC35-Thunderbird-Bridge-3.4.0b1.xpi`).

### Hinweis
Die Notizdateien im gewählten Ordner sind unverschlüsselt. An den Notizen auf dem IC35 wird nichts verändert. Ein Fehler beim Speichern der Notizen bricht den Sync nicht ab.

---

## English

### New
- Every sync also reads all IC35 notes (memos) read-only and saves them as text files.
- The target folder is set in the app under **Notizen nach:** (notes to) via **Ordner wählen …** (choose folder) and stored permanently. Without a folder, notes are skipped.
- One file per note, named after subject and IC35 ID, e.g. `Einkauf [IC35-000012].txt`.
- Changed notes are updated; if the subject changes, the file is renamed. No files are deleted.
- The log is shown to the right of the controls (with scrollbar, full window height).
- The completion message additionally lists new, updated and renamed notes.

### Fixed
- The setup help now shows the correct file name of the Thunderbird add-on (`IC35-Thunderbird-Bridge-3.4.0b1.xpi`).

### Note
The note files in the selected folder are not encrypted. Notes on the IC35 are not modified. An error while saving notes does not abort the sync.

# 3.4.0b3 · Kalender automatisch laden

Nach Verbindung des Thunderbird-Add-ons werden Kalender und Aufgabenlisten automatisch geladen. Gespeicherte Ziel-IDs bleiben ausgewählt. Bei Verbindungsfehlern erfolgt ein erneuter Versuch nach 15 Sekunden, ohne Popup. Während einer Synchronisation startet kein automatischer Ladevorgang.

# 3.4.0b2 · Thunderbird automatisch starten

Beim normalen App-Start wird Thunderbird geöffnet, falls es in der aktuellen Windows-Sitzung noch nicht läuft. Bereits laufende Instanzen bleiben unverändert. Bei fehlender Installation oder Startfehler erscheint ein Hinweis im Protokoll. Paketprüfungen und Hintergrunddienste starten Thunderbird nicht.

# 3.4.0b1 · Google-Tasks-Listen über Thunderbird

- Unterstützt Aufgabenlisten des Google-Providers, unabhängig vom Listennamen.
- Dauerhafte Zuordnung von Google-Aufgaben-IDs; unbestätigte Neuanlagen werden nicht automatisch wiederholt.
- Neuer Buttontext: Kalender und Aufgabenlisten laden.
- Neues IC35-Add-on 3.4.0.12 erforderlich. Grenzen und Testumfang siehe README.

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
