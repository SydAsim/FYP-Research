"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { z } from "zod";
import { apiGet, rowSchema, text } from "@/lib/api";
import {
  DataTable,
  EmptyState,
  LoadingState,
  MetricCard,
  PageHeading,
  Panel,
  ProblemPanel,
} from "./ui";

const schema = z.object({
  counts: rowSchema,
  recent_events: z.array(rowSchema),
  research_metrics_available: z.boolean(),
});

export function DashboardView() {
  const query = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiGet("/v1/dashboard/summary", schema),
    refetchInterval: 10000,
  });
  return (
    <>
      <PageHeading
        eyebrow="OPERATIONS OVERVIEW"
        title="Dashboard"
        description="Live counts are read from PostgreSQL. Research rates appear only after the independent evaluation harness produces them."
        action={
          <Link className="button" href="/">
            Start a call →
          </Link>
        }
      />
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ProblemPanel
          error={query.error}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <>
          <div className="metric-grid">
            <MetricCard
              label="Calls recorded"
              value={query.data.counts.calls}
              detail="Durable call sessions"
            />
            <MetricCard
              label="Corrected workflows"
              value={query.data.counts.corrected_workflows}
              detail="Current revision above 1"
            />
            <MetricCard
              label="Unknown effects"
              value={query.data.counts.unknown_effects}
              detail="Reconciliation may still be required"
              tone="warn"
            />
            <MetricCard
              label="Open repair obligations"
              value={query.data.counts.open_repairs}
              detail="Speech correction outstanding"
              tone="bad"
            />
          </div>
          <div className="two-column">
            <Panel title="Recent durable events">
              {query.data.recent_events.length ? (
                <DataTable
                  rows={query.data.recent_events}
                  columns={[
                    { key: "event_name", label: "Event" },
                    { key: "workflow_id", label: "Workflow", format: "id" },
                    { key: "intent_revision", label: "Revision" },
                    {
                      key: "occurred_at",
                      label: "UTC event time",
                      format: "date",
                    },
                  ]}
                />
              ) : (
                <EmptyState title="No events yet" />
              )}
            </Panel>
            <Panel title="Research health">
              <p>
                <strong>{text(query.data.counts.open_handoffs)}</strong> open
                human handoffs
              </p>
              <p>
                <strong>{text(query.data.counts.satisfied_receipts)}</strong>{" "}
                uninvalidated satisfied receipts
              </p>
              <div className="alert">
                Clean task success, unsupported confirmation rate, and latency
                confidence intervals are not available until Phase 6 records
                independent scenario metrics.
              </div>
              <Link href="/evaluation" className="button secondary">
                View evaluation →
              </Link>
            </Panel>
          </div>
        </>
      )}
    </>
  );
}
