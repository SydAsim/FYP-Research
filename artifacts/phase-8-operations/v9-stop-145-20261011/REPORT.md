# Phase 8 status and authorized idle-host preservation — 11 October 2026

145 BACKED_UP / 1,355 PLANNED / zero active: 9.67% of original execution slots
retained. This is not a claim that all research outcomes passed.

The durable pause is DRIVER_FAILURE at 2026-10-10T18:06:53.908883Z
(10 October 23:06:53 Pakistan time). Campaign service failed; watchdog was
running. The underlying driver exception has not been diagnosed in this status
task. Journals, notices, last original row, pause and clock anchor are preserved.

The watchdog was quiesced only after verifying zero active executions and the
unchanged closed boundary. All 145 backup receipt hashes and pinned S3 versions
passed. Frozen backup code produced a consistent complete master; independent
version-specific download/member/continuation readback passed on the host.
The second inspection archive includes the master and diagnostic records.
Both S3 heads, exact sizes, SHA metadata and native SHA checksums passed locally
before idle-host stop. A full local archive download is not claimed.

Master: b40bc792c0e7c9d94edc513a24bfae1abe8536475947be13a1ee35949b6ced08
Version: 3pLbzfgLl6SW0nbeiXBi3QZiCEvGt4pt
Inspection: d1d39c50f1d8feb5abf9947d091028282c8b44febfac5b4968b407c85f68c84d
Version: rf5sZnSScpbJumI57NXYIbXgpUtncRv8

Host i-057344e5372faf62f verified STOPPED at 2026-10-11T16:05:07.617447+00:00.
Encrypted owned root vol-09dbb42bbf607f5de retained; nothing deleted.
Next unchanged: sequence 146, P2, attempt 1,
01a11705-11f1-772d-8190-c43552871801. No restart, pause clearing, admission, replay,
replacement, regrading, frozen-source change or deadline reset.

Existing US$60 admission guard / US$65 ceiling, 80-GiB caps and absolute deadline
22 October 2026 15:24:23.810674 UTC unchanged. This task does not establish new
continuation feasibility. Stored EBS/S3 still cost money while compute is stopped.
The existing 48-hour stopped-root reserve requires a retention/continuation
decision by 2026-10-13T16:04:13.525847+00:00; no deletion authorized.
Diagnosis and a reviewed qualified continuation decision remain outstanding.
