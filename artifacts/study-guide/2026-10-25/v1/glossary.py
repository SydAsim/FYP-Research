"""Beginner definitions specific to the study, not executable protocol rules."""

from __future__ import annotations

GLOSSARY: list[tuple[str, str]] = [
    (
        "Ablation",
        "A comparison that removes an implemented component/package to inspect its increment. "
        "Our P1/P2 comparison removes P2's repair package, not only its database persistence.",
    ),
    (
        "Accepted intent",
        "A validated request version formally recorded by the backend. A model proposal or "
        "partial transcript has not necessarily crossed this boundary.",
    ),
    (
        "ACK / acknowledgement",
        "A report that something was received or progressed. Provider acknowledgement and "
        "client playback acknowledgement are different events with different meanings.",
    ),
    (
        "ACID",
        "Atomicity, consistency, isolation and durability: properties of local database "
        "transactions. They do not automatically extend across an unrelated opaque provider.",
    ),
    (
        "Admission",
        "Allowing the next saved execution to start after relevant authority, evidence, "
        "source, budget, resource and deadline guards pass.",
    ),
    (
        "AFT",
        "Accelerated-failure-time model: describes event time multiplicatively. Our accepted "
        "fit uses a lognormal form with arm and stratum terms, under qualified assumptions.",
    ),
    (
        "Agent",
        "Software coordinating actions toward a request. In the main campaign, structured "
        "intents bypassed the language model's proposal ability.",
    ),
    (
        "Alignment",
        "A mapping between content such as a word and its audio/time position. Scripted "
        "indexes do not establish accurate alignment of intelligible speech.",
    ),
    (
        "API",
        "Application programming interface: agreed commands, inputs, outputs and error "
        "semantics between components.",
    ),
    (
        "Append-only truth log",
        "Provider simulator history that adds committed facts without silently replacing old "
        "ones. It lets the independent oracle reconstruct what occurred.",
    ),
    (
        "Arm",
        "An explicit experimental configuration, here B3, P1 or P2. It is not a model brand, a "
        "participant, or a fault timing phase.",
    ),
    (
        "Artifact",
        "A retained research output such as source, data, manifest, trace or report. A local "
        "artifact is not automatically publicly accessible.",
    ),
    (
        "Attempt",
        "A specific planned attempt identity. Main originals remain attempt 1; separately "
        "labelled diagnostic reads/runs do not replace them.",
    ),
    (
        "Authority",
        "Recorded permission and policy binding for an action. In the protocol it can concern "
        "claims; operationally it concerns reviewed deployment/launch limits.",
    ),
    (
        "BACKED_UP",
        "A research ledger retention state. It says evidence reached the verified backup step, "
        "not that the appointment or communication succeeded.",
    ),
    (
        "Baseline",
        "The comparison system. A competent baseline includes meaningful known safeguards so a "
        "proposed feature is not rewarded for beating an artificially weak system.",
    ),
    (
        "Barrier",
        "Named wait/release event at a specific workflow boundary. More precise for race tests "
        "than hoping a fixed sleep produces the intended ordering.",
    ),
    (
        "Binding",
        "A recorded association between identities, versions or evidence. Its strength depends "
        "on what actually generated and verified the association.",
    ),
    (
        "Bootstrap",
        "A computational method that resamples observed units. Our timing analysis keeps an "
        "input's three arms together; resampling cannot manufacture independence.",
    ),
    (
        "Budget",
        "An explicit limit, possibly monetary, time-based, storage-based or action-count "
        "based. Always state its unit.",
    ),
    (
        "B3",
        "Competent baseline with idempotency, reconciliation, revision invalidation, staging, "
        "compensation and playback tracking, plus ordinary evidence checks and corrective "
        "statements.",
    ),
    (
        "Candidate",
        "A proposed version awaiting the relevant review. A candidate's existence does not "
        "itself authorize freeze, deployment or research execution.",
    ),
    (
        "Censoring",
        "The exact event time is not established within the observation basis. Censoring is "
        "not proof the event is impossible or never happens.",
    ),
    (
        "Claim",
        "A consequential assertion, such as a booking confirmation or cancellation. Its exact "
        "predicate matters; 'created again' and 'rescheduled in place' are not identical.",
    ),
    (
        "Claim permit",
        "Scoped deterministic permission for a specific claim using applicable evidence. It is "
        "not an external provider commit or universal proof of truth.",
    ),
    (
        "Clean case",
        "An input in the planned ordinary-work stratum, used to assess useful task completion "
        "without the non-clean fault challenge.",
    ),
    (
        "Cluster",
        "Observations treated together because they share a unit. Here an input carries "
        "B3/P1/P2 results; there can also be unmodeled family/host/time dependence.",
    ),
    (
        "Co-primary",
        "One of the two prespecified main comparison questions. Secondary findings were not "
        "retroactively promoted because they looked more favorable.",
    ),
    (
        "Collector",
        "Instrument code retaining observations through the saved deadline, including after a "
        "driver return or recognized refusal.",
    ),
    (
        "Commit",
        "Durable external/local state change at a defined boundary. In this title it primarily "
        "means transactional effect, not merely a Git source-code commit.",
    ),
    (
        "Compensation",
        "An additional action intended to address a prior external effect. It can fail and "
        "does not erase history.",
    ),
    (
        "Complete corrective communication",
        "The declared supported-update plus explicit-withdrawal criterion when relevant, "
        "evaluated on fixed eligible recovery inputs. Its wording matcher is narrow.",
    ),
    (
        "Confidence interval",
        "Range produced by a procedure with a claimed repeated-sampling coverage property "
        "under assumptions. It is not automatically a probability that a fixed parameter lies "
        "inside this particular interval.",
    ),
    (
        "Confirmatory",
        "An interpretation based on planned questions and satisfied inferential requirements. "
        "The retained helper claim guards remain restricted.",
    ),
    (
        "Construct validity",
        "Whether a measure captures the intended underlying idea. A fixed prefix may measure a "
        "message format more narrowly than general belief repair.",
    ),
    (
        "Context draw",
        "One generated appointment context from the declared fixed recipe frame. It is the "
        "conditional sampling unit, not a naturally sampled caller.",
    ),
    (
        "Controller",
        "Application process validating commands and coordinating accepted domain decisions. "
        "Its belief is not the independent provider truth.",
    ),
    (
        "Convergence",
        "An optimizer satisfying its numerical stopping conditions. It does not validate the "
        "model form or causal interpretation.",
    ),
    (
        "Correction success",
        "Frozen endpoint checking successful correction to the accepted final target. Eligible "
        "for the 200 non-clean inputs, not all 500.",
    ),
    (
        "Cross-tab",
        "Counts of combinations of two recorded variables, such as raw FAILED versus correct "
        "final business state.",
    ),
    (
        "Decisive content",
        "Words conveying an outcome or relevant time rather than introductory filler. Scripted "
        "word-index evidence is the study's proxy.",
    ),
    (
        "Dependency",
        "Something a piece of work relies on. It can mean data/control lineage in a workflow "
        "or a software package needed by a runtime; distinguish them.",
    ),
    (
        "Deterministic",
        "Defined code rules decide from relevant inputs, instead of relying on unconstrained "
        "model prose to authorize consequences.",
    ),
    (
        "Diagnostic p-value",
        "A test output interpreted with its specific null, missingness and dependence "
        "limitations. It is not a probability the paper is correct.",
    ),
    (
        "Discordant pair",
        "A matched input on which two arms differ in the binary outcome. The observed business "
        "correction comparison has no discordant pairs.",
    ),
    (
        "DOI",
        "Persistent scholarly identifier assigned through an appropriate registration route. A "
        "local PDF or ordinary web URL does not create one.",
    ),
    (
        "Drain pass",
        "One iteration of the reviewed drain process. The limit is 30 passes, not 30 seconds.",
    ),
    (
        "Driver",
        "The program issuing the scenario's actions. Raw driver completion differs from "
        "independent business or speech success.",
    ),
    (
        "Durable",
        "Stored so the relevant fact/work survives process interruption under the system's "
        "persistence assumptions. It does not alone guarantee a consumer executes it.",
    ),
    (
        "EBS",
        "AWS block storage for a host filesystem. A stopped instance can retain its disk and "
        "evidence, with ongoing storage costs.",
    ),
    (
        "EC2",
        "AWS virtual-machine service used as a Linux execution host in this project, not the "
        "proposed agent mechanism.",
    ),
    (
        "Endpoint",
        "Either an HTTP address or a measured research outcome. A professor may mean either; "
        "clarify from context.",
    ),
    (
        "Estimand",
        "The exact quantity of interest: here arm differences over the declared fixed "
        "simulator recipe/context mixture.",
    ),
    (
        "Evidence",
        "Available observations supporting a particular claim at a particular time. Evidence "
        "can be missing, stale or bound to the wrong version.",
    ),
    (
        "Execution ID",
        "Saved identity of one input-arm-attempt original. Continuing collection must preserve "
        "it rather than create a replacement outcome.",
    ),
    (
        "Explicit withdrawal",
        "Identifying a previously exposed statement as outdated/withdrawn, not merely giving a "
        "new time. Our grader recognizes a fixed prefix.",
    ),
    (
        "Exposure",
        "Content reaching the relevant recorded playback boundary under the instrument. It "
        "does not prove attention or comprehension.",
    ),
    (
        "External validity",
        "How far a result transfers beyond the tested setting. Natural callers and different "
        "provider ecosystems remain untested.",
    ),
    (
        "Fault injection",
        "Deliberately causing a planned error/timing condition, such as dropping a reply after "
        "commit. Distinct from an accidental infrastructure failure.",
    ),
    (
        "Fixture",
        "A versioned scenario/configuration input defining conditions and expected protocol "
        "structure. It is preserved after freeze rather than edited to fit a result.",
    ),
    (
        "Freeze",
        "Version/hash binding of an accepted research package. Freezing is not the same as "
        "launching it or claiming code is bug-free.",
    ),
    (
        "Full-duplex",
        "Listening and output can overlap. Support for a full-duplex product path does not "
        "mean the main campaign evaluated natural full-duplex speech.",
    ),
    (
        "Git commit",
        "A source-history snapshot identity. Different from a provider transaction commit, "
        "although both concern recorded state at different boundaries.",
    ),
    (
        "Grading",
        "Applying the frozen outcome instrument. This guide reads existing grades; it does not "
        "rerun the oracle or change outcomes.",
    ),
    (
        "Hash / SHA-256",
        "A content fingerprint. Matching a trusted hash supports identical bytes, not "
        "scientific truth or absence of bugs.",
    ),
    (
        "Hidden commit",
        "A provider effect occurs but its acknowledgement is unavailable to the controller. "
        "The world can be settled while local knowledge remains UNKNOWN.",
    ),
    (
        "Holm adjustment",
        "A multiple-comparison procedure for the declared diagnostic family. Adjustment does "
        "not fix a biased endpoint or missing evidence.",
    ),
    (
        "Horizon",
        "Observation limit used by the study, here 600 seconds per original under the accepted "
        "saved deadline rules.",
    ),
    (
        "HTTP 409",
        "Conflict response status. Its meaning requires exact endpoint/request/problem details "
        "and evidence; status alone is not a refusal classifier.",
    ),
    (
        "Idempotency",
        "Repeating the same logical operation under the provider contract does not add extra "
        "effects. Changed intent needs separate semantics.",
    ),
    (
        "Identification bound",
        "Range consistent with observed and unknown outcomes in the sample. It is not a "
        "confidence interval for sampling uncertainty.",
    ),
    (
        "Invariant",
        "A property that should remain true across allowed transitions, such as preserving "
        "accepted intent and not using stale evidence to authorize a claim.",
    ),
    (
        "IANA time zone",
        "Named regional time zone retained with appointments, such as Asia/Karachi, distinct "
        "from a bare UTC offset.",
    ),
    (
        "Lease",
        "Temporary ownership of queued work, used to coordinate workers. A lease needs "
        "crash/recovery handling; it is not permanent completion.",
    ),
    (
        "Ledger",
        "Durable operational record of identities, progress, notices and retention. Different "
        "from the provider's truth log and the application's business database.",
    ),
    ("Lineage", "Recorded relationship showing which earlier data or work an output depends on."),
    (
        "LLM",
        "Large language model. It may propose language or actions, but the main study did not "
        "compare its learned capability.",
    ),
    (
        "Lognormal",
        "Distributional form where the logarithm of positive time has a normal-shaped "
        "distribution. It is an assumption in the accepted AFT model.",
    ),
    (
        "Manifest",
        "Inventory binding files/objects, identities and hashes. Its usefulness depends on "
        "trusted original commitments and verification.",
    ),
    (
        "McNemar test",
        "Paired binary-outcome test focusing on discordant directions. The reported "
        "communication calculation is diagnostic and has seven missing pairs.",
    ),
    (
        "Model",
        "May mean a learned LLM, a mathematical timing model, or a conceptual execution model. "
        "The cited papers do not all propose neural models.",
    ),
    (
        "Monotonic clock",
        "A clock for elapsed time within a boot, distinguished from calendar wall time. Boot "
        "identity and paired measurement remain important.",
    ),
    (
        "N/A",
        "Structurally not eligible for an endpoint. Different from UNKNOWN, where the question "
        "applies but sufficient evidence is unavailable.",
    ),
    (
        "Native audio",
        "Model interface handling speech directly. Optional adapters do not turn the main "
        "typed/scripted study into a native-audio model comparison.",
    ),
    (
        "Noninferiority margin",
        "Largest accepted loss relative to the comparator for a defined endpoint. Here five "
        "percentage points for clean usefulness under the planned rule.",
    ),
    (
        "Observation",
        "A recorded piece of provider/client evidence at a time. It may differ from what "
        "actually happened in the external system.",
    ),
    (
        "Operation ID",
        "Identity of a logical external action. It is not the same as a new execution ID, "
        "accepted revision or provider resource version.",
    ),
    (
        "Oracle",
        "Independent grader using simulator truth, scripted targets and relevant observations, "
        "rather than accepting controller confidence as ground truth.",
    ),
    (
        "Orthogonal dimensions",
        "Separate state axes that can coexist, such as effect committed, evidence unknown and "
        "repair pending.",
    ),
    (
        "Outbox",
        "A durable record of work/effects awaiting publication or dispatch. Recording an item "
        "is different from proving it was externally delivered.",
    ),
    (
        "P1 / P2",
        "Our main study's prevention-related and prevention-plus-repair profiles. Other papers "
        "and older timing diagrams can use these labels differently.",
    ),
    (
        "Paired analysis",
        "Comparison preserving the same input's outcomes across arms, rather than treating all "
        "rows as independent unrelated observations.",
    ),
    (
        "Percentage point",
        "Absolute difference between percentages. From 80% to 85% is five points, not a "
        "five-percent relative increase.",
    ),
    (
        "Pinned version",
        "An exact retained source/dependency/object version. It prevents silently reading a "
        "newer object under an old name.",
    ),
    (
        "Playback",
        "Output reaching the client's recorded media progress. "
        "Generated/queued/published/completed are separate lifecycle events.",
    ),
    (
        "Postcondition",
        "Condition that should hold after an action, checked independently where possible "
        "before assuming success or retry safety.",
    ),
    (
        "PostgreSQL",
        "Durable relational database used for correctness-relevant application records. The "
        "simulator also has isolated provider-side persistence.",
    ),
    (
        "Predicate",
        "Precisely stated condition a claim asserts, such as creation, cancellation or "
        "in-place rescheduling. Similar wording can imply different facts.",
    ),
    (
        "Primary outcome",
        "Main endpoint selected by the design before inspecting results. A more exciting "
        "secondary endpoint cannot simply replace it.",
    ),
    (
        "Protocol",
        "Rules governing how components coordinate knowledge, authority, effects, output and "
        "recovery.",
    ),
    (
        "Provenance",
        "Traceable origin and history of data/code/results, including source bindings, "
        "exports, hashes, notices and backups.",
    ),
    (
        "Proxy",
        "Observable substitute for a concept. Logical word ACKs proxy exposure without "
        "establishing real intelligible speech or comprehension.",
    ),
    (
        "Publication",
        "In this protocol, releasing output into a media/message path. In academic discussion, "
        "publishing a paper means something different.",
    ),
    (
        "Raw status",
        "Original driver label such as FAILED or COMPLETED, retained separately from "
        "independent outcome grades.",
    ),
    (
        "Receipt",
        "Structured verification record scoped to operation, revision, predicate, resource "
        "version, source and validity. It can be SATISFIED, VIOLATED or UNKNOWN.",
    ),
    (
        "Recipe",
        "Fixed family of scenario/fault conditions. Context variation gives new inputs without "
        "making a new independent research domain.",
    ),
    (
        "Reconciliation",
        "Checking authoritative status/resource evidence after ambiguity to determine possible "
        "effects and whether retry is safe. The reviewed limit is eight attempts.",
    ),
    (
        "Redis",
        "Optional disposable cache/hint store, never the only retained copy of a "
        "correctness-relevant fact in this contract.",
    ),
    (
        "Refusal",
        "Application-level rejection of a requested action/claim. Only narrowly recognized "
        "evidence-supported cases qualify for expected-outcome handling.",
    ),
    (
        "Repair obligation",
        "Persistent record of corrective work owed for incompatible exposed content. Its "
        "creation, discovery, delivery and escalation are distinct concerns.",
    ),
    (
        "Replay",
        "Issuing scenario commands again. This differs from resuming evidence collection or "
        "downloading an already executed original's record.",
    ),
    (
        "Resource version",
        "Specific provider resource state to which observations/claims can be bound. Same "
        "appointment ID or same time phrase does not guarantee same version.",
    ),
    (
        "Restricted mean",
        "Timing summary evaluated up to an accepted horizon rather than assuming indefinite "
        "follow-up. Here interpreted under the frozen scripted-completion rules.",
    ),
    (
        "Retraction",
        "Explicitly withdrawing or identifying earlier content as outdated. The implemented "
        "matcher is narrower than open-language semantic retraction.",
    ),
    (
        "Revision",
        "Numbered accepted version of a request. More than one revision does not prove that "
        "the provider performed an in-place reschedule.",
    ),
    (
        "Risk difference",
        "Difference in outcome proportions between arms in a defined population/frame and "
        "subtraction direction.",
    ),
    (
        "S3",
        "AWS object storage used with versioned evidence backups. Knowing an object key "
        "without its required version/hash can be insufficient.",
    ),
    (
        "SATISFIED / VIOLATED / UNKNOWN",
        "Verification's three knowledge verdicts: supported, contradicted, or not sufficiently "
        "established under the rules.",
    ),
    (
        "Seed",
        "Starting value for repeatable computational random draws. It improves "
        "reproducibility, not the truth of an independence assumption.",
    ),
    (
        "Semantic",
        "Concerning meaning. Semantic correctness is broader than literal string matching; the "
        "study's correction matcher has a documented wording restriction.",
    ),
    (
        "Serial",
        "One original execution admitted at a time in the saved order. It simplifies some "
        "isolation concerns but introduces shared-time/host limitations.",
    ),
    (
        "Sidecar",
        "Separate explanatory/amendment metadata preserving an original rather than "
        "overwriting it. Only the previously accepted first-two timing sidecars were reused.",
    ),
    (
        "Simulator",
        "Controlled external provider implementation with fault injection and independent "
        "truth logging. Synthetic does not mean the application code/database effects were "
        "imaginary.",
    ),
    (
        "SSM / CloudShell",
        "AWS managed control and interactive shell facilities used operationally. They are "
        "distinct from an always-running campaign service and from research-arm behavior.",
    ),
    (
        "STT / TTS",
        "Speech-to-text and text-to-speech. The main campaign bypassed these natural-speech "
        "uncertainties through typed intents/scripted audio.",
    ),
    (
        "Staging",
        "Holding a planned effect/output before its release condition. A queued or staged "
        "acknowledgement does not prove an external effect occurred.",
    ),
    (
        "Stale",
        "No longer applicable to the accepted intent or relevant resource state. A statement "
        "can become outdated after having been valid earlier.",
    ),
    ("Stratum", "A prespecified scenario group: CLEAN, HIDDEN_COMMIT, PLAYOUT or OTHER_BOUNDARY."),
    (
        "Synthetic",
        "Constructed under controlled rules rather than sampled from natural human calls. "
        "Conclusions must respect that frame.",
    ),
    (
        "Telemetry",
        "Internal state/log information useful for understanding a mechanism. It must not "
        "automatically replace independent outcome evidence.",
    ),
    (
        "Timeout",
        "Waiting limit reached. It does not by itself prove whether an external action committed.",
    ),
    (
        "Trace",
        "Time-ordered retained evidence about one execution's requests, observations, output, "
        "grades and operational context.",
    ),
    (
        "Truth versus knowledge",
        "What occurred in the provider versus what the application's applicable observations "
        "justify. The oracle's privileged truth is not silently given to the arm.",
    ),
    (
        "UNKNOWN",
        "Insufficient relevant evidence, not a convenient success/failure value. Applies to "
        "different layers with their own definitions.",
    ),
    (
        "UTC",
        "Common timestamp reference retained for ordering/accounting; original appointment "
        "time-zone identity is also retained where applicable.",
    ),
    (
        "Validity interval",
        "Time window within which evidence/authorization applies, subject to its other "
        "identity and version conditions.",
    ),
    (
        "Version drift",
        "Actual source/dependencies differ from expected pinned material. A safe runner pauses "
        "rather than silently blessing the difference.",
    ),
    (
        "Watchdog",
        "Independent guard-checking process. A pause and stopped compute are different states; "
        "separate shutdown controls and verification matter.",
    ),
]
