"use client";

import { ResourceList } from "@/components/resource-list";

export default function Page() {
  return (
    <ResourceList
      eyebrow="OPERATIONS"
      title="Appointments"
      description="Authoritative rows with current receipt visibility. A stored row alone is not a verified outcome."
      path="/v1/appointments"
      columns={[
        {
          key: "id",
          label: "Appointment",
          format: "id",
          href: (row) => `/appointments/${row.id}`,
        },
        { key: "resident_name", label: "Resident" },
        { key: "starts_at", label: "Start", format: "date" },
        { key: "timezone", label: "IANA zone" },
        { key: "resource_key", label: "Resource" },
        { key: "observed_version", label: "Version" },
        { key: "verification_label", label: "Verification", format: "status" },
      ]}
      transform={(row) => ({
        ...row,
        observed_version: row.version,
        verification_label: row.current_receipt_id ? "SATISFIED" : "UNKNOWN",
      })}
    />
  );
}
