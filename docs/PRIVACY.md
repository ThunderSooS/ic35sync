# Datenschutzerklärung für Siemens IC35 Sync

Stand: 14. September 2026 · Softwarestand: 3.3.0a3

## Ansprechpartner und Geltungsbereich

Herausgeber und Ansprechpartner für Datenschutzfragen:
**Christian Thomas**

E-Mail: **c.thomas.nrw@gmail.com**

Diese Erklärung beschreibt die Windows-Anwendung Siemens IC35 Sync und ihre
Projektwebsite unter https://ic35.thundersoos.cc/. Die Anwendung synchronisiert
einen Siemens IC35 mit vom Nutzer ausgewählten Zielen. Sie besitzt keinen
eigenen Server, auf dem der Herausgeber die synchronisierten Inhalte sammelt.
Das bedeutet nicht, dass die Anwendung keine personenbezogenen Daten verarbeitet:
Sie verarbeitet diese auf dem PC, dem IC35 und über die ausgewählten Dienste.

## Daten und Verwendungszwecke der Anwendung

Je nach aktivierten Funktionen verarbeitet die Anwendung:

- **Kontakte:** auf dem IC35 und im lokalen CardDAV-Adressbuch vorhandene
  Kontaktfelder, beispielsweise Namen, Telefonnummern, Anschriften und E-Mail-Adressen.
- **Kalender:** die Liste verfügbarer Google-Kalender einschließlich ihrer
  Kennungen und Zugriffsrollen sowie Termine des ausgewählten Kalenders und
  IC35-Termine. Dazu gehören insbesondere Titel, Beschreibung, Ort, Beginn,
  Ende, Wiederholungsinformationen und technische Kennungen/Änderungsstände.
- **Aufgaben:** verfügbare Google-Aufgabenlisten und ihre Kennungen sowie Aufgaben
  der ausgewählten Liste und die IC35-Liste „Zu Erledigen“, insbesondere Titel,
  Notizen, Fälligkeitsdatum und Erledigt-Status. Für den Geräteabgleich werden
  auch lokale Felder wie Startdatum, Priorität und Kategorie verarbeitet.
- **Memos:** Titel, Text, Kategorie und Dateiinformationen der IC35-Memos und
  des ausgewählten lokalen TXT-/Markdown-Ordners.
- **Betriebsdaten:** Einstellungen, serielle Schnittstelle, Dateipfade,
  Zuordnungen zwischen Datensätzen, Änderungsstände, Fehlerprotokolle und
  Operationsjournale sowie Sicherungskopien.

Google-Antworten können zusätzliche Metadaten enthalten, etwa Angaben zu
Organisatoren oder Teilnehmern bei Terminen sowie Hierarchieinformationen bei
Aufgaben. Soweit vollständige Antworten in Sicherungen oder Berichten abgelegt
werden, können diese Angaben dort ebenfalls enthalten sein, auch wenn sie nicht
auf dem IC35 dargestellt werden.

Die Verarbeitung dient dem vom Nutzer gestarteten bidirektionalen Abgleich,
der Erkennung von Änderungen und Konflikten und der nachvollziehbaren Behandlung
von Fehlern. Der Abgleich kann Inhalte auf beiden Seiten anlegen, ändern und
löschen. Ein Vollbackup kann weitere Inhalte der Gerätedatenbanken enthalten.

## Google-Anmeldung und Berechtigungen

Die Anmeldung erfolgt auf Googles Seiten im Browser. Die Anwendung erhält
OAuth-Zugriffstokens und gegebenenfalls Refresh-Tokens, nicht das Google-Passwort.
Kalender und Tasks verwenden derzeit getrennte Tokens.

| Berechtigung | Zweck |
| --- | --- |
| `calendar.calendarlist.readonly` | Kalender zur Auswahl des Sync-Ziels auflisten. |
| `calendar.events` | Termine im ausgewählten Kalender für den Zweiwegeabgleich lesen, anlegen, ändern und löschen. |
| `tasks` | Aufgabenlisten zur Auswahl auflisten und Aufgaben in der ausgewählten Liste lesen, anlegen, ändern, erledigen und löschen. |

Die von Google gewährten Berechtigungen sind technisch weiter gefasst als ein
einzelnes Ziel. Die Anwendung verwendet die ausgewählten Kalender und Listen
für den Abgleich. Die Kalenderberechtigung ersetzt keine Google-Kontaktefreigabe;
Kontakte werden über den lokalen CardDAV-Dienst verarbeitet.

