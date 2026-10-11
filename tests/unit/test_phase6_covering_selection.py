"""Phase 6 coverage selection is deterministic and does not inflate independence."""

from packages.domain.revision_policy import revision_transition
from research.scenario_dsl.covering import candidates, coverage_manifest, covering_array, pairs


def test_constrained_covering_array_covers_every_declared_feasible_pair() -> None:
    selected = covering_array()
    assert selected == covering_array()
    assert len(selected) < len(candidates())
    assert set().union(*(pairs(row) for row in selected)) == set().union(
        *(pairs(row) for row in candidates())
    )
    assert coverage_manifest()["uncovered_pairs"] == []


def test_revision_reuse_compares_instants_and_retains_iana_zone() -> None:
    desired = {
        "requested_start": "2026-11-05T15:00:00+05:00",
        "requested_end": "2026-11-05T16:00:00+05:00",
        "timezone": "Asia/Karachi",
    }
    observed = {
        "starts_at": "2026-11-05T10:00:00+00:00",
        "ends_at": "2026-11-05T11:00:00+00:00",
        "timezone": "Asia/Karachi",
    }
    assert revision_transition("ADDITIVE_COMPATIBLE", desired, observed, True) == "REUSE"
    assert revision_transition("RETRACTION", desired, observed, False) == "CANCEL"
    assert revision_transition("REPLACEMENT", desired, observed, False) == "COMPENSATE"
    assert (
        revision_transition("ADDITIVE_COMPATIBLE", desired, {**observed, "timezone": "UTC"}, True)
        == "RESCHEDULE"
    )
