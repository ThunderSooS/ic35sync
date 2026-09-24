# IC35 Sync Beta · 3.4.0a11

**IC35 Sync Beta für Windows 10/11 (64 Bit).** Kontakte, einzelne Termine und Aufgaben werden in beide Richtungen mit einem Siemens IC35 synchronisiert. Die Sync-App benötigt keine eigene Cloud-Anmeldung und keine JSON-Zugangsdaten. Das mitgelieferte Add-on verbindet bereits vorhandene Thunderbird-Kalender, einschließlich Google-CalDAV- und anderer Netzwerkkalender. Thunderbird verwaltet weiterhin deren Anmeldung und Serversynchronisation.

[English](README.en.md) · [Datenschutz](PRIVACY.md) · [Änderungen](CHANGELOG.md) · [Lizenz](LICENSE)

## Einen vorhandenen Thunderbird-Kalender verwenden

Den vorhandenen Kalender und die Handy-Einrichtung unverändert lassen. Die Verbindung lautet:

`IC35 ↔ Sync-App ↔ Thunderbird-Add-on ↔ vorhandener Kalenderdienst ↔ Handy`

1. Neues Setup installieren. Das Add-on `IC35-Thunderbird-Bridge-3.4.0a9.xpi` liegt danach neben der EXE und wird zusätzlich als Download angeboten.
2. In Thunderbird über **Add-ons und Themes → Zahnrad → Add-on aus Datei installieren** die XPI installieren.
3. In der Sync-App **Thunderbird-Add-on koppeln** drücken. Den kopierten Code in den Einstellungen des Add-ons einfügen und **Verbinden** drücken.
4. In der App **Kalender aus Thunderbird laden** drücken und bei **Termine aus** den gewünschten Kalender mit dem Zusatz **· Thunderbird** auswählen.
5. Für Aufgaben separat einen unterstützten Kalender wählen oder **Lokale IC35-Sammlung** belassen. Google Tasks wird nicht über diese CalDAV-Verbindung bereitgestellt.

Getestet mit Thunderbird **153.0.1**; das Add-on ist vorerst auf **153.x** begrenzt, da es interne Kalender-Schnittstellen verwendet. Thunderbird zeigt für diese Art Add-on eine weitreichende Berechtigungsabfrage. Der mitgelieferte Code verwendet Kalenderfunktionen, keine E-Mails oder Kontopasswörter.

Bei Netzwerkkalendern müssen Thunderbird und die Sync-App laufen und der Kalenderdienst erreichbar sein. Schreibgeschützte/deaktivierte Kalender werden nicht zur Auswahl angeboten. Der Kalender wird vor dem Abgleich aktualisiert; offline wartende Änderungen oder Ladefehler stoppen den Vorgang. Änderungen gehen an den bestehenden Kalender und können dadurch auch auf dem Handy erscheinen. Serien und andere unten genannte Einschränkungen bleiben bestehen.

Kontakte verwenden weiterhin das lokale CardDAV-Adressbuch. Eine alternative Auswahl bestehender Thunderbird-Adressbücher ist nicht Teil dieser Version.

## Installation und erster Start

1. `IC35-Sync-Beta-3.4.0a11-Setup.exe` ausführen. Python muss nicht separat installiert werden. Das Setup installiert für das aktuelle Windows-Konto, ohne Administratorrechte.
2. **IC35 Sync Beta** starten und den COM-Anschluss des Docks auswählen. Die Zeitzone muss zur Uhr des IC35 passen (Vorgabe `Europe/Berlin`).
3. Das mitgelieferte Add-on `IC35-Thunderbird-Bridge-3.4.0a9.xpi` in Thunderbird installieren und Thunderbird neu starten.
4. In der App **Thunderbird-Add-on koppeln** drücken, den Kopplungscode in den Add-on-Einstellungen einfügen und **Verbinden** drücken.
5. **Kalender aus Thunderbird laden** drücken und den gewünschten Kalender bzw. die Aufgabensammlung mit dem Zusatz **· Thunderbird** auswählen.

### Kontakte

Im Thunderbird-Adressbuch **Neues Adressbuch → CardDAV-Adressbuch hinzufügen** wählen:

- Benutzername: `ic35`
- Adresse: `http://127.0.0.1:5233/ic35/addressbook/`
- Falls Thunderbird ein Passwort abfragt: `ic35`. Es handelt sich um den lokalen Dienst, der kein echtes Kontopasswort prüft.

