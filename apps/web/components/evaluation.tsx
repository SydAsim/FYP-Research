"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { z } from "zod";
import { apiGet, rowSchema, rowsSchema, text } from "@/lib/api";
import {
  DataTable,
  EmptyState,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
  StatusChip,
} from "./ui";

const runSchema = z.object({
  run: rowSchema,
  cases: z.array(rowSchema),
  executions: z.array(rowSchema),
  metrics: z.array(rowSchema),
});

export function EvaluationOverview() {
  const query = useQuery({
    queryKey: ["evaluation-runs"],
    queryFn: () => apiGet("/v1/evaluation/runs?limit=100", rowsSchema),
  });
  return (
    <>
      <PageHeading
        eyebrow="RESEARCH EVALUATION"
        title="Evaluation"
        description="Independent scenarios, executions, exclusions, and timeouts are reported separately."
        action={
          <Link className="button" href="/experiments/new">
            New experiment →
          </Link>
        }
      />
      <div className="alert info">
        B0, B1, B2, B3, P1, and P2 are explicit system arms. Repetitions do not
        increase the independent scenario count.
      </div>
      <Panel title="Evaluation runs">
        {query.isPending ? (
          <LoadingState />
        ) : query.isError ? (
          <ProblemPanel
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        ) : query.data.length ? (
          <DataTable
            rows={query.data}
            columns={[
              {
                key: "id",
                label: "Run",
                format: "id",
                href: (row) => `/evaluation/runs/${row.id}`,
              },
              {
                key: "name",
                label: "Name",
                href: (row) => `/evaluation/runs/${row.id}`,
              },
              { key: "status", label: "Status", format: "status" },
              { key: "independent_scenarios", label: "Independent scenarios" },
              { key: "executions", label: "Executions" },
              { key: "exclusions", label: "Exclusions" },
              { key: "timeouts", label: "Timeouts" },
              { key: "created_at", label: "Created", format: "date" },
            ]}
          />
        ) : (
          <EmptyState
            title="No evaluation runs"
            detail="Create a draft manifest to prepare a run. The independent harness is implemented in Phase 6."
          />
        )}
      </Panel>
      <div className="two-column">
        <Panel title="Primary endpoints">
          <p>
            Correction success, unsupported confirmation rate, clean task
            success, outcome coverage, and p50/p95 response latency require
            independent oracle records and denominators.
          </p>
        </Panel>
        <Panel title="Analysis guardrails">
          <p>
            Confidence intervals are not shown until execution metrics contain
            valid numerators, denominators, exclusions, and a recorded analysis
            version.
          </p>
        </Panel>
      </div>
    </>
  );
}

export function EvaluationRunDetail({ id }: { id: string }) {
  const query = useQuery({
    queryKey: ["evaluation-run", id],
    queryFn: () => apiGet(`/v1/evaluation/runs/${id}`, runSchema),
  });
  if (query.isPending)
    return (
      <>
        <PageHeading title="Evaluation run" />
        <LoadingState />
      </>
    );
  if (query.isError)
    return (
      <ProblemPanel error={query.error} onRetry={() => void query.refetch()} />
    );
  const { run, cases, executions, metrics } = query.data;
  const arms = ["B0", "B1", "B2", "B3", "P1", "P2"];
  return (
    <>
      <PageHeading
        eyebrow="FROZEN MANIFEST"
        title={text(run.name)}
        description={`Run ${id}`}
        action={
          <Link className="button secondary" href="/evaluation">
            ← All runs
          </Link>
        }
      />
      <div className="panel">
        <div className="filter-row">
          <StatusChip value={run.status} />
          <span>
            Manifest hash{" "}
            <span className="mono">{text(run.manifest_hash)}</span>
          </span>
        </div>
        <p>
          Source commit {text(run.source_commit)} · migration{" "}
          {text(run.migration_version)} · analysis {text(run.analysis_version)}
        </p>
        <pre className="mono">
          {JSON.stringify(run.manifest_json ?? {}, null, 2)}
        </pre>
      </div>
      <Panel title="Arm comparison">
        {executions.length ? (
          <DataTable
            rows={arms.map((arm) => ({
              arm,
              independent_scenarios: new Set(
                executions
                  .filter((item) => item.system_arm === arm)
                  .map((item) => item.case_id),
              ).size,
              executions: executions.filter((item) => item.system_arm === arm)
                .length,
              exclusions: executions.filter(
                (item) => item.system_arm === arm && item.status === "EXCLUDED",
              ).length,
              timeouts: executions.filter(
                (item) => item.system_arm === arm && item.status === "TIMEOUT",
              ).length,
            }))}
            columns={[
              { key: "arm", label: "System arm" },
              { key: "independent_scenarios", label: "Scenarios" },
              { key: "executions", label: "Executions" },
              { key: "exclusions", label: "Exclusions" },
              { key: "timeouts", label: "Timeouts" },
            ]}
          />
        ) : (
          <EmptyState title="No executions yet" />
        )}
      </Panel>
      <div className="two-column">
        <Panel title={`Scenarios (${cases.length})`}>
          {cases.length ? (
            <DataTable
              rows={cases}
              columns={[
                { key: "scenario_key", label: "Scenario" },
                { key: "fixture_hash", label: "Fixture hash" },
                { key: "seed", label: "Seed" },
              ]}
            />
          ) : (
            <EmptyState title="No scenarios" />
          )}
        </Panel>
        <Panel title={`Recorded metrics (${metrics.length})`}>
          {metrics.length ? (
            <DataTable
              rows={metrics}
              columns={[
                { key: "metric_name", label: "Metric" },
                { key: "numeric_value", label: "Value" },
                { key: "numerator", label: "Numerator" },
                { key: "denominator", label: "Denominator" },
              ]}
            />
          ) : (
            <EmptyState title="No metrics" />
          )}
        </Panel>
      </div>
      <div className="alert">
        Replay bundles and deterministic reruns require the independent Phase 6
        harness. This view does not grade controller state as oracle truth.
      </div>
    </>
  );
}
