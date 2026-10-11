"""Remove only the expressly authorized stopped previous host and root disk."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0,str(REPO / "artifacts/phase-8-runner-amendment/v3"))
from controls import hash_file, read, write_new
from storage import verify_local
from handover import verify_members
from ops import aws

RUN = "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
OLD = "i-034252c3e9b083abf"
DISK = "vol-0f667d76019af7a47"


def main() -> None:
    imported = read(HERE / "prepare-import-status1-result.json")["result"]
    if imported["Status"] != "Success":
        raise ValueError("NO_VERIFIED_HANDOVER_NO_CLEANUP")
    proof = json.loads(next(x for x in imported["StandardOutputContent"].splitlines() if x.startswith("{")))
    if proof["status"] != "PASS" or proof["backed_up"] != 2 or proof["planned"] != 1498:
        raise ValueError("CLOSED_TWO_ORIGINAL_HANDOVER_REQUIRED")
    native = read(HERE / "actual-deployment-binding.json")["instance_id"]
    if native == OLD:
        raise ValueError("NEW_HOST_MUST_BE_DISTINCT")
    evidence = read(HERE.parent / "v1/poststop-local-evidence.json")["objects"]
    first = read(REPO / "artifacts/phase-8-runner-amendment/v3/handover-qualification.json")["proof"]["originals"][0]["pinned_cloud"]
    local = [(first,Path("C:/fyp-p85/stopped-attempt1/slot1/x/slot"),Path("C:/fyp-p85/stopped-attempt1/slot1/t/e.tar.gz"))]
    local += [(o["proof"],Path(o["extracted"]),Path("C:/p8c1")/o["label"]/"t/e.tar.gz") for o in evidence]
    for n,(p,folder,archive) in enumerate(local):
        verify_local(archive,p["sha256"]); verify_members(folder)
        head = aws("cleanup-original-head-"+str(n),["s3api","head-object","--bucket",p["bucket"],"--key",p["key"],"--version-id",p["version_id"],"--checksum-mode","ENABLED"])
        if head["ContentLength"] != p["bytes"] or base64.b64decode(head["ChecksumSHA256"]).hex() != p["sha256"]:
            raise ValueError("INDEPENDENT_COPY_DRIFT")
    p=proof["prelaunch_backup"]
    aws("cleanup-new-prelaunch-head",["s3api","head-object","--bucket",p["bucket"],"--key",p["key"],"--version-id",p["version_id"],"--checksum-mode","ENABLED"])
    node=aws("cleanup-stopped-ownership",["ec2","describe-instances","--instance-ids",OLD])["Reservations"][0]["Instances"][0]
    disk=aws("cleanup-root-ownership",["ec2","describe-volumes","--volume-ids",DISK])["Volumes"][0]
    if (node["State"]["Name"] != "stopped" or dict((x["Key"],x["Value"]) for x in node["Tags"]).get("research.owner") != RUN
        or dict((x["Key"],x["Value"]) for x in disk["Tags"]).get("research.owner") != RUN
        or disk["Attachments"][0]["InstanceId"] != OLD or disk["Attachments"][0]["Device"] != "/dev/sda1"
        or node["BlockDeviceMappings"][0]["Ebs"]["VolumeId"] != DISK):
        raise ValueError("EXACT_OLD_HOST_ROOT_OWNERSHIP_FAILED")
    write_new(HERE / "cleanup-evidence-gate.json",{"status":"PASS","old_host":OLD,"old_root":DISK,"new_host_untouched":native,
        "local_and_pinned_s3_copies":len(local),"new_host_import_readback":"PASS","versioned_prelaunch_backup":p,
        "authority":"Explicit human item 7 for previous temporary stopped host/root only","no_s3_or_local_evidence_deleted":True})
    aws("old-host-termination",["ec2","terminate-instances","--instance-ids",OLD])
    aws("old-host-terminated-wait",["ec2","wait","instance-terminated","--instance-ids",OLD],120)
    aws("old-root-available-wait",["ec2","wait","volume-available","--volume-ids",DISK],120)
    aws("old-root-deletion",["ec2","delete-volume","--volume-id",DISK])
    write_new(HERE / "old-cleanup-complete.json",{"status":"PASS","old_host":OLD,"old_root":DISK,"new_host_untouched":native,
        "evidence_preserved":True,"new_root_deletion_authorized":False})
    print(json.dumps(read(HERE / "old-cleanup-complete.json")))


if __name__ == "__main__":
    main()
