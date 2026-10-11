"use client";

import { ResourceList } from "@/components/resource-list";

export default function Page() {
  return (
    <ResourceList
      eyebrow="CALL JOURNAL"
      title="Call history"
      description="Media completion is distinct from business resolution."
      path="/v1/calls"
      columns={[
        {
          key: "call_id",
          label: "Call",
          format: "id",
          href: (row) => `/call/${row.call_id}/summary`,
        },
        { key: "actor_name", label: "Synthetic caller" },
        { key: "started_at", label: "Started", format: "date" },
        { key: "ended_at", label: "Ended", format: "date" },
        { key: "media_status", label: "Media", format: "status" },
        { key: "current_revision", label: "Revision" },
        {
          key: "workflow_id",
          label: "Trace",
          format: "id",
          href: (row) => `/calls/${row.call_id}/trace`,
        },
      ]}
    />
  );
}
