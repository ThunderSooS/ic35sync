# IC35 Sync 3.4.0

Synchronisation des Siemens IC35 mit Thunderbird unter Windows: Kontakte, Einzeltermine, Aufgaben und Notizen. [English documentation](README.en.md).

## Downloads

[Veröffentlichung 3.4.0](https://github.com/ThunderSooS/ic35sync/releases/tag/v3.4.0)

| Datei | Verwendung |
| --- | --- |
| IC35-Sync-3.4.0-Setup.exe | Empfohlene Installation |
| IC35-Sync-3.4.0-Windows.zip | Vollständiger Programmordner für manuellen Start |
| IC35-Sync-3.4.0-Source.zip | Zum Build passender Quellcode mit Buildskripten |
| IC35-Thunderbird-Bridge-3.4.0.13.xpi | Thunderbird-Erweiterung |
| SHA256SUMS.txt | SHA-256-Prüfsummen |
| BUILD-MANIFEST.json | Quellstand und dokumentierte Buildprüfungen |

Die Bridge hat eine unabhängige Versionsnummer. Ihr Manifest erlaubt Thunderbird 153.x; andere Thunderbird-Versionen sind damit nicht automatisch kompatibel.

## Installation und Aktualisierung

1. IC35- und Thunderbird-Daten sichern. Bei einem Update die bestehende Installation und deren Daten zunächst behalten.
2. Alle IC35-Sync-Fenster schließen und das Setup ausführen.
3. Vorhandene Einstellungen, Kopplung und Sync-State nicht löschen. Historische interne Ordnernamen bleiben aus Kompatibilitätsgründen erhalten.
4. Die XPI bei Bedarf separat in Thunderbird über Add-ons und Themes → Zahnrad → Add-on aus Datei installieren. Der Windows-Installer installiert die Erweiterung nicht automatisch in Thunderbird.

Für den manuellen Start das Windows-ZIP vollständig entpacken. IC35Thunderbird.exe und _internal müssen im selben Programmordner bleiben. Nicht nur die EXE herauskopieren. Die Ordnerverpackung vermeidet das erneute Entpacken beim Start; sie garantiert keine bestimmte Startzeit und beseitigt nicht jede mögliche Windows-Zugriffssperre.

## Erster Abgleich

1. Thunderbird geöffnet lassen. In IC35 Sync den Dock-COM-Anschluss und die IC35-Zeitzone wählen.
2. Thunderbird-Add-on koppeln: den Code aus der App in die Erweiterungseinstellungen übernehmen. Den Kopplungscode nicht veröffentlichen.
3. Kalender und Aufgabenlisten laden und die gewünschten Ziele auswählen. Vorhandene Netzwerkkalender werden über Thunderbird angesprochen; Kontozugangsdaten bleiben dort.
4. Für Kontakte das lokale CardDAV-Adressbuch in Thunderbird einrichten. Die Einrichtungshilfe in der App nennt die Adressen.
5. Thunderbird vor dem Geräteabgleich synchronisieren. Dann den Abgleich in der App starten und die Taste der SyncStation erst bei Aufforderung drücken.
6. Ergebnis und Protokoll prüfen und Thunderbird danach erneut synchronisieren. Anfangs entbehrliche Testeinträge verwenden.

Die lokalen Sammlungen nutzen Port 5233, die gekoppelte Bridge Port 5234, jeweils auf 127.0.0.1. Die App muss für diese Dienste laufen. Keine Portfreigabe im Router einrichten.

## Notizen als Textdateien

Einen eigenen Notizordner wählen, keine Sammlung beliebiger Textdateien. Neue .txt-Dateien ohne IC35-ID werden als neue Notizen behandelt. Zugeordnete Dateien tragen den Zusatz [IC35-000012]; diesen nicht zur Konfliktbereinigung entfernen, wenn keine Neuanlage gewünscht ist.

Anlegen, Bearbeiten, Umbenennen und Löschen werden bei vorhandener Zuordnung in beide Richtungen abgeglichen. Eine Löschung bei gleichzeitiger Änderung auf der Gegenseite bleibt ein Konflikt. Dateien mit IC35-ID ohne gespeicherte Zuordnung werden nicht automatisch gelöscht oder neu auf dem Gerät angelegt. Bei absichtlich bereits gelöschten Notizen können solche Restdateien nach Prüfung in einen Sicherungsordner außerhalb des Sync-Ordners verschoben werden.

Der IC35 erlaubt beim Notizbetreff 60 und beim Text 255 Byte in Windows-1252; Zeilenumbrüche benötigen auf dem Gerät CRLF. Zu lange oder nicht darstellbare Texte werden nicht gekürzt, sondern übersprungen. Die Textdateien im Notizordner sind unverschlüsselt.

## Schutz und bekannte Grenzen

- Gespeicherter Vergleichsstand, Konfliktprüfungen, Rücklesen und Wiederaufnahmejournale schützen den Abgleich. Sie ersetzen keine Datensicherung.
- Bei Aufgabenlöschungen werden ausschließlich gültige DTSTAMP- und LAST-MODIFIED-Wertänderungen gesondert behandelt. Andere Eigenschaften bleiben geschützt.
- Serien, Serienausnahmen, ganztägige Termine und Besprechungseinladungen werden nicht allgemein bidirektional synchronisiert. Geschützte oder nicht unterstützte Einträge können übersprungen werden.
- Ein erfolgreicher Gesamtlauf kann trotzdem Notizkonflikte oder übersprungene Einträge enthalten. Die Zusammenfassung und das Protokoll sind maßgeblich.
- Die Ursache verlorener Notizzuordnungen und sämtliche möglichen Windows-Startprobleme sind nicht allgemein behoben.

Bei Problemen zuerst Fehlermeldung, Dateipfad und Sicherheitsprotokolle prüfen. Virenschutz nicht pauschal deaktivieren. State- und Kopplungsdateien nicht auf Verdacht löschen. Ausführliche Protokolle können persönliche Daten enthalten; nur erforderliche, möglichst anonymisierte Ausschnitte teilen.

## Entwickler und Nachweise

Der reguläre Windows-Build ist scripts/build_final_release.py ohne Argumente. --publish ist ausschließlich für eine ausdrücklich genehmigte Veröffentlichung vorgesehen und kann main, Tag und öffentliches Release verändern. Auf GitHub lösen normale Dokumentationscommits nur einen Build aus, keine Veröffentlichung.

Der unveränderliche Stand von v3.4.0 und dessen Downloads kann älter sein als diese Dokumentation auf main. Dokumentationsänderungen ersetzen veröffentlichte Dateien nicht automatisch.

[Änderungen](RELEASE-NOTES.md) · [Versionshistorie](CHANGELOG.md) · [Prüfumfang](VALIDATION.md) · [Datenschutz](PRIVACY.md) · [Drittanbieterhinweise](THIRD_PARTY_NOTICES.md) · [Lizenz](LICENSE)
