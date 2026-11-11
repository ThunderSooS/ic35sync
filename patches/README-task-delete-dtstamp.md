# Experimental task deletion candidate

Status: staged patch only; dav_sync.py is NOT modified by this commit. No release or EXE is built.
The user's actual differing Thunderbird properties have NOT been identified.
Do not use this candidate to delete real tasks until the cause is confirmed.

The patch tolerates only a valid root-VTODO DTSTAMP value change for tasks.
Semantic fields must remain equal. LAST-MODIFIED, UID, status, due date,
LOCATION, unknown properties and all other text stay protected.

Run isolated baseline tests (expects the existing DTSTAMP conflict):

```powershell
python -m unittest discover -s tests -p test_task_delete_dtstamp_candidate.py -v
```

Run the candidate in memory, without modifying source or accessing hardware:

```powershell
$env:IC35_TEST_DTSTAMP_CANDIDATE = '1'
python -m unittest discover -s tests -p test_task_delete_dtstamp_candidate.py -v
Remove-Item Env:IC35_TEST_DTSTAMP_CANDIDATE
```

To apply the staged diff in a disposable checkout, first run:

```powershell
git apply --check patches/task-delete-dtstamp.patch
git apply patches/task-delete-dtstamp.patch
```

Then run the complete project suite in its configured Windows development environment.
The full suite, real Thunderbird, Windows DPAPI, the installed b4 EXE and IC35 hardware
have not been validated with this candidate. A source patch does not update an installed EXE.
No personal task titles, profiles, local paths or device dumps are included.
