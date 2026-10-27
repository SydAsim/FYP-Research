"""Teaching notes for all 52 prose blocks of the preserved full manuscript."""

from __future__ import annotations

NOTES: list[tuple[str, str, str, str, str]] = [
    (
        "Abstract: the entire study in one paragraph",
        "The opening sentence separates doing the job from having enough proof to announce it. "
        "The next sentence adds a second problem: giving new information may leave an older "
        "statement uncorrected. The paragraph then names the three implementations and the "
        "size of the completed comparison. Its business result is a tie. Its narrower "
        "communication result concerns explicit withdrawal. The final sentences tell you the "
        "test's boundaries: a fixed wording rule and scripted playback. Read the abstract as "
        "problem, proposed mechanisms, method, result, then limitation. It does not promise a "
        "better language model.",
        "Abstract = compressed overview; competent baseline = a comparison system with "
        "meaningful existing protections; paired = the same input tested under each arm; "
        "explicit withdrawal = clearly identifying an earlier statement as outdated.",
        "A clerk can correctly move your appointment while never telling you. Another clerk "
        "can tell you the new time without saying the earlier time no longer applies. These "
        "are different accomplishments.",
        "Do not compress this abstract into 'P2 is 100% accurate'. Its 33/33 communication "
        "result has a special denominator and a narrow instrument.",
    ),
    (
        "Introduction: why a missing reply is dangerous",
        "The booking service can save the 12:15 appointment and then lose the reply. The "
        "controller sees a timeout, not a reliable statement that nothing happened. Meanwhile, "
        "the resident changes the desired time to 14:15. Repeating the first create request "
        "might add another booking. Muting audio prevents additional output but cannot remove "
        "an external booking or make previously played words disappear. This paragraph "
        "introduces six separate boundaries because each answers a different question.",
        "Commit = make an external change durable; external effect = a booking or cancellation "
        "outside the controller; accepted intent = the request the server has formally "
        "accepted; playback = output reaching the client media path.",
        "A restaurant places your takeaway order, but your app loses internet before the "
        "receipt arrives. Pressing order again is not automatically safe.",
        "The times are an explanatory example. They are not a transcript of a real resident or "
        "one universal campaign case.",
    ),
    (
        "Introduction: the incremental research question",
        "The first sentence credits established API ideas. The second acknowledges earlier "
        "research on transactions and revisions. The bold question asks what the additional "
        "mechanisms achieve once these strong protections already exist. 'Incremental' means "
        "the extra effect beyond the comparator. This prevents winning simply by comparing a "
        "careful implementation with an obviously unsafe one.",
        "API = the agreed request/response interface; idempotent = repeats of the same logical "
        "request do not create extra effects; transactional runtime = software coordinating "
        "effects and settlement; incremental benefit = improvement attributable to an added "
        "package under this comparison.",
        "To evaluate a new seat belt, compare with a functioning existing seat belt rather "
        "than a car with none.",
        "This study does not run Atomix or Cordon as experimental arms. Related-work "
        "discussion is not a head-to-head benchmark.",
    ),
    (
        "Introduction: a refusal can protect truth and still leave a task unfinished",
        "A business outcome asks what exists at the provider. A communication outcome asks "
        "what was justified and delivered. If evidence is insufficient, refusing a decisive "
        "confirmation may be the right action. It still means the desired confirmation was not "
        "delivered. Likewise, a driver returning normally is only a process fact. The baseline "
        "can justify claims from its ordinary observations; requiring it to generate P1's "
        "special receipt objects would bias the measurement.",
        "Backend = server-side application; refusal = an application deliberately rejecting a "
        "request; driver = the research program issuing the scenario; outcome credit = the "
        "grader's assessment of externally observable success.",
        "An honest receptionist says 'I cannot confirm yet' after a payment timeout. Honesty "
        "is valuable, but it is not the same as completing the confirmation task.",
        "Never label every refusal as a successful business outcome or every HTTP error as an "
        "infrastructure outage.",
    ),
    (
        "Introduction: what the paper contributes",
        "There are three claimed outputs: a working contract, a comparison instrument, and "
        "results from that instrument. 'Bounded' means the claim has an explicitly stated "
        "scope. The business comparison did not distinguish the arms; the communication "
        "measure did in a limited subset. A negative primary result remains a result when the "
        "comparator and methods are meaningful. None of this invents database transactions or "
        "proves the system correct under every possible schedule.",
        "Protocol = agreed rules across components; instrument = software used to create and "
        "measure experiments; primary outcome = a main endpoint selected in the plan; negative "
        "finding = no demonstrated benefit on the question tested.",
        "Building a calibrated thermometer and learning that two rooms have the same "
        "temperature can be valuable even without discovering a hotter room.",
        "A new combination is not automatically novel. Its scientific value must be judged "
        "against prior work and the quality of evidence.",
    ),
    (
        "Related work: transaction boundaries",
        "This paragraph recognizes known work on retry safety and on deciding when effects "
        "should settle. Its purpose is positioning, not importing those papers' performance "
        "claims. Our focus is a particular outcome statement and its exposure history. We did "
        "not implement each cited runtime and compare its results with ours.",
        "Settlement = deciding which effects are final; lineage = a record of what an output "
        "depends on; authority = permission to cause a consequence; antecedent = relevant "
        "earlier work.",
        "An office approval process can govern when a letter is sent. Our question "
        "additionally tracks whether an already delivered message needs a correction.",
        "The reference guide later summarizes these papers briefly. Do not claim that all of "
        "their mechanisms are absent from our comparator or present in our code.",
    ),
    (
        "Related work: changing instructions and recovery",
        "A request can change while work is running. Prior research already studies preserving "
        "useful progress and recovering consistently. The cited papers concern different "
        "recovery formulations. Our experiments test the frozen booking implementation, not a "
        "universal replacement for those systems.",
        "Reversibility = whether an action can be undone; admissible = allowed by the "
        "correctness conditions; downstream = work depending on an earlier result; recovery "
        "boundary = the point from which work can safely continue.",
        "If a draft shopping list changes, unused notes can be edited. If a package has "
        "already shipped, editing the notes cannot undo shipment.",
        "The existence of our revision counter is not evidence that we invented online "
        "revision handling.",
    ),
    (
        "Related work: observations and receipts",
        "Verification before retry and receipts for claims are established approaches. This "
        "study combines them with revision, resource-version, exposure, and repair records. "
        "The important conceptual separation is between observing an action, storing an "
        "observation, and authorizing a statement about it.",
        "Postcondition = a condition that should hold after an action; receipt = structured "
        "evidence about a check; provenance = where evidence came from; predicate = a "
        "statement that can be checked as satisfied, violated, or unknown.",
        "A delivery scan is evidence. It is not automatically permission to tell the customer "
        "that a different package arrived.",
        "Our receipt is not a cryptographic proof of the provider's entire internal history.",
    ),
    (
        "Related work: generated output versus played output",
        "Speech can be produced ahead of what the client has played. Existing dialogue work "
        "studies this gap and repair. Here the measured question is whether booking-related "
        "words have applicable support and whether outdated content is explicitly withdrawn. "
        "We do not claim that our tone-based setup is equivalent to another paper's live "
        "speech evaluation.",
        "Incremental generation = producing a response in pieces; model-facing context = "
        "information available to a model; playback boundary = the recorded progress point of "
        "output; semantic = concerning meaning.",
        "A video player may download a whole scene while the viewer has watched only its first "
        "seconds. Downloaded and watched are different facts.",
        "An ACK is client testimony about progress. It cannot establish attention or "
        "understanding.",
    ),
    (
        "Related work: what kind of benchmark this is",
        "A benchmark is a shared testing setup. The cited benchmark family examines tool "
        "interaction and grounded voice tasks. Our experiment deliberately bypasses "
        "recognition and intent generation to study deterministic protocol behavior. Its 91% "
        "business rate cannot be ranked against a different benchmark's model success rate.",
        "Grounded task = one whose result is checked against an environment; typed intent = "
        "structured request supplied directly; leaderboard = a ranked comparison under a "
        "common protocol.",
        "A brake test on a controlled track and a driving test in city traffic measure related "
        "but different abilities.",
        "Do not advertise the study as a Gemini-versus-GPT comparison. Those are not its arms.",
    ),
    (
        "Related work: why novelty stays qualified",
        "The author checked selected relevant original sources. That is not an exhaustive "
        "search of all publications. The plausible contribution is the evaluated combination "
        "and endpoint separation. Whether it is sufficiently original is a review question, "
        "not something established by its number of test cases.",
        "Primary source = the authors' paper or official description; systematic review = a "
        "defined search and screening process; priority = being the first to establish "
        "something.",
        "Knowing several nearby buildings does not prove there is no similar building "
        "elsewhere in the city.",
        "Avoid 'nobody in industry does this' and 'world first'. Neither follows from the "
        "current evidence.",
    ),
    (
        "System: where authority comes from",
        "A model may suggest a request, but server rules decide whether to accept it. "
        "PostgreSQL saves the accepted revision and correctness-relevant records. Redis can "
        "accelerate disposable operations but cannot be the only place that remembers an "
        "obligation or accepted request. Typed inputs remove one source of variability from "
        "the main experiment.",
        "PostgreSQL = durable relational database; Redis = optional in-memory cache; "
        "deterministic = the same relevant inputs and rules lead to the same decision; "
        "revision = numbered accepted version of intent.",
        "A receptionist's rough note is a proposal. An approved entry in the appointment "
        "register is the accepted record.",
        "A durable local record does not give the application omniscient knowledge of an "
        "opaque external provider.",
    ),
    (
        "System: orthogonal state dimensions",
        "A single SUCCESS or FAILED label loses information. The provider may have committed, "
        "the controller may not know, old speech may be invalid, and a repair may still be "
        "owed. All four can be true together. Orthogonal means these questions have separate "
        "axes rather than being squeezed into a single line of states.",
        "Orthogonal = represented separately; product state = the combination of several state "
        "dimensions; local knowledge = what observations justify, not everything that is true.",
        "A parcel can be delivered, its tracking page delayed, its notification unsent, and "
        "its customer complaint unresolved at the same time.",
        "The dimension chart is a conceptual map. It is not the exact list of executable "
        "transition rules.",
    ),
    (
        "System: UNKNOWN, reconciliation, receipt, and permit",
        "Timeout is a statement about waiting, not proof of no external effect. Reconciliation "
        "checks provider status or resources before another write. Repeating one logical "
        "operation keeps its identity; changing the actual request needs a linked new one. The "
        "receipt names which operation, revision, predicates, version, source, and validity "
        "period it concerns. A permit is then a scoped authorization to say something, not a "
        "second booking commit.",
        "UNKNOWN = insufficient knowledge; reconciliation = matching observations with "
        "possible effects; validity interval = the period during which evidence is applicable; "
        "SATISFIED/VIOLATED/UNKNOWN = three-valued verification.",
        "A dated inspection certificate for apartment A cannot certify apartment B after "
        "renovation. Its identity, version, and date matter.",
        "A satisfied receipt can later become inapplicable. Stored evidence is not eternally "
        "current.",
    ),
    (
        "System: why a publication check is not enough",
        "The world can change between generation, publication, and playback. A new accepted "
        "request or changed provider version can invalidate previously usable support. The "
        "statement's particular words and predicate matter: 'exists at 14:15' and 'was "
        "rescheduled in place' are not identical claims. B3 is also allowed to check evidence "
        "and refuse.",
        "Applicable = relevant and valid for this claim now; publication = releasing a segment "
        "into the output path; decisive = conveying a consequential outcome, such as "
        "confirmation or a specific appointment time.",
        "A boarding gate announcement drafted five minutes ago may need checking again before "
        "it plays.",
        "Our experiment does not establish that permits defeat every possible "
        "publication/playback race.",
    ),
    (
        "System: preventing future output versus repairing past exposure",
        "Deleting a queued segment can prevent future exposure. Once decisive content has "
        "reached playback, preventing later output alone cannot address the already exposed "
        "statement. P2 therefore records a repair obligation. A delayed ACK can reveal "
        "exposure after a correction was accepted, so handlers need to maintain the correct "
        "obligation history across event orderings.",
        "Obligation = stored work that remains owed; duplicate ACK = repeated report of an "
        "event; delayed ACK = a report received after the event time; durable = surviving a "
        "process restart.",
        "If the receptionist already said the wrong room number, muting the telephone "
        "afterward does not correct that number. Another supported statement is required.",
        "Surviving storage is only one part of delivery. A consumer must discover the "
        "obligation and successfully deliver or escalate it.",
    ),
    (
        "Figure 1: how to read independent dimensions",
        "Read each row as a separate question: what was accepted, what happened, what is "
        "known, what may be said, what reached playback, and what remains owed. Do not read "
        "down the rows as a compulsory sequence from Intent to Repair. A repair row can remain "
        "pending after the business effect is complete.",
        "Coexist = be true at the same time; conceptual figure = explanatory diagram; mutually "
        "exclusive = unable to be true together.",
        "A dashboard can show fuel, speed, engine temperature, and a warning simultaneously. "
        "It is not one combined status with only four values.",
        "Scripted exposure is a measurement proxy, not a claim about a real listener's mental "
        "state.",
    ),
    (
        "Table 1: what the arm names mean",
        "B3 is the protected baseline. P1 adds both permits and explicit product-state "
        "invariants. P2 adds the played-content repair package. Their names are configuration "
        "labels, not names of three language models. A correct ordinary baseline update "
        "receives the same observable credit as an equivalent proposed-arm update.",
        "Arm = experimental configuration; ablation = removing a component to examine its "
        "increment; frozen = version-pinned for the comparison.",
        "Compare three versions of the same booking office: established safeguards, extra "
        "authorization checks, then authorization plus a persistent correction desk.",
        "Because P1 adds two switches together, the design cannot isolate which one caused a "
        "difference.",
    ),
    (
        "Measurement: the grader must not trust the system's own confidence",
        "The grader uses the external script, provider truth, ordinary observations, generated "
        "segments, and client reports. It does not award success because an arm's receipt says "
        "SATISFIED or because its repair row says done. This reduces self-grading. Internal "
        "obligation data is useful for mechanism inspection but is not substituted for "
        "externally supported communication.",
        "Oracle = independent outcome checker; controller belief = what the application "
        "thinks; telemetry = internal diagnostic records; label neutrality = not changing a "
        "grade because the arm name changes.",
        "A driving examiner observes the car's path rather than accepting the dashboard's "
        "'excellent driving' message.",
        "Independent implementation does not mean infallible. The grader can contain bugs or "
        "narrow semantic assumptions.",
    ),
    (
        "Measurement: separate questions, separate answers",
        "The endpoint list prevents one good result from hiding a different failure. Correct "
        "database state, true wording, applicable evidence, exposure, final update, and "
        "explicit withdrawal are distinct. The start of 'Your maintenance ...' is not "
        "sufficient evidence that a confirmation or time was exposed. The study uses logical "
        "word positions and tones, so its evidence does not establish acoustic "
        "intelligibility.",
        "Endpoint = the exact result being measured; N/A = not applicable by design; UNKNOWN = "
        "applicable but insufficient evidence; alignment = mapping a word to an audio "
        "position.",
        "Hearing the introduction 'Your train ...' does not tell you whether 'is cancelled' "
        "was played next.",
        "An acknowledgement without suitable word/audio alignment cannot prove which real "
        "spoken words a person heard.",
    ),
    (
        "Design: 500 draws from 50 recipe families",
        "A recipe defines a kind of event ordering and fault. Context fills in appointment "
        "details under its constraints. Drawing with replacement means the same family can "
        "recur. Every sampled input is tested under each arm, keeping those three rows "
        "together. The estimand is the average arm difference for this declared synthetic "
        "mixture, not for every conceivable customer call.",
        "Sampling frame = eligible source of test inputs; stratum = planned group of "
        "scenarios; estimand = the precise quantity the study aims to estimate; cluster = "
        "observations kept together because they belong to one unit.",
        "Testing ten meal recipes with different ingredient amounts gives many preparations, "
        "but not hundreds of independent cuisines.",
        "Independent context draws are an assumption. A shared host and repeated families can "
        "create additional dependence.",
    ),
    (
        "Table 2: count inputs and executions correctly",
        "There are 300 clean inputs, 100 hidden-commit inputs, 60 playout inputs, and 40 "
        "other-boundary inputs. Each gets three executions. Thus 500 inputs produce 1,500 "
        "rows, not 1,500 independent scenarios. The correction weights are 100/200, 60/200, "
        "and 40/200 after excluding the 300 clean inputs from that correction endpoint.",
        "Allocation = the planned number assigned to each stratum; denominator = the total "
        "eligible units for a fraction; correction weight = a stratum's contribution to the "
        "planned correction mixture.",
        "Five hundred exam questions answered by three students produce 1,500 answers, but "
        "still only 500 distinct questions in the comparison.",
        "The 33 recovery inputs are a designated subset, not an extra 33 inputs added to the 500.",
    ),
    (
        "Design: controlled faults and full observation",
        "The serial schedule and identities are saved. Each arm receives comparable "
        "conditions. Named barriers pause at a specific event boundary instead of hoping a "
        "sleep catches the right race. The collector keeps observing for the full saved "
        "600-second horizon after the final request, even when the driver returns or refuses. "
        "After interruption it resumes collection for the same execution and deadline, rather "
        "than issuing the business commands again.",
        "Barrier = an explicit wait/release point; horizon = observation period; checkpoint = "
        "saved progress; replay = issuing commands again; serial = one original execution "
        "admitted at a time.",
        "A crash test triggers the obstacle at the marked sensor line, rather than guessing "
        "when the car reaches it with a stopwatch.",
        "A full window does not guarantee every asynchronous event was captured. Collection "
        "gaps require separate treatment.",
    ),
    (
        "Design: BACKED_UP is an evidence status",
        "All planned executions have saved original records and verified backup transitions. "
        "There is one admission per identity, followed by export after the saved deadline and "
        "backup. That establishes accounting and preservation. It does not certify a "
        "successful booking or a successful confirmation. Pauses and instrument amendments "
        "remain part of the history.",
        "Admission = allowing the next planned execution to start; export = saving a portable "
        "record; BACKED_UP = ledger state indicating retained verified evidence; amendment = "
        "explicitly versioned change.",
        "A hospital archive can contain a complete record of an unsuccessful treatment. "
        "Archive completeness and treatment success are different facts.",
        "This is a document-storage analogy only; the application itself contains no medical "
        "workflow.",
    ),
    (
        "Analysis: two primary endpoints and a clean-case tolerance",
        "The primary comparison is P2 minus B3. Correction success uses the 200 non-clean "
        "inputs; hidden-commit exposure uses the 100 hidden-commit inputs. A weighted mean "
        "preserves the planned recipe mix. Conservative paired bounds retain uncertainty "
        "despite zero observed discordances. The analysis allocates error across the two "
        "primary questions. Clean cases check whether added protection loses too much ordinary "
        "usefulness, with a five-percentage-point tolerance.",
        "Risk difference = success proportion in one arm minus that in another; saturated cell "
        "means = estimate a separate arm-by-stratum mean; co-primary = one of two main planned "
        "outcomes; noninferiority margin = largest tolerated loss.",
        "If the intended workload is half hidden commit, its result receives half the "
        "correction weight even if one later selects an interesting trace.",
        "The stored claim guards remain restricted. A computed bound is not blanket "
        "authorization for a confirmatory claim.",
    ),
    (
        "Analysis: prevent selection bias in recovery evaluation",
        "The study chooses the 33 recovery opportunities before looking at which arm created "
        "repair rows. Otherwise P2 could be evaluated on an easy subset that B3 never entered. "
        "Missingness bounds ask how the result changes under every allowed assignment of "
        "unknown binary outcomes. Holm addresses the declared family of ten diagnostics. "
        "Omitting fixed time blocks checks whether the primary tie depends on one part of the "
        "execution order.",
        "Post-treatment selection = selecting units using a variable affected by the arm; "
        "missingness bound = range consistent with unknown outcomes; Holm = multiple-test "
        "adjustment; sensitivity check = test how interpretation depends on a choice or "
        "assumption.",
        "Compare delivery services on the same planned packages, not just the packages each "
        "service chose to mark as needing attention.",
        "A sensitivity check addresses the assumption it varies, not every possible source of "
        "bias.",
    ),
    (
        "Analysis: timing and the bootstrap",
        "The timing calculation resamples input IDs, keeping each input's B3/P1/P2 results "
        "together. Two thousand draws give the paired timing interval; a separate thousand "
        "draws assess uncertainty in an AFT model. A fixed seed makes the computational random "
        "draws repeatable. The endpoint is completion of a supported scripted ACK, not the "
        "time until a customer understands the corrected appointment.",
        "Bootstrap = repeatedly resampling observed units; censored = the event time is only "
        "partly known; AFT = a model describing multiplicative changes in time; lognormal = "
        "logarithm of time follows a normal-shaped distribution; seed = reproducible "
        "random-number starting value.",
        "Keep three test versions of the same case on one index card and resample cards, not "
        "individual results torn from their cases.",
        "Shared-host dependence and informative censoring can invalidate an otherwise neatly "
        "calculated interval.",
    ),
    (
        "Table 3: know whether TRUE is good or bad",
        "Final business correctness and supported updates are favorable when TRUE. Forbidden "
        "effects and unsupported exposure are adverse when TRUE. Every table fraction uses "
        "that endpoint's eligible denominator. Different rows are different questions; you "
        "cannot subtract their counts to infer overlap unless the paired row-level "
        "relationship was actually checked.",
        "Favorable endpoint = higher is desirable; adverse endpoint = higher indicates harm; "
        "marginal count = total for one outcome without the joint relationship to another "
        "outcome.",
        "A school can report 90 students passing maths and 80 passing English. That alone does "
        "not tell you exactly how many passed both.",
        "The separate raw-status cross-tab is available because that overlap was checked from "
        "row-level data.",
    ),
    (
        "Results: the main business comparison tied",
        "Each arm finishes 455 of 500 business targets correctly. Removing the 300 clean "
        "successes leaves 155 of 200 successful corrections. Hidden commit contributes 73 "
        "successes, playout 56, and other boundary 26. The paired correction difference is "
        "exactly zero in the observed sample. The conservative interval still allows effects "
        "in either direction in the declared frame under its assumptions. Zero events in the "
        "hidden-commit adverse endpoint is not proof that the risk is impossible.",
        "Percentage point = absolute difference between percentages; conservative = "
        "deliberately avoiding overly narrow uncertainty; discordance = a paired case where "
        "arms differ.",
        "If two thermometers give the same readings in your test rooms, that supports a tie "
        "there. It does not prove they will always agree everywhere.",
        "Do not call the zero difference a proof that the mechanisms are useless. The study's "
        "frame and implementation limit the conclusion.",
    ),
    (
        "Results: clean usefulness and block sensitivity",
        "Every arm succeeds on all 300 clean inputs. The one-sided lower bound says the "
        "estimated clean difference is compatible with at most a limited loss under the "
        "accepted rule; it is above the allowed negative five-point margin. Removing any one "
        "of twenty temporal blocks leaves the primary correction difference at zero. That "
        "stability concerns this endpoint, not all aspects of the system.",
        "One-sided bound = uncertainty focused on one direction; lower bound = lower end of "
        "the permitted range; stationarity = behavior remaining stable over time.",
        "A protection feature should not stop normal customers from completing ordinary work. "
        "Clean inputs provide that usefulness check.",
        "Three hundred clean successes do not prove production success is exactly 100%.",
    ),
    (
        "Table 4: UNKNOWN stays visible",
        "B3 has four recorded unsupported exposures, 481 negative grades, and 15 unknowns. P1 "
        "and P2 have zero recorded positive grades, the same 481 negative grades, and 19 "
        "unknowns. The table deliberately makes unknown testimony visible. The apparent "
        "four-event advantage disappears as a certain prevention claim when you inspect the "
        "paired unknown results.",
        "FALSE for an adverse endpoint = no adverse event established under the grading rule; "
        "UNKNOWN = relevant evidence insufficient; paired counterpart = the same input under "
        "another arm.",
        "A security camera that misses the doorway cannot certify that nobody entered. Missing "
        "footage is not a clean negative observation.",
        "Never report this as 'B3 made four errors and P2 proved zero risk'.",
    ),
    (
        "Results: the four exposure cases do not identify prevention",
        "All four B3 positive exposure grades come from a playout recipe where the provider "
        "version changes before playback. Their proposed-arm counterparts lack enough evidence "
        "for a definite exposure grade. These cases are not in the hidden-commit primary "
        "group. Previously valid content can also become outdated after a later revision; that "
        "is distinct from content being stale at its original playback time.",
        "Resource version = identifier of a particular state of an appointment; stale = no "
        "longer applicable to the currently accepted situation; counterpart UNKNOWN = no "
        "conclusive paired answer.",
        "A timetable statement can be correct when announced and later need withdrawing after "
        "the train is rescheduled.",
        "An earlier statement needing correction does not necessarily mean it was false when "
        "first spoken.",
    ),
    (
        "Results: FAILED and COMPLETED are process labels",
        "There are 141 raw driver failures and 1,359 normal completions. Every failed driver "
        "record has correct final business state but no supported final update. Another 135 "
        "normal completions have incorrect business state. The original record and the "
        "independent grades therefore tell different stories. Do not rewrite the raw statuses "
        "to make a nicer success percentage.",
        "Raw = original retained value; cross-tabulation = counting combinations of two "
        "variables; exception = a program signalling a problem; infrastructure failure = a "
        "technical malfunction, not automatically any rejected application request.",
        "An ATM can dispense cash then fail to print the receipt. A smooth screen animation "
        "can also complete while a requested transfer is not achieved. Observe both facts.",
        "The compact evidence does not establish that every one of the 141 failures had the "
        "same refusal cause.",
    ),
    (
        "Recovery results: an update is not the full correction criterion",
        "Every arm delivers a supported corrected update in the 33 planned challenges. P2 "
        "additionally receives complete communication credit in all 33. Each comparator has 26 "
        "definite failures and seven unknowns for that stricter endpoint. The result is about "
        "the implemented withdrawal criterion, not baseline inability to update the "
        "appointment.",
        "Ordinary update = supported current information; complete corrective communication = "
        "the declared update-plus-withdrawal requirement when applicable; comparator = arm "
        "used as a reference.",
        "'Your appointment is now at 14:15' gives a new time. 'My earlier confirmation was "
        "outdated; your appointment is at 14:15' explicitly addresses the previous message as "
        "well.",
        "These sentences are teaching examples. The grader's actual accepted prefix is "
        "documented separately.",
    ),
    (
        "Figure 2: explain all three colors",
        "The P2 bar contains 33 known successes. The B3 and P1 bars contain 26 known failures "
        "plus seven unknowns. The gray and amber parts must not be merged as 33 proven "
        "failures. Separately, ordinary update performance is 33/33 for every arm. The graphic "
        "depicts a specific secondary endpoint and its missingness.",
        "Stacked bar = colored parts making up one planned total; denominator = 33 eligible "
        "inputs per arm; descriptive plot = a picture of recorded counts, not a causal proof.",
        "An attendance chart should distinguish absent students from students whose attendance "
        "sheet was lost.",
        "The bars do not show real people hearing or understanding a correction.",
    ),
    (
        "Recovery results: the five challenge families",
        "The 33 inputs are divided 9+7+7+7+3. The challenges vary whether output finished, a "
        "decisive ACK arrived late, time words were partly played, another revision arrived "
        "after reconnect, or a worker restarted before repair. The seven partial-time cases "
        "are exactly where comparator communication grades are unknown. This locates "
        "missingness instead of hiding it in a total.",
        "Reconnect = client session returns after disconnection; decisive-time playback = "
        "content reaches a consequential time phrase; restart-before-repair = worker is "
        "restarted between recorded obligation and delivery.",
        "Five different fire drills can test different procedures even when they all end at "
        "the same assembly point.",
        "Having a restart recipe does not, by itself, prove unattended production recovery. "
        "The actual consumer path and orchestration matter.",
    ),
    (
        "Recovery analysis: tiny p-values and seven unknowns",
        "Among known pairs, 26 favor P2 and none favor the baseline. McNemar examines this "
        "imbalance; Holm adjusts within the planned diagnostic family. Seven pairs remain "
        "missing. If all seven unknown baseline results were successes, P2's advantage is "
        "26/33. If all were failures, it is 33/33. That yields 78.79 to 100 percentage points "
        "as a sample identification range, not a confidence interval for a wider population.",
        "p-value = probability of data at least as incompatible with a specified null model, "
        "assuming that model and its conditions; identification bound = possible range given "
        "missing outcomes; diagnostic = exploratory/qualified interpretation.",
        "You can count what every missing answer might do without pretending to know which "
        "answer it actually contained.",
        "A tiny p-value is not the probability our theory is true and does not repair a narrow "
        "endpoint or violated assumptions.",
    ),
    (
        "Recovery telemetry: 40 obligations across 33 inputs",
        "One input can create more than one obligation when another revision arrives. Thus 40 "
        "obligations across 33 inputs is consistent. All end REPAIR_PLAYED in the retained "
        "internal telemetry. That describes obligation state, not independent proof of every "
        "service being continuously available. The sampled trace explicitly invokes repair "
        "workers from the experiment.",
        "Telemetry = diagnostic state emitted by components; REPAIR_PLAYED = internal terminal "
        "delivery state; unattended discovery = a service finding pending work without a "
        "manual/driver call to deliver that particular repair.",
        "A to-do list can have two tasks for one customer. Marking them complete is "
        "informative, but it is not independent proof that an autonomous clerk found them.",
        "Do not say 'P2 autonomously recovers every crash' from this telemetry.",
    ),
    (
        "Measurement: the fixed phrase is a serious limitation",
        "The withdrawal matcher accepts a particular prefix on a supported, fully acknowledged "
        "final update. It does not understand arbitrary equivalent language. P2 intentionally "
        "produces the matching type of correction, so the finding includes a message-format "
        "component. A different baseline phrase might satisfy a human while receiving no "
        "explicit-withdrawal credit here. The independent, label-neutral instrument still has "
        "a limited construct.",
        "Construct = the underlying concept a measure intends to represent; template-specific "
        "= tied to prescribed wording; semantic equivalence = different wording with the same "
        "meaning; human belief repair = a listener revising their understanding.",
        "A spelling checker that accepts one correct synonym but rejects another has a real "
        "rule, but does not measure all ways of expressing the idea.",
        "This is why we cannot attribute the secondary finding solely to durable storage or "
        "claim better human understanding.",
    ),
    (
        "Table 5: plus means slower in this endpoint",
        "The P2-B3 difference is about 0.2593 seconds; P1-B3 is 0.2251 seconds; P2-P1 is "
        "0.0342 seconds. Positive means the proposed arm takes longer on the recorded timing "
        "measure. The intervals come from paired input resampling. These values concern "
        "supported scripted completion and a restricted horizon, not customers' conversation "
        "experience.",
        "Restricted mean = timing summary capped at a chosen horizon; paired bootstrap "
        "interval = uncertainty computed while preserving each case's comparison; second = the "
        "unit here, unlike retry attempts or drain passes.",
        "An extra document check can slightly delay issuing a receipt even while it protects "
        "the claims made on that receipt.",
        "Do not market a latency improvement; the recorded differences point the other way.",
    ),
    (
        "Timing: event observations, censoring, and model convergence",
        "There are 408 supported completions per arm, totaling 1,224 events. The other 276 "
        "records are censored. The AFT model's time ratio of about 1.226 means a "
        "multiplicative time factor under that model, not 1.226 seconds. All bootstrap fits "
        "converged, so none was silently discarded. But solving an optimization problem does "
        "not establish that lognormal timing or independent censoring is true.",
        "Event = observed endpoint completion; censored row = exact completion time not "
        "established within the observation basis; time ratio = multiplicative factor; "
        "convergence = optimizer meets its stopping conditions.",
        "A calculator can correctly fit a straight line to a curved relationship. Numerical "
        "success does not prove the chosen shape is right.",
        "Keep missing-event and historical infrastructure labels visible. Do not reinterpret "
        "all censoring as harmless waiting.",
    ),
    (
        "Trace 145: right booking, wrong claim predicate",
        "The provider committed the first booking before losing its reply. Recovery "
        "established the old effect, cancelled it, and created the corrected booking. It did "
        "not perform an in-place reschedule. The frozen selection logic nevertheless asked to "
        "say RESCHEDULED_APPOINTMENT because the revision number exceeded one. The verifier "
        "rejected that predicate. This combines a studied application limitation with a "
        "collector-classification problem that was separately amended.",
        "Predicate mismatch = requested statement asserts a fact unsupported by actual "
        "operations; synthesis input = structured facts/claim type supplied to output "
        "generation; classifier = instrument code deciding whether a refusal is expected or a "
        "technical stop.",
        "A shop refunds an old purchase and creates a new order. Saying 'we edited your "
        "original order' may misdescribe what actually happened.",
        "The application claim-selection behavior was not silently improved midway. The "
        "original FAILED status and grades remain.",
    ),
    (
        "Trace 59: factual phrase versus applicable evidence",
        "The appointment-time phrase can be true while its supporting observation refers to an "
        "old resource version. The retained grade therefore separates truth from evidence at "
        "playback. Final business state is also separately false in this input. One sentence "
        "of confirmation can contain a correct time component without satisfying the full "
        "evidence contract.",
        "Version binding = evidence identifies exactly which resource state it concerns; "
        "scalar = a single value; oracle completeness = ability to correctly handle every "
        "relevant condition.",
        "A document says a machine was safe at inspection version 4. The machine is still on "
        "the same floor at version 5, but that unchanged detail does not renew the inspection.",
        "This illustration does not imply all true statements require this particular "
        "application's receipt format.",
    ),
    (
        "Trace 82: correction can itself become outdated",
        "The trace includes an initial confirmation, a revision-two repair that is "
        "interrupted, and a later revision-three correction. Delayed earlier testimony is "
        "retained rather than discarded because it is inconvenient. Two obligations end "
        "played, while final state, supported update, and withdrawal receive favorable grades. "
        "The control explicitly invokes workers, so this trace demonstrates a recorded path "
        "rather than autonomous service discovery.",
        "Revision three = the third accepted target; terminal state = final recorded state of "
        "a particular record; orchestration = controlling which process runs when.",
        "You begin apologizing for a 12:15 booking with a new 14:15 time, but the customer "
        "asks for tomorrow at 15:15 before the apology finishes. The repair must follow the "
        "newest accepted target.",
        "The illustrative time story is a teaching aid. The original export is the authority "
        "for the exact retained sequence.",
    ),
    (
        "Validity: are we measuring the thing we care about?",
        "Construct validity asks whether the instrument represents the intended concept. Tones "
        "and ACK indexes can test protocol behavior but not attention or intelligible-word "
        "exposure. The fixed wording criterion captures one implemented form of explicit "
        "correction. Internal telemetry cannot replace the independent output measure. Equal "
        "ordinary-update results keep the positive finding in context.",
        "Validity = how well an inference is supported; proxy = substitute measurement; "
        "testimony = a reported observation; construct validity = fit between a measure and "
        "its intended concept.",
        "Counting opened textbooks measures access to books, not necessarily comprehension of "
        "their content.",
        "Do not convert a protocol proxy into a claim about human psychology.",
    ),
    (
        "Validity: what did each arm actually change?",
        "The shared claim-selection limitation can affect every arm. P1 changes permits and "
        "product-state rules together. P2 changes a repair package that includes what is said "
        "and how obligations are stored. Therefore an arm difference identifies the effect of "
        "that implemented package under the study, not the isolated effect of one storage "
        "mechanism. Frozen implementations may behave differently from idealized mechanisms.",
        "Confounding within a package = multiple changing components prevent isolating one; "
        "causal attribution = assigning a change in outcome to a particular cause; idealized = "
        "assuming a perfectly implemented concept.",
        "If a new teaching course changes both textbook and instructor, better marks cannot be "
        "attributed to the textbook alone.",
        "Answering 'durability alone caused 33/33' would exceed this design.",
    ),
    (
        "Validity: independence is an assumption",
        "The 1,500 rows belong to 500 paired inputs drawn from 50 fixed families. Host load "
        "and time can influence several rows. Operational interruptions can introduce "
        "additional dependence. The temporal omission check preserves the primary tie but is "
        "not a full proof of independent timing errors. Original analysis flags remain "
        "restricted rather than being changed after a pleasing result.",
        "Temporal drift = conditions changing with time; independence = one unit's uncertainty "
        "not influencing another's after the model's conditions; confirmatory = supporting a "
        "planned inference under satisfied assumptions.",
        "Students taking an exam in a hot room may share a room effect. More answers do not "
        "remove that dependence.",
        "Do not call 1,500 rows an effective sample size of 1,500 independent cases.",
    ),
    (
        "Validity: preserve timing history rather than rewriting it",
        "Four original records retain infrastructure-failure censor labels. Two previously "
        "accepted sidecars create a separate timing view with label-only changes; numeric "
        "outcomes and durations remain identical. This task did not create another sidecar or "
        "regrade old cases. A historical label does not establish whether censoring is "
        "statistically independent of the outcome.",
        "Sidecar = separate amendment metadata stored beside an original; retrospective "
        "regrading = changing a past outcome after seeing evidence/results; administrative "
        "censoring = observation stopping for reasons appropriately independent under the "
        "analysis assumptions.",
        "Add an explanatory note next to an old lab entry rather than erasing the original ink.",
        "A separate view must remain traceable to the original, including limitations its "
        "relabeling does not solve.",
    ),
    (
        "Validity: provenance is not a universal deployment guarantee",
        "Nine controller-binding segments preserve the history of different operational "
        "versions. Their records connect identities, admission, exports, and backups. They are "
        "not hardware-level attestations of every running binary. Hashes support unchanged "
        "bytes and post-deadline exports support accounting; neither guarantees complete "
        "observation. The study has no evidence about real callers, speech-model rankings, "
        "payments, or software-update agents.",
        "Binding = recorded association between identities/versions; attestation = independent "
        "evidence about what actually ran; external validity = transfer of results beyond the "
        "tested setting.",
        "A signed travel itinerary records intended flights. It is not, by itself, proof of "
        "every minute of the passenger's journey.",
        "Use the term 'controlled protocol evaluation', not 'production-certified voice system'.",
    ),
    (
        "Reproducibility: what was checked",
        "The analysis retains all originals. The ledger joins original identities to export "
        "and backup records. Its chained notices support traceability. The final source "
        "inventory still matches after local analysis. However, earlier originals were "
        "admitted under earlier controller bindings, so the paper does not pretend the entire "
        "campaign used the last operational binary.",
        "Hash = content fingerprint; chained notice = event record linked by hashes to earlier "
        "notices; inventory = list of files and fingerprints; provenance = the history showing "
        "where a result came from.",
        "Keep every version of a laboratory procedure and record which version applied to "
        "which sample.",
        "A hash proves byte identity with a trusted commitment, not that the content's "
        "scientific claim is true.",
    ),
    (
        "Reproducibility: results package versus full archive collection",
        "The compact local package contains the CSV, compact records, calculations, checks, "
        "instructions, and selected trace examples. It is not every large raw archive or a "
        "bundled computer environment. The long SHA-256 identifies the returned evidence "
        "bundle. A companion map links claims to files. The manuscript does not invent a "
        "public DOI or imply a private local file is a public research deposit.",
        "SHA-256 = a standard 256-bit cryptographic content fingerprint; CSV = table stored as "
        "comma-separated text; runtime = interpreter and dependencies; DOI = persistent "
        "identifier assigned through an appropriate registration route.",
        "A book's index helps locate material, but is not the full library it indexes.",
        "Publishing an artifact would require an intentional release and appropriate checks; "
        "it has not occurred merely because a PDF exists.",
    ),
    (
        "Conclusion: the strongest honest story",
        "The business endpoint ties beyond the competent baseline. The secondary result "
        "distinguishes ordinary current information from the fixed explicit-withdrawal "
        "criterion. This supports a reporting discipline that keeps effect, knowledge, "
        "exposure, and correction separate. It does not establish a breakthrough or "
        "durability's isolated benefit. Software updates are a possible analogy only; no "
        "update benchmark was run. The contribution is a bounded systems/measurement study, "
        "including a negative primary finding.",
        "Implication = a lesson supported by a result; transfer hypothesis = a proposed "
        "extension to a new setting; negative primary finding = planned main comparison does "
        "not demonstrate an advantage.",
        "A careful experiment can show that the established safety measures already handle a "
        "problem well, while revealing a narrower communication gap worth studying.",
        "The study's completion and a useful manuscript do not guarantee novelty, acceptance, "
        "or a publication venue.",
    ),
]
