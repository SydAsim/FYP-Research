"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { z } from "zod";
import { apiGet, dateTime, DataRow, rowSchema, text } from "@/lib/api";
import {
  EmptyState,
  Identifier,
  LoadingState,
  MetricCard,
  PageHeading,
  Panel,
  ProblemPanel,
  StatusChip,
} from "./ui";

const schema = z.object({
  call: rowSchema,
  workflows: z.array(rowSchema),
  operations: z.array(rowSchema),
  repairs: z.array(rowSchema),
  events: z.array(rowSchema),
  voice_events: z.array(rowSchema),
  receipts: z.array(rowSchema),
  segments: z.array(rowSchema),
  playback_events: z.array(rowSchema),
  utterances: z.array(rowSchema),
});
const tracks = [
  "ALL",
  "INTENT",
  "OPERATION",
  "VERIFICATION",
  "SPEECH",
  "VOICE",
] as const;

function eventTrack(event: DataRow): string {
  const name = text(event.event_name ?? event.event_type);
  if (/Revision|Intent|Utterance/i.test(name)) return "INTENT";
  if (/Verif|Receipt|Evidence/i.test(name)) return "VERIFICATION";
  if (/Speech|Claim|Permit|Playback|Repair|Audio/i.test(name)) return "SPEECH";
  if (event.raw_json) return "VOICE";
  return "OPERATION";
}

export function WorkflowTrace({ callId }: { callId: string }) {
  const query = useQuery({
    queryKey: ["trace", callId],
    queryFn: () => apiGet(`/v1/calls/${callId}/timeline`, schema),
    refetchInterval: 5000,
  });
  const [track, setTrack] = useState<string>("ALL");
  const [selected, setSelected] = useState<DataRow | null>(null);
  if (query.isPending)
    return (
      <>
        <PageHeading title="Workflow trace" />
        <LoadingState />
      </>
    );
  if (query.isError)
    return (
      <ProblemPanel error={query.error} onRetry={() => void query.refetch()} />
    );
  const {
    call,
    workflows,
    operations,
    receipts,
    segments,
    playback_events: playback,
    repairs,
    voice_events: voice,
    events,
  } = query.data;
  const workflow = workflows.at(-1);
  const current = operations.find(
    (op) =>
      op.workflow_id === workflow?.id &&
      op.intent_revision === workflow?.current_revision &&
      op.applicability === "CURRENT",
  );
  const merged: DataRow[] = [
    ...events,
    ...voice.map((item): DataRow => ({
      ...item,
      event_name: item.event_type,
      occurred_at: item.occurred_at,
    })),
  ].sort(
    (a, b) =>
      new Date(text(a.occurred_at)).getTime() -
      new Date(text(b.occurred_at)).getTime(),
  );
  const filtered = merged.filter(
    (event) => track === "ALL" || eventTrack(event) === track,
  );
  return (
    <>
      <PageHeading
        eyebrow="CAUSAL AUDIT"
        title="Workflow trace"
        description="Events are ordered by recorded occurrence; raw provider payloads remain available beside normalized events."
        action={
          <Link className="button secondary" href={`/call/${callId}/summary`}>
            Call summary →
          </Link>
        }
      />
      <div className="metric-grid">
        <MetricCard
          label="Accepted revision"
          value={workflow?.current_revision ?? 0}
          detail="Latest accepted intent"
        />
        <MetricCard
          label="Processing phase"
          value={current?.processing_phase ?? "NO OPERATION"}
        />
        <MetricCard
          label="Effect knowledge"
          value={current?.effect_knowledge ?? "UNKNOWN"}
        />
        <MetricCard
          label="Speech eligibility"
          value={current?.speech_eligibility ?? "BLOCKED"}
        />
      </div>
      <div className="alert info">
        Conversation: <strong>{text(call.conversation_phase)}</strong> ·
        Applicability:{" "}
        <strong>{text(current?.applicability, "NO OPERATION")}</strong> ·
        Provider truth / independent oracle:{" "}
        <strong>not recorded in this trace</strong>. These dimensions are not
        one linear state.
      </div>
      {repairs.some(
        (item) => item.state !== "CLOSED" && item.state !== "REPAIR_PLAYED",
      ) && (
        <div className="alert error">
          A stale decisive claim was exposed. Durable repair is pending or
          escalated.
        </div>
      )}
      <div className="two-column">
        <Panel
          title="Durable event timeline"
          action={<span className="subtle">{filtered.length} events</span>}
        >
          <div className="filter-row">
            {tracks.map((name) => (
              <button
                className={`button ${track === name ? "" : "secondary"}`}
                key={name}
                onClick={() => setTrack(name)}
              >
                {name}
              </button>
            ))}
          </div>
          {filtered.length ? (
            <div className="event-list">
              {filtered.map((event) => (
                <button
                  className="event"
                  style={{
                    textAlign: "left",
                    borderTop: 0,
                    borderRight: 0,
                    borderBottom: 0,
                    background: "transparent",
                    width: "100%",
                  }}
                  key={text(event.id)}
                  onClick={() => setSelected(event)}
                >
                  <strong>{text(event.event_name)}</strong>{" "}
                  <StatusChip value={eventTrack(event)} />
                  <span className="event-time">
                    {dateTime(event.occurred_at)} · revision{" "}
                    {text(event.intent_revision)} · sequence{" "}
                    {text(event.workflow_sequence)}
                  </span>
                  <Identifier value={event.id} />
                </button>
              ))}
            </div>
          ) : (
            <EmptyState title="No events on this track" />
          )}
        </Panel>
        <Panel title="Event inspector">
          {selected ? (
            <>
              <h3>{text(selected.event_name)}</h3>
              <p>
                <Identifier value={selected.id} />
              </p>
              <p>
                Trace <span className="mono">{text(selected.trace_id)}</span>
              </p>
              <h3>Normalized</h3>
              <pre className="mono">
                {JSON.stringify(
                  selected.normalized_json ?? selected.payload ?? {},
                  null,
                  2,
                )}
              </pre>
              <h3>Raw provider event</h3>
              <pre className="mono">
                {JSON.stringify(selected.raw_json ?? {}, null, 2)}
              </pre>
            </>
          ) : (
            <EmptyState
              title="Choose an event"
              detail="Select a timeline entry to inspect recorded facts and causal identifiers."
            />
          )}
        </Panel>
      </div>
      <div className="two-column">
        <Panel title="Verification receipts">
          {receipts.length ? (
            receipts.map((receipt) => (
              <p key={text(receipt.id)}>
                <Identifier value={receipt.id} />{" "}
                <StatusChip value={receipt.result} /> revision{" "}
                {text(receipt.intent_revision)} · resource version{" "}
                {text(receipt.observed_resource_version)} · invalidated{" "}
                {text(receipt.invalidated_at, "no")}
              </p>
            ))
          ) : (
            <EmptyState title="No receipts" />
          )}
        </Panel>
        <Panel title="Speech and exposure">
          <p>
            {segments.length} durable segments · {playback.length} playback
            acknowledgements · {repairs.length} repair obligations
          </p>
          {segments.map((segment) => (
            <p key={text(segment.id)}>
              <Identifier value={segment.id} />{" "}
              <StatusChip value={segment.state} /> revision{" "}
              {text(segment.intent_revision)} · played{" "}
              {text(segment.last_played_ms)} ms
            </p>
          ))}
        </Panel>
      </div>
      <div className="alert">
        Deterministic replay bundles and independent oracle grades are produced
        by the Phase 6 research harness. No grade is inferred from controller
        state.
      </div>
    </>
  );
}
