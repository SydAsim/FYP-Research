# Commit-Aware Voice Agent: one-page overview

**What is the project?** A voice appointment agent that keeps track of what the caller now wants, what the provider actually did, and what the agent may safely say.

**The example.** You request maintenance at 3 PM. The provider books it but its reply is lost. You then ask for 4 PM. A timeout does not prove that 3 PM failed. Repeating the request could create another booking; stopping the assistant does not undo the first booking.

**How it works.** The server saves each accepted request in PostgreSQL. It records a stable operation before sending. If the result is uncertain, it checks the provider before another write. It then moves or compensates the old booking, verifies the current result and authorizes a specific confirmation. The model proposes the request; it cannot directly book or declare success.

**What if old speech already played?** The proposed full protocol records a persistent obligation to withdraw incompatible content and deliver a supported current update. Restarting a worker must not erase that responsibility. Sending audio is different from completed playback, and a client acknowledgement does not prove human understanding.

**What is the research question?** When do those additional rules protect a caller beyond a competent baseline's ordinary checks? B3 is that strong baseline; P1 adds bound speech permissions; P2 adds persistent corrective responsibility. Equal observable behaviour must receive equal grades.

**What is established?** Local code and PostgreSQL tests exercise revisions, unknown outcomes, permits, playback records and repair discovery. The revised six-fixture set ties at 5/6 business success in all three arms. Selected tests show extra freshness checks and explicit P2 withdrawal, not general superiority.

**What is proposed next?** A candidate with 500 new typed/scripted inputs: 300 clean, 100 hidden commit, 60 playback and 40 other. Three arms mean 1,500 planned executions, not 1,500 independent scenarios. All are unstarted. Calibration is separate. The target is a fixed simulator mixture, not real callers.

**What remains?** Supervisor review of scope, assumptions, power and observation scheduling, then a new freeze before evaluation. Real speech exposure, human understanding, general superiority and novelty remain unproven. The app is a research instrument; telephony transfer and a built-in dialer are future product work.
