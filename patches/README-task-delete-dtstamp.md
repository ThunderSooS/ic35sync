# Historischer DTSTAMP-Testpatch

Diese Datei dokumentiert einen überholten Zwischenschritt. patches/task-delete-dtstamp.patch ist nicht der aktuelle Fix und darf nicht auf den veröffentlichten Quellstand angewendet werden.

IC35 Sync 3.4.0 verwendet task_delete_metadata.py direkt aus dav_sync.py. Der aktuelle Vergleich berücksichtigt ausschließlich gültige Wertänderungen von DTSTAMP und LAST-MODIFIED bei Aufgabenlöschungen; andere Eigenschaften bleiben geschützt. Eine Build-Injektion ist nicht mehr erforderlich.

Die aktuellen Tests stehen in tests/test_task_delete_dtstamp_candidate.py; der Dateiname ist historisch. Für einen normalen Windows-Build scripts/build_final_release.py ohne --publish verwenden. Benutzeranleitung und Grenzen stehen in ../README.md, ../RELEASE-NOTES.md und ../VALIDATION.md.

Die alte Patchdatei bleibt nur zur Nachvollziehbarkeit erhalten. Frühere Anleitungen zur In-Memory-Aktivierung und zur manuellen Anwendung gelten nicht für 3.4.0.
