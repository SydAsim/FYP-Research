"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiGet, dateTime, summarySchema, text } from "@/lib/api";
import {
  Identifier,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
  StatusChip,
} from "./ui";

export function CallSummaryView({ callId }: { callId: string }) {
  const query = useQuery({
    queryKey: ["summary", callId],
    queryFn: () => apiGet(`/v1/calls/${callId}/summary`, summarySchema),
    refetchInterval: 5000,
  });
  if (query.isPending)
    return (
      <>
        <PageHeading title="Call summary" />
        <LoadingState />
      </>
    );
  if (query.isError)
    return (
      <ProblemPanel error={query.error} onRetry={() => void query.refetch()} />
    );
  const value = query.data;
  const confirmed =
    value.business_resolution === "RESOLVED_VERIFIED" &&
    value.verification_result === "SATISFIED" &&
    Boolean(value.receipt_id);
  const heading = confirmed
    ? "Current outcome verified"
    : value.business_resolution === "REPAIR_PENDING"
      ? "Correction pending"
      : value.business_resolution === "HANDOFF_CREATED"
        ? "Human follow-up created"
        : "Still checking";
  return (
    <>
      <PageHeading
        eyebrow="CALL OUTCOME"
        title="Call summary"
        description="Media completion and business resolution are separate."
        action={
          <Link href="/" className="button secondary">
            Return home
          </Link>
        }
      />
      <div
        className={`result-hero ${confirmed ? "good" : value.business_resolution === "REPAIR_PENDING" ? "bad" : ""}`}
      >
        <StatusChip
          value={confirmed ? "RESOLVED_VERIFIED" : value.business_resolution}
        />
        <h2>{heading}</h2>
        <p>{value.current_statement}</p>
        {confirmed && value.receipt_id && (
          <div>
            Current receipt <Identifier value={value.receipt_id} />
          </div>
        )}
      </div>
      <div className="two-column">
        <Panel title="Call and request">
          <dl className="key-values">
            <div className="key-value">
              <dt>Call</dt>
              <dd>
                <Identifier value={value.call_id} />
              </dd>
            </div>
            <div className="key-value">
              <dt>Media status</dt>
              <dd>
                <StatusChip value={value.media_status} />
              </dd>
            </div>
            <div className="key-value">
              <dt>Started</dt>
              <dd>{dateTime(value.started_at)}</dd>
            </div>
            <div className="key-value">
              <dt>Ended</dt>
              <dd>{dateTime(value.ended_at)}</dd>
            </div>
            <div className="key-value">
              <dt>Latest accepted revision</dt>
              <dd>{value.latest_revision}</dd>
            </div>
            <div className="key-value">
              <dt>Verification result</dt>
              <dd>
                <StatusChip value={value.verification_result} />
              </dd>
            </div>
          </dl>
          <h3>Current desired state</h3>
          <pre className="mono">
            {JSON.stringify(value.desired_state, null, 2)}
          </pre>
        </Panel>
        <Panel title="Recovery and evidence">
          <p>
            Unresolved operations continue after the call ends. Historical
            effects remain in the trace even after correction.
          </p>
          {value.handoff_id && (
            <p>
              Handoff <Identifier value={value.handoff_id} href="/handoffs" />
            </p>
          )}
          {value.repair_obligation_id && (
            <p className="alert error">
              Repair obligation{" "}
              <Identifier value={value.repair_obligation_id} />
            </p>
          )}
          {value.operations.length > 0 &&
            value.operations.map((op) => (
              <p key={text(op.id)}>
                <Identifier value={op.id} />{" "}
                <StatusChip value={op.processing_phase} />{" "}
                <StatusChip value={op.effect_knowledge} />
              </p>
            ))}
          <Link className="button secondary" href={`/calls/${callId}/trace`}>
            Inspect workflow trace →
          </Link>
        </Panel>
      </div>
    </>
  );
}