Thunderbird verwaltet die Anmeldung und Serversynchronisation des gewählten Kalenders. Die IC35-App benötigt dafür keine Google-Zugangsdaten oder JSON-Dateien. Beim ersten Abgleich werden vorhandene Einträge in beide Richtungen übernommen und eindeutig gleiche Einträge verknüpft.

## Täglicher Ablauf

1. App öffnen und in Thunderbird Adressbuch/Kalender synchronisieren. Während des Geräteabgleichs keine Einträge bearbeiten.
2. **Alles mit Thunderbird synchronisieren** drücken. Die Startansage ertönt.
3. Nach Aufforderung die Taste am IC35-Dock drücken. Der erkannte Verbindungsaufbau wird sichtbar bestätigt und mit einem Ton quittiert.
4. Abschluss abwarten. Danach Thunderbird erneut synchronisieren, damit die Geräteänderungen angezeigt werden.

Ein normaler Abgleich benötigt eine Dock-Verbindung und startet ohne zusätzliche Bestätigungsfrage. Ein Vollbackup wird nur über **Nur Vollbackup** angefordert.

## Was wird abgeglichen?

| Bereich | Unterstützt |
| --- | --- |
| Kontakte | Vor-/Nachname, Firma, private/geschäftliche Telefonnummer, Mobilnummer, Fax, eine Anschrift, zwei E-Mail-Adressen, URL, Geburtstag, Notiz |
| Kalender | Einzeltermine mit Anfang/Ende, Betreff, Notiz und einer kompatiblen Anzeige-Erinnerung |
| Aufgaben | Betreff, Notiz, Start-/Fälligkeitsdatum ohne Uhrzeit, offen/erledigt, hoch/normal/niedrig |
| Änderungen | Anlegen, Bearbeiten und Löschen in beiden Richtungen nach erfolgreicher Zuordnung |

Kalenderzeiten werden in die eingestellte IC35-Zeitzone umgerechnet. Das Gerät kennt selbst keine Zeitzonen; neue Gerätetermine werden als lokale Uhrzeiten bereitgestellt. Thunderbird entsprechend auf dieselbe Zeitzone einstellen.

Diese Alpha überspringt nicht sicher darstellbare Einträge und nennt den Grund im Protokoll: Terminserien und Ausnahmen, ganztägige Termine, Einladungen, Aufgaben mit Uhrzeit/Erinnerungen/Zwischenstatus sowie zu lange Texte oder Zeichen außerhalb Windows-1252. Komplexe Kontakte mit mehreren Anschriften, zusätzlichen Namensbestandteilen oder mehreren Nummern desselben Typs werden ebenfalls übersprungen. Fotos und zusätzliche Thunderbird-Felder werden nicht auf den IC35 übertragen; bei Änderungen einer vorhandenen Ressource bleiben nicht abgebildete Eigenschaften erhalten. Kategorien werden nicht bidirektional abgeglichen. IC35-Memos sind nicht Bestandteil dieser Ausgabe.

## Konflikte, Sicherungen und Fehler

- Unterschiedliche Änderungen auf beiden Seiten bzw. Löschen auf einer und Ändern auf der anderen Seite stoppen den geplanten Abgleich. Beide Einträge auf denselben gewünschten Stand bringen und erneut starten. State-Dateien nicht löschen.
- Geräte-Schreibvorgänge werden zurückgelesen. Thunderbird-Schreibvorgänge verwenden Versionsprüfungen (ETags). Ein dauerhaftes Journal verhindert blindes Wiederholen nach einem Abbruch. Ein mehrdeutiger unterbrochener Vorgang stoppt mit Fehlermeldung.
- Ein Fehler während einer laufenden Übertragung kann nach einzelnen bereits übernommenen Änderungen auftreten. Der nächste Lauf prüft den gespeicherten Zwischenstand; dies ist keine Transaktion mit automatischem Rollback.
- Vor einem Abgleich wird eine geschützte Datensatz-Sicherung angelegt. Das ist **kein vollständiges IC35-Speicherbackup** und benötigt keinen zusätzlichen Dock-Tastendruck.
- **Nur Vollbackup** erstellt separat eine vollständige `database_….org.dpapi`. Die App enthält keine Rückschreibfunktion für diese Vollbackups. **Geschützte Datei exportieren** erzeugt eine entschlüsselte Kopie, keine Wiederherstellung auf dem Gerät.
- DPAPI-Dateien können grundsätzlich nur mit dem zugehörigen Windows-Konto entschlüsselt werden. Exporte sind unverschlüsselt.

