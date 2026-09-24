# Deinen bestehenden Kalender „twitch“ verbinden

## Einmal einrichten

1. Die bisherige IC35-App schließen und **IC35-Thunderbird-3.4.0a4-Setup.exe** installieren. Bei einem Update von a2 kann das bereits gekoppelte Add-on bleiben.
2. Thunderbird öffnen. Den vorhandenen Kalender **twitch unverändert lassen** – weder Adresse ändern noch Einträge verschieben.
3. In Thunderbird **Add-ons und Themes** öffnen. Beim Zahnrad **Add-on aus Datei installieren** wählen und **IC35-Thunderbird-Bridge-3.4.0a9.xpi** auswählen. Auch bei bereits installiertem älteren Add-on erforderlich. Danach Thunderbird neu starten. Die Datei gibt es separat zum Download und nach Installation unter `%LOCALAPPDATA%\Programs\IC35ThunderbirdAlpha`.
4. **IC35 Sync Beta** starten. **Thunderbird-Add-on koppeln** drücken; dadurch wird ein Code kopiert.
5. In Thunderbird die Einstellungen des neuen **IC35 Thunderbird Bridge**-Add-ons öffnen, den Code einfügen und **Verbinden** drücken. Kurz warten, bis „verbunden“ angezeigt wird.
6. In der Sync-App **Kalender aus Thunderbird laden** drücken.
7. Bei **Termine aus** den Eintrag **twitch · Thunderbird […]** auswählen. Die Auswahl wird beim Start eines Abgleichs gespeichert.
8. Bei **Aufgaben aus** vorerst **Lokale IC35-Sammlung** belassen oder einen anderen in Thunderbird angezeigten, aufgabenfähigen Kalender wählen. Google Tasks ist nicht Bestandteil des Google-CalDAV-Kalenders.

Kontakte werden weiterhin über das lokale IC35-CardDAV-Adressbuch abgeglichen. Dessen Einrichtung und die optionale lokale Aufgaben-Sammlung stehen unter **Thunderbird einrichten** bzw. in der README.

## Erster Test

1. Zuerst über **Nur Vollbackup** ein Gerätebackup erstellen.
2. Einen einfachen Testtermin ohne Wiederholung in „twitch“ anlegen und in Thunderbird synchronisieren. Den normalen Google-/Handy-Abgleich kurz abwarten.
3. In der IC35-App **Alles mit Thunderbird synchronisieren** drücken und nach Aufforderung die Dock-Taste drücken.
4. Auf dem IC35 prüfen, ob der Testtermin vorhanden ist. Anschließend dort den Titel ändern und erneut synchronisieren.
5. Prüfen, ob die Änderung in Thunderbird und danach auf dem Handy erscheint.

**Der Abgleich verarbeitet den ganzen gewählten Kalender, nicht ausschließlich den Testtermin.** Vorhandene unterstützte Einzeltermine werden beim ersten Lauf ebenfalls übertragen. Das gilt auch für bereits vorhandene IC35-Termine in Richtung „twitch“. Einträge ohne eindeutige Dublettenzuordnung werden nicht automatisch zusammengeführt. Bei verschiedenen Inhalten kann daher eine zusätzliche Kopie entstehen.

Serien, ganztägige Termine, Einladungen und andere nicht unterstützte Einträge werden mit Begründung übersprungen. Die Auswahl „twitch“ löst diese Einschränkung nicht auf.

## Im Alltag

Thunderbird und die Sync-App geöffnet lassen. Thunderbird muss den Netzwerkkalender online erreichen können. Während des IC35-Abgleichs keine Einträge am Handy oder in Thunderbird bearbeiten. Die App lässt den gewählten Kalender vorab aktualisieren; bei Offline-Änderungen oder Fehlern stoppt sie. Thunderbird erledigt weiterhin den Austausch mit Google. Die Sync-App bekommt dafür keine Google-Passwörter oder OAuth-Dateien.

Die neue Verbindung wurde mit Thunderbird 153.0.1 und künstlichen lokalen/CalDAV-Testkalendern geprüft. Der vollständige Ablauf mit deinem Google-Kalender und dem echten IC35 steht noch aus.
