"""Pure named fault placement, separate from wall-clock timing."""

from dataclasses import dataclass

from research.scenario_dsl.models import Barrier, FaultFamily, ScenarioCase, stable_hash


@dataclass(frozen=True)
class Placement:
    barrier: Barrier
    fault: FaultFamily
    request_index: int
    target: str

    @property
    def hash(self) -> str:
        return stable_hash(
            {
                "barrier": self.barrier.value,
                "fault": self.fault.value,
                "request_index": self.request_index,
                "target": self.target,
            }
        )


def schedule(case: ScenarioCase) -> Placement:
    if case.fault_family is FaultFamily.PROVIDER_CONFLICT:
        return Placement(case.correction_barrier, case.fault_family, 2, "BEFORE_COMMIT:2")
    targets = {
        Barrier.P2: "BEFORE_COMMIT:1",
        Barrier.P3: "AFTER_COMMIT_BEFORE_RESPONSE:1",
        Barrier.P4: "AFTER_RESPONSE:1",
    }
    target = targets.get(case.correction_barrier, f"{case.correction_barrier.value}:1")
    return Placement(case.correction_barrier, case.fault_family, 1, target)
