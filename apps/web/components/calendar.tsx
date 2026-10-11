"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { apiGet, rowsSchema, text } from "@/lib/api";
import { LoadingState, PageHeading, Panel, ProblemPanel } from "./ui";

export function CalendarView() {
  const [month, setMonth] = useState(
    () => new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  );
  const start = new Date(
    month.getFullYear(),
    month.getMonth(),
    1,
  ).toISOString();
  const end = new Date(
    month.getFullYear(),
    month.getMonth() + 1,
    1,
  ).toISOString();
  const query = useQuery({
    queryKey: ["calendar", start],
    queryFn: () =>
      apiGet(
        `/v1/appointments?limit=100&from=${encodeURIComponent(start)}&to=${encodeURIComponent(end)}`,
        rowsSchema,
      ),
  });
  const firstWeekday = new Date(
    month.getFullYear(),
    month.getMonth(),
    1,
  ).getDay();
  const days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const cells = Array.from(
    { length: Math.ceil((firstWeekday + days) / 7) * 7 },
    (_, index) => index - firstWeekday + 1,
  );
  return (
    <>
      <PageHeading
        eyebrow="SCHEDULE"
        title="Calendar"
        description="Only a current applicable verification receipt produces a verified badge."
        action={
          <Link href="/appointments" className="button secondary">
            List view →
          </Link>
        }
      />
      <Panel
        title={month.toLocaleString(undefined, {
          month: "long",
          year: "numeric",
        })}
        action={
          <div className="filter-row">
            <button
              className="button secondary"
              aria-label="Previous month"
              onClick={() =>
                setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))
              }
            >
              ←
            </button>
            <button
              className="button secondary"
              onClick={() =>
                setMonth(
                  new Date(new Date().getFullYear(), new Date().getMonth(), 1),
                )
              }
            >
              Today
            </button>
            <button
              className="button secondary"
              aria-label="Next month"
              onClick={() =>
                setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))
              }
            >
              →
            </button>
          </div>
        }
      >
        {query.isPending ? (
          <LoadingState />
        ) : query.isError ? (
          <ProblemPanel
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        ) : (
          <>
            <div
              className="calendar-grid"
              role="grid"
              aria-label="Appointments by day"
            >
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((name) => (
                <div className="calendar-head" key={name}>
                  {name}
                </div>
              ))}
              {cells.map((day, index) => {
                const date = new Date(
                  month.getFullYear(),
                  month.getMonth(),
                  day,
                );
                const entries = query.data.filter(
                  (row) =>
                    typeof row.starts_at === "string" &&
                    new Date(row.starts_at).toDateString() ===
                      date.toDateString(),
                );
                return (
                  <div
                    className={`calendar-cell ${day < 1 || day > days ? "calendar-outside" : ""}`}
                    key={index}
                    role="gridcell"
                  >
                    <span className="calendar-day">{date.getDate()}</span>
                    {entries.map((row) => (
                      <Link
                        href={`/appointments/${row.id}`}
                        className={`calendar-entry ${row.current_receipt_id ? "verified" : "unverified"}`}
                        key={text(row.id)}
                      >
                        <strong>
                          {new Date(text(row.starts_at)).toLocaleTimeString(
                            [],
                            { hour: "2-digit", minute: "2-digit" },
                          )}
                        </strong>
                        <span>
                          {row.current_receipt_id ? "Verified" : "Checking"}
                        </span>
                      </Link>
                    ))}
                  </div>
                );
              })}
            </div>
            {query.data.length === 100 && (
              <p className="alert">
                The month contains at least 100 rows. Use the paginated
                appointment list to inspect the rest.
              </p>
            )}
          </>
        )}
      </Panel>
      <div className="alert info">
        Amber striped entries are stored appointment rows without a current
        applicable verification receipt. They are not outcome confirmations.
      </div>
    </>
  );
}
