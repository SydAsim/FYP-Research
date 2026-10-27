"""Eight new-only offline controls; no research driver or application stack."""

from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from controls import Policy, guard, hash_file, read
from operational_limits import effective_policy, verified_limits
from staging_retention import remove_redundant_staging

HERE = Path(__file__).parent
GIB = 1024**3


class LimitControls(unittest.TestCase):
    def original(self) -> Policy:
        return Policy.model_validate(read(HERE / "original-launch-policy.json"))

    def bundle(self, root: Path) -> tuple[Path, str]:
        folder = root / "0083" / "attempt-cal-only"
        folder.mkdir(parents=True)
        (folder / "trace.json").write_text('{"calibration_only":true}')
        (folder / "manifest.json").write_text(
            json.dumps({"files": {"trace.json": hash_file(folder / "trace.json")}})
        )
        archive = folder.parent / (folder.name + ".tar.gz")
        with tarfile.open(archive, "x:gz") as output:
            output.add(folder, arcname="slot")
        return archive, hash_file(archive)

    def test_01_historical_policy(self) -> None:
        p = self.original()
        self.assertEqual(p.admission_committed_usd, 55)
        self.assertEqual(p.cloud_limit_bytes, 30 * GIB)
        self.assertEqual(p.backup_archive_limit_bytes, 50 * GIB)
        self.assertEqual(p.model_dump(mode="json"), read(HERE / "original-launch-policy.json"))

    def test_02_effective_policy(self) -> None:
        limits = verified_limits()
        p = effective_policy(read(HERE / "original-launch-policy.json"))
        self.assertEqual(
            (p.admission_committed_usd, p.cloud_limit_bytes, p.backup_archive_limit_bytes),
            (60, 60 * GIB, 60 * GIB),
        )
        self.assertEqual(p.budget_usd, 65)
        self.assertEqual(p.stop_at, self.original().stop_at)
        self.assertAlmostEqual(
            p.committed_cost(p.host_started_at) - self.original().committed_cost(p.host_started_at),
            2.0,
        )
        self.assertEqual(
            limits.qualified_v6_package_hash,
            "3807d690ad46abdd07da12710ea933e03e3d86fb4440f5933b186db74de76a34",
        )

    def test_03_thresholds(self) -> None:
        p = effective_policy(read(HERE / "original-launch-policy.json"))
        sample = {
            "available_memory_bytes": 8 * GIB,
            "system_free_bytes": 100 * GIB,
            "output_free_bytes": 100 * GIB,
            "backup_free_bytes": 100 * GIB,
            "working_bytes": 0,
            "backup_bytes": 59 * GIB,
        }
        at = p.host_started_at + timedelta(hours=300)
        guard(p, sample, at, 59 * GIB)
        with self.assertRaisesRegex(ValueError, "CLOUD_30GIB_LIMIT"):
            guard(p, sample, at, 60 * GIB)
        with self.assertRaisesRegex(ValueError, "BACKUP_RESERVATION_STOP"):
            guard(p, {**sample, "backup_bytes": 59 * GIB + 1}, at, 59 * GIB)
        with self.assertRaisesRegex(ValueError, "ESTIMATED_COMMITTED_COST_STOP"):
            guard(p, sample, p.host_started_at + timedelta(hours=354), 0)

    def test_04_verified_redundancy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cal-v7-retention-") as temp:
            base = Path(temp)
            archive, digest = self.bundle(base)
            self.assertTrue(remove_redundant_staging(archive, digest, base, 83))
            self.assertEqual(hash_file(archive), digest)
            self.assertFalse((archive.parent / "attempt-cal-only").exists())
            self.assertFalse(remove_redundant_staging(archive, digest, base, 83))

    def test_05_missing_archive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cal-v7-missing-") as temp:
            base = Path(temp)
            archive, digest = self.bundle(base)
            archive.rename(archive.with_suffix(".retained"))
            with self.assertRaises(FileNotFoundError):
                remove_redundant_staging(archive, digest, base, 83)
            self.assertTrue((archive.parent / "attempt-cal-only" / "trace.json").exists())

    def test_06_corruption(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cal-v7-corrupt-") as temp:
            base = Path(temp)
            archive, digest = self.bundle(base)
            with self.assertRaisesRegex(ValueError, "LOCAL_ARCHIVE_DRIFT"):
                remove_redundant_staging(archive, "0" * 64, base, 83)
            (archive.parent / "attempt-cal-only" / "trace.json").write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "STAGING_CONTENT_NOT_REDUNDANT"):
                remove_redundant_staging(archive, digest, base, 83)
            self.assertTrue(archive.exists())

    def test_07_outside_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cal-v7-outside-") as temp:
            base = Path(temp)
            archive, digest = self.bundle(base)
            with self.assertRaisesRegex(ValueError, "STAGING_OUTSIDE_OWNED_SEQUENCE"):
                remove_redundant_staging(archive, digest, base / "another", 83)
            self.assertTrue((archive.parent / "attempt-cal-only").exists())

    def test_08_historical_exclusion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cal-v7-history-") as temp:
            base = Path(temp)
            archive, digest = self.bundle(base)
            with self.assertRaisesRegex(ValueError, "HISTORICAL_STAGING_PROTECTED"):
                remove_redundant_staging(archive, digest, base, 82)
            self.assertTrue((archive.parent / "attempt-cal-only").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
