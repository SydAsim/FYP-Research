"use client";

import Link from "next/link";
import { ApiError, DataRow, dateTime, text } from "@/lib/api";
import { statusTone } from "@/lib/status-tone";

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {action && <div className="heading-action">{action}</div>}
    </div>
  );
}

export function StatusChip({ value }: { value: unknown }) {
  const label = text(value, "UNKNOWN");
  const tone = statusTone(label);
  return (
    <span className={`status-chip ${tone}`}>
      <span aria-hidden="true" className="status-dot" />
      {label.replaceAll("_", " ")}
    </span>
  );
}

export function Identifier({ value, href }: { value: unknown; href?: string }) {
  const id = text(value);
  return (
    <span className="identifier">
      {href ? (
        <Link href={href} title={id}>
          {id.slice(0, 8)}…
        </Link>
      ) : (
        <span title={id}>{id.slice(0, 8)}…</span>
      )}
      <button
        type="button"
        title="Copy identifier"
        aria-label={`Copy ${id}`}
        onClick={() => void navigator.clipboard?.writeText(id)}
      >
        ⧉
      </button>
    </span>
  );
}

export function ProblemPanel({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const apiError = error instanceof ApiError ? error : null;
  const title = apiError?.problem.title ?? "Could not load this view";
  return (
    <div className="state-panel error-panel" role="alert">
      <div className="state-icon">!</div>
      <h2>{title}</h2>
      <p>
        {apiError?.problem.detail ?? "Check your connection and try again."}
      </p>
      {apiError?.status === 409 && (
        <p>The record changed. Reload before submitting a new command.</p>
      )}
      {apiError?.problem.trace_id && (
        <p className="mono subtle">Trace {apiError.problem.trace_id}</p>
      )}
      {onRetry && (
        <button className="button secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title = "No records yet",
  detail,
}: {
  title?: string;
  detail?: string;
}) {
  return (
    <div className="state-panel empty-panel">
      <div className="state-icon">◇</div>
      <h2>{title}</h2>
      <p>
        {detail ??
          "Records appear here when the durable workflow creates them."}
      </p>
    </div>
  );
}

export function LoadingState() {
  return (
    <div className="loading-stack" role="status" aria-label="Loading">
      <div className="skeleton wide" />
      <div className="skeleton" />
      <div className="skeleton" />
    </div>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: unknown;
  detail?: string;
  tone?: string;
}) {
  return (
    <div className={`metric-card ${tone ?? ""}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{text(value, "—")}</div>
      {detail && <div className="metric-detail">{detail}</div>}
    </div>
  );
}

export function DataTable({
  rows,
  columns,
}: {
  rows: DataRow[];
  columns: {
    key: string;
    label: string;
    href?: (row: DataRow) => string;
    format?: "date" | "status" | "id";
  }[];
}) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={text(row.id ?? row.call_id, String(index))}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.format === "date" ? (
                    dateTime(row[column.key])
                  ) : column.format === "status" ? (
                    <StatusChip value={row[column.key]} />
                  ) : column.format === "id" ? (
                    <Identifier
                      value={row[column.key]}
                      href={column.href?.(row)}
                    />
                  ) : column.href ? (
                    <Link className="table-link" href={column.href(row)}>
                      {text(row[column.key])}
                    </Link>
                  ) : (
                    text(row[column.key])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Panel({
  title,
  children,
  action,
}: {
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