Die Anwendung nutzt Google-Daten für diese sichtbaren Synchronisationsfunktionen,
nicht für Werbung, Profilbildung, Verkauf oder das Training von KI-Modellen.
Die Nutzung und Weitergabe
von über Google-APIs erhaltenen Daten erfolgt gemäß der
[Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
einschließlich ihrer Limited-Use-Anforderungen.

## Empfänger und Datenübertragung

Google-Anmeldung und API-Anfragen erfolgen direkt zwischen dem PC und Google
über HTTPS. Ausgewählte Kalender- und Aufgabeninhalte werden zwischen Google,
dem PC und dem IC35 übertragen. Für Googles eigene Verarbeitung gilt die
[Google-Datenschutzerklärung](https://policies.google.com/privacy).

Thunderbird greift auf einen lokalen Radicale/CardDAV-Dienst zu. Memos werden
in den ausgewählten Ordner geschrieben. Liegt dieser in einem Cloud-Sync-Ordner,
kann der vom Nutzer eingerichtete Cloud-Client die Dateien an seinen Anbieter
übertragen. Dessen Zugriffs-, Freigabe- und Aufbewahrungseinstellungen gelten
zusätzlich. Andere Personen können Inhalte sehen, wenn der Nutzer entsprechende
Kalender, Ordner oder Konten mit ihnen teilt.

Die Anwendung übermittelt keine Telemetrie oder automatischen Fehlerberichte an
den Herausgeber. Zur Installation werden Softwareabhängigkeiten aus
Python-Paketquellen abgerufen; dabei fallen bei diesen Anbietern technische
Verbindungsdaten an. Die Anwendung überträgt dabei keine Sync-Inhalte.

## Speicherung und Schutz

Der Standarddatenordner dieser Vorabversion lautet
`%APPDATA%\IC35SyncPreview`. Über `IC35_SYNC_DATA_DIR` kann ein anderer Ordner
gewählt werden. Dort liegen Einstellungen, Tokens, lokale CardDAV-Daten,
Sync-Zuordnungen, Exporte, Protokolle, Berichte und Sicherungen. Memos liegen
zusätzlich im gewählten Notizordner. Daten verbleiben außerdem auf dem IC35
und in den ausgewählten Google-Diensten.

Protokolle und Sicherungen können vollständige personenbezogene Inhalte
enthalten; auch hexadezimale Geräteprotokolle sind nicht anonymisiert.
Ein manuelles Geräte-Vollbackup liegt unter `backups`. Kleine Sicherungen von
Sync-Vorgängen und Operationsjournale entstehen auch ohne manuelles Vollbackup.

Die Anwendung verschlüsselt Tokens und lokale Inhalte in Version 3.3.0a3 nicht
zusätzlich. Ihr Schutz hängt von Windows-Zugriffsrechten, dem Benutzerkonto und
gegebenenfalls einer vom Nutzer aktivierten Datenträgerverschlüsselung ab.
Auch für Dateien auf dem IC35 verspricht die Anwendung keine Verschlüsselung.
Der lokale CardDAV-Dienst verwendet HTTP ohne Passwort auf `127.0.0.1:5232`.
Er ist auf den eigenen Rechner beschränkt; lokale Programme können darauf zugreifen.
Der Google-Anmeldeablauf verwendet einen kurzzeitig gestarteten lokalen
Rückrufserver. Die Datenübertragung zu Google selbst erfolgt über HTTPS.

## Aufbewahrung, Widerruf und Löschung

Es gibt derzeit keine allgemeine automatische Löschfrist für lokale Sync-Daten,
Protokolle oder Sicherungen. Sie bleiben bis zur manuellen Entfernung bestehen;
die Deinstallation allein entfernt sie nicht automatisch. Das Löschen eines
Termins oder einer Aufgabe entfernt nicht automatisch ältere Sicherungskopien.
Google und gegebenenfalls andere Cloud-Anbieter verwalten ihre eigenen Kopien
nach ihren jeweiligen Regeln.

Um die Nutzung zu beenden:

1. Die Sync-App schließen und keine weiteren Abgleiche starten.
2. Den Zugriff auf Siemens IC35 Sync in den
   [Google-Kontoverbindungen](https://myaccount.google.com/connections) widerrufen.
   Dadurch wird die Berechtigung beendet, nicht automatisch der Inhalt gelöscht.
3. Falls gewünscht, den verwendeten lokalen App-Datenordner sowie separat
   gespeicherte Exporte, Notizdateien und Sicherungskopien entfernen. In einem
   Cloud-Ordner kann eine Dateilöschung auch dort synchronisiert werden.
4. Inhalte auf dem IC35 und in Google Calendar/Tasks bei Bedarf in diesen
   Systemen separat löschen. Dortige Papierkörbe und Aufbewahrungsregeln beachten.

Nicht einzelne Zuordnungsdateien während der weiteren Nutzung löschen: Ohne
Abgleichhistorie kann ein neuer Lauf verbliebene Inhalte wieder übernehmen oder
doppelt anlegen. Für eine vollständige Beendigung zuerst den Google-Zugriff
widerrufen. Der Herausgeber kann lokale Dateien oder Inhalte im Google-Konto
des Nutzers nicht aus der Ferne löschen.

## Support und öffentliche Fehlerberichte

Bei einer freiwilligen Supportanfrage erhält der Herausgeber die mitgeteilten
Kontaktdaten, Nachricht und beigefügten Dateien und verwendet sie zur Bearbeitung
der Anfrage. Rohprotokolle, Tokens und Backups sollten nicht öffentlich geteilt
werden. Bitte zunächst nur einen bereinigten Fehlertext senden. Für die Einsicht
in konkrete zusätzliche Sync-Inhalte ist eine ausdrückliche Freigabe einzuholen.

Supportanfragen und beigefügte Dateien werden spätestens 30 Tage nach Abschluss
der Anfrage gelöscht, soweit keine gesetzliche Aufbewahrungspflicht entgegensteht.
Bei einer solchen Pflicht wird die weitere Nutzung auf den Aufbewahrungszweck
beschränkt. Diese Frist gilt für die beim Herausgeber verwalteten Supportkopien,
nicht für öffentliche GitHub-Issues und von Dritten angefertigte Kopien.
Über den oben genannten
Kontakt kann die Löschung von beim Herausgeber vorhandenen Supportdaten
angefragt werden. Öffentliche GitHub-Issues sind für andere sichtbar; Kopien
durch Dritte lassen sich nicht vollständig zurückholen. Für GitHub gilt dessen
[Datenschutzerklärung](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

## Besuch der Projektwebsite

Die Website wird über GitHub Pages bereitgestellt. Beim Aufruf werden technische
Verbindungsdaten wie IP-Adresse und HTTP-Anfragedaten an den Hostinganbieter
übermittelt. Die am 14.09.2026 geprüfte Datenschutzerklärungsseite lädt zusätzlich
Anchor.js von `cdnjs.cloudflare.com`; dabei erhält auch dieser Dienst technische
Anfragedaten. Dies ist ein externer Skriptabruf, keine Übertragung der lokalen
Kalender-, Aufgaben- oder Kontaktdaten durch die Sync-App.

Cloudflare verwaltet das DNS der Domain. Der Eintrag `ic35` steht auf
„DNS only“; Cloudflare dient für diese Subdomain nicht als Website-Proxy.
Der oben beschriebene externe cdnjs-Abruf erfolgt trotzdem. Informationen zu diesen Anbietern:
[GitHub](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)
und [Cloudflare](https://www.cloudflare.com/privacypolicy/).
Für deren technische Protokolle wird hier keine vom Herausgeber kontrollierte
Löschfrist zugesichert.

## Datenschutzrechte und Änderungen

Soweit die gesetzlichen Voraussetzungen vorliegen, können betroffene Personen
Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung und
Datenübertragbarkeit verlangen sowie einer Verarbeitung widersprechen und eine
Einwilligung widerrufen. Sie können sich außerdem an die zuständige
Datenschutzaufsichtsbehörde wenden. Anfragen zu Daten beim Herausgeber richten
Sie bitte an den oben angegebenen Kontakt; Daten bei Google oder anderen
Anbietern sind zusätzlich bei diesen zu verwalten.

Soweit der Herausgeber personenbezogene Daten im Anwendungsbereich der DSGVO
verarbeitet, erfolgt die Bereitstellung und Absicherung der Projektwebsite sowie
die Bearbeitung allgemeiner Supportanfragen auf Grundlage berechtigter Interessen
an einem erreichbaren und funktionierenden Open-Source-Projekt (Art. 6 Abs. 1
Buchst. f DSGVO). Eine gesondert erteilte Einwilligung zur Einsicht in bestimmte
Supportdateien ist Grundlage dieser Einsicht (Art. 6 Abs. 1 Buchst. a DSGVO) und
kann für die Zukunft widerrufen werden. Gesetzlich vorgeschriebene Aufbewahrungen
beruhen auf Art. 6 Abs. 1 Buchst. c DSGVO. Die OAuth-Freigabe legt die technischen
Google-Zugriffsrechte fest; sie bestimmt nicht pauschal die Rechtsgrundlage jeder
Verarbeitung durch andere beteiligte Dienste.

Änderungen dieser Erklärung werden mit einem neuen Standdatum auf der
Projektwebsite veröffentlicht. Neue Zwecke oder zusätzliche Zugriffe auf
Google-Daten müssen vor ihrer Nutzung offengelegt werden; erforderliche neue
Einwilligungen werden zuvor eingeholt.
