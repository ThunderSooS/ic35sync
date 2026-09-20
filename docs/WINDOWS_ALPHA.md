# Windows-Alpha 3.3.0a8

Die Setup-EXE installiert Siemens IC35 Sync für das aktuelle Windows-Konto.
Python, Google-Bibliotheken, Radicale und Sounds sind in der Programm-EXE
enthalten. Eine separate Python-Installation oder install.bat ist nicht nötig.
Voraussetzung: Windows 10/11 x64 und ein funktionierender Treiber für die
serielle Verbindung zum IC35-Dock. Der Installer installiert keine Gerätetreiber.

## Installation und Daten

1. IC35-Sync-3.3.0a8-Alpha-Setup.exe starten.
2. Installationsordner bestätigen; Desktop-Verknüpfung ist optional.
3. Siemens IC35 Sync Alpha aus dem Startmenü öffnen.

Standardordner: %LOCALAPPDATA%\Programs\IC35SyncAlpha.
Datenordner bleibt %APPDATA%\IC35SyncPreview. Vorhandene Einstellungen,
Zuordnungen, verschlüsselte Tokens und Backups werden weiterverwendet.
Die Deinstallation entfernt das Programm, nicht diesen persönlichen Datenordner.
Die alte Python-Version vor dem Start schließen; beide Varianten verwenden
denselben State und denselben lokalen CardDAV-Port.

Die EXE entpackt beim Start mitgelieferte Bibliotheken temporär. Das ist
kein Download und erfordert keine Python-Installation. Der erste Start kann
einige Sekunden dauern.

## Status vor Veröffentlichung

Geprüft am 20.09.2026: 43 automatisierte Tests bestanden; vollständige
App-Oberfläche mit isoliertem Datenordner aufgebaut; gebündeltes Tk, Google-
API-Definitionen, OAuth-Client und Sounddateien geprüft; CardDAV-Unterprozess
aus der EXE auf einem separaten Loopback-Port mit HTTP 200 erreichbar.
Installer-Grundlage 3.3.0a7: Installation im separaten Testordner, identische
installierte EXE und anschließende Deinstallation erfolgreich geprüft.
3.3.0a8 ergänzt die neue Startansage und sichtbare Dock-Bestätigung.

- Alpha: kein getesteter Geräte-Restore, bestehende Datenschutzgrenzen gelten.
- Google-Datenzugriffsprüfung noch offen; Google kann den bekannten
  Hinweis zur nicht überprüften App anzeigen.
- EXE und Setup sind nicht mit einem Herausgeberzertifikat signiert.
  Windows kann daher einen Hinweis zum unbekannten Herausgeber anzeigen.
- Ein echter IC35-Sync und Google-Browserlogin mit dieser gebündelten EXE
  müssen noch vom Nutzer geprüft werden. Tests der Python-Vorversion ersetzen
  diesen Installer-Test nicht.
- Die persönliche TTS-Ansage ist enthalten. Vor öffentlicher Veröffentlichung
  die Weitergaberechte an dieser extern erzeugten Aufnahme klären oder sie
  durch einen eigenen neutralen Ton ersetzen.

## Nachvollziehbarer Build

Python 3.12 x64 mit Tcl/Tk verwenden. Build-Abhängigkeiten sind in
build-requirements.txt festgehalten. In einer eigenen virtuellen Umgebung:

```text
python -m pip install -r build-requirements.txt
python scripts/build_windows.py PFAD_ZUM_DESKTOP_OAUTH_CLIENT
python scripts/smoke_windows.py
ISCC.exe installer.iss
```

Inno Setup 6.7.3 wurde zum Erstellen des Installers verwendet.
Build und Starttests müssen in einer Windows-Umgebung mit funktionierendem
Tcl/Tk laufen. Der Pakettest verwendet nur künstlichen Speicher und einen
vorübergehenden Loopback-Port; kein Sync mit Google oder dem IC35.
Build-Ausgabe: dist/IC35Sync.exe sowie die Setup-EXE.
Der Desktop-OAuth-Client wird ausdrücklich beim Build angegeben. Nutzer-Tokens,
persönliche Einstellungen und Backups werden nicht eingesammelt.
Mitgelieferte Drittanbieter-Lizenztexte stehen nach Installation unter licenses.

Quellen: https://pyinstaller.org/en/stable/usage.html und
https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm
