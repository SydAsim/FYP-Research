"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, rowSchema, text } from "@/lib/api";
import { LoadingState, PageHeading, Panel, ProblemPanel } from "./ui";

export function SettingsView() {
  const query = useQuery({
    queryKey: ["settings"],
    queryFn: () => apiGet("/v1/settings", rowSchema),
  });
  return (
    <>
      <PageHeading
        eyebrow="SYSTEM PROFILE"
        title="Settings"
        description="Read-only configuration. Correctness-relevant settings are versioned and frozen with an evaluation run."
      />
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ProblemPanel
          error={query.error}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <div className="two-column">
          <Panel title="Environment">
            <dl className="key-values">
              {Object.entries(query.data).map(([key, value]) => (
                <div className="key-value" key={key}>
                  <dt>{key.replaceAll("_", " ")}</dt>
                  <dd>{text(value)}</dd>
                </div>
              ))}
            </dl>
          </Panel>
          <Panel title="Research boundaries">
            <p>
              PostgreSQL retains all correctness facts. Redis is optional for
              ephemeral coordination.
            </p>
            <p>
              The strict research arm uses provider-neutral cascaded STT, LLM,
              and TTS. Native audio is an optional comparison adapter.
            </p>
            <p>
              Decisive outcome speech requires a current claim permit,
              applicable receipt, and playback gate.
            </p>
            <div className="alert">
              No secrets or provider credentials are exposed on this page.
            </div>
          </Panel>
        </div>
      )}
    </>
  );
}
