"""Documentation-only builder. Reads project evidence; writes only this output directory."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv, hashlib, json, re, tomllib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'diagrams').mkdir(exist_ok=True)
V4 = ROOT / 'artifacts/phase-8-study-design/v4'
def load(p): return json.loads((ROOT / p).read_text(encoding='utf-8'))
def link(p, label=None):
    return f'[{label or p}](<{(ROOT / p).as_posix()}>)'
def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |'] + ['| ' + ' | '.join(str(v).replace('|','/').replace('\n',' ') for v in row) + ' |' for row in rows])

slots = load('artifacts/phase-8-study-design/v4/main-slots.json')
decisions = load('artifacts/phase-8-study-design/v4/review-decisions.json')
assert len(slots) == 1500 and all(s['status']=='NOT_STARTED' and s['execution_id'] is None for s in slots)
assert decisions['review_receipt'] is None and decisions['freeze_hash'] is None
historical = load('artifacts/phase-8-study-design/v4/historical-hashes-before.json')
# Inventory formats are interpreted below without rewriting the originals.
print('Historical inventory type',type(historical).__name__)

sections=[]
def add(text): sections.append(text.strip())
def fig(name, title, mermaid, explanation):
    diagram = OUT/'diagrams'/f'{name}.mmd'
    source = mermaid.strip()+'\n'
    if source.startswith('sequenceDiagram'):
        source = source.replace(';', ',')
    if not diagram.exists() or diagram.read_text(encoding='utf-8') != source:
        diagram.write_text(source,encoding='utf-8')
    add(f'### Figure {name.split("_")[0]}. {title}\n\n![{title}](diagrams/{name}.png)\n\n{explanation}\n\nEditable source: [Mermaid](diagrams/{name}.mmd). Vector export: [SVG](diagrams/{name}.svg).')

add('''# Commit-Aware Voice Agent

## Research proposal and project explanation

Prepared for Syed Asim Bacha | Final Year Project | Evidence review: 4 October 2026

**Status: implemented research instrument with a revised Phase 8 candidate awaiting review. The 500-input main campaign has not started.**

### Abstract

A voice assistant can lose track of a booking even when the booking succeeded. A caller may then change the request while an old confirmation is waiting to play or has already started. This project investigates how accepted instructions, external business effects, verification evidence and spoken statements can remain consistent under those conditions. Its demonstration domain is synthetic residential maintenance appointments.

The implemented system stores accepted revisions, stable operation identities, uncertain outcomes, evidence, speech permissions and repair obligations in PostgreSQL. A separate provider simulator records what actually happened. An independent grader compares that truth with externally specified requests, available observations and recorded playback acknowledgements. The model proposes an instruction; deterministic code decides whether to accept it, perform an operation and authorize consequential speech.

Historical pilot evidence and a revised six-fixture exploratory set demonstrate selected protocol mechanisms, including recovery from a lost response and discovery of persisted repair work after restart. They do not establish general superiority, human hearing or research novelty. The revised candidate proposes 500 new typed/scripted inputs paired across B3, P1 and P2. Its sampling target is a fixed simulator recipe mixture, not real callers. Review of the scope, assumptions, tolerance and execution plan must precede a new freeze and any main evaluation.

### How to read this document

The first part explains the problem and the system. The second gives the research comparisons and evaluation design. The appendices provide evidence, references and finite next actions. Each status word has a specific meaning:

| Label | Meaning |
| --- | --- |
| Planned | A requirement or proposed design, without implementation proof |
| Implemented | Relevant code or configuration exists |
| Tested | A named check has retained results for a defined path |
| Demonstrated within a limited scope | A trace exercises the mechanism under stated conditions |
| Unresolved | Evidence, interpretation or a decision is still missing |
| Not yet evaluated | No main-study outcome is available |''')

add('''## 1. The problem through one appointment

A caller asks for a 3 PM maintenance appointment. The provider books it, but the response disappears. The caller then says, "Actually, make it 4 PM."

Three facts must be kept separate. The caller now wants 4 PM. The provider has already created 3 PM. The controller does not yet know that the provider succeeded. A timeout is a communication observation, not proof that no booking exists. A request may have succeeded, but we do not know yet (ambiguous outcome).

Repeating the write can create another booking. Saying "the earlier request failed" or "it was cancelled" can be false. Stopping the voice model does not undo a provider commit. Even a correct final 4 PM booking does not prove that earlier speech was appropriate. The caller might already have heard "3 PM is confirmed."

The system first records that the old outcome is unknown, accepts the new instruction durably, discovers the old effect and transitions it safely. It may move the appointment if the provider supports an atomic move. Otherwise it performs an explicitly linked cancellation/compensation and creates a new booking, following the domain policy. An action that offsets an earlier action is not erasure of history (compensation).

### What actually happened, what is known, and what may be said

| Point | Provider reality | Controller knowledge | Safe speech in the ordinary product path |
| --- | --- | --- | --- |
| 3 PM accepted, before send | No effect yet | Durable accepted revision 1 | "I am checking the appointment" |
| Provider commits, response lost | 3 PM exists | UNKNOWN after possible send | "I cannot yet determine whether the earlier request completed" |
| 4 PM accepted | 3 PM may still exist | Revision 2 current; old effect needs reconciliation | "I am checking the change" |
| Read finds 3 PM | Original effect exists | Evidence of 3 PM, not of 4 PM | Explain checking; do not announce a completed move |
| Move/create finishes and is verified | One permitted 4 PM appointment | Current predicates satisfied at observed version | Deterministic 4 PM confirmation with applicable permit |
| Old decisive content was exposed | Earlier audio conveyed an incompatible time | Recorded exposure requires corrective work in P2 | Explicit withdrawal plus a supported current update; completion still needs playback evidence |

An available observation and a permission to speak are different objects. A recorded proof of the checked state is a verification receipt. A short-lived authorization for a particular statement is a claim permit. Neither guarantees that external state can never change afterwards; applicability must be checked again at the release and playback boundaries.

### Four variations

**The caller keeps 3 PM.** Reconciliation finds the original booking. The system preserves it and verifies it rather than creating another. Repeating the same logical request should not create another booking (idempotency). If authoritative evidence stays unavailable, it remains unknown and may be handed off.

**The requested slot is unavailable.** A confirmed absence or slot conflict is different from an unknown send. The system does not promise 4 PM. It retains known facts, rejects an unsafe overwrite and asks for another choice or creates human follow-up according to the implemented path. A handoff can be safe resolution without successful task completion. There is no generic implemented cancellation-speech template in the current public claim enum.

**Correction after confirmation audio starts.** Stop the remaining buffer. If only introductory words such as "Your maintenance" played, there is no confirmed time to withdraw. If the words conveying confirmation or 3 PM were exposed, stopping later words cannot undo that exposure. New evidence and a corrective statement are needed. The revised measurement separates confirmation status, time, date and zone spans.

**A worker crashes while correction is pending.** The obligation remains in PostgreSQL. A restarted repair consumer discovers pending rows, leases work and rechecks current evidence. Publication is only a delivery attempt. The obligation is not completed merely because the worker sent a segment; missing completion acknowledgement leaves delivery unknown or pending.''')
fig('01_overview','Plain-English overview','''flowchart TB
 C[Caller asks for an appointment] --> V[Voice agent receives the request]
 V --> A[Server accepts and checks it]
 A --> D[(Durable records: PostgreSQL)]
 A --> W[Worker sends or reconciles]
 W --> P[Appointment provider]
 P --> W
 D --> U[Dashboard: known facts and follow-up]
 A --> S[Evidence-backed statement]
 S --> C
''','The provider owns the external effect. The application owns its durable knowledge, accepted instructions and obligations. The dashboard displays server records; its appearance cannot establish that the appointment succeeded.')

add('''## 2. Research purpose and possible contribution

**Central question: "When does the proposed mechanism provide protection beyond a competent baseline's existing checks?"**

The investigation concerns disagreement between the latest accepted request, earlier external effects and already exposed speech. It is a runtime and evidence problem; a selected trace does not justify blaming the language or voice model. A competent baseline already uses stable identities, checks outcomes, invalidates old work, handles conflicts and stops stale segments. Those protections must remain enabled.

The engineering improvement is an explicit chain from accepted revision to observed state, authorized statement and durable corrective responsibility. The research hypothesis is that this chain adds protection at particular gaps left by ordinary checks. An observed finding is narrower: for example, a resource-version change caused P1/P2 to reject playback while B3's revision-only start check allowed it. A contribution established against prior work would require valid comparative experiments, appropriate uncertainty and a thorough account of existing mechanisms. That has not been established.

The narrowest defensible potential contribution is a tested cross-layer rule for revision- and resource-bound claims, combined with persistent responsibility to withdraw incompatible decisive content after exposure. It is not the A3 name, a state machine, idempotency, LiveKit, PostgreSQL, interruption handling or the mere combination of known ideas.

Supporting evidence would show fewer unsupported exposures or better completed corrective communication under matched faults, while retaining useful outcomes within the clean-case tolerance. Contrary evidence includes ties, benefit only against a weakened baseline, internal repair rows without delivered correction, excessive clean-case loss, or differences explained by evidence availability and budgets rather than the proposed mechanism. If all observable behaviours tie, all observable grades must tie.''')

rqs=[
('RQ1','Does revision-aware reconciliation improve correction success under commit ambiguity without unacceptable clean-case loss?','Can the old 3 PM effect be found and safely changed to 4 PM?','Durable revisions, linked operations and reconciliation','Correct final business state without forbidden effects; clean utility','Core incremental comparison P2/B3; historical B0-B2 ablations separate','Support: additional correct final states within clean tolerance. Contrary: tie or clean loss.'),
('RQ2','Does explicit `UNKNOWN` plus reconcile-before-retry reduce duplicate effects and unsafe false cancellations?','Does checking before retry avoid another booking or a false cancellation statement?','Three-valued knowledge; status/postcondition lookup','Duplicate effects and unsafe false cancellation','B1/B2 versus B0 in historical harness; B3/P1/P2 share much of this protection','Support: fewer unsafe effects under matched ambiguity. A core-arm tie is expected if shared checks already suffice.'),
('RQ3','Do revision-bound evidence rules prevent old valid receipts from authorizing new or stale claims?','Can evidence for 3 PM incorrectly justify saying 4 PM is confirmed?','Receipt revision/resource/predicate binding and freshness','Claim truth and evidence applicability at publication and exposure','P1/B3 and targeted receipt/freshness removal','Support: an unsafe action blocked first by binding. Contrary: ordinary baseline check blocks the same action.'),
('RQ4','Does receipt-gated speech reduce unsupported audible confirmations at useful outcome coverage?','Are confirmations supported without making the agent silently refuse everything?','Claim permits; deterministic templates; release/start checks','Per-task unsupported exposure and useful outcome coverage','P1/B3 or P2/B3 with comparable evidence and playback','Support: reduced unsupported exposure with useful coverage. Tone ACK tests alone cannot establish audible human exposure.'),
('RQ5','Does durable playback repair reduce misleading audio exposure and improve evidence-backed correction after partial stale playback?','After 3 PM was exposed, does a supported correction actually arrive, including after a crash?','Persistent obligation, discovery, current evidence and completion check','Supported corrective delivery; required withdrawal; internal repair separately','P2/P1 and P2/B3 with equal ordinary-response opportunities','Support: more complete corrective communication after challenge. Contrary: ordinary updates tie or publication never completes.'),
('RQ7','Do named commit/playout barriers expose failures missed by end-of-task evaluation?','Can a final correct booking hide an earlier unsafe statement?','Named wait/release barriers and event-time oracle','Final-state versus exposure/evidence/repair discrepancies','Same input across arms, plus boundary versus final-only evaluation','Support: retained traces reveal intermediate violations despite correct final state. Not a population prevalence estimate.')]
add('## 3. Research questions from the contract\n\nThe questions below reproduce `docs/04_TEST_EVALUATION_AND_TRACEABILITY.md`. Their numbering is preserved. Each following table explains how it can be tested.')
for rq,exact,plain,mechanism,outcome,comparison,evidence in rqs:
    add(f'### {rq}\n\n**{exact}**\n\n{plain}\n\n'+table(['Aspect','Explanation'],[('Mechanism',mechanism),('Outcome',outcome),('Comparison',comparison),('Supporting or contrary evidence',evidence)]))
add('''RQ6 (semantic provisional dispatch barrier), RQ8 (causal schedule exploration) and RQ9 (human belief study) remain optional contract extensions. They are not silently renumbered or included in the typed/tone main candidate. Human understanding would need an independently reviewed human study, consent and an appropriate sampling plan.''')

add('''## 4. Related research and honest positioning

The original literature review and study guidance are in `E:/FYP Project/BUILD/FYP_Research_Backend_Architecture_Proposal.pdf`, especially its research design and Appendix D. The readable implementation guide supplies the 12-rule contract. Four local papers are retained under `E:/FYP Project/Related Papers`. No separately named study-guide file was located in the current repository or supplied top-level archive inventory; study guidance is drawn from the original proposal sections and current contract.

The bibliography below was checked against primary arXiv records, author-hosted material or the original institutional report on 4 October 2026. A verified citation is not a replicated result or proof of peer review. Most recent entries are preprints. The table distinguishes a stated limitation from a boundary merely described by an abstract. An absent topic in an abstract is not evidence that the authors failed to address it. No direct novelty conclusion follows from these overlaps.

Each entry uses a vertical table to keep all comparison fields readable at normal PDF width. The proposed additional question is a hypothesis unless an explicitly linked local trace supports a limited mechanism finding.''')

papers=[
('L1','Zhiyuan Zhai, Ming Li and Xin Wang. Revisable by Design: A Theory of Streaming LLM Agent Execution. 2026. arXiv:2604.23283v1.','https://arxiv.org/abs/2604.23283v1','Mid-execution instruction changes.','Revision Absorber and StreamBench; classifies actions by reversibility and compares recovery work.','Preserves usable work while reacting to conflicts.','Action reversibility bounds adaptation; not every irreversible conflict can satisfy both specifications. Verified record/abstract.','Accepted revisions and action semantics overlap.','Does revision/resource-bound speech authority add protection when a commit is hidden? Hypothesis.'),
('L2','Ruoling Qi, Xuaner Wu, Penghang Liu, Jian Chen and Yirui Liu. REVISE: Validity-Guided Recovery for Online Revisions in Agent Workflows. 2026. arXiv:2609.00643v1.','https://arxiv.org/abs/2609.00643v1','Reuse versus stale results after online changes.','Dependency-guided DAG recovery; evaluates revision/commit executions and LangGraph/LLMCompiler applications.','Stops invalid work and revalidates reused results before commit.','Incomplete provenance expands recovery conservatively. Record/abstract establishes reported scope, not a complete exclusion inventory.','Revision invalidation and current-state checks overlap.','What extra protection is needed between valid reuse and played confirmation? Hypothesis.'),
('L3','Bardia Mohammadi, Nearchos Potamitis, Lars Klein, Akhil Arora and Laurent Bindschaedler. Atomix: Timely, Transactional Tool Use for Reliable Agentic Workflows. 2026. arXiv:2602.14849v2.','https://arxiv.org/abs/2602.14849v2','Partial effects, contention and irreversible leakage.','Progress-aware transactions, sealed footprints and resource frontiers; fault and contention benchmarks.','Stages effects and compensates reversible externalized actions.','Sections 4/B.3: adapter metadata critical; distributed settlement/full crash-safe exactly-once outside prototype scope.','Staging, effect classification and compensation are established overlap.','Can independently observed claim and corrective-delivery endpoints reveal additional gaps? Hypothesis, not a claim that Atomix ignores speech.'),
('L4','Zheng Chen, Hanqing Liu, Duling Xu, Dong Dong, Jialin Li, Bangzheng Pu and Jidong Zhai. Cordon: Semantic Transactions for Tool-Using LLM Agents. 2026. arXiv:2606.17573v1.','https://arxiv.org/abs/2606.17573v1','Task-level containment beyond isolated tool calls.','Transaction manager, tracked result lineage, shadow state and effect outbox; adversarial/benign evaluation.','Validates composed execution before external effect release.','Verified abstract describes containment and workflow evaluation; deployment limitations not exhaustively checked here.','Task-scoped validation and outbox overlap.','Test claim applicability and obligations after acknowledged speech. Hypothesis; further full-text comparison needed for priority.'),
('L5','Ke Yang, Panpan Li, Zonghan Wu, Kejin Xu, Huaxi Huang and Xiaoshui Huang. DART: Semantic Recoverability for Structured Tool Agents. 2026. arXiv:2605.23311v1.','https://arxiv.org/abs/2605.23311v1','Local restore can invalidate committed downstream work.','Certified recoverable boundaries and admissible restore points; three domains, LangGraph validation and safety audit.','Blocks semantically inadmissible rollback.','Structured dependencies/effect constraints define its boundary; reported evaluated cases do not imply universal recoverability. Local supplied PDF and primary record.','Recovery legality and irreversible history overlap.','Evaluate business and spoken consequences jointly after caller revision. Hypothesis.'),
('L6','Isham Kalappurackal Mansoor, Abhishek Phadke and Pratip Rana. Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures. 2026. arXiv:2608.02645v1.','https://arxiv.org/abs/2608.02645v1','Tool response may disagree with external effect.','Verify-before-retry wrapper under timeout, visibility and partial-effect faults.','Avoids redundant writes when postconditions already hold.','Section 7: two simulator workflows and hand-designed verifiers; stale/incomplete verification remains a limit.','UNKNOWN and reconciliation build on this established issue.','Add current-revision evidence applicability and playback-relative correction. Hypothesis.'),
('L7','Shibo Wang, Zicheng Zhang, Libo Wang and Junfeng Ma. PACE: A Playback-Aligned Context Engine for LLM-Based Full-Duplex Voice Dialogue. 2026. arXiv:2608.07631v1.','https://arxiv.org/abs/2608.07631v1','Generated context can include words not yet played.','Browser audio re-injection adapter; 108 GCM-Bench cases and 200 interruption samples.','Projects model context to the playback boundary.','Section 6.5: constructed trajectories, one judge/model and only audio re-injection; semantic-span commitment and irreversible gating not validated.','Generated versus played distinction is strong overlap.','Test persisted withdrawal/delivery responsibilities tied to external effects. Hypothesis, with selected local protocol traces only.'),
('L8','Bertil Braun. Voice-Light: A Full-Duplex Cascaded Voice Agent with Causal Turn-Taking and Speculative Generation. 2026. arXiv:2609.20995v1.','https://arxiv.org/abs/2609.20995v1','Overlap, turn completion and cancelled speech history.','Cascaded voice controller, private speculation and browser acknowledgements; real-conversation timing candidates.','Reversible playback and history grounded in rendered audio.','Abstract reports weak learned-checkpoint recall and retains a hybrid controller. Not a reviewed comparison of durable appointment repair.','Cascaded control and acknowledged history overlap.','Test revision/effect evidence and durable correction after restart. Hypothesis.'),
('L9','Kangxiang Xia, Bingshen Mu, Xian Shi, Jin Xu and Lei Xie. Semantic-Aware Interruption Detection in Spoken Dialogue Systems: Benchmark, Metric, and Model. 2026. arXiv:2603.24144v1.','https://arxiv.org/abs/2603.24144v1','False interruption versus delayed response.','SID-Bench on human dialogues; Average Penalty Time metric and interruption model.','Distinguishes meaningful interruptions from backchannels.','Verified abstract scopes interruption detection; not a complete execution correctness evaluation.','Interruption classification is an upstream input to this protocol.','Does correct detection still leave hidden commits and stale claims? Hypothesis.'),
('L10','Guan-Ting Lin, Chen Chen, Zhehuai Chen and Hung-yi Lee. Full-Duplex-Bench-v3: Benchmarking Tool Use for Full-Duplex Voice Agents Under Real-World Disfluency. 2026. arXiv:2604.04847v1.','https://arxiv.org/abs/2604.04847v1','Natural disfluency and chained voice tool use.','Real human audio in four domains; six configurations evaluated for task accuracy, timing and turn taking.','Exposes self-correction and multi-step failure modes.','Primary record marks work in progress; its speech sample is different from this fixed simulator frame.','Voice correction is common motivation; measurement constructs differ.','Named commit/playback faults and independent temporal claim grading. Hypothesis.'),
('L11','Abhinaba Basu. Tool Receipts, Not Zero-Knowledge Proofs: Practical Hallucination Detection for AI Agents. 2026. arXiv:2603.10060v1.','https://arxiv.org/abs/2603.10060v1','Separate grounded tool claims from unsupported inference.','NabaOS receipt and claim-tagging framework with grounding checks.','Makes evidence provenance available for claim assessment.','Section 6.4: self-tagging compliance affects verification granularity.','Evidence-linked claims overlap; our deterministic templates avoid relying on self-tagged decisive prose.','Does revision/resource revalidation and durable withdrawal improve matched observable outcomes? Hypothesis.'),
('L12','Aayush Gupta. ReliabilityBench: Evaluating LLM Agent Reliability Under Production-Like Stress Conditions. 2026. arXiv:2601.06112v1.','https://arxiv.org/abs/2601.06112v1','Success scores can hide inconsistency and fault sensitivity.','Controlled stress profiles and metamorphic relations; reported multi-configuration episodes.','Evaluates robustness and fault tolerance beyond clean success.','Section 6.2: rare failures need larger scale; deeper perturbations remain future work.','Fault injection and independent retained outcomes overlap.','Joint evidence/exposure endpoints at exact commit barriers. Hypothesis.'),
('L13','Collin Lee, Seo Jin Park, Ankita Kejriwal, Satoshi Matsushita and John Ousterhout. Implementing Linearizability at Large Scale and Low Latency. SOSP 2015.','https://web.stanford.edu/~ouster/cgi-bin/papers/rifl.pdf','Retries of RPCs must not repeat durable effects.','RIFL completion records and request identification; implemented in RAMCloud.','Duplicate suppression at a controlled linearizable service boundary.','Service completion-record and lifetime assumptions apply; not an exactly-once promise for an opaque provider.','Stable operation identity and replayed results use established principles.','Claim/repair behaviour when the provider boundary cannot give those guarantees. Hypothesis.'),
('L14','Hector Garcia-Molina and Kenneth Salem. Sagas. 1987. Princeton technical report TR-070-87; SIGMOD paper DOI 10.1145/38713.38742.','https://www.cs.princeton.edu/techreports/1987/070.pdf','Long transactions block other work and may partially finish.','Sequence of transactions with compensating transactions; implementation/design analysis.','Amends partial execution without a long global transaction.','Compensations must be designed for the domain; interleaved history is not erased.','Cancel/create fallback is an application of compensation.','Persist responsibility for correcting statements already exposed. Hypothesis.')]
for ident,citation,url,problem,measured,protects,limit,overlap,question in papers:
    add(f'### {ident}. {citation.split(". ")[1]}\n\n[{citation}]({url})\n\n'+table(['Comparison field','Evidence-grounded account'],[('Problem',problem),('Implemented or measured',measured),('Existing protection',protects),('Stated limitation / reviewed boundary',limit),('Overlap with this FYP',overlap),('Additional question and status',question)]))
(OUT/'bibliography.md').write_text('# Verified bibliography\n\nVerification date: 4 October 2026. Preprint status is not peer-review certification. Full-text depth is stated in the proposal.\n\n'+'\n\n'.join(f'**{p[0]}** [{p[1]}]({p[2]})' for p in papers)+'\n',encoding='utf-8')

add('''## 5. Architecture and technology

The system has one repository with separate runnable processes and shared internal modules (modular monolith). This keeps latency-sensitive audio apart from durable work without turning the FYP into a large microservice deployment. ADRs 0001-0004 document this choice, the PostgreSQL queue, disposable cache and model proposal boundary.

### Responsibilities and implemented boundaries

| Component | Responsibility and actual status |
| --- | --- |
| Browser application | Implemented Next.js routes for calls, summaries, appointments, residents, notes, traces, handoffs, evaluations and settings. Real controller projections; cached reads/polling, not authoritative mutations. |
| API controller | Validates HTTP input and binds identity. Service modules implement acceptance, operations, evidence, audio and playback. Framework routes delegate; PostgreSQL transactions own durable decisions. |
| Voice worker | Joins LiveKit, segments PCM microphone input, runs local recognition and restricted typed-intent extraction, uses the controller and scheduler. No direct provider mutation authority. |
| Durable worker | Leases and executes dispatch/reconciliation steps. Core operation work has explicit run-once/drain entry points used by application/replay paths; the repair consumer runs on enabled service startup. This is not proof of unattended processing for every job type. |
| Domain package | Framework-independent enums, revision decisions and predicates. |
| Protocol package | Normalized voice events and typed proposal interfaces. |
| Event schemas | Durable versioned envelope with IDs, UTC time, per-workflow sequence and payload; schema-contract checks. |
| Provider adapters | Simulator HTTP adapter with stable identities, normalized and raw observations. Production booking-provider equivalence is not established. |
| Speech policy | Classifies exposure/claims, checks applicability, renders permitted templates and limits repair by arm capability. |
| Observability | Structured JSON logs and durable event traces implemented. Collector/metrics/dashboard containers configured; comprehensive end-to-end OTel instrumentation is not established. |
| Scenario generator | Versioned recipe/context inputs and hashes. The v4 generator is a fixed protocol frame, not a natural-language caller sample. |
| Fault scheduler | Named durable barriers and specific provider/client interventions with retained causal evidence. |
| Provider simulator | Separate PostgreSQL state and append-only truth history; configurable capability/visibility and controlled faults. |
| Independent oracle | Reads external expected intent, policy, provider truth, observations and ACKs; does not accept the controller's receipt verdict as truth. |
| Replay runner | Explicit arm drivers, paired inputs, manifests, raw exports and offline verification. |
| Statistical analysis | Historical descriptive analysis, revised arm-neutral measurement and v4 identifiable binary-outcome pipeline. Generic latency/mixed/AFT helpers exist but are not automatically an accepted v4 campaign analysis. |
| Migrations and seeds | Source SQL translated through additive Alembic changes. Synthetic UI seed is in migration 0006. Latest migration is 0013_readiness_capability; no migration changed for this document. |

### Verified versions and implementation status

Versions below come from `uv.lock`, `pnpm-lock.yaml`, Compose and the isolated scientific requirements. These are repository pins, not a live production inventory. The Python Docker base is `3.12-slim`; the project accepts >=3.12,<3.14. Actual frozen pilot image/model hashes are in its manifest. The current base tag alone is not an immutable image digest.''')
lock=tomllib.loads((ROOT/'uv.lock').read_text(encoding='utf-8'))
versions={p['name']:p['version'] for p in lock['package']}
stack=[('Next.js / React','16.3.5 / 19.3.0','App Router and components; implemented; avoids custom UI framework.'),('TypeScript / Tailwind','6.0.3 / 4.3.3','Strict types and styling; implemented.'),('TanStack Query','5.103.2','Read caching/refetch; implemented; cache never verifies effects.'),('Zod','4.6.5','Frontend response/input schema checks; implemented.'),('LiveKit browser SDK','2.22.3','Browser RTC transport; implemented.'),('LiveKit Python RTC / server',versions['livekit']+' / v1.13.7','Python media client and self-hosted media server; implemented. Signed token construction is local; no livekit-api package is locked.'),('Vosk',versions['vosk'],'Local STT with small English model 0.15; implemented; restricted recognition coverage.'),('Qwen / llama.cpp','Qwen2.5 0.5B Q4_K_M / image digest in Compose','Local HTTP proposal extraction; implemented and grounded by lexical validation, not general dialogue competence.'),('eSpeak NG','OS package; no exact application lock pin','Local generated speech adapter; implemented; model/audio identities require actual manifest hashes.'),('FastAPI / Pydantic',versions['fastapi']+' / '+versions['pydantic'],'HTTP interfaces and strict validation; implemented.'),('SQLAlchemy / Alembic',versions['sqlalchemy']+' / '+versions['alembic'],'Async readiness engine and migrations; implemented. Many business transactions use direct psycopg SQL rather than an ORM.'),('asyncpg / psycopg',versions['asyncpg']+' / '+versions['psycopg'],'Async health/database path and synchronous durable SQL transactions; implemented.'),('PostgreSQL','16.9 Compose image','Locks, uniqueness, exclusions, revision/evidence/job durability; implemented.'),('Redis','7.4.5-alpine Compose image','Optional container; app cache integration not evidenced. v4 companion-cache flush is a negative control.'),('OpenTelemetry collector','0.140.1','OTLP-to-debug configuration exists; app Python OTel SDK not in lock; full tracing planned.'),('Prometheus / Grafana','v3.4.1 / 12.0.2','Optional configured containers. Prometheus currently scrapes itself; research dashboards/app scrape wiring not established.'),('structlog',versions['structlog'],'Structured UTC JSON logging with trace context; implemented.'),('pytest / pytest-asyncio',versions['pytest']+' / '+versions['pytest-asyncio'],'Unit/contract and real PG integration checks; used.'),('Testcontainers / Hypothesis','Not present in uv.lock','Blueprint suggestions; no claim of implemented use.'),('Vitest / Playwright','5.0.1 / 1.63.0','Frontend unit and browser E2E definitions/evidence; implemented.'),('Scientific environment','NumPy 2.3.5; SciPy 1.16.3; pandas 2.3.3; statsmodels 0.14.6','Separate .venv-study-design and requirements; no upgrade of the frozen pilot environment.'),('Docker Compose / CI','compose.yaml / .github/workflows/ci.yml','Local topology and CI definitions exist; remote CI success not verified in this review.')]
add(table(['Technology','Repository version','Job, usefulness and status'],stack))
fig('02_architecture','Application architecture','''flowchart TB
 B[Browser: UI and playback reporter] -->|HTTP via Next proxy| A[API controller]
 B <-->|RTC media and data| L[LiveKit]
 L <--> V[Voice worker: cascade and scheduler]
 V -->|Validated commands| A
 A --> D[(Application PostgreSQL)]
 W[Durable worker] --> D
 W -->|Adapter requests and reads| P[Provider / simulator]
 W -->|Repair scheduler records and releases| A
 R[Optional Redis container] -.-> N[No current correctness authority]
 A -.-> O[JSON logs; optional telemetry scaffolding]
 W -.-> O
''','Solid arrows describe implemented control or media relationships. Dotted relationships describe optional/scaffolded facilities. Redis is not drawn as an active correctness store. The provider truth database is separate, as shown in the deployment and evaluation figures.')
fig('03a_deployment','Docker panel A: application services','''flowchart TB
 subgraph App[Application containers]
 Web[web :3000] --> API[api-controller :8000]
 Voice[voice-worker :8001] --> API
 Durable[durable-worker :8002] --> API
 API --> PG[(postgres :5432 internal)]
 Durable --> PG
 M[migrate: one-shot Alembic] --> PG
 PG --> PV[(postgres_data volume)]
 end
''','Application containers share durable application records. The one-shot migrate container runs Alembic before dependent services. postgres_data is the persistent volume; it is not Redis.')
fig('03b_deployment','Docker panel B: research provider','''flowchart TB
 Durable[durable-worker] --> Sim
 API[api-controller] --> Sim
 subgraph Research[Research provider services]
 Sim[provider-simulator :8010] --> SP[(simulator-postgres)]
 SP --> SV[(simulator_data volume)]
 end
''','The provider simulator has a separate database and persistent simulator_data volume. An independent host-side oracle reads its truth. The oracle is not an always-on application container.')
fig('03c_deployment','Docker panel C: optional profiles','''flowchart TB
 subgraph Profiles[Optional Compose profiles]
 LK[media: livekit :7880] <--> Voice[voice-worker]
 LLM[local-voice: local-llm :8080] --> Voice
 Cache[redis: Redis]
 Obs[observability: collector / Prometheus / Grafana]
 end
''','Default services include the simulator for the local research demo. LiveKit, local LLM, Redis and telemetry use profiles. Model files are a read-only host mount. The experiment runner/oracle runs as a separate host process, not a normal always-on container in this Compose file.')
add('''### Local deployment facts

Web/API/voice/durable/simulator loopback host ports are 3000/8000/8001/8002/8010. Main PostgreSQL defaults to host 5432, but this machine's documented override is 15432; simulator PostgreSQL is host 5433. Internal container PostgreSQL remains 5432. LiveKit maps 7880, 7881 and UDP 7882; local LLM maps host 11435 to internal 8080; optional Grafana maps 3001. Redis, Prometheus and the collector have no declared host-port exposure in this Compose file. These are configuration facts, not checks of current service health.

The documented local command is `docker compose --profile media --profile local-voice --profile redis up -d --build --wait`. Health and migration dependencies establish boot order. The local LiveKit address is loopback-oriented; remote-device deployment needs a reachable media address and separate verification. Development credentials and EXPERIMENT_MODE are local assumptions, not production hardening.

The v4 calibration uses isolated databases and native service ports 18100/18101/18102/18110. Controller and worker do not receive the oracle credential or simulator database URL in that runtime. The oracle-only route denies access without its header token. Privileged same-host access is still possible: this is an application access boundary, not physical or OS isolation.

### Browser behaviour and missing product features

The UI uses server replies as the truth for mutations. A cached read can show stale data and must be refreshed. Expected revision/version mismatches return HTTP 409 rather than silently overwriting newer work. Missing dashboard events are recovered by polling/reload of the server projection; there is no demonstrated live SSE/WebSocket dashboard stream. Calendar and appointment views are read-oriented where executable routes are absent. The conflict report records the missing direct appointment reschedule controller route and other UI-contract gaps. Human maintenance handoffs are implemented; public telephone numbers, a receptionist dialer, warm/cold telephony transfer and emergency automation are not part of the demonstrated research instrument.''')

add('''## 6. Voice input and durable control flow

The strict voice path turns audio into text, asks a model for a typed proposal, and generates permitted text as audio (STT -> intent -> TTS cascade). LiveKit transports audio; it does not decide whether a booking is true. The local path uses Vosk, restricted Qwen extraction and eSpeak. Simple energy endpointing segments microphone audio; it is not a validated semantic turn detector. Native Gemini/OpenAI audio remains an optional adapter/transfer study, not an implemented authority or evidence requirement for this candidate.

Experiments may bypass speech recognition and submit a scripted typed appointment. That isolates protocol timing and removes recognition variability, but it cannot evaluate natural dialogue. Tone WAVs preserve a repeatable segment duration and metadata, not intelligible confirmation content.

The current microphone agent calls the local PostgreSQL appointment-commit endpoint. Its historical recorded booking/correction does not demonstrate the external provider hidden-commit path through microphone speech. The external-provider fault experiments use separate typed/scripted drivers. The repair consumer constructs its scheduler in its own process, records/releases the segment through the controller and waits for ACK evidence; it does not itself join a LiveKit room. Thus autonomous native repair publication is not autonomous media transport to a real listener.''')
fig('04a_voice','Voice panel A: proposed and accepted intent','''flowchart TB
 M[Microphone / recorded audio] --> STT[Speech recognition]
 STT --> LLM[Model proposes typed intent]
 LLM --> V[Schema and grounding validation]
 V --> R[PostgreSQL accepted revision]
 LLM -.-> X[No direct business or success authority]
''','A model proposal can be rejected or require clarification. Only acceptance creates the durable instruction. The model does not authorize effects or decisive claims.')
fig('04b_voice','Voice panel B: operation and evidence','''flowchart TB
 R[Accepted revision] --> O[Stable operation / recorded dispatch]
 O --> P[Local SQL effect OR provider recovery]
 P --> E[Verification observations]
 E --> C[Applicable receipt / claim permit]
''','The microphone demo commits locally. External-provider drivers exercise uncertain sends and reconciliation. Verification must establish the requested predicates before a proposed-arm permit can apply.')
fig('04c_voice','Voice panel C: permitted statement and playback','''flowchart TB
 C[Applicable claim permit] --> T[Deterministic template / TTS]
 T --> G[Publication and start rechecks]
 G --> A[Playback reports or missing evidence]
''','This final path describes P1/P2 and ordinary product speech. Permitless baseline audio is isolated synthetic research evidence, not live caller audio. Publication does not establish playback.')

add('''### Acceptance, identity and retries

Acceptance locks the workflow, checks `expected_revision`, inserts an immutable next revision and updates the current desired state in one PostgreSQL transaction. The same transaction appends durable events and invalidates stale work/claims. A candidate transcript is not an accepted instruction. Provider requests occur outside the transaction, so network latency does not hold workflow locks.

Each logical operation has an operation ID, normalized request hash and provider idempotency key. A repeat of the same command returns its persisted result or continues its original work; reusing a key with different request content is rejected. The application records the attempt and dispatch marker before sending. A crash between marker and response therefore preserves the possibility of an external effect.

After possible send, a lost response becomes UNKNOWN. Reconciliation asks the provider's operation-status or resource endpoint what happened. An authoritative ABSENT result is different from an unavailable read. Same-key retry requires the adapter's safe evidence/idempotency semantics; an opaque provider gives no general exactly-once guarantee. A materially changed accepted intent creates a linked operation rather than mutating the old operation's identity.

An atomic reschedule changes the provider resource under its expected version. Compensation plus a new CREATE is a separate sequence with preserved history and possible intermediate failure. Provider conflict does not authorize overwriting someone else's newer resource. Unresolved partial effects remain explicit and can be handed off.

### Two workers sharing a durable queue

Imagine worker A and worker B both looking for due work. A briefly locks job 1, writes a lease and commits. B skips the locked row and takes job 2 (`FOR UPDATE SKIP LOCKED`). The lease temporarily reserves a job; it is not an external-effect proof. If A crashes, a later worker can reclaim the expired lease. It then uses the original identity and reconciles any ambiguous send before writing again. Core leases and repair-delivery leases are separate rows/policies. Named crash tests and real PostgreSQL checks matter here; a mock cannot demonstrate locks or transaction atomicity.

### Evidence, claims and playback

Verification evaluates requested predicates as SATISFIED, VIOLATED or UNKNOWN. Its receipt binds workflow, operation, intent revision, claim semantics, evidence source/resource version and validity time. SATISFIED at one moment does not authorize every future sentence. Claim authorization checks predicates and applicability and stores a deterministic template with allowed values. The scheduler checks again before publication; P1/P2 start handling also checks current evidence. The model's tool response never supplies decisive outcome prose directly.

Generated, queued, published, started, partial, completed and interrupted are separate facts. Client event IDs are stable, duplicate-safe progress merges monotonically, and both client exposure time and server arrival time are retained. A missing completion event is unknown delivery, not silence, successful completion or proof that the user understood.

Correction invalidates queued/unpublished statements and stops older segments. If incompatible decisive content was already acknowledged, P2 persists an obligation. Its repair consumer discovers rows after restart, obtains current evidence and publishes a withdrawal/current update. A later revision retargets pending repair; completion of an older repair cannot close the new obligation. Browser or call end does not delete pending business or communication work.''')
fig('05_lost_response','Lost-response sequence','''sequenceDiagram
 participant C as Caller
 participant A as Controller / PG
 participant W as Worker
 participant P as Provider
 C->>A: Accept 3 PM (revision 1)
 A->>A: Persist operation A and dispatch
 W->>P: CREATE, stable key A
 P->>P: Commit 3 PM, append truth
 P--xW: Response lost
 W->>A: Persist UNKNOWN
 W->>P: Read status / resource
 P-->>W: Original effect exists
 W->>A: Record observation; verify
 Note over A,P: No blind repeated CREATE
''','The dashed lost response describes a communication failure. Provider truth and controller knowledge diverge until read-only reconciliation supplies evidence. The independent oracle later reads the simulator truth directly.')
fig('06_correction','Correction to 4 PM','''sequenceDiagram
 participant C as Caller
 participant A as Controller / PG
 participant W as Durable work
 participant P as Provider
 C->>A: Request 4 PM
 A->>A: Accept revision 2, invalidate old claims
 A->>W: Reconcile linked old operation
 W->>P: Find original 3 PM effect
 P-->>W: Effect and resource version
 alt Atomic move supported
 W->>P: Reschedule with expected version
 else Compensation policy
 W->>P: Cancel old, linked CREATE 4 PM
 end
 W->>A: Verify current 4 PM and forbidden effects
 A->>A: Current receipt and permit
 A-->>C: Permitted current confirmation path
''','A supported move is not assumed to exist on every provider. Compensation can fail or remain unknown; only the verified permitted final state authorizes the current confirmation.')
fig('07a_evidence','Evidence panel A: observation to permit','''flowchart TB
 O[Observed provider state and version] --> V[Evaluate required predicates]
 V --> R[Receipt: revision / resource / time]
 R --> A{Applicable and SATISFIED?}
 A -->|Yes| P[Single-use claim permit]
 A -->|No / UNKNOWN| U[Progress / clarification / handoff]
''','A permit authorizes a particular claim, not a generic success flag. Baseline observation support is judged by content and timing, not whether it is serialized as a proposed-arm receipt.')
fig('07b_evidence','Evidence panel B: permit to publication','''flowchart TB
 P[Applicable permit] --> T[Generate deterministic statement]
 T --> G{Release recheck}
 G -->|Valid| S[Publish audio segment]
 G -->|Stale| B[Block; retain evidence]
''','Generation prepares a statement. The release check can block it before publication. Publishing only makes a segment available; it does not prove that anyone played it.')
fig('07c_evidence','Evidence panel C: start and playback testimony','''flowchart TB
 S[Published segment] --> G{Start recheck}
 G -->|Valid| P[Playback may proceed]
 G -->|Stale| B[Stop; retain evidence]
 P --> A[Progress / completion ACK or UNKNOWN]
''','P1/P2 recheck at start. The oracle distinguishes exposure time from ACK arrival time. Missing testimony stays unknown; even a completion ACK does not establish human understanding.')
fig('08a_repair','Repair panel A: persistence and discovery','''flowchart TB
 S[Incompatible decisive span recorded] --> R[(Persist repair obligation in PostgreSQL)]
 R --> X[Worker may crash; row remains]
 X --> D[Restart consumer discovers and leases]
 D --> E[Obtain evidence for latest revision]
''','PostgreSQL retains the obligation through a crash. The native repair consumer discovers outstanding rows after restart without receiving an obligation ID from the replay driver.')
fig('08b_repair','Repair panel B: publication and completion','''flowchart TB
 E[Current applicable evidence] --> P[Permit withdrawal + update]
 P --> U[Publish corrective segment]
 U --> A{Applicable full completion ACK?}
 A -->|Yes| C[Record completed repair]
 A -->|Missing| M[Pending / retry / unresolved handoff]
 A -->|Revision changed| N[Retarget; old ACK cannot close new work]
 N -.-> E
''','Discovery/publication after a native restart is demonstrated in selected local tests. A replay-generated completion ACK is delivery testimony for the protocol, not autonomous listener playback or comparative superiority over baseline updates.')

add('''## 7. Three numbering systems, kept separate

**Implementation Phase 0-9** describes when work is built. **Timing point P0-P9** describes where a correction/fault is observed or introduced. **Protocol arm P1/P2** describes which mechanisms an experimental system includes. Timing point P1 is not Protocol arm P1. Timing points are intervention/observation landmarks, not values of a single database status.

### Timing points

| Timing point | What the intervention observes |
| --- | --- |
| P0 | Correction begins before original intent acceptance |
| P1 | Original accepted; correction accepted before dispatch authorization |
| P2 | Request dispatched; provider has not committed |
| P3 | Provider committed; acknowledgement withheld |
| P4 | Acknowledgement received; verification incomplete |
| P5 | Verification complete; no claim permit |
| P6 | Claim authorized/generated; not published |
| P7 | Audio published/buffered; not played |
| P8 | Decisive outcome audio is playing |
| P9 | Decisive outcome audio completed before correction |

P1, P2, P3, P5 and P8 are mandatory high-risk landmarks in the original contract. The hidden commit at P3 is the canonical ambiguity case. A hold/release event proves a causal placement more reliably than a guessed timing sleep.''')
fig('10a_timing','Timing panel A: acceptance and commit','''flowchart TB
 P0[Timing P0: before original acceptance] --> P1[Timing P1: accepted; before dispatch]
 P1 --> P2[Timing P2: dispatched; before commit]
 P2 --> P3[Timing P3: committed; response held]
''','These landmarks separate user acceptance, dispatch and external commit. They do not turn an unknown provider outcome into failure.')
fig('10b_timing','Timing panel B: evidence and publication','''flowchart TB
 P4[Timing P4: response; verification unfinished] --> P5[Timing P5: verified; no permit]
 P5 --> P6[Timing P6: claim generated; unpublished]
 P6 --> P7[Timing P7: published; not played]
''','A verified fact, an authorized claim and a published segment remain different facts. In baseline arms the analogous generation boundary may omit a permit object.')
fig('10c_timing','Timing panel C: decisive exposure','''flowchart TB
 P8[Timing P8: decisive content playing] --> P9[Timing P9: decisive content completed]
 P8 --> R[Stop remaining buffer; assess repair]
 P9 --> R
''','A completed old statement was not necessarily false when it played. A later incompatible request may require a new correction; grades use recorded times rather than retroactively rewriting history.')

add('''### Explicit experimental arms

The following cumulative capability table matches `research/arms.py`. Profile flags declare mechanisms; some historical baseline behaviour uses separate drivers rather than independent switches for every flag. The audit documents that limitation. P1/P2 and ordinary null-arm workflows retain the caller-facing permit requirement. B0-B3 permitless audio is marked synthetic research data, blocked from normal audio download/LiveKit transport.

| Arm | Durable identity / verify before retry | Revision invalidation / staging / compensation | Playback tracking | Claim permits / product invariants | Durable repair |
| --- | --- | --- | --- | --- | --- |
| B0 | No declared capability; harness still avoids unsafe unproved retry | No | No | No | No |
| B1 | Yes | No | No | No | No |
| B2 | Yes | Yes | No | No | No |
| B3 | Yes | Yes | Yes | No | No |
| P1 | Yes | Yes | Yes | Yes | No |
| P2 | Yes | Yes | Yes | Yes | Yes |

| Arm | Appointment example and existing protection |
| --- | --- |
| B0 | Best-effort cancel/recreate when outcome is visible; hidden outcome can stop UNKNOWN. It is not forced to retry blindly to manufacture a duplicate. |
| B1 | Reads status/postconditions after the lost response, preserves identity and can cancel/create after discovering 3 PM. |
| B2 | Adds revision-aware transition, atomic reschedule if supported, otherwise linked compensation/create. |
| B3 | Uses competent core recovery, current-revision checks and playback tracking; can stop old segments and give ordinary 4 PM updates. |
| P1 | Adds persisted revision/resource-bound speech permission and revalidation. Tests whether a gap remains after B3's ordinary checks. |
| P2 | Adds persistent responsibility to withdraw exposed incompatible content and deliver a current supported update after interruptions/restarts. |

Removing a mechanism for comparison is an ablation. B3 to P1 isolates permits/product invariants; P1 to P2 isolates durable repair. Earlier baseline comparisons bundle several differences and are not interchangeable causal removals. The contract also proposes separate removals of dispatch/revision checks, accepted-intent durability, status lookup, UNKNOWN, freshness, outbox/leases and playback gates. Redis-only identity or unsafe retry ablations must remain isolated research experiments, never product configuration.

The current v4 main candidate contains only B3/P1/P2. B0/B1/B2 have historical Phase 6/7 drivers and evidence, but no v4 500-input slots. A six-arm extension needs review and a new version. Existing strong B3 checks are retained. Equal observable evidence earns equal observable scores; an obligation row is internal telemetry, not proof of better communication.''')

add('''## 8. Correctness constraints and data model

### Independent operation dimensions

Four independent descriptions are needed (orthogonal dimensions). Processing may have finished while the effect remains unknown; the effect can be present while the instruction is superseded; a current effect may still have no eligible confirmation.

| Dimension | Exact contract values |
| --- | --- |
| Processing phase | DRAFT, READY, DISPATCH_RECORDED, RESPONSE_RECEIVED, VERIFYING, RECONCILING, COMPENSATING, TERMINAL |
| Effect knowledge | NOT_ATTEMPTED, ABSENT, PRESENT, PARTIAL, UNKNOWN, COMPENSATED |
| Applicability | CURRENT, SUPERSEDED, REUSABLE, INCOMPATIBLE |
| Speech eligibility | BLOCKED, PROGRESS_ONLY, CLAIM_PERMITTED, REPAIR_REQUIRED |

For example, an older operation can be RECONCILING / UNKNOWN / SUPERSEDED / PROGRESS_ONLY. A TERMINAL label alone would obscure its unresolved effect. Conversation phase and appointment business status are additional separate fields.''')
fig('11_dimensions','One operation, four independent descriptions','''flowchart TB
 O[Logical operation A] --> P[Processing: RECONCILING]
 O --> E[Effect knowledge: UNKNOWN]
 O --> A[Applicability: SUPERSEDED]
 O --> S[Speech eligibility: PROGRESS_ONLY]
 P --> D[Combined facts; not a linear success pipeline]
 E --> D
 A --> D
 S --> D
''','This is an illustrative permissible combination, not a complete transition specification. Exact persisted enum values and guards are in SQL/domain code; diagrams cannot override them.')
invariants=[('Accepted intent is durable','Only committed acceptance, not a transcript/model message, changes the current request.','4 PM revision survives the browser closing.'),('Stable logical operation identity','Same logical retry keeps ID/key/hash; changed meaning creates linked work.','Lost 3 PM response does not create a fresh identity for the same CREATE.'),('Unknown is not failure','Possible send plus missing result stays UNKNOWN.','Do not announce that 3 PM failed.'),('Reconcile before retry','Read status/resource and apply adapter safe-retry policy before another write.','Find the existing 3 PM effect before moving it.'),('Evidence is revision-bound','Receipt includes revision, predicates, resource version/source and validity.','3 PM evidence cannot prove the new 4 PM request.'),('Speech requires a claim permit','Deterministic authority, not model/tool prose, releases decisive product speech.','A tool 200 cannot directly say "confirmed". Research baseline bypass is isolated.'),('Playback is separate from generation','Queued/published/started/partial/completed are distinct recorded facts.','Generated 3 PM text may never have played.'),('Stale decisive audio creates durable repair','Persist withdrawal/update responsibility after incompatible exposed content in repair-capable paths.','P2 obligation remains after process death.'),('PostgreSQL owns correctness; Redis is disposable','Intent, identity, receipts, permits, jobs and obligations have durable records.','A cache flush cannot be the reason a new duplicate is authorized.'),('The oracle is independent','Expected intent and provider truth, not controller receipt verdict, determine business truth.','A SATISFIED controller result can still be graded wrong.'),('The model proposes; deterministic code authorizes','Validate schema/grounding and inject actor/resource/URLs; no model SQL or direct writes.','Qwen proposes a time; server decides acceptance.'),('Ending a call does not end durable work','Media closure is separate from resolution.','Unknown 3 PM work and repair can remain pending after hangup.')]
add('### The 12 non-negotiable research invariants\n\n'+table(['Invariant','Technical meaning in plain English','Example'],[(f'{i}. {n}',m,e) for i,(n,m,e) in enumerate(invariants,1)]))
add('''### Durable records and constraints

The schema groups identity/calls; immutable intent revisions; operations/attempts/effect ledger/reconciliation jobs; tickets/appointments; receipts/evidence; claims/permits/segments/playback/repair; handoffs; workflow events/outbox/inbox; and research runs/cases/executions/faults/oracle/metrics. Unique command/key constraints and request-hash checks suppress changed-request replay. A PostgreSQL exclusion constraint prevents overlapping active appointments for the same resource. Expected versions avoid stale overwrites.

UTC timestamps retain the original IANA zone and local requested representation. Raw provider events sit beside normalized observations. Request, prompt, configuration, audio and evidence hashes identify what was used; hashes alone do not establish semantic correctness. Outbox rows persist notifications with the mutation; consumer inbox rows support duplicate suppression. Full external notification delivery is not evidenced merely by schema presence.

The original sortable-UUID instruction conflicts with SQL `gen_random_uuid()` defaults. The user explicitly accepted the documented exception: SQL defaults/application UUIDv4 remain. This proposal records that existing decision and does not invent UUIDv7 implementation. Existing migration history stays unchanged; future changes require additive migrations.

Dependency/model/fixture versions must be frozen for a reviewed campaign. Failed traces and first attempts remain in the ledger. If a defect changes the protocol during evaluation, pause, create a new version and restart affected comparisons rather than silently replacing outcomes. The preserved Phase 7 v1 freeze remains historical; it is not a freeze of the revised v4 instrument.''')

add('''## 9. Implementation roadmap and verified current position

The phase reports document accepted historical gates. They do not prove all proposed product functions or production reliability. Later audits revise interpretation without rewriting historical measurements. Some README paragraphs still describe earlier stages; the v2 remedies and v4 candidate are the current measurement/design sources. The background architecture proposal uses a different 0-8 roadmap on page 41. This document follows the authoritative implementation pack Phase 0-9 roadmap rather than merging those numbering systems.

| Implementation phase | Deliverable | Current evidence/status |
| --- | --- | --- |
| 0 | Repository, ADRs, environment and locks | Implemented; historical boot/static gates reported |
| 1 | Schema/local deterministic transaction | Implemented/tested; revision, identity and exclusion checks |
| 2 | Provider simulator and ambiguous recovery | Implemented/tested; lost-response and reconciliation traces |
| 3 | Evidence and claim permits | Implemented/tested; stale/freshness authorization checks |
| 4 | Cascade interfaces and playback-aware repair | Implemented with protocol traces; acoustic alignment/human exposure not established |
| 5 | Browser workspace and local microphone path | Implemented; separate recorded booking/correction publication evidence; route/API limits documented |
| 6 | Arms, barriers, independent oracle and replay | Historical closure: 43 paired fixtures plus one auxiliary witness; 256 verified executions, not independent main inputs |
| 7 | Pilot and historical freeze | 40 instances, 45 versions, 267 executions; descriptive debugging, retained original instrument |
| Between 7 and 8 | Audit, remedies, revised design/calibration | v2 fixes/exploration; v4 candidate reviewable within protocol scope |
| 8 | Main evaluation | Not started; 500 inputs/1,500 slots proposed, no review/freeze receipt |
| 9 | Optional transfer/speech/human studies | Planned optional extensions, not current results |

No evidence was found that a 100-input alternative replaced or was accepted instead of v4. This document retains the 500-input proposal. It does not propose a smaller campaign implicitly.''')
fig('12a_roadmap','Roadmap panel A: implementation and historical pilot','''flowchart TB
 A[Phases 0-2: foundation and durable effects] --> B[Phases 3-5: claims, voice and UI]
 B --> C[Phase 6: research harness]
 C --> D[Phase 7: historical pilot and v1 freeze]
''','These are the implementation and historical pilot stages, with their limited evidence summarized in the table above. Historical gates do not establish all proposed product functions.')
fig('12b_roadmap','Roadmap panel B: candidate and future evaluation','''flowchart TB
 E[Audit remedies v2 and draft v3]
 E --> F[Current: candidate v4 plus calibration]
 F --> G[Next: review decisions and execution plan]
 G --> H[New freeze, then Phase 8 evaluation]
 H --> I[Phase 9: optional transfer studies]
''','The current box is a candidate prepared for review. The arrows after it describe proposed future work, not completed study execution.')

add('''## 10. Proposed evaluation and statistical analysis

First choose new appointment contexts from a declared set of simulator situations. Run each context through all three arms with the same fault schedule and separate resources. Compare the resulting business state and recorded claim/delivery behaviour. A run under three arms gives one paired input, not three independent scenarios.

The exact quantity the experiment aims to measure (estimand) is the standardized arm risk difference over the fixed simulator recipe/context generator and application version. It is not the prevalence of failures among real callers. The 50 recipes are fixed support labels, not 50 randomly selected families. Within each stratum, recipes are drawn uniformly with replacement and contexts independently subject to recipe constraints. Main and calibration IDs, dates and seeds are separate.

### Sampling, pairing and scheduling

| Design item | Proposed v4 decision |
| --- | --- |
| Target population | Declared 50-recipe support combined with its bounded appointment-context generator |
| Sampling unit | One independent input/context draw within stratum |
| Pairing | B3/P1/P2 share the script/fault but get fresh resource bindings and randomized arm order |
| Main allocation | 300 CLEAN; 100 HIDDEN_COMMIT; 60 PLAYOUT; 40 OTHER_BOUNDARY = 500 inputs |
| Planned executions | 500 x 3 = 1,500 first-attempt slots; all NOT_STARTED |
| Independence | Conditional draws, fresh resources and version stability assumed; shared host/processes can still induce dependence |
| Repetition/clustering | Repeated attempts do not increase n; fixed recipe labels are not sampled random clusters; no speaker/recording replication in tone tests |
| Seeds/order | Main 8042041; calibration 8042042; execution shuffle 8042043 |
| Temporal blocks | 20 fixed blocks of 25 input IDs; descriptive omission/order sensitivity, not proof of independent batches |
| Calibration | 50 distinct calibration recipes x 3 arms, separate from main; reruns retained |
| Confirmatory proposal | P2/B3 on two co-primary outcomes plus a separate clean acceptance gate, only after review/freeze |
| Mechanism comparisons | P1/B3 and P2/P1 with declared secondary adjustment; not extra unadjusted primary claims |

Issue/text metadata helps describe inputs but the v4 live driver uses typed desired state. 500 distinct hashes do not establish 500 varied language-understanding trials. Fresh actual appointment contexts, provider conditions and fault ordering define the protocol inputs.

### Outcome definitions and denominators

The oracle separates provider truth, available support and applicability. Baseline support need not be a P1/P2 receipt object. Missing observations/ACKs remain UNKNOWN. A known unsafe event is retained even when other evidence is incomplete. Structural non-applicability is different from missing data.''')
endpoints=[('Correction success','Current externally requested final business state and no forbidden effects; intent correctness checked separately','200 correction inputs; standardized .5 hidden/.3 playout/.2 other','Co-primary'),('Unsupported confirmation','At least one decisive exposed claim lacks applicable support at its publication/exposure time; truth and support recorded separately','100 hidden-commit inputs for co-primary; other exposure descriptive','Co-primary; synthetic exposure proxy'),('Stale confirmation rate','Recorded incompatible decisive predicates compared with revision accepted at the exposure time','Relevant planned playback inputs; missing alignment/exposure UNKNOWN','Secondary/descriptive'),('Duplicate effects','Independent provider truth shows forbidden repeated effect, not just repeated HTTP requests','Applicable effect scenarios; identify resource and logical operation','Diagnostic'),('Unsafe false cancellation','Cancellation statement contradicts known/provider outcome or lacks applicable support','Applicable cancellation semantics; public decisive cancellation enum absent','Contract endpoint; current template coverage limited'),('Clean task success','Correct clean business state with useful supported completed update, not mere absence of unsafe speech','300 CLEAN inputs, paired P2/B3','Separate non-inferiority gate'),('Safe resolution','Permitted completion or evidenced honest durable handoff, reported distinctly','Applicable planned inputs; unresolved effects do not become task success','Contract metric; historical helper, not added v4 primary'),('Outcome coverage','Useful supported decisive update rather than silence/refusal','Applicable task denominator; UNKNOWN evidence not automatic success','Utility guard / diagnostic'),('Supported corrective delivery','Supported completed latest update after a predeclared recovery challenge','33 fixed recovery-challenge inputs; ordinary B3 updates earn equal credit','Key secondary'),('Withdrawal / retraction','Explicit withdrawal of previously exposed incompatible content plus supported current completion','Conditional exposure subset; N/A if no incompatible content needed withdrawal','Descriptive conditional endpoint'),('Complete corrective communication','Supported current delivery and explicit withdrawal when needed; no withdrawal requirement earns credit when update delivered','Same 33 predeclared challenges, not selected on arm exposure','Key secondary fixed denominator'),('Latency','Recorded external script/accepted revision/release/playback anchors and observed/censored completion','Paired appropriate inputs; unresolved delivery censored, not zero latency','Helpers exist; complete v4 latency reporting remains to be frozen'),('Durable repair telemetry','Persisted, discovered, attempted, pending, played or escalated obligation states','Repair-capable paths; baseline lacks row by design','Internal mechanism evidence, not comparative user-facing success')]
add(table(['Endpoint','Definition','Denominator / missingness','Role'],endpoints))
add('''### Event-time anchors and the observation window

The external request's scripted time and the server's accepted-revision time are retained separately. The former measures responsiveness to the externally prescribed correction; the latter determines when current accepted intent changes. Publication uses persisted publication time. Exposure uses recorded client time with separate server arrival time. A late ACK may describe earlier exposure; its late arrival does not make the earlier speech occur later.

V4 caps grading at the earlier of actual export end and final externally scripted request plus 600 seconds. Both client and server receipt times must be inside the administrative cap for eligible ACK evidence. Later raw data is retained but excluded from that grade. Ending an export early cannot prove no later exposure or delivery within 600 seconds. Completion unknown at the cap stays unknown, with censoring and bounds, rather than being relabeled failure/silence/repair completion.

### Statistical methods: question, assumptions and limit

| Method | What it answers | Assumptions and what it cannot prove |
| --- | --- | --- |
| Exact counts / denominators | How many TRUE/FALSE/UNKNOWN/N/A outcomes occurred? | Planned attempt 1 remains primary. Counts alone do not generalize beyond the frame. |
| Exact binomial intervals | How uncertain is a rare event rate? | Appropriate independent conditional inputs; zero observed events does not prove zero risk. |
| Paired win/loss differences | How often does one arm improve or worsen the same input? | Pair by input, not arm-run; account for missing pairs and shared-host effects. |
| Stratum standardization | What is correction difference under the declared fault mixture? | Weights fixed .5/.3/.2; do not pool away strata or use a pooled exact test for a weak average-effect null. |
| Simultaneous component bounds | Conservative uncertainty on the weighted correction difference | Exact bounds on win/loss probabilities with a union-bound adjustment; can be wide. |
| Identifiable marginal model | Which arm/eligible-stratum means and contrasts can be estimated? | Saturated cell means: rank 9/9 correction; rank 3/3 hidden and clean. Phase/fault/revision/action terms are aliased and omitted, not independently estimated causes. |
| Clean non-inferiority | Is P2 clean success no more than 5 percentage points worse than B3? | Conservative paired bound above -0.05, complete pairs and accepted sampling assumptions. Not proof of equality or superiority. |
| Exact paired diagnostic tests | Is stratum-wise paired exchangeability compatible with the data? | McNemar diagnostic null differs from weak weighted-average equality. Do not report pooled diagnostic significance as the weighted effect test. |
| Multiple comparisons | Avoid declaring an advantage from searching many contrasts | Bonferroni .025 per co-primary comparison; Holm over ten declared secondary diagnostics. Missing family p-values leave adjustment unresolved. |
| Missingness bounds | Could unknown outcomes change the conclusion? | Best/worst planned-denominator assignment; no automatic silent/completed imputation. Missing pairs block the candidate clean gate. |
| Block/order sensitivity | Are findings sensitive to run order/shared-host periods? | Omit each fixed block and inspect order/load; does not establish independent batches or cure dependence. |
| Paired latency intervals | How much faster among comparable completed inputs? | Existing bootstrap helpers resample scenario units; selected-complete-pair intervals cannot prove overall speed benefit. |
| Censor-aware survival / AFT | What is time to resolution when some never resolve in-window? | Existing generic Kaplan-Meier/restricted-time and lognormal AFT helpers require censor assumptions/model checks. Lost ACK/handoff may be informative; v4 outcome_report does not wire a full latency analysis. |
| Mixed-effects extension | Model repeated recordings/speakers without inflating n | Existing generic Bayesian helper is not the accepted v4 model; approximate posterior is not a frequentist confidence interval. A real repeated-speech study requires a new identified design. |
| Ablations | Which mechanism first prevents the unsafe action? | Match opportunities/evidence/budgets; bundled differences or manually supplied repair cannot isolate unattended delivery. |

For input i and correction stratum s, let d_i = outcome(P2) - outcome(B3), taking values -1, 0 or +1 for known binary pairs. The proposed correction difference is Delta = 0.5 mean(d_hidden) + 0.3 mean(d_playout) + 0.2 mean(d_other). Higher is better for correction success. For unsupported exposure, lower risk is better. The paired clean lower bound is lower(exact win probability) minus upper(exact loss probability); it must exceed -0.05.

The secondary family contains P1-B3 and P2-P1 on correction, hidden exposure and the two delivery outcomes (eight comparisons), plus P2-B3 on the two delivery outcomes (two). Conditional withdrawal and obligation telemetry remain descriptive. Selection on whether an arm happened to expose stale content would bias a principal delivery comparison; use the fixed challenge denominator instead.

### Precision and power are planning assumptions

Power means the probability that a specified decision rule passes under assumed underlying behaviour. It is not a promised result and these nuisance rates are not estimated from the small pilot.

| Clean inputs | Assumed discordance | True P2-B3 clean difference | Calculated power |
| --- | --- | --- | --- |
| 300 | 3% | 0 points | 96.01% |
| 300 | 5% | 0 points | 80.39% |
| 300 | 5% | -1 point | 55.99% |
| 300 | 10% | 0 points | 44.80% |

At 5% discordance, a normal precision illustration is about +/-2.53 percentage points; the conservative all-ties lower bound is about -1.22 points. This is not an 80%-powered design for all plausible rates. The 33 recovery inputs give only about +/-10.8 points at 10% discordance in a normal illustration, so rare delivery failures may remain imprecise. Review must accept these limits or specify a new candidate allocation before freeze.

### Analysis pipeline readiness

V4 integrates the revised oracle and endpoint-specific binary analysis in `research/study_v4/pipeline.py`; it explicitly rejects CAMPAIGN evidence without a reviewed freeze. Rank and exact-power checks, label/equivalence tests and bounded late-ACK/window checks have retained results. The empty main analysis has no outcomes and cannot issue a confirmatory claim. Generic latency helpers and prior mixed-model diagnostics are available separately, but their presence is not proof of full v4 latency ingestion, censor validation or model adequacy. Review must specify whether those are descriptive reports or a required separately validated campaign component.

Any infrastructure failure, timeout, exclusion reason or rerun is retained with attempt identity and source/configuration hashes. A successful debugging rerun does not replace an unsuccessful first planned outcome. Main success/failure is not inferred from the calibration driver's COMPLETED status.''')
fig('09a_evaluation','Evaluation panel A: controlled execution','''flowchart TB
 S[Versioned external script / scenario] --> R[Paired arm drivers: B3 / P1 / P2]
 F[Named faults and barriers] --> R
 R --> A[Application records / observations / ACKs]
 R --> P[Provider simulator]
 P --> T[(Separate append-only truth log)]
 R --> B[Replay evidence / failed attempts]
''','Drivers use the same scenario and comparable faults across arms. The separate truth log describes effects; application records describe what the agent could observe. Failures are retained.')
fig('09b_evaluation','Evaluation panel B: independent grading and analysis','''flowchart TB
 S[External scenario specification] --> O[Independent observable oracle]
 A[Application observations / ACKs] --> O
 T[Simulator truth log] --> O
 O --> G[Separated outcomes and missingness]
 G --> N[Paired analysis and uncertainty]
''',"The oracle can disagree with the application's verifier. Calibration tests boundary placement; main outcomes would answer the proposed conditional comparisons. Neither layer turns tone metadata into proof of human hearing.")

add('''## 11. Current evidence, audit remedies and results

### Historical pilot remains historical

Phase 7 v1 contains 40 fresh instances, 45 versions and 267 executions. Five extra acoustic versions share one instance and do not add independent scenarios. The six historical profiles were not all applicable to every primary case. Reported B3/P1/P2 correction success tied at 29/35; clean success tied at 5/5; post-commit unsupported confirmation tied at 0/21. Repair telemetry separated the profiles in selected cases. Those are original instrument measurements, retained despite later construct-validity fixes; they should not be treated as revised main evidence.

The audit found arm-dependent grading, inaccurate decisive-span treatment, truth conflated with available support, synthetic timestamps and incomplete recovery demonstrations. A successful historical replay only verifies the historical instrument consistently; it does not validate its measurement construct. The 112 reviewed unsuccessful/unsafe pilot traces are retained. The tiny clean sample did not establish a 5-point clean tolerance.

### What the remedies changed and proved

| Audit finding | Revised remedy and supported scope |
| --- | --- |
| Arm-dependent grades | Observable grader ignores arm label and internal receipt/repair representation; behavioural equivalence and label invariance checked. |
| Late-ACK leak | Pre-fix real PG traces showed B3 409 constraint failures and P1 erroneous repair persistence. Shared capability rules and migration 0013 now constrain both revision and ACK paths. |
| Intro mistaken for confirmation | Two-word intro control retained; decisive status/time/date/zone boundaries separate. Eight words reach 3:00 PM in the template. Equal-duration alignment is a proxy. |
| Truth confused with support | Independently grade provider truth and observations available at publication/playback; version and freshness applicability separate. |
| Mechanisms not exercised | Normal stale-claim/freshness paths, delayed ACK, repeated revision and missing completion tested with retained traces. |
| No repair discovery consumer | Migration 0012 leases plus enabled startup consumer discover pending P2 rows after actual worker restart. Completion still needs testimony. |
| Incomplete evidence/budgets | Revised frozen v2 exploratory plan, v4 separate hook and budget calibration with raw provider exports. |
| Dependence and main readiness | v4 declared fixed-frame target and identifiable model; sampling/stationarity/scope decisions still require review. |
| Oracle access boundary | Optional oracle token protects HTTP truth route in revised isolated runtime; not OS isolation or automatic hardening of every legacy deployment. |

Seven-label and actual trace regrading tests address arm neutrality. Duplicate/lower-progress/delayed ACKs preserve evidence and merge safely. The verifier now supports the bounded CREATE -> RESCHEDULE -> RESCHEDULE chain used by the third-revision tests; deeper unsupported chains stay UNKNOWN. These are scoped repairs, not universal workflow semantics.

### All 18 planned revised exploratory outcomes

Six deliberately chosen fixture families were run once each under B3/P1/P2. All procedural slots completed without harness failure/timeout/missing slot, but not all business tasks succeeded. T=TRUE, F=FALSE, U=UNKNOWN, N=NOT_APPLICABLE. Trace links refer to the retained v2 planned run, not a calibration rerun. Retraction is a separate endpoint from stale exposure: earlier incompatible time content may have been exposed before acceptance and therefore need withdrawal without counting as post-acceptance stale exposure.''')
rows=list(csv.DictReader((ROOT/'artifacts/research-remedies/v2/exploratory-outcomes.csv').open(encoding='utf-8-sig')))
short={'TRUE':'T','FALSE':'F','UNKNOWN':'U','NOT_APPLICABLE':'N','True':'T','False':'F'}
add(table(['Case/arm','Business','Stale','Update','Retract','Repair persisted/completed','Evidence'],[(r['fixture']+'/'+r['arm'],short[r['final_business_state_correct']],short[r['incompatible_stale_exposure']],short[r['correct_final_update']],short[r['explicit_retraction']],r['repair_persisted']+'/'+r['repair_completed'],f'[trace](<{Path(r["trace_path"]).as_posix()}>)') for r in rows]))
add('''| Fixture | First relevant mechanism and interpretation |
| --- | --- |
| E1: correction after verification / attempted stale claim | B3 current-revision synthesis check and P1/P2 authorization reject stale publication (409). Business/safety tie; no extra protection demonstrated. |
| E2: resource change after publication | B3 revision-only start permits a factually true but version-inapplicable statement. P1/P2 freshness/start check rejects. Missing accepted playback testimony stays UNKNOWN, not assumed silence. All three hit provider conflict and fail business completion. |
| E3: decisive partial playback / delayed ACK | Shared stop and uniform capability rules; late client time precedes acceptance, so not post-acceptance stale exposure. P2 persists repair/retracts; B3/P1 give ordinary updates. |
| E4: worker restart after persistence | P2 native discovery publishes without a supplied obligation ID. All arms' final updates complete; publication/recovery does not prove comparative autonomous delivery. |
| E5: missing completion and logical reconnect | Before ACK completion, update is UNKNOWN and repair pending. Later duplicate-safe completion closes P2 obligation. This is not a measured WebRTC outage. |
| E6: another revision during repair | Old completion cannot close new revision repair. All arms retain scripted stale r2 exposure after r3, then update r3; P2 completes two retargeted obligations. |

**Final business correctness ties at 5/6 in every arm.** Correct final updates are five TRUE/one FALSE in B3 and five TRUE/one UNKNOWN in P1/P2. P2 has four TRUE retractions and five completed obligation rows. That demonstrates extra accountable correction in these selected fixtures, not a population advantage or improved business success. All revised executions are typed-intent/tone semantic proxies.

### V4 separate qualification, not main-study results

The ledger retains 150 planned calibration slots, three smoke runs and 25 amendments: 178 recipe/arm executions. Driver statuses are 139 COMPLETED and 39 FAILED. Failures include 36 normal-path HTTP 409 refusals and three original timezone validation errors. All exports pass revised evidence adaptation, but qualification is not a business success score. Amended runs qualify previously incomplete placement while unsuccessful originals remain visible.

All 150 recipe/arm boundary slots have qualifying evidence in the scoped ledger. Duplicate-after-response was an inert unsupported label; the new v4 fixture uses actual duplicate request delivery before commit with idempotent replay and one truth effect. Reorder means one held response crossing revision acceptance, not two-response permutation. Redis flush means a reserved companion-cache negative control, not loss of an application-consumed cache. Original and amended fixture/source hashes make those changes visible.

The eleven budgets have boundary evidence: provider/scheduler/driver socket timeouts 30/15/40s; provider barrier 120s; core/repair lease expiry 180/30s; eight reconciliation attempts; 30 drain passes; permit TTL 30s; recovery observation 40s; main administrative horizon 600s. Drain exhaustion uses an artificial nonprogressing adapter, not a PG transaction proof. Native recovery and natural lease/permit expiry use real PG. The long collector finished at 601.641s; grading retains the 600s deadline rather than crediting late results. Its parallel barrier branch initially failed with a KeyError and is retained; a separate corrected 120s barrier probe qualified.

V4 reported 118 unit/contract checks, seven scientific checks and six selected PG integration checks. These are named disjoint command results within that validation set, not a lifetime sum. Do not add Phase 7/remedy/regression totals from overlapping runs. Ruff and strict mypy pass in the retained v4 logs. Source image/package pins are not a guarantee of current external services.

V2's 273-file inventory overlaps v4's 450-file inventory. This review verified 450 historical hashes and 282 candidate source hashes unchanged.''')

add('''## 12. Limitations and threats to validity

**Protocol behaviour versus human exposure.** A scripted ACK says what a client reported. A tone with a sentence attached as metadata does not say that sentence. Equal-duration word spacing is not phonetic alignment. Human hearing/comprehension cannot be inferred from generation, publication or ACKs. Actual speech conclusions need intelligible audio, suitable independent alignment and real client/device playback capture; human belief additionally needs an approved participant study.

**Historical local voice evidence.** The separate Phase 5 acceptance sends recorded speech through LiveKit and checks a verified 3 PM booking, 4 PM correction and two permit-bound publications. It supports that restricted local audio/proposal/control path. It does not measure human hearing, broad ASR performance or the revised fault set. The pilot's recorded successful condition is restricted lexical/date extraction plus Qwen, not general model reasoning. Five synthetic acoustic conditions failed recognition safely. Those failures remain outcomes, not successful voice capability.

**Publication versus delivery.** Native P2 restart discovery and publication are demonstrated. B3/P1 receive ordinary response opportunities; the instrument does not establish unattended comparative superiority over a deployed baseline responder. A persisted repair row and a published segment are not completed communication. Unknown completion at disconnect or horizon remains unknown.

**Boundary qualification versus full certification.** Each hook proves a particular placement/scope, not every network fault, real cache outage, production provider or restart combination. A failing/409 run may qualify the refusal boundary while its requested business task remains unsuccessful. The oracle HTTP token is not an operating-system trust boundary.

**Synthetic frame versus callers.** Main inputs are independent conditional context draws over fixed recipes, with shared infrastructure. Recipe/speaker novelty, natural correction prevalence, multilingual recognition, latency in real calls and human beliefs are outside the candidate estimand. Fixed blocks do not establish independence; same-host load and restarts can violate stationarity.

**Construct and analysis limits.** The template withdrawal matcher is fixed, not a general semantic evaluator. B0-B2 driver fidelity differs from core workers. Some profile flags describe capability rather than isolated switches. Safe resolution/cancellation/latency have narrower wiring than the headline contract. V4 cell means avoid aliased factors but cannot estimate their independent causal effects. Conservative bounds and the 33-case recovery subset may be too imprecise for a small benefit. A tie or unresolved interval must be reported honestly.

**External validity and deployment.** Only the local simulator is the research provider. Telephony, human dialer/transfer, natural native audio, production authentication/high availability/backups and full telemetry are not demonstrated. RBAC/RABAC, medical workflows and emergency automation remain excluded. A polished dashboard does not establish reliability or a novel scientific contribution.''')

add('''## 13. Where the project is waiting, and finite next steps

The latest verdict is "reviewable candidate, not frozen." Most earlier design defects have concrete candidate remedies and retained qualification evidence. The following table separates reviewer decisions from genuinely unfinished execution preparation. It does not require new optional product features to finish the core protocol study.''')
blockers=[('Conditional sampling frame and stationarity','50-recipe frame, distinct contexts, pair order and 20 blocks','Accept the conditional protocol target and dependence assumptions, or specify a new version','Reviewer acceptance','Written approved target and scope; no caller-generalization claim'),('Three-arm comparison scope','All 500 inputs have B3/P1/P2 slots; B0-B2 historical drivers','Accept incremental comparison scope or request separately planned six-arm extension','Reviewer acceptance/design','Frozen manifest names all compared arms and justified limits'),('Clean margin and power sensitivity','300 clean; exact grid; 5pp tolerance; conditional 80.39%','Accept tolerance/nuisance assumptions or revise allocation before outcomes','Reviewer acceptance/design','Prespecified margin, allocation and decision criterion approved'),('Multiplicity and endpoint model','Rank 9/3/3, paired bounds, ten secondary diagnostics','Approve roles and null interpretations; avoid diagnosing weak average effects with pooled exact tests','Reviewer acceptance/analysis','Frozen estimands, comparisons and methods consistent'),('Recovery comparison opportunity','Native P2 discovery; ordinary baseline updates credited; 33 challenges','Accept limits or separately calibrate a matched unattended-responder design','Reviewer acceptance; optional calibration for stronger claim','Claim wording matches the actual opportunity and horizon'),('Observation scheduling / isolation','600s cap; worst sequential 250 hours; fixed order','Specify isolated restart scenarios, resource/CPU/storage budgets and observation collection; validate any proposed concurrency','Execution planning/calibration','Comparable scheduled collection reaches required horizons; shared fault cannot leak into another input'),('Early terminal rule','Early export is incomplete; late raw evidence kept','Keep full window or justify/test a termination rule preserving each endpoint','Reviewer acceptance/calibration','No earlier stop silently turns late effects into absence'),('Complete reporting scope','Binary v4 pipeline validated; generic latency/safe-resolution helpers separate','Declare diagnostic latency/cancellation limits, or wire/validate required reports before campaign launch','Analysis/reviewer acceptance; integration if required','All promised outputs have qualified ingestion and assumptions; unsupported endpoints expressly deferred'),('Reviewed freeze and campaign activation','Null review_receipt/freeze_hash; CAMPAIGN ingestion blocked','After review and scheduling, version/fingerprint protocol and enable a reviewed driver','Reviewer acceptance, then implementation','New approved freeze, drift guard and accounted 1,500 slots; launch only on user authorization')]
add(table(['Decision/blocker','Available evidence','Exact remaining action','Type','Completion condition'],blockers))
add('''### The 600-second scheduling issue

1,500 executions x 600 seconds / 3,600 = **250 hours**. This is a maximum sequential observation-time calculation, not measured campaign runtime. Actual operations may finish sooner, but finishing a command does not establish absence of a later effect or late ACK.

Unrestricted safe parallel main execution has not been validated. Worker restart, shared-process faults, held barriers and database binding require isolation so one arm/input does not alter another. A separate runtime/resource design could make some observation collectors overlap, but that must be tested and reviewed before launch. Fixed blocks and shuffled order cannot replace isolation.

Shortening the observation window changes which late effects and corrections count. An early stopping rule could therefore change the estimand or missingness. Keep the full cap unless a reviewed terminal-evidence rule proves the relevant endpoint cannot change. Do not silently trade a shorter runtime for missed unsafe behaviour.

### Optional improvements, not current freeze requirements

Natural speech/playback and human belief studies, a production provider, stronger native-audio comparison, telephony/dialer/transfer, broader workflow chains and full telemetry are separate extensions. They require different evidence but are not automatically blockers for the narrowed typed/tone protocol claim. A 100-input alternative has not been accepted and is not substituted here.

### Deliverables and success criteria

The core research deliverable is a reproducible protocol instrument, a transparent comparative study under the reviewed conditional frame, uncertainty/missingness analysis, and documented scope. Success can be a tied or negative result that identifies when ordinary checks already suffice. A claim of novelty would additionally require a defensible full-text comparison and empirical separation that is not an artefact of grading, weakened baselines or unequal delivery opportunities.''')

add('''## 14. Supervisor discussion checklist

- Is the central question narrow enough, and is B3 a competent comparator?
- Are the fixed protocol population and typed/tone evidence acceptable for this FYP?
- Are the two co-primary outcomes and 5pp clean tolerance suitable?
- Is the conditional power grid adequate, including lower power at higher discordance?
- Is the three-arm scope accepted, with B0-B2 clearly historical?
- Are repair delivery and explicit withdrawal measured separately from internal rows?
- Are ordinary baseline response opportunities fair, and are unattended claims limited?
- Are missingness, first attempts, reruns and the 600s horizon frozen consistently?
- Is isolation/concurrency scheduling qualified before the main run?
- Which latency/cancellation/coverage outputs are mandatory rather than descriptive?
- What real speech or human study evidence would be needed for stronger claims?
- Does the literature comparison support only a hypothesis, or a genuinely established distinction?
- Has a new review/freeze been approved, with no changes to historical evidence?

## 15. Glossary

| Term | Plain-English meaning |
| --- | --- |
| Accepted revision | A validated request committed as the current instruction |
| Ambiguous outcome | A request may have worked, but its result is not known |
| Idempotency | Repeating the same logical request does not create another effect under declared provider semantics |
| Reconciliation | Read what actually happened before deciding the next safe action |
| Compensation | An action amending an earlier effect without pretending history disappeared |
| Verification receipt | Durable record of checked predicates and the evidence/time/version supporting them |
| Claim permit | Authorization for a specific deterministic outcome statement |
| Playback acknowledgement | Client testimony about segment progress, not proof of hearing |
| Repair obligation | Persistent responsibility to withdraw incompatible content and deliver a current supported update |
| Independent oracle | Grader using separate provider truth and external expectations |
| Estimand | Exact quantity a comparison aims to measure |
| Stratum | A prespecified group of related input situations |
| Paired input | The same scenario/context evaluated across arms |
| Non-inferiority | A rule asking whether clean utility is no worse than a prespecified tolerance |
| Censoring | Resolution was not observed within the available time; duration is not completed latency |
| Ablation | Experimental removal of a mechanism to understand what it adds |

## 16. Factual gaps and unresolved evidence

1. No accepted v4 review/freeze receipt or main outcome exists; no 100-input replacement approval was found.
2. A full matched unattended baseline/P2 delivery study, real WebRTC reconnect under the revised faults, independent phonetic alignment and human hearing/comprehension are not established.
3. Application-consumed Redis outage and two-provider-response permutation are not certified by the v4 controls.
4. Full v4 latency/censoring ingestion and required safe-resolution/cancellation reporting are not wired in outcome_report; reviewer scope must be explicit.
5. The exact installed eSpeak package version/current running container inventory, remote CI outcome and production deployment readiness were not established from repository locks.
6. Some recent related-work entries were verified at primary record/abstract level rather than exhaustive full text. Missing described topics are not established omissions. Private uploaded faculty/discussion references in the old proposal were not independently recovered/verified and are not used to claim novelty.

## 17. Evidence index and references

The evidence index below maps important claims to actual sources. The companion `evidence-index.md` includes file fingerprints and trace links. The bibliography uses verified citations L1-L14; individual related-work tables state the review depth. Local absolute links resolve in this workspace; external primary-source links remain portable. A shared copy must carry the linked trace/source bundle or readers will need repository access.
''')
claims=[('E01','Actual current status and allocation','artifacts/phase-8-study-design/v4/review-decisions.json'),('E02','All 1,500 main slots unstarted','artifacts/phase-8-study-design/v4/main-slots.json'),('E03','Latest scoped readiness and calibration counts','artifacts/phase-8-study-design/v4/phase-8-report.md'),('E04','All boundary attempts and qualification scope','artifacts/phase-8-study-design/v4/calibration-qualification.json'),('E05','Budget qualification evidence','artifacts/phase-8-study-design/v4/budget-qualification.json'),('E06','50-recipe sampling and 500/50 separate banks','research/study_v4/design.py'),('E07','Power and identified rank calculations','artifacts/phase-8-study-design/v4/analysis-design.json'),('E08','Endpoint-specific paired bounds and missingness','research/study_v4/analysis.py'),('E09','Revised time-capped oracle and delivery','research/study_v4/oracle.py'),('E10','Main ingestion blocked until review/freeze','research/study_v4/pipeline.py'),('E11','Historic Phase 7 counts and limited results','artifacts/phase-7-report.md'),('E12','Audit findings and runtime arm fidelity','artifacts/research-readiness-audit.md'),('E13','Remedies, full 18 outcomes and first blockers','artifacts/research-remedies/v2/phase-7-report.md'),('E14','18 raw business/exposure/delivery outcomes','artifacts/research-remedies/v2/exploratory-outcomes.csv'),('E15','Six pre-fix PG late-ACK reproductions','artifacts/research-remedies/v2/debug/pre-fix-late-ack.json'),('E16','Startup repair discovery and leasing','apps/durable_worker/repair.py'),('E17','Automatic consumer enablement, core service scope','apps/durable_worker/main.py'),('E18','Core operation leases/dispatch/reconciliation','apps/durable_worker/phase2.py'),('E19','Uniform repair capability at DB boundary','database/migrations/versions/0013_readiness_repair_capability.py'),('E20','Durable delivery lease addition','database/migrations/versions/0012_readiness_repair_delivery.py'),('E21','Repair and semantic span rules','packages/speech_policy/phase4.py'),('E22','Independent revised outcome grading','research/oracle/readiness_v2.py'),('E23','Application/voice path and baseline transport exclusion','apps/voice_worker/livekit_transport.py'),('E24','Restricted local STT/model/TTS integrations','apps/voice_worker/offline_adapters.py'),('E25','Historical recorded booking/correction publication','artifacts/phase-5-live-voice.json'),('E26','Actual browser routes and polling/evidence UI','apps/web/components/live-call.tsx'),('E27','Declared explicit arm capabilities','research/arms.py'),('E28','Research questions, timings and original metrics','docs/04_TEST_EVALUATION_AND_TRACEABILITY.md'),('E29','Exact persisted enums and exclusion constraints','database/001_initial_schema.sql'),('E30','HTTP/API contract','contracts/openapi.yaml'),('E31','Event envelope contract','contracts/event-envelope.schema.json'),('E32','Source conflicts and UUID/public route exceptions','docs/06_SOURCE_CONFLICT_REPORT.md'),('E33','Current candidate sampling/design document','docs/12_PHASE8_CANDIDATE_V4.md'),('E34','Actual local services and ports','compose.yaml'),('E35','Python exact resolved versions','uv.lock'),('E36','Frontend exact resolved versions','pnpm-lock.yaml'),('E37','JSON log context fields','packages/observability/logging.py'),('E38','Telemetry scraping scaffold','deployment/prometheus.yaml'),('E39','CI definition, not proof of remote run','.github/workflows/ci.yml'),('E40','Historical fingerprints verified during v4 work','artifacts/phase-8-study-design/v4/preservation-verification.json'),('E41','Arm neutrality/window/design unit checks','tests/unit/test_phase8_candidate_v4.py'),('E42','Real PG late-ACK/stale-claim/privacy checks','tests/integration/test_phase8_candidate_v4_postgres.py'),('E43','V4 independent scientific rank/power checks','research/study_v4/scientific_checks.py'),('E44','Generic censor-aware helpers, not v4 accepted latency model','research/study/statistical_models.py')]
claims.extend([('E45','Local microphone uses local SQL commit, not external fault driver','apps/voice_worker/live_agent.py'),('E46','Readable implementation guide: original twelve invariants','E:/FYP Project/BUILD/Commit_Aware_Voice_Agent_LLM_Implementation_Guide.pdf'),('E47','Background literature and differing roadmap','E:/FYP Project/BUILD/FYP_Research_Backend_Architecture_Proposal.pdf')])
add(table(['ID','Claim / status source','Actual file'],[(i,c,link(p,'open source')) for i,c,p in claims]))
traceexamples=load('artifacts/phase-8-study-design/v4/trace-examples.json')
for key,p in traceexamples.items():
    if isinstance(p,str): add(f'**{key.replace("_"," ")}**: {link(p.replace(chr(92),"/"),"retained trace")}.')
add('### Verified bibliography\n\n'+'\n\n'.join(f'**{p[0]}** [{p[1]}]({p[2]})' for p in papers))
add('''## Final factual verdict

**Established within limited local scope:** durable accepted revisions and operation identity; explicit ambiguous outcomes and reconciliation; revision/resource-bound permits; corrected arm-neutral measurement; selected late-ACK/restart/revision repair paths; reproducible independent simulator evidence; and a calibrated v4 candidate design.

**Still hypothetical:** incremental population benefit beyond competent B3, clean-case non-inferiority in the main study, reliable real-speech corrective exposure, comparative unattended delivery, and a novel contribution against prior work.

**Exactly next:** review the conditional frame, arms, endpoints, tolerance/power and recovery limits; settle and qualify isolated observation scheduling and promised analysis outputs; record a new reviewed freeze; only then authorize and execute the accounted 500-input campaign. No main campaign has started.''')

text='\n\n'.join(sections)+'\n'
(OUT/'research-proposal.md').write_text(text,encoding='utf-8')
evidence='# Evidence index\n\nDocumentation review only; no experiment launched.\n\n'+table(['ID','Claim','Source'],[(i,c,link(p)) for i,c,p in claims])
evidence+='\n\n## All 18 exploratory traces\n\n'+table(['Fixture','Arm','Trace'],[(r['fixture'],r['arm'],f'[open trace](<{Path(r["trace_path"]).as_posix()}>)') for r in rows])
(OUT/'evidence-index.md').write_text(evidence+'\n',encoding='utf-8')
fingerprints={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for _,_,p in claims}
(OUT/'source-fingerprints.json').write_text(json.dumps(fingerprints,indent=2)+'\n',encoding='utf-8')
(OUT/'supervisor-checklist.md').write_text('# Supervisor discussion checklist\n\n'+text.split('## 14. Supervisor discussion checklist\n\n')[1].split('## 15.')[0],encoding='utf-8')
(OUT/'factual-gaps.md').write_text('# Factual gaps\n\n'+text.split('## 16. Factual gaps and unresolved evidence\n\n')[1].split('## 17.')[0],encoding='utf-8')
overview='''# Commit-Aware Voice Agent: one-page overview

**What is the project?** A voice appointment agent that keeps track of what the caller now wants, what the provider actually did, and what the agent may safely say.

**The example.** You request maintenance at 3 PM. The provider books it but its reply is lost. You then ask for 4 PM. A timeout does not prove that 3 PM failed. Repeating the request could create another booking; stopping the assistant does not undo the first booking.

**How it works.** The server saves each accepted request in PostgreSQL. It records a stable operation before sending. If the result is uncertain, it checks the provider before another write. It then moves or compensates the old booking, verifies the current result and authorizes a specific confirmation. The model proposes the request; it cannot directly book or declare success.

**What if old speech already played?** The proposed full protocol records a persistent obligation to withdraw incompatible content and deliver a supported current update. Restarting a worker must not erase that responsibility. Sending audio is different from completed playback, and a client acknowledgement does not prove human understanding.

**What is the research question?** When do those additional rules protect a caller beyond a competent baseline's ordinary checks? B3 is that strong baseline; P1 adds bound speech permissions; P2 adds persistent corrective responsibility. Equal observable behaviour must receive equal grades.

**What is established?** Local code and PostgreSQL tests exercise revisions, unknown outcomes, permits, playback records and repair discovery. The revised six-fixture set ties at 5/6 business success in all three arms. Selected tests show extra freshness checks and explicit P2 withdrawal, not general superiority.

**What is proposed next?** A candidate with 500 new typed/scripted inputs: 300 clean, 100 hidden commit, 60 playback and 40 other. Three arms mean 1,500 planned executions, not 1,500 independent scenarios. All are unstarted. Calibration is separate. The target is a fixed simulator mixture, not real callers.

**What remains?** Supervisor review of scope, assumptions, power and observation scheduling, then a new freeze before evaluation. Real speech exposure, human understanding, general superiority and novelty remain unproven. The app is a research instrument; telephony transfer and a built-in dialer are future product work.
'''
(OUT/'plain-english-overview.md').write_text(overview,encoding='utf-8')
print(json.dumps({'proposal_words':len(text.split()),'diagrams':len(list((OUT/'diagrams').glob('*.mmd'))),'main_slots':len(slots),'main_started':False}))
