"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { z } from "zod";
import { apiGet, rowSchema, text } from "@/lib/api";
import { KeyValues } from "./resource-list";
import {
  DataTable,
  EmptyState,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
  StatusChip,
} from "./ui";

const schema = z.object({
  appointment: rowSchema,
  effects: z.array(rowSchema),
  receipts: z.array(rowSchema),
});

export function AppointmentDetail({ id }: { id: string }) {
  const query = useQuery({
    queryKey: ["appointment", id],
    queryFn: () => apiGet(`/v1/appointments/${id}`, schema),
  });
  if (query.isPending)
    return (
      <>
        <PageHeading title="Appointment" />
        <LoadingState />
      </>
    );
  if (query.isError)
    return (
      <ProblemPanel error={query.error} onRetry={() => void query.refetch()} />
    );
  const { appointment, receipts, effects } = query.data;
  const receipt = receipts.find(
    (item) => item.id === appointment.current_receipt_id,
  );
  return (
    <>
      <PageHeading
        eyebrow="APPOINTMENT DETAIL"
        title="Appointment record"
        description="Stored status and current verification are shown separately."
        action={
          <Link className="button secondary" href="/appointments">
            ← Appointments
          </Link>
        }
      />
      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-label">Current evidence</div>
          <div className="metric-value">
            <StatusChip value={receipt ? "SATISFIED" : "UNKNOWN"} />
          </div>
          <div className="metric-detail">
            {receipt
              ? "Applicable receipt found"
              : "No applicable current receipt"}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Stored row state</div>
          <div className="metric-value" style={{ fontSize: 18 }}>
            {receipt ? text(appointment.status) : "Verification pending"}
          </div>
          <div className="metric-detail">
            {receipt
              ? "Matched to current evidence"
              : "Inspect the raw row in the audit trace"}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Row version</div>
          <div className="metric-value">{text(appointment.version)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Intent revision</div>
          <div className="metric-value">
            {text(appointment.source_intent_revision)}
          </div>
        </div>
      </div>
      <Panel title="Current authoritative record">
        <KeyValues
          data={appointment}
          keys={[
            { key: "id", label: "Appointment ID" },
            { key: "resident_id", label: "Resident ID" },
            { key: "ticket_id", label: "Ticket ID" },
            { key: "resource_key", label: "Resource" },
            { key: "starts_at", label: "Starts", format: "date" },
            { key: "ends_at", label: "Ends", format: "date" },
            { key: "timezone", label: "Original IANA time zone" },
            { key: "source_workflow_id", label: "Workflow" },
          ]}
        />
      </Panel>
      <div className="two-column">
        <Panel title="Effect history">
          {effects.length ? (
            <DataTable
              rows={effects}
              columns={[
                { key: "id", label: "Effect", format: "id" },
                { key: "operation_id", label: "Operation", format: "id" },
                { key: "effect_type", label: "Type" },
                { key: "created_at", label: "Created", format: "date" },
              ]}
            />
          ) : (
            <EmptyState title="No effect history" />
          )}
        </Panel>
        <Panel title="Verification history">
          {receipts.length ? (
            <DataTable
              rows={receipts}
              columns={[
                { key: "id", label: "Receipt", format: "id" },
                { key: "result", label: "Result", format: "status" },
                { key: "intent_revision", label: "Revision" },
                { key: "observed_resource_version", label: "Version" },
              ]}
            />
          ) : (
            <EmptyState title="No receipts" />
          )}
        </Panel>
      </div>
    </>
  );
}
