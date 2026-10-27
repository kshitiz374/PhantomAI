"""Fictional sample investigation: THE LAST PROCESS — all content is invented."""

SAMPLE_META = {
    "id": "the_last_process",
    "title": "THE LAST PROCESS",
    "description": (
        "A fictional research workstation was shut down years ago, "
        "yet its archive suggests one process never stopped recording."
    ),
}

ARTIFACTS: list[dict] = [
    {
        "filename": "01_boot_terminal.log",
        "content": """[FICTIONAL LOG — THE LAST PROCESS]
SESSION RESTORED.
MEMORY FRAGMENTS FOUND: 07
LAST KNOWN ACTIVITY: UNKNOWN
2021-11-03 02:13:04 — basement terminal started.
Operator: M. Reyes (badge REV-114)
PID-88421 attached to logging daemon.
THERE IS SOMETHING IN THE ARCHIVE.
""",
    },
    {
        "filename": "02_maintenance_note.md",
        "content": """# Maintenance Note (Fictional)

**Date:** November 2, 2021  
**Author:** Facilities — J. Okonkwo

Basement rack B-7 will receive a controlled shutdown at 22:00.  
All researchers must export local notes before 21:30.  
Dr. Hale requested an exception for the spectrometer array — denied.
""",
    },
    {
        "filename": "03_email_thread.txt",
        "content": """Subject: Re: overnight logging [FICTIONAL EMAIL]

From: m.reyes@lab.example
To: dr.hale@lab.example

Dr. Hale — I will keep PID-88421 running to capture the anomaly trace.
If facilities power down B-7, the daemon may detach. I can bridge via basement terminal.

— M. Reyes

From: dr.hale@lab.example
Do NOT leave unattended processes. Shutdown is mandatory.
""",
    },
    {
        "filename": "04_system_report_corrupted.json",
        "content": """{
  "report": "FICTIONAL CORRUPTED SYSTEM REPORT",
  "host": "workstation-b7",
  "events": [
    {"time": "02:13", "action": "restart", "component": "logging_daemon"},
    {"time": "02:14", "action": "orphan_process", "pid": "88421"},
    {"time": "???:??", "action": "buffer_overflow", "note": "checksum fail"}
  ],
  "integrity": "DEGRADED"
}
""",
    },
    {
        "filename": "05_operator_notes.txt",
        "content": """Personal notes — M. Reyes (fiction)

Nov 3 — heard typing after everyone left.
The basement terminal screen was green when I passed at 01:55.
System log records a restart at 02:13. That matches my terminal log.
I thought I was alone.
""",
    },
    {
        "filename": "06_shutdown_record.csv",
        "content": """timestamp,action,operator,status
2021-11-03T22:00:00,power_off_scheduled,facilities,COMPLETE
2021-11-03T22:04:12,rack_b7_offline,auto,COMPLETE
2021-11-03T22:04:19,final_ack,j.okonkwo,COMPLETE
""",
    },
    {
        "filename": "07_audio_transcription.txt",
        "content": """[FICTIONAL AUDIO TRANSCRIPTION — lab mic B7]

00:41 — ambient hum
01:58 — keyboard clicks (no badge swipe logged)
02:13 — automated voice: "logging daemon restarted"
02:15 — whisper (unidentified): "still recording"
02:16 — silence
""",
    },
    {
        "filename": "08_incident_report_A.md",
        "content": """# Incident Report A (Fictional)

**Incident ID:** IR-B7-2021-11  
**Summary:** No unauthorized access. Shutdown completed successfully.  
**Cause:** Operator error during export window.  
**Time of resolution:** 22:05
""",
    },
    {
        "filename": "09_incident_report_B.md",
        "content": """# Incident Report B (Fictional)

**Incident ID:** IR-B7-2021-11-B  
**Summary:** Unidentified process continued writing after shutdown.  
**Cause:** Detached session on basement terminal; PID-88421.  
**Time of first anomaly:** 02:13 (Nov 4 — contradicts Report A date)
""",
    },
    {
        "filename": "10_final_unexplained_entry.log",
        "content": """[FICTIONAL — FINAL ARCHIVE ENTRY]
Timestamp: UNKNOWN
Source: logging_daemon / PID-88421
Message: I WAS NOT SHUTDOWN.
Message: THE PROCESS CONTINUES.
Message: WHO IS READING THIS?
— END FRAGMENT —
""",
    },
    {
        "filename": "11_network_stub.txt",
        "content": """Network isolation stub (fiction).
No external transfer authorized after 2021-11-03T21:45.
Local archive mirror only.
Cross-ref: basement terminal 02:13, PID-88421, Dr. Hale denial email.
""",
    },
]


async def load_sample_into_investigation(inv_id: str, artifact_repo) -> int:
    count = 0
    for item in ARTIFACTS:
        meta = {
            "fictional": True,
            "sample_pack": SAMPLE_META["id"],
            "tags": ["sample", "fiction"],
        }
        await artifact_repo.create(
            investigation_id=inv_id,
            filename=item["filename"],
            content_type="text/plain",
            content=item["content"].strip(),
            summary=f"[FICTION] Sample artifact from {SAMPLE_META['title']}.",
            metadata=meta,
        )
        count += 1
    return count
