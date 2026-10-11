"""A deliberately closed campaign entry point during study design review."""

import argparse
from typing import Any


class CampaignBlocked(RuntimeError):
    pass


def require_reviewed_freeze(manifest: dict[str, Any]) -> None:
    if manifest.get("status") != "REVIEWED_FROZEN":
        raise CampaignBlocked(
            "Study is DRAFT: no campaign execution or campaign ingestion permitted"
        )
    if not manifest.get("review_receipt") or not manifest.get("freeze_hash"):
        raise CampaignBlocked("Missing human review receipt or immutable freeze")
    if manifest.get("unresolved_decisions"):
        raise CampaignBlocked(
            "Resolve the sampling, tolerance and driver decisions before freezing"
        )
    # This design change set intentionally has no campaign runner implementation.
    raise CampaignBlocked(
        "Reviewed driver qualification and source-integrity gate not installed yet"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 8 remains unstarted")
    parser.add_argument("--start", action="store_true")
    parser.parse_args()
    require_reviewed_freeze({"status": "DRAFT"})


if __name__ == "__main__":
    main()
