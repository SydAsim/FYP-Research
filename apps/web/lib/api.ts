import { z } from "zod";
import type { components } from "./api-types";

export type CallSession = components["schemas"]["CallSession"];
export type CallSummary = components["schemas"]["CallSummary"];
export type DataRow = Record<string, unknown>;

const problemSchema = z.looseObject({
  title: z.string(),
  detail: z.string().optional(),
  status: z.number(),
  trace_id: z.string().optional(),
  retryable: z.boolean().optional(),
});
export type ApiProblem = z.infer<typeof problemSchema>;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly problem: ApiProblem,
  ) {
    super(problem.detail ?? problem.title);
  }
}

export const rowSchema = z.record(z.string(), z.unknown());
export const rowsSchema = z.array(rowSchema);
export const configSchema = z.object({
  mode: z.literal("DEMO"),
  synthetic_resident_id: z.uuid().nullable(),
  livekit_url: z.string(),
  voice_path: z.string(),
  database: z.string(),
});
export const callSessionSchema = z.object({
  call_id: z.uuid(),
  workflow_id: z.uuid(),
  media_status: z.enum(["CREATED", "CONNECTING", "CONNECTED", "ENDED"]),
  livekit_room: z.string(),
  livekit_token: z.string(),
});
export const summarySchema = z.object({
  call_id: z.uuid(),
  media_status: z.string(),
  business_resolution: z.enum([
    "RESOLVED_VERIFIED",
    "RESOLVED_REFUSED",
    "UNRESOLVED_RECOVERING",
    "HANDOFF_CREATED",
    "REPAIR_PENDING",
  ]),
  latest_revision: z.number().int().nonnegative(),
  current_statement: z.string().nullable(),
  receipt_id: z.uuid().nullable(),
  handoff_id: z.uuid().nullable(),
  verification_result: z.enum(["SATISFIED", "VIOLATED", "UNKNOWN"]),
  desired_state: rowSchema,
  operations: rowsSchema,
  repair_obligation_id: z.uuid().nullable(),
  started_at: z.string(),
  ended_at: z.string().nullable(),
});

export async function apiGet<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<T> {
  return apiRequest(path, schema);
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  schema: z.ZodType<T>,
  idempotencyKey?: string,
): Promise<T> {
  return apiRequest(path, schema, body, idempotencyKey);
}

async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  body?: unknown,
  idempotencyKey?: string,
): Promise<T> {
  const response = await fetch(`/api/backend${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(body === undefined ? {} : { "content-type": "application/json" }),
      ...(idempotencyKey ? { "idempotency-key": idempotencyKey } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const raw: unknown = await response.json();
  if (!response.ok) {
    const parsed = problemSchema.safeParse(raw);
    throw new ApiError(
      response.status,
      parsed.success
        ? parsed.data
        : { title: "Request failed", status: response.status },
    );
  }
  return schema.parse(raw);
}

export function text(value: unknown, fallback = "—"): string {
  if (typeof value === "string" || typeof value === "number")
    return String(value);
  return fallback;
}

export function record(value: unknown): DataRow {
  return rowSchema.safeParse(value).data ?? {};
}

export function rows(value: unknown): DataRow[] {
  return rowsSchema.safeParse(value).data ?? [];
}

export function dateTime(value: unknown): string {
  if (typeof value !== "string") return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
