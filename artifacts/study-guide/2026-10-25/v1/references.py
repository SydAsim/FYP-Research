"""Brief original-source paraphrases; no external paper is reproduced."""

from __future__ import annotations

REFERENCES: list[tuple[str, str, str, str, str]] = [
    (
        "1. Featonby - Making retries safe with idempotent APIs",
        "Engineering article, not a language model",
        "https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/",
        "The article explains why retrying a request can repeat an unwanted side effect. "
        "Caller-provided identifiers distinguish another attempt at the same logical request "
        "from a new intent. Late requests and changed parameters require explicit API "
        "semantics. This is practical distributed-systems guidance, not an AI architecture we "
        "trained.",
        "Our baseline already has durable operation identity and reconciliation. We apply "
        "known ideas; our results do not invent them. The article is not an experimental arm, "
        "and our AWS hosting decision is a separate issue.",
    ),
    (
        "2. Atomix - Timely, Transactional Tool Use for Reliable Agentic Workflows",
        "Transactional runtime research; arXiv preprint version v2",
        "https://arxiv.org/html/2602.14849v2",
        "Atomix coordinates settlement of tool effects. It records resource reads/effects, "
        "seals a transaction's footprint, and uses progress information to determine when "
        "earlier conflicting work can no longer arrive. Effect classes determine what can be "
        "buffered, compensated or gated before release. It is a runtime for workflows, not the "
        "name of a foundation language model.",
        "Our question emphasizes the evidence and exposure history of an outcome statement, "
        "including later correction. We did not run Atomix against B3/P1/P2. Gating "
        "irreversible effects is established prior work, not our first-ever invention.",
    ),
    (
        "3. Cordon - Semantic Transactions for Tool-Using LLM Agents",
        "Task-scoped transactional runtime; cited as an arXiv preprint",
        "https://arxiv.org/html/2606.17573v1",
        "Cordon treats a task as a validation and commit boundary. Its design tracks result "
        "lineage, reversible local changes, staged outward effects, delegated authority and "
        "recovery metadata. It validates the composed flow rather than approving isolated "
        "calls without their dependencies. 'Semantic transaction' here names a runtime "
        "abstraction, not a newly trained neural model.",
        "It is close prior work for composed effect/authority boundaries. Our study evaluates "
        "a particular booking claim/repair contract and does not establish that Cordon lacks "
        "an equivalent capability or performs worse.",
    ),
    (
        "4. Revisable by Design - A Theory of Streaming LLM Agent Execution",
        "Theory and revision-recovery algorithm; arXiv preprint",
        "https://arxiv.org/abs/2604.23283v1",
        "The paper studies users intervening while an agent is executing. Its action taxonomy "
        "distinguishes idempotent, reversible, compensable and irreversible actions. It "
        "explains how the action space constrains what revision can achieve and proposes a "
        "rollback-based recovery algorithm. The 'model' includes a formal execution model, "
        "which is different from an LLM's learned weights.",
        "It prevents us from claiming that concurrent revisions or irreversible consequences "
        "are new ideas. Our experiment concerns frozen booking implementations and measured "
        "communication endpoints, not a stronger theorem about revisability.",
    ),
    (
        "5. REVISE - Validity-Guided Recovery for Online Revisions in Agent Workflows",
        "Validity-guided workflow runtime; arXiv preprint",
        "https://arxiv.org/html/2609.00643v1",
        "REVISE uses recorded data/control dependencies to determine which workflow work a "
        "changed instruction invalidates. It preserves work whose validity is established, "
        "recomputes affected regions, and revalidates before commit. Incomplete provenance "
        "causes more conservative recovery. Its reported applications include "
        "LangGraph/LLMCompiler and Qwen3-14B; that is their evaluation setup, not our "
        "campaign's model.",
        "Our protocol also respects accepted revisions, but our study does not measure "
        "selective recomputation savings or compare algorithms directly. A revision counter "
        "alone is not a novelty claim.",
    ),
    (
        "6. DART - Semantic Recoverability for Structured Tool Agents",
        "Recovery-boundary framework; arXiv preprint",
        "https://arxiv.org/abs/2605.23311v1",
        "DART asks when restoring a local checkpoint remains meaningful after downstream work "
        "has already committed. It identifies admissible restore boundaries under dependency "
        "and effect constraints rather than assuming that mechanically restoring bytes is "
        "enough. The framework can block a restore that would invalidate committed work. It is "
        "not an interchangeable model API.",
        "This reinforces the distinction between local recovery and external consequences. Our "
        "study measures booking/evidence/playback behavior and cannot claim to replace DART or "
        "outperform its evaluated recovery cases.",
    ),
    (
        "7. Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures",
        "Verification-aware tool wrapper; arXiv preprint",
        "https://arxiv.org/abs/2608.02645v1",
        "The work examines tool behavior such as a timeout after dispatch, delayed visibility, "
        "and partial updates. Its wrapper combines postcondition checking, verification before "
        "retry, and idempotency keys. The key idea is strengthening interaction semantics "
        "without requiring a new underlying language model.",
        "Those protections belong in a competent baseline, which is why our B3 includes "
        "related safeguards. Our incremental comparison concerns claim/repair packages beyond "
        "that baseline. We did not reproduce this paper's model/task results as part of the "
        "1,500 originals.",
    ),
    (
        "8. Tool Receipts, Not Zero-Knowledge Proofs",
        "Claim/evidence verification framework; arXiv preprint",
        "https://arxiv.org/html/2603.10060v1",
        "The paper links response claims to recorded tool executions and classifies their "
        "epistemic source. Its described runtime creates signed tool receipts and checks "
        "statements against them. A receipt is practical evidence about execution; it is not a "
        "zero-knowledge proof that every inference is correct. The framework and its benchmark "
        "are different objects from a trained base model.",
        "Our receipt objects additionally participate in the implemented "
        "revision/resource/claim contract. Receipt-based verification itself is not our "
        "invention. We make no direct detection-rate comparison against this paper.",
    ),
    (
        "9. Skantze and Hjalmarsson - Towards Incremental Speech Generation in Dialogue Systems",
        "SIGDIAL 2010 speech-generation research",
        "https://aclanthology.org/W10-4301/",
        "This work considers producing speech incrementally while interpretation and response "
        "planning continue. Self-monitoring and revision matter because later input can change "
        "what should be said. It is a dialogue-system generation approach, not a contemporary "
        "foundation-model API.",
        "It establishes that incremental output and correction have a long research history. "
        "Our focus is the connection to external booking evidence and the measured withdrawal "
        "endpoint. Our tones do not reproduce a human speech-generation evaluation.",
    ),
    (
        "10. PACE - A Playback-Aligned Context Engine for LLM-Based Full-Duplex Voice Dialogue",
        "Playback/context middleware and benchmark; arXiv preprint",
        "https://arxiv.org/html/2608.07631v1",
        "PACE addresses divergence between generated output, client playback and model-facing "
        "context. It records playback progress and repairs context after interruption, with an "
        "actual audio-only path through a black-box realtime voice model. It distinguishes "
        "playback evidence from attention/comprehension and discusses conditions needed for "
        "semantic alignment.",
        "It is close prior work, not a competitor we tested. Our outcome is booking claim "
        "support and corrective communication under scripted proxies. PACE's own configuration "
        "labels, including P1, are unrelated to our P1 arm.",
    ),
    (
        "11. Tau-bench - Tool-Agent-User Interaction in Real-World Domains",
        "Interactive evaluation benchmark; 2024 paper",
        "https://arxiv.org/abs/2406.12045",
        "Tau-bench supplies tool interfaces, domain policies and simulated users to evaluate "
        "interactive agents. It checks final database state against annotated goals and "
        "examines repeated-run reliability through pass^k. A benchmark is a test environment "
        "and scoring protocol, not a foundation model.",
        "Its final-state approach is relevant background, but our instrument separately "
        "reports evidence/exposure/correction. Our 91% cannot be compared to its success rates "
        "because tasks, input paths, models and conditions differ. We did not claim a new "
        "leaderboard record.",
    ),
    (
        "12. Tau-Voice - Full-Duplex Voice Agents on Real-World Domains",
        "Grounded voice-agent benchmark; arXiv preprint",
        "https://arxiv.org/abs/2603.13686",
        "Tau-Voice evaluates full-duplex voice interaction on grounded tasks, including "
        "realistic audio conditions and verifiable task completion. It connects voice "
        "interaction quality with tool-based goals. It is a benchmark for evaluating agents, "
        "not the name of a single voice model.",
        "Our typed-input/tone path does not measure accent robustness, recognition, natural "
        "conversation or its voice capability gap. The two studies motivate related questions "
        "but do not share a denominator. A future real-speech evaluation would need its own "
        "reviewed protocol.",
    ),
]
