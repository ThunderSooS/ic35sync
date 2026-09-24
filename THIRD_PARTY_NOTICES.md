# Herkunft und Lizenzhinweise

Dieses Projekt wird unter GNU GPL Version 2 veröffentlicht; siehe [LICENSE](LICENSE).
Die Python-Fassung ist eine Weiterentwicklung des persönlichen IC35-Sync-Clients.

## IC35Link 1.18

Die Protokollimplementierung wurde anhand von IC35Link 1.18 und dessen
Protokolldokumentation aufgebaut. Der ältere Python-Code beschreibt unter anderem
die Schreibsequenzen ausdrücklich als Nachbildung von IC35Link. Deshalb wird
die Veröffentlichung vorsorglich GPL-kompatibel behandelt; es wird keine
unabhängige Neuentwicklung sämtlicher Protokollteile behauptet.

Originalhinweis aus `src/syntrans.c`: **Copyright (C) 2000 Thomas Schulz**.
IC35Link enthält die GNU General Public License Version 2 in `COPYING`.
Maßgebliche Referenzen: `src/syntrans.c`, `doc/ic35sync.txt`, `doc/ic35mgr.txt`.

- Projekt: https://ic35link.sourceforge.net/
- Quellarchiv: https://ic35link.sourceforge.net/download/ic35link-1.18.tar.gz
- Betroffene Python-Module: `ic35_protocol.py`, `manager_protocol.py`,
  `todo_protocol.py`.

Änderungen gegenüber den historischen Werkzeugen: Python/Windows-Transport,
GUI, lokaler CardDAV-/CalDAV-Abgleich, strenge Rückleseprüfung und Journale.
Die historischen C-Quellen werden nicht in dieses Repository kopiert.

## Python-Abhängigkeiten

Die EXE bündelt Python und die Abhängigkeiten aus `requirements.txt`.
`build-requirements.txt` hält die verwendeten Versionen fest. Der Installer liefert
die Lizenzhinweise im Ordner `licenses` mit; `build-licenses` enthält diese auch
im Quellpaket. Der PyInstaller-Bootloader steht unter GPL mit der ausdrücklich
vorgesehenen Ausnahme für gebündelte Anwendungen. Die jeweiligen Paketlizenzen
gelten zusätzlich zur Projektlizenz. Radicale wird mit seinen GPL-Lizenzhinweisen ausgeliefert.

Der Radicale-Kompatibilitätsstarter verwendet Radicale als installiertes Paket
und behandelt unter Windows den Fehlercode 1314 beim Symlink-Test.

## Sounds und Namen

Die WAV-Dateien sind für dieses Projekt synthetisch erzeugte Signaltöne
und werden unter der Projektlizenz bereitgestellt. Die beiden MP3-Sprachansagen
wurden vom Herausgeber aus ttsMP3.com bereitgestellt und aus der vorherigen
Ausgabe übernommen; eine darüber hinausgehende Rechteprüfung wurde nicht vorgenommen.
Es werden keine Siemens- oder Thunderbird-Logos mitgeliefert. Die Produktnamen
beschreiben die Kompatibilität; das Projekt ist unabhängig.
