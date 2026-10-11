"""Use the existing preservation/shutdown authority; never clear a pause."""
import base64
import json
from datetime import UTC, datetime, timedelta
from ops import HERE, aws
from controls import read, write_new

reply = read(HERE / "preserve-stop-145-status2-result.json")["result"]
assert reply["Status"] == "Success" and reply["ResponseCode"] == 0
retained = json.loads(reply["StandardOutputContent"].splitlines()[-1])
summary = retained["summary"]
assert summary["counts"] == {"BACKED_UP": 145, "PLANNED": 1355}
assert summary["pause"]["reason"] == "DRIVER_FAILURE"
assert summary["full_readback"] == "PASS" and summary["all_145_pinned_backups_verified"]
assert summary["next"]["sequence"] == 146 and summary["next"]["state"] == "PLANNED"
write_new(HERE / "preservation-proof.json", retained)
for label, proof in (("master", summary["master_backup"]), ("inspection", retained["inspection"])):
    head = aws(label + "-independent-version-head", ["s3api", "head-object", "--bucket", proof["bucket"], "--key", proof["key"], "--version-id", proof["version_id"], "--checksum-mode", "ENABLED"])
    assert head["VersionId"] == proof["version_id"]
    assert head["ContentLength"] == proof["bytes"] and head["Metadata"]["sha256"] == proof["sha256"]
    assert base64.b64decode(head["ChecksumSHA256"]).hex() == proof["sha256"]
host = aws("ownership-before-stop", ["ec2", "describe-instances", "--instance-ids", "i-057344e5372faf62f"])["Reservations"][0]["Instances"][0]
assert host["State"]["Name"] == "running"
assert any(m["Ebs"]["VolumeId"] == "vol-09dbb42bbf607f5de" and not m["Ebs"]["DeleteOnTermination"] for m in host["BlockDeviceMappings"])
stopping_at = datetime.now(UTC)
aws("idle-host-stop", ["ec2", "stop-instances", "--instance-ids", host["InstanceId"]])
aws("wait-host-stopped", ["ec2", "wait", "instance-stopped", "--instance-ids", host["InstanceId"]], 120)
host = aws("verified-stopped-host", ["ec2", "describe-instances", "--instance-ids", host["InstanceId"]])["Reservations"][0]["Instances"][0]
volume = aws("verified-retained-root", ["ec2", "describe-volumes", "--volume-ids", "vol-09dbb42bbf607f5de"])["Volumes"][0]
assert host["State"]["Name"] == "stopped"
assert volume["Attachments"][0]["InstanceId"] == host["InstanceId"] and not volume["Attachments"][0]["DeleteOnTermination"]
value = {"status": "PAUSED_PRESERVED_HOST_STOPPED", "at_utc": datetime.now(UTC).isoformat(), "host_id": host["InstanceId"], "host_state": "stopped", "root": volume["VolumeId"], "root_deleted": False, "counts": summary["counts"], "pause": summary["pause"], "next": summary["next"], "master_backup": summary["master_backup"], "inspection_backup": retained["inspection"], "independent_master_readback": "PASS_ON_HOST_FROM_PINNED_S3_VERSION", "local_independent_S3_version_heads": "PASS", "full_local_archive_download": "NOT_PERFORMED; pinned external copy and retained root verified", "campaign_restarted": False, "pause_cleared": False, "source_modified": False, "originals_replayed": False, "original_deadline": "2026-10-22T15:24:23.810674Z", "retained_root_decision_deadline": (stopping_at + timedelta(hours=48)).isoformat(), "root_cause": "DRIVER_FAILURE durable reason; underlying driver exception not yet diagnosed"}
write_new(HERE / "final-status.json", value)
report = f"""# Phase 8 status and authorized idle-host preservation — 11 October 2026

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

Master: {summary['master_backup']['sha256']}
Version: {summary['master_backup']['version_id']}
Inspection: {retained['inspection']['sha256']}
Version: {retained['inspection']['version_id']}

Host {host['InstanceId']} verified STOPPED at {value['at_utc']}.
Encrypted owned root {volume['VolumeId']} retained; nothing deleted.
Next unchanged: sequence 146, P2, attempt 1,
{summary['next']['execution_id']}. No restart, pause clearing, admission, replay,
replacement, regrading, frozen-source change or deadline reset.

Existing US$60 admission guard / US$65 ceiling, 80-GiB caps and absolute deadline
22 October 2026 15:24:23.810674 UTC unchanged. This task does not establish new
continuation feasibility. Stored EBS/S3 still cost money while compute is stopped.
The existing 48-hour stopped-root reserve requires a retention/continuation
decision by {value['retained_root_decision_deadline']}; no deletion authorized.
Diagnosis and a reviewed qualified continuation decision remain outstanding.
"""
with (HERE / "REPORT.md").open("x", encoding="utf-8", newline="\n") as target:
    target.write(report)
print(json.dumps(value, indent=2))
