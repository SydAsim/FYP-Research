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
} from "./ui";

const schema = z.object({
  resident: rowSchema,
  tickets: z.array(rowSchema),
  appointments: z.array(rowSchema),
  notes: z.array(rowSchema),
  calls: z.array(rowSchema),
});

export function ResidentDetail({ id }: { id: string }) {
  const query = useQuery({
    queryKey: ["resident", id],
    queryFn: () => apiGet(`/v1/residents/${id}`, schema),
  });
  if (query.isPending)
    return (
      <>
        <PageHeading title="Resident record" />
        <LoadingState />
      </>
    );
  if (query.isError)
    return (
      <ProblemPanel error={query.error} onRetry={() => void query.refetch()} />
    );
  const { resident, tickets, appointments, notes, calls } = query.data;
  return (
    <>
      <PageHeading
        eyebrow="SYNTHETIC RESIDENT"
        title={text(resident.display_name)}
        description="Maintenance access, scheduling, and communication data only."
        action={
          <Link className="button secondary" href="/residents">
            ← Residents
          </Link>
        }
      />
      <div className="alert info">
        This record is synthetic. Actor binding:{" "}
        <span className="mono">{text(resident.subject)}</span>. No medical
        information is held in this view.
      </div>
      <Panel title="Overview">
        <KeyValues
          data={resident}
          keys={[
            { key: "id", label: "Resident ID" },
            { key: "property_name", label: "Property" },
            { key: "unit_ref", label: "Unit" },
            { key: "timezone", label: "IANA zone" },
            { key: "version", label: "Resource version" },
          ]}
        />
        <div className="two-column">
          <div>
            <h3>Contact and access</h3>
            <pre className="mono">
              {JSON.stringify(resident.contact_json ?? {}, null, 2)}
            </pre>
          </div>
          <div>
            <h3>Scheduling preference</h3>
            <pre className="mono">
              {JSON.stringify(
                resident.scheduling_preference_json ?? {},
                null,
                2,
              )}
            </pre>
          </div>
        </div>
      </Panel>
      <Panel title="Maintenance tickets">
        {tickets.length ? (
          <DataTable
            rows={tickets}
            columns={[
              { key: "id", label: "Ticket", format: "id" },
              { key: "issue_type", label: "Issue" },
              { key: "description", label: "Description" },
              { key: "status", label: "Status", format: "status" },
            ]}
          />
        ) : (
          <EmptyState title="No tickets" />
        )}
      </Panel>
      <Panel title="Appointments">
        {appointments.length ? (
          <DataTable
            rows={appointments}
            columns={[
              {
                key: "id",
                label: "Appointment",
                format: "id",
                href: (row) => `/appointments/${row.id}`,
              },
              { key: "starts_at", label: "Start", format: "date" },
              { key: "timezone", label: "Zone" },
              { key: "version", label: "Version" },
            ]}
          />
        ) : (
          <EmptyState title="No appointments" />
        )}
      </Panel>
      <div className="two-column">
        <Panel title="Notes and preferences">
          {notes.length ? (
            <DataTable
              rows={notes}
              columns={[
                { key: "category", label: "Category" },
                { key: "note_text", label: "Note" },
                { key: "source", label: "Source" },
                { key: "created_at", label: "Created", format: "date" },
              ]}
            />
          ) : (
            <EmptyState title="No notes" />
          )}
        </Panel>
        <Panel title="Calls">
          {calls.length ? (
            <DataTable
              rows={calls}
              columns={[
                {
                  key: "id",
                  label: "Call",
                  format: "id",
                  href: (row) => `/calls/${row.id}/trace`,
                },
                { key: "media_status", label: "Media", format: "status" },
                { key: "started_at", label: "Started", format: "date" },
              ]}
            />
          ) : (
            <EmptyState title="No calls" />
          )}
        </Panel>
      </div>
    </>
  );
}
