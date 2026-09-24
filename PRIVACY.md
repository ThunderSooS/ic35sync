# Datenverarbeitung / Data handling · Thunderbird 3.4.0a2

Herausgeber / Publisher: Christian Thomas. Kontakt / Contact: c.thomas.nrw@gmail.com.

## Deutsch

Neu in dieser Version: Das optionale Thunderbird-Add-on übermittelt Inhalte des in der Sync-App ausgewählten Kalenders über eine mit einem Kopplungscode geschützte Loopback-Verbindung (Port 5234). Es liest und schreibt diesen Kalender über Thunderbird. Bei einem dort eingerichteten Netzwerkkalender übermittelt Thunderbird die Änderungen an dessen Anbieter – bei „twitch“ also Google – und empfängt Änderungen von dort. Der Nutzer behält die bestehende Kontoanmeldung in Thunderbird; Google-Passwörter und OAuth-Token werden nicht an die Sync-App übertragen. Die unten beschriebenen lokalen Sammlungen bleiben eine alternative Datenquelle und werden für Kontakte weiterhin verwendet.

Der Kopplungscode und die Bindung an das Thunderbird-Profil werden in der Sync-App mit Windows DPAPI gespeichert. Das Add-on speichert den Code und eine zufällige Profilkennung in seinem lokalen Thunderbird-Erweiterungsspeicher. Das Add-on enthält keine Telemetrie und greift nicht auf E-Mails zu. Seine technische Experiment-Berechtigung ist weiter gefasst als diese implementierten Funktionen.

Diese Desktop-Ausgabe verarbeitet Kontakte, Termine und Aufgaben für den vom Nutzer gestarteten Abgleich zwischen dem angeschlossenen Siemens IC35 und lokalen, in Thunderbird eingebundenen Sammlungen. Der mitgelieferte DAV-Dienst ist nur über die Loopback-Adresse dieses PCs erreichbar. Die App verwendet keine Cloud-Anmeldung, sendet keine Organizerdaten an den Herausgeber und enthält keine Telemetrie oder automatische Fehlerübermittlung.

Daten werden mit dem angeschlossenen IC35 und über den lokalen DAV-Dienst mit Thunderbird ausgetauscht. Andere Programme auf demselben PC können grundsätzlich auf diesen passwortlosen lokalen Dienst zugreifen. Die App greift nicht direkt auf andere in Thunderbird eingerichtete Konten zu. Vom Nutzer getrennt konfigurierte Thunderbird-Dienste und das Kopieren von Daten in solche Konten unterliegen deren jeweiligen Einstellungen.

Lokale DAV-Sammlungen werden als gewöhnliche Dateien gespeichert. Thunderbird verwaltet eigene lokale Kopien. Sync-State, Wiederaufnahmejournal, Datensatzsicherungen, Organizerexporte, Geräte-Vollbackups und ausführliche App-Protokolle werden mit Windows DPAPI für das aktuelle Windows-Konto geschützt. Ein technisches Dienst-Startprotokoll und COM-/Zeitzoneneinstellungen sind unverschlüsselt. Über den Exportbutton ausdrücklich erzeugte Kopien sind ebenfalls unverschlüsselt. Es gibt keine automatische Löschfrist; die Deinstallation entfernt den persönlichen Datenordner nicht.

Der Herausgeber erhält Supportdateien nur, wenn Nutzer diese freiwillig zusenden. Sie werden ausschließlich zur Bearbeitung der Anfrage verwendet, nicht verkauft oder zu Werbung/Profilbildung genutzt und bis spätestens 30 Tage nach Abschluss der Anfrage gelöscht. Bei Zusendung per E-Mail verarbeitet der verwendete E-Mail-Anbieter die Nachricht zur Zustellung und Speicherung. Bitte nur erforderliche, möglichst anonymisierte Angaben senden.

Diese Datei beschreibt die Desktop-App. Hosting-Websites und Downloadplattformen verarbeiten Aufrufe nach ihren eigenen Datenschutzhinweisen. Änderungen an einer öffentlich gehosteten Datenschutzerklärung werden durch dieses lokale Paket nicht automatisch veröffentlicht.

## English

New in this version: the optional Thunderbird add-on exchanges the selected calendar's contents with the sync app over a pairing-code-protected loopback connection (port 5234). It reads and writes that calendar through Thunderbird. For an existing network calendar, Thunderbird transfers changes to and from its provider, such as Google for the user's “twitch” calendar. The account login stays in Thunderbird; Google passwords and OAuth tokens are not passed to the sync app. The local collections described below remain an alternative source and are still used for contacts.

The app stores the pairing code and pinned Thunderbird profile using Windows DPAPI. The add-on stores the code and a random profile identifier in Thunderbird's local extension storage. It contains no telemetry and does not access email. Its technical Experiment permission is broader than these implemented functions.

This desktop edition processes contacts, events and tasks to perform user-initiated synchronization between the connected Siemens IC35 and local collections used by Thunderbird. Its DAV service is accessible only through this computer's loopback address. The app has no cloud login, does not send organizer data to the publisher and contains no telemetry or automatic error reporting.

Data is exchanged with the connected IC35 and with Thunderbird through the local DAV service. Other software running on the same PC may access this passwordless local service. The app does not directly access other Thunderbird accounts. Services separately configured by the user in Thunderbird, and copying entries into those accounts, follow those services' own settings.

Local DAV collections and Thunderbird caches are ordinary local files. Sync state, recovery journals, record snapshots, organizer exports, full-device backups and detailed application logs use current-user Windows DPAPI. Technical service-start logs and COM/time-zone settings are unencrypted. Copies explicitly created with the export button are plaintext. There is no automatic retention limit; uninstalling does not remove the personal data directory.

The publisher receives support files only when voluntarily sent by the user. They are used solely to resolve the request, not sold or used for advertising/profiling, and deleted no later than 30 days after the request is closed. When sent by email, the email provider processes the message for delivery and storage. Send only necessary information, preferably anonymized.

This file describes the desktop app. Hosting and download sites process visits under their own privacy notices. This local package does not automatically publish changes to a hosted privacy policy.
