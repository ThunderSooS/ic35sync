# Sicherheit

Ab 3.3.0a4 schützt Windows DPAPI Google-Tokens sowie neue Sicherungen,
Exporte und Sync-Protokolle für das aktuelle Windows-Konto. Vorhandene Archive
werden nicht pauschal verschlüsselt. Grenzen und Exportmöglichkeiten stehen in
[Lokaler Datenschutz](docs/LOCAL_DATA_PROTECTION.md).

Bitte keine Zugangsdaten, persönlichen Daten oder vollständigen Gerätebackups
in öffentlichen Issues veröffentlichen. Verwende nach Einrichtung des GitHub-
Repositories dessen privaten Meldeweg (Private vulnerability reporting), sofern
der Herausgeber ihn aktiviert hat. Ein privater Kontakt ist noch nicht eingerichtet.

Die Vorabversion verwendet lokalen unverschlüsselten State und einen
passwortlosen Loopback-CardDAV-Dienst. Sie ist nicht für einen gemeinsam
genutzten, nicht vertrauenswürdigen PC oder eine Freigabe ins LAN ausgelegt.
