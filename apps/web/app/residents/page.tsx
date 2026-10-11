"use client";

import { ResourceList } from "@/components/resource-list";

export default function Page() {
  return (
    <ResourceList
      eyebrow="SYNTHETIC DIRECTORY"
      title="Residents"
      description="Only synthetic maintenance-domain identities are included."
      path="/v1/residents"
      columns={[
        {
          key: "id",
          label: "Resident",
          format: "id",
          href: (row) => `/residents/${row.id}`,
        },
        {
          key: "display_name",
          label: "Name",
          href: (row) => `/residents/${row.id}`,
        },
        { key: "property_name", label: "Property" },
        { key: "unit_ref", label: "Unit" },
        { key: "open_tickets", label: "Open tickets" },
        { key: "timezone", label: "IANA zone" },
      ]}
    />
  );
}
