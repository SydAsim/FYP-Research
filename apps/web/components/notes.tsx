"use client";

import { useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { apiGet, apiPost, rowSchema, rowsSchema, text } from "@/lib/api";
import {
  DataTable,
  EmptyState,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
} from "./ui";

const categories = [
  "SCHEDULING_PREFERENCE",
  "ACCESS_INSTRUCTION",
  "MAINTENANCE_CONTEXT",
  "COMMUNICATION_PREFERENCE",
  "FOLLOW_UP",
];

export function NotesView() {
  const notes = useQuery({
    queryKey: ["notes"],
    queryFn: () => apiGet("/v1/notes?limit=100", rowsSchema),
  });
  const residents = useQuery({
    queryKey: ["residents-for-notes"],
    queryFn: () => apiGet("/v1/residents?limit=100", rowsSchema),
  });
  const [residentId, setResidentId] = useState("");
  const [category, setCategory] = useState(categories[0]);
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const command = useRef<string | null>(null);
  const selected = residents.data?.find((row) => row.id === residentId);

  async function save() {
    if (!selected || !note.trim() || pending) return;
    setPending(true);
    setError(null);
    command.current ??= crypto.randomUUID();
    try {
      await apiPost(
        "/v1/notes",
        {
          command_id: command.current,
          resident_id: residentId,
          category,
          note_text: note.trim(),
          expected_resident_version: selected.version,
        },
        rowSchema,
      );
      command.current = null;
      setNote("");
      void notes.refetch();
      void residents.refetch();
    } catch (caught) {
      setError(caught);
      if ((caught as { status?: number }).status === 409)
        void residents.refetch();
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="RESIDENT CONTEXT"
        title="Notes and preferences"
        description="Human notes are versioned and scoped to synthetic maintenance data."
      />
      <div className="two-column">
        <Panel title="Add human note">
          <div className="filter-row">
            <label className="field">
              Synthetic resident
              <select
                value={residentId}
                onChange={(event) => {
                  setResidentId(event.target.value);
                  command.current = null;
                }}
              >
                <option value="">Select resident</option>
                {residents.data?.map((row) => (
                  <option key={text(row.id)} value={text(row.id)}>
                    {text(row.display_name)} · {text(row.unit_ref)}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Category
              <select
                value={category}
                onChange={(event) => {
                  setCategory(event.target.value);
                  command.current = null;
                }}
              >
                {categories.map((value) => (
                  <option key={value} value={value}>
                    {value.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="field">
            Maintenance or scheduling note
            <textarea
              value={note}
              maxLength={2000}
              onChange={(event) => {
                setNote(event.target.value);
                command.current = null;
              }}
            />
          </label>
          <p className="subtle">
            Expected resident version: {text(selected?.version)}. Extracted
            notes require separate server validation.
          </p>
          {error !== null && (
            <ProblemPanel
              error={error}
              onRetry={() => {
                setError(null);
                void residents.refetch();
              }}
            />
          )}
          <button
            className="button"
            disabled={!selected || !note.trim() || pending}
            onClick={() => void save()}
          >
            {pending ? "Saving…" : "Save note"}
          </button>
        </Panel>
        <Panel title="Scope policy">
          <p>
            Permitted: scheduling preferences, maintenance access instructions,
            communication preferences, maintenance context, and follow-up. Notes
            from a call remain provisional until validated by the server.
          </p>
          <div className="alert info">
            No medical workflows or emergency automation are part of this FYP.
          </div>
        </Panel>
      </div>
      <Panel title="Durable note history">
        {notes.isPending ? (
          <LoadingState />
        ) : notes.isError ? (
          <ProblemPanel
            error={notes.error}
            onRetry={() => void notes.refetch()}
          />
        ) : notes.data.length ? (
          <DataTable
            rows={notes.data}
            columns={[
              { key: "resident_name", label: "Resident" },
              { key: "category", label: "Category" },
              { key: "note_text", label: "Note" },
              { key: "source", label: "Source" },
              { key: "validated", label: "Validated" },
              { key: "created_at", label: "Created", format: "date" },
            ]}
          />
        ) : (
          <EmptyState title="No notes yet" />
        )}
      </Panel>
    </>
  );
}
