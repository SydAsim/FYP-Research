"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { apiGet, DataRow, rowsSchema, text } from "@/lib/api";
import {
  DataTable,
  EmptyState,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
} from "./ui";

export interface ResourceColumn {
  key: string;
  label: string;
  format?: "date" | "status" | "id";
  href?: (row: DataRow) => string;
}

export function ResourceList({
  title,
  eyebrow,
  description,
  path,
  columns,
  empty,
  transform,
  action,
}: {
  title: string;
  eyebrow?: string;
  description?: string;
  path: string;
  columns: ResourceColumn[];
  empty?: string;
  transform?: (row: DataRow) => DataRow;
  action?: React.ReactNode;
}) {
  const [offset, setOffset] = useState(0);
  const [online, setOnline] = useState(() =>
    typeof navigator === "undefined" ? true : navigator.onLine,
  );
  useEffect(() => {
    const yes = () => setOnline(true);
    const no = () => setOnline(false);
    window.addEventListener("online", yes);
    window.addEventListener("offline", no);
    return () => {
      window.removeEventListener("online", yes);
      window.removeEventListener("offline", no);
    };
  }, []);
  const query = useQuery({
    queryKey: ["list", path, offset],
    queryFn: () =>
      apiGet(
        `${path}${path.includes("?") ? "&" : "?"}limit=25&offset=${offset}`,
        rowsSchema,
      ),
    retry: 1,
  });
  const data = query.data?.map((item) => transform?.(item) ?? item) ?? [];
  return (
    <>
      <PageHeading
        eyebrow={eyebrow}
        title={title}
        description={description}
        action={action}
      />
      {!online && (
        <div className="alert">
          Offline. Showing the last loaded view while waiting to reconnect.
        </div>
      )}
      {query.isFetching && !query.isPending && (
        <div className="alert info" role="status">
          Refreshing authoritative records…
        </div>
      )}
      <Panel title={title}>
        {query.isPending ? (
          <LoadingState />
        ) : query.isError ? (
          <ProblemPanel
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        ) : data.length === 0 ? (
          <EmptyState title={empty ?? `No ${title.toLowerCase()} yet`} />
        ) : (
          <DataTable rows={data} columns={columns} />
        )}
        <div className="pagination">
          <span>
            {query.isSuccess ? `${offset + 1}–${offset + data.length}` : "—"}{" "}
            shown · server paginated
          </span>
          <div>
            <button
              disabled={offset === 0 || query.isFetching}
              onClick={() => setOffset(Math.max(0, offset - 25))}
            >
              Previous
            </button>{" "}
            <button
              disabled={data.length < 25 || query.isFetching}
              onClick={() => setOffset(offset + 25)}
            >
              Next
            </button>
          </div>
        </div>
      </Panel>
    </>
  );
}

export function KeyValues({
  data,
  keys,
}: {
  data: DataRow;
  keys: { key: string; label: string; format?: "date" | "status" | "id" }[];
}) {
  return (
    <dl className="key-values">
      {keys.map((field) => (
        <div className="key-value" key={field.key}>
          <dt>{field.label}</dt>
          <dd>
            {field.format === "date" && typeof data[field.key] === "string"
              ? new Date(String(data[field.key])).toLocaleString()
              : text(data[field.key])}
          </dd>
        </div>
      ))}
    </dl>
  );
}
