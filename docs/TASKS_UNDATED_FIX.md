# 3.3.0a3: Aufgaben ohne Datum

Das Gerät DCS15 1.51 setzt bei zwei leeren Datumsfeldern Start=20000101
und Ende=20001231. Beim Kontrolllesen wird ausschließlich dieses genaue
Wertepaar akzeptiert; alle anderen Felder müssen unverändert übereinstimmen.

Für eine verknüpfte Google-Aufgabe ohne Datum bleibt dieses Ersatzdatum lokal.
Änderungen an Titel oder Erledigt-Status übertragen kein Ersatzdatum zu Google.
Ein auf dem IC35 neu gesetztes anderes Datum wird normal synchronisiert.
Unverknüpfte Aufgaben mit diesen Jahreszahlen werden nicht pauschal umgedeutet.

Nach dem beobachteten Abbruch kann das vorhandene Operationsjournal die bereits
angelegte Aufgabe wieder zuordnen, sofern genau ein neuer passender Datensatz
vorliegt und die Google-Aufgabe unverändert ist. Bei Mehrdeutigkeit bleibt der
Abbruch bestehen. State-Dateien und Journale nicht manuell löschen.

Offline geprüft: exakte Normalisierung, Wiederzuordnung, unveränderter Folgelauf,
Statusänderung ohne erfundenes Fälligkeitsdatum und bewusste Datumsänderung.
Am 13.09.2026 am Gerät bestätigt: erfolgreicher Gesamtabgleich mit Wiederzuordnung
der vorhandenen Testaufgabe, Erledigung auf dem IC35 nach Google übertragen und
anschließende Löschung in Google auf dem IC35 umgesetzt.
