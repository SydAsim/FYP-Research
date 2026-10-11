export type StatusTone = "good" | "bad" | "warn" | "neutral";

const good = new Set(["SATISFIED", "RESOLVED_VERIFIED", "REPAIR_PLAYED"]);
const bad = new Set(["VIOLATED", "FAILED", "OVERDUE", "REPAIR_PENDING"]);
const warn = new Set([
  "UNKNOWN",
  "UNRESOLVED_RECOVERING",
  "HANDOFF_CREATED",
  "RECONCILING",
  "REPAIR_REQUIRED",
  "OPEN",
  "PENDING",
  "ESCALATED",
]);

export function statusTone(value: string): StatusTone {
  if (good.has(value)) return "good";
  if (bad.has(value)) return "bad";
  if (warn.has(value)) return "warn";
  return "neutral";
}
