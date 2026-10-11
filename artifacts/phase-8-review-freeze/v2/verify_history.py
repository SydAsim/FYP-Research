"""Read-only historical byte check, using the baseline captured before v2 editing."""

from controls import hash_file, read, utc, write_new
from runner import HERE, REPO


def verify() -> None:
    expected = read(HERE / "preserved-before.json")
    for name, digest in expected.items():
        if hash_file(REPO / name) != digest:
            raise ValueError("HISTORICAL_HASH_DRIFT: " + name)
    write_new(
        HERE / "preservation-before-assembly.json",
        {
            "status": "UNCHANGED",
            "at": utc().isoformat(),
            "files": len(expected),
            "stage": "BEFORE_FINAL_PACKAGE_ASSEMBLY",
            "baseline": (
                "preserved-before.json copied before v2 edits from verified historical inventories"
            ),
            "baseline_sha256": hash_file(HERE / "preserved-before.json"),
            "chronology_limit": (
                "This stream reread is before final assembly; "
                "it is not represented as an earlier pre-edit reread."
            ),
        },
    )


if __name__ == "__main__":
    verify()
