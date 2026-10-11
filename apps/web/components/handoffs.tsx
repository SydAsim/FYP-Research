"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiGet, apiPost, rowSchema, rowsSchema, text } from "@/lib/api";
import {
  EmptyState,
  Identifier,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
  StatusChip,
} from "./ui";

export function HandoffsView() {
  const query = useQuery({
    queryKey: ["handoffs"],
    queryFn: () => apiGet("/v1/handoffs?limit=100", rowsSchema),
    refetchInterval: 10000,
  });
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [note, setNote] = useState("");

  async function change(
    row: Record<string, unknown>,
    action: "acknowledge" | "resolve",
  ) {
    const id = text(row.id);
    setBusy(id);
    setError(null);
    try {
      await apiPost(
        `/v1/handoffs/${id}/${action}`,
        {
          command_id: crypto.randomUUID(),
          expected_state: row.state,
          note: action === "resolve" ? note : null,
          administrative_closure: action === "resolve",
        },
        rowSchema,
      );
      setNote("");
      void query.refetch();
    } catch (caught) {
      setError(caught);
      void query.refetch();
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="HUMAN REVIEW"
        title="Human handoffs"
        description="Unresolved maintenance outcomes are routed to people with known and unknown facts visible."
      />
      <div className="alert info">
        Administrative closure records a human decision. It does not create a
        verification receipt or claim the requested action succeeded.
      </div>
      {error !== null && (
        <ProblemPanel
          error={error}
          onRetry={() => {
            setError(null);
            void query.refetch();
          }}
        />
      )}
      <Panel title="Handoff queue">
        {query.isPending ? (
          <LoadingState />
        ) : query.isError ? (
          <ProblemPanel
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        ) : query.data.length === 0 ? (
          <EmptyState
            title="No open handoffs"
            detail="Handoffs appear when durable recovery needs human review."
          />
        ) : (
          <div className="event-list">
            {query.data.map((row) => (
              <div className="event" key={text(row.id)}>
                <div className="filter-row">
                  <strong>
                    <Identifier value={row.id} />
                  </strong>
                  <StatusChip value={row.priority} />
                  <StatusChip value={row.state} />
                </div>
                <p>
                  {text(row.reason_code)} · {text(row.resident_name)} · workflow{" "}
                  <Identifier value={row.workflow_id} />
                </p>
                <p>
                  <strong>Known:</strong> {JSON.stringify(row.known_facts)}
                  <br />
                  <strong>Unknown:</strong> {JSON.stringify(row.unknown_facts)}
                </p>
                <p className="subtle">Deadline: {text(row.deadline_at)}</p>
                {row.state === "OPEN" && (
                  <button
                    className="button secondary"
                    disabled={busy === row.id}
                    onClick={() => void change(row, "acknowledge")}
                  >
                    Acknowledge
                  </button>
                )}
                {row.state === "ACKNOWLEDGED" && (
                  <div className="filter-row">
                    <label className="field">
                      Administrative closure note
                      <input
                        value={note}
                        onChange={(event) => setNote(event.target.value)}
                      />
                    </label>
                    <button
                      className="button secondary"
                      disabled={busy === row.id || !note.trim()}
                      onClick={() => void change(row, "resolve")}
                    >
                      Close administratively
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>
    </>
  );
}
