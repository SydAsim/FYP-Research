# Final evidence package-only correction v3

Status: FIVE LOCAL OFFLINE CONTROLS PASS; CLOUDSHELL PACKAGE-ONLY RUN OUTSTANDING.

## Demonstrated defect and preserved evidence

The returned log reaches1500/1500 with22198827558 recovery bytes and7333seconds
remaining. The traceback is in evidence helper v2.bundle_records, line248:
record[key] raises KeyError('fixture_hash'). v2.KEYS incorrectly required that
field on every record, including the legacy cached735-result derivative.
Inspection of the real sealed cached objects confirms the field is absent;
modern736–1500 compact records include it. The original cached objects had already
been validated against identities/receipts and frozen case metadata. The new
v2 test used uniform synthetic objects and missed this real schema difference.

The failure occurs before all-results.json is written. It follows full retrieval,
not a new research execution or a change to its outcome. Preserve the original
v1/v2 scripts, attempts, old failure and completion metadata,765record files,
requests and original caches. No more S3 GETs are needed. The first interrupted
1129 transport completion remains UNKNOWN; its explicitly labelled second read
and aggregate retrieval accounting remain in v2 metadata.

## Narrow correction and measured checks

New cloud_package_final_v3.py imports only hash-pinned v2/v1 helpers and never
calls recover/main/AWS. It validates all1500 saved identities/order/archive/version
bindings. The cached735 must equal the authenticated extraction-control cache
exactly; no field or outcome is added. Their fixture binding is explicitly from
the sealed extraction-control identities. Modern765 continue to require their
recorded fixture_hash, analysis-row identity and grade/value agreement. Existing
prepare_dataset.py independently validates all500 frozen case bindings afterward.

The helper verifies exact765record and765standardrequest filenames; the separate
1129 additional request and original request hash; exact v2 source/control,
original deadline, limits,372completedGETs/22198827558bytes, fresh prerequisite
hash, preserved-file hashes and the specific expected KeyError failure. Other
failures/missing/conflicting evidence stop. Existing outputs or a prior v3attempt
are refused rather than overwritten. The final bundle retains the same four
members; explicit packaging and prior failure provenance is inside the hashed
all-results payload. Raw outcomes, grades, original analysis rows and historical
status records are not changed. No regrading, timing sidecar or research replay.

Five focused local offline controls PASS in15.853seconds: exact bug reproduction
using actual735cached schema; full mixed-schema staged filesystem and bundle
roundtrip with all original bytes unchanged; altered cache rejection; missing/wrong
modern fixture rejection; missing/duplicate identities and output collision
rejection. The full roundtrip includes765temporary record files,765requests,
original/second attempt metadata, retained failure, independent member hashes and
unchanged historical-file hashes. New765records in these controls are explicitly
synthetic; no scenarios or application stacks ran. Earlier simpler five-control
pass is retained separately. Ruff and Linux-target mypy PASS without SDK-import
exceptions. CloudShell executes the same five small offline checks before local
packaging; local Windows checks are not claimed to be Linux execution.

192MiB total-stage/2MiB failure reserve,48MiB payload and32MiB bundle limits remain.
Packaging has60seconds and the original2026-10-25T16:40:05.249100Z extraction
absolute bound; no reset. No dependencies, network clients, SDK calls, cloud
resources, campaign boot, frozen application/fixture/grader/analysis changes,
evidence deletion or outcome replacement. Passing controls are bounded evidence,
not a guarantee every operational path is error-free.

## Exact manual handoff

File: C:/Users/syeda/Downloads/cloud_package_final_v3.py
SHA256: e215465063681c12b942465be866861f479835c3ea3bebbb7c69dd024c074117
Bytes: 21656

Upload beside both old scripts in /home/cloudshell-user. Follow HANDOFF.md once.
Expected PASS with1500records and network_requests0, final bundle bytes/SHA256.
Download /home/cloudshell-user/fyp-phase8-final-evidence-v1/final-records.tar.gz
and return its printed SHA256. Locally verify it before the unchanged dataset
assembler and final statistical analysis. No completed-analysis claim yet.
