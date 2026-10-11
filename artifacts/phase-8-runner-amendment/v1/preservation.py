"""Read-only historical fingerprint verification; output only in the amendment."""

from pathlib import Path

from controls import hash_file, read, utc, write_new

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V2 = ROOT / "artifacts/phase-8-review-freeze/v2"
ORIGINAL = Path(
    "C:/fyp-p85/stopped-attempt1/slot1/x/slot/executions/"
    "01a11705-11f0-79f1-9293-78f7f8207f70/export.json"
)
ORIGINAL_HASH = "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b"


def expected_files() -> dict[str, str]:
    files = {str(ROOT / n): h for n, h in read(V2 / "preserved-before.json").items()}
    files.update({str(ROOT / n): h for n, h in read(V2 / "review-inventory.json")["files"].items()})
    files.update(
        {
            str(V2 / n): h
            for n, h in read(V2 / "final-verification.json")["verification_artifact_hashes"].items()
        }
    )
    freeze = ROOT / "artifacts/phase-8-freeze/v1"
    files.update({str(freeze / n): h for n, h in read(freeze / "checksums.json")["files"].items()})
    operations = ROOT / "artifacts/phase-8-launch/v1/operational-checksums.json"
    ops = read(operations)
    files.update({str(ROOT / n): h for n, h in ops["project_files"].items()})
    # Local retained recovery copies use absolute Windows paths.
    files.update(
        {str(Path(ops["recovery_root"]) / n): h for n, h in ops["recovered_files"].items()}
    )
    for p in (
        V2 / "review-inventory.json",
        V2 / "final-verification.json",
        V2 / "campaign-source.tar.gz",
        freeze / "checksums.json",
        operations,
    ):
        files[str(p)] = hash_file(p)
    files[str(ORIGINAL)] = ORIGINAL_HASH
    return files


def verify(stage: str) -> None:
    baseline = HERE / "preservation-baseline.json"
    if stage == "before":
        files = expected_files()
        write_new(HERE / "preservation-expected.json", files)
        drift = []
        for name, expected in list(files.items()):
            actual = hash_file(Path(name))
            if actual == expected:
                continue
            if name != str(ROOT / "artifacts/phase-8.5-report.md"):
                raise ValueError("HISTORICAL_HASH_DRIFT: " + name)
            data = Path(name).read_bytes()
            end = data.index(b"\n")
            recovered = b"# Phase 8.5 deployment and guarded launch report" + data[end:]
            import hashlib

            if hashlib.sha256(recovered).hexdigest() != expected:
                raise ValueError("PREEXISTING_REPORT_NOT_RECOVERABLE")
            for label, raw in (("as-found", data), ("sealed-recovered", recovered)):
                with (HERE / f"historical-report-{label}.md").open("xb") as out:
                    out.write(raw)
            drift.append(
                {
                    "path": name,
                    "sealed_sha256": expected,
                    "as_found_sha256": actual,
                    "only_difference": "Inspection request inserted into title",
                    "original_recovered_byte_identical": True,
                    "original_file_changed_by_amendment": False,
                }
            )
            files[name] = actual
        write_new(HERE / "preexisting-drift.json", drift)
        write_new(baseline, files)
    else:
        files = read(baseline)
    for name, expected in files.items():
        if hash_file(Path(name)) != expected:
            raise ValueError("HISTORICAL_HASH_DRIFT: " + name)
    write_new(
        HERE / f"preservation-{stage}.json",
        {
            "status": "PASS",
            "at_utc": utc().isoformat(),
            "files": len(files),
            "baseline_sha256": hash_file(baseline),
            "first_original_sha256": ORIGINAL_HASH,
            "raw_status": read(ORIGINAL)["status"],
            "stage": stage,
            "cloud_operations": 0,
            "main_driver_replays": 0,
            "preexisting_discrepancy": read(HERE / "preexisting-drift.json"),
        },
    )


if __name__ == "__main__":
    import sys

    verify(sys.argv[1])
