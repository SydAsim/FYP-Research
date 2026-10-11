import { NextRequest } from "next/server";

async function forward(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  if (path[0] !== "v1" || path.some((part) => !/^[a-zA-Z0-9-]+$/.test(part))) {
    return Response.json(
      { title: "Invalid API path", status: 400 },
      { status: 400 },
    );
  }
  const base = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  const target = new URL(`${base}/${path.join("/")}`);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of ["content-type", "idempotency-key"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    const resultHeaders = new Headers();
    for (const name of ["content-type", "x-trace-id", "x-total-count"]) {
      const value = upstream.headers.get(name);
      if (value) resultHeaders.set(name, value);
    }
    return new Response(upstream.body, {
      status: upstream.status,
      headers: resultHeaders,
    });
  } catch (error) {
    const traceId = crypto.randomUUID();
    console.error("api_proxy_failure", { trace_id: traceId, path, error });
    return Response.json(
      {
        type: "about:blank",
        title: "API unavailable",
        status: 503,
        detail:
          "The controller could not be reached. Retry after connectivity returns.",
        trace_id: traceId,
        retryable: true,
      },
      { status: 503, headers: { "content-type": "application/problem+json" } },
    );
  }
}

export const GET = forward;
export const POST = forward;