Datenordner: `%APPDATA%\IC35ThunderbirdAlpha`. Darin liegen `radicale` (lokale Sammlungen), `thunderbird_state.dpapi`, gegebenenfalls `pending.dpapi`, `backups`, `exports`, `logs` und `reports`. Add-on-Zuordnungen und deren Sicherungen liegen getrennt pro Kalenderauswahl unter `sync_states`; der Kopplungscode liegt geschützt in `addon_pairing.dpapi`. Ein unvollständiger Abgleich mit einer anderen Auswahl muss zuerst abgeschlossen werden. Die lokalen DAV-Dateien und Thunderbird-Caches sind nicht durch die App verschlüsselt. Keine automatische Aufräumfrist. Der Button **Datenordner** öffnet den Ordner.

Die bisherigen Datenordner, Zugangsdaten und Zuordnungen älterer Ausgaben werden nicht migriert oder gelöscht. Diese Alpha verwendet einen eigenen Installer, Datenordner und Port. Pro Datenordner nur **einen IC35** verwenden; die Gerätekennung ist keine garantierte individuelle Seriennummer. Nach Zurücksetzen/Austausch des Geräts den bisherigen State nicht weiterverwenden, sondern eine getrennte Neueinrichtung mit gesicherten Daten planen. Eine Deinstallation lässt persönliche Daten bestehen.

## Entwicklungsstand und Test

43 automatisierte Tests prüfen Zuordnung, Änderungen/Löschungen, Konflikte, Wiederaufnahme, Kopplungsschutz und Kalenderauswahl. Ein isoliertes Thunderbird-153.0.1-Profil prüft das echte Add-on mit lokalen und zwischengespeicherten CalDAV-Kalendern, inklusive Änderungen auf beiden Seiten, Versionskonflikten und Serverausfall. Die Windows-EXE wird separat auf Startfähigkeit, Tk-Oberfläche und DPAPI geprüft. Dein Google-Kalender wurde für diese Tests nicht verwendet.

**Der neue Thunderbird-Gesamtabgleich ist noch nicht an echter IC35-Hardware bestätigt.** Der serielle Transport stammt aus der bisherigen Ausgabe. Vor produktiver Nutzung mit einem Testkontakt, einem Einzeltermin und einer Aufgabe jeweils beide Richtungen und Löschungen prüfen. Vor dem ersten Hardwaretest ein manuelles Vollbackup erstellen.

## Quellcode und eigener Build

Benötigt Python **3.12** unter Windows. Die Runtime-Abhängigkeiten stehen in `requirements.txt`; `build-requirements.txt` dokumentiert die konkreten Versionen dieses Builds.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe desktop_entry.py
.\.venv\Scripts\python.exe scripts/build_windows.py
```

Der Build erstellt auch die XPI aus `addon/`. Anschließend `installer.iss` mit Inno Setup 6 kompilieren. `scripts/package_source.py` erstellt ein Quellarchiv aus einer festen Dateiliste und prüft dessen ZIP-Integrität. `scripts/smoke_windows.py` prüft die gebaute EXE einschließlich ihres eingebetteten DAV-Dienstes ohne Gerätezugriff. `scripts/test_thunderbird.py` nutzt eine separate, künstliche Thunderbird-Testumgebung. Es werden keine persönlichen Daten, Schlüssel oder State-Dateien verpackt.

Für GitHub den Quellcode als vollständigen neuen Stand verwenden, nicht einfach über alle alten Dateien kopieren: alte Cloud-Module und frühere Build-Konfigurationen gehören nicht in diese Ausgabe. Installer unter Releases bereitstellen. GPL-2.0; Herkunft und weitere Lizenzen siehe `THIRD_PARTY_NOTICES.md`.

## Serien und Wiederaufnahme ab a4

Passende Einzeltermine auf dem IC35 werden bei vorhandener Thunderbird-Serie übersprungen, auch bei abweichender Erinnerung. Die Serie wird nicht bearbeitet. Eine im unterbrochenen CREATE nachweislich erzeugte Einzelkopie wird nach verschlüsselter Sicherung und erneuter Prüfung entfernt. Fremde oder nachträglich inhaltlich bearbeitete Duplikate werden nicht automatisch gelöscht. State und pending.dpapi nicht entfernen; unverändert denselben Kalender auswählen. Add-on a2 muss nicht neu installiert werden.
