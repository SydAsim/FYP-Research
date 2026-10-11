"""Run scoped regressions against isolated application services and real PG."""

import argparse
import subprocess
import sys
from uuid import uuid4

from research.remedies.preserve import OUTPUT, ROOT
from research.remedies.runtime import (
    API,
    SIM_DATABASE,
    SIMULATOR,
    VOICE,
    WORKER,
    Runtime,
    prepare_databases,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regression", action="store_true")
    args = parser.parse_args()
    prepare_databases()
    identifier = str(uuid4())
    if args.regression:
        with Runtime(OUTPUT / f"validation/regression-services-{identifier}") as runtime:
            env = {
                **runtime.env,
                "SIMULATOR_DATABASE_URL": SIM_DATABASE,
                "PHASE2_API_URL": API,
                "PHASE2_SIMULATOR_URL": SIMULATOR,
                "PHASE2_WORKER_URL": WORKER,
                "PHASE4_VOICE_URL": VOICE,
            }
            # Legacy truth callers run only on an explicitly unprotected regression
            # simulator. Access-denial tests use the isolated protected v2 runtime.
            runtime.stop("simulator")
            runtime.token = ""
            runtime.start("simulator")
            targets = [
                "tests/unit",
                "tests/contract",
                "tests/integration/test_phase1_postgres.py",
                "tests/integration/test_phase2_postgres.py",
                "tests/integration/test_phase2_simulator.py",
                "tests/integration/test_phase3_postgres.py",
                "tests/integration/test_phase4_postgres.py",
                "tests/integration/test_phase5_ui.py",
            ]
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-q",
                    *targets,
                    f"--junitxml={OUTPUT / f'validation/regression-{identifier}.xml'}",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
    else:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                "tests/unit/test_readiness_v2.py",
                "tests/integration/test_readiness_v2_postgres.py",
                f"--junitxml={OUTPUT / f'validation/remedies-{identifier}.xml'}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
    name = "regression" if args.regression else "remedies"
    (OUTPUT / f"validation/{name}-{identifier}.log").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    print(result.stdout)
    print(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
