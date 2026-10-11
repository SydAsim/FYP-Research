import { expect, test, type APIRequestContext } from "@playwright/test";

const apiURL = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8004";
const key = () => crypto.randomUUID();

async function jsonPost(
  request: APIRequestContext,
  path: string,
  data: Record<string, unknown>,
) {
  const response = await request.post(`${apiURL}${path}`, { data });
  expect(response.ok(), `${path}: ${await response.text()}`).toBeTruthy();
  return response.json() as Promise<Record<string, unknown>>;
}

test.describe("Phase 5 browser routes", () => {
  let callId: string;
  let residentId: string;
  let appointmentId: string;
  let runId: string;

  test.beforeAll(async ({ request }) => {
    const config = await request.get(`${apiURL}/v1/public/config`);
    expect(config.ok()).toBeTruthy();
    residentId = (await config.json()).synthetic_resident_id;
    const call = await request.post(`${apiURL}/v1/calls`, {
      data: { consent: true, resident_id: residentId },
      headers: { "Idempotency-Key": key() },
    });
    expect(call.status()).toBe(201);
    callId = (await call.json()).call_id;

    const fixture = await jsonPost(request, "/internal/phase1/fixtures", {
      command_id: key(),
    });
    const workflowId = String(fixture.workflow_id);
    await jsonPost(request, `/v1/workflows/${workflowId}/revisions`, {
      command_id: key(),
      expected_revision: 0,
      change_class: "INITIAL",
      desired_state: {
        ticket_id: fixture.ticket_id,
        requested_start: "2026-11-04T15:00:00+05:00",
        requested_end: "2026-11-04T16:00:00+05:00",
        timezone: "Asia/Karachi",
      },
      candidate_source: {
        utterance_id: (fixture.utterance_ids as string[])[0],
        model: "phase5-browser",
        prompt_hash: "phase5-browser-v1",
        transcript_version: 1,
      },
    });
    const operation = await jsonPost(request, "/v1/operations/appointments", {
      command_id: key(),
      workflow_id: workflowId,
      expected_intent_revision: 1,
      expected_resource_version: 0,
      idempotency_key: `phase5-browser:${key()}`,
    });
    const committed = await jsonPost(
      request,
      `/v1/operations/${operation.operation_id}/commit-local`,
      { command_id: key() },
    );
    appointmentId = String(committed.appointment_id);
    await jsonPost(request, "/internal/phase3/verifications", {
      command_id: key(),
      operation_id: operation.operation_id,
      expected_intent_revision: 1,
      claim_type: "CURRENT_APPOINTMENT",
    });
    const draft = await jsonPost(request, "/v1/evaluation/runs", {
      command_id: key(),
      name: `Browser draft ${key()}`,
      fixture_version: "synthetic-maintenance-v1",
      final_intent: "Maintenance appointment at corrected time",
      correction_phase: "P8",
      provider_behavior: "HIDDEN_COMMIT",
      fault_family: "RESPONSE_LOSS",
      arms: ["B3", "P1"],
      seeds: [1],
      oracle_required: true,
      model_profile: "strict-cascade",
    });
    runId = String(draft.run_id);
  });

  const routes: [string, string][] = [
    ["/", /voice agent that/i.source],
    ["/dashboard", "Dashboard"],
    ["/calendar", "Calendar"],
    ["/appointments", "Appointments"],
    ["/residents", "Residents"],
    ["/notes", "Notes and preferences"],
    ["/calls", "Call history"],
    ["/handoffs", "Human handoffs"],
    ["/evaluation", "Evaluation"],
    ["/experiments/new", "New experiment"],
    ["/settings", "Settings"],
  ];

  for (const [path, heading] of routes) {
    test(`${path} renders its data view`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator("h1")).toContainText(new RegExp(heading, "i"));
      await expect(page.locator(".error-panel")).toHaveCount(0);
    });
  }

  const detailRoutes: [() => string, string][] = [
    [() => `/call/${callId}`, "Live call"],
    [() => `/call/${callId}/summary`, "Call summary"],
    [() => `/calls/${callId}/trace`, "Workflow trace"],
    [() => `/appointments/${appointmentId}`, "Appointment record"],
    [() => `/residents/${residentId}`, "Demo Resident"],
    [() => `/evaluation/runs/${runId}`, "Browser draft"],
  ];

  for (const [path, heading] of detailRoutes) {
    test(`${heading} loads a durable record`, async ({ page }) => {
      await page.goto(path());
      await expect(page.locator("h1")).toContainText(heading);
      await expect(page.locator(".error-panel")).toHaveCount(0);
    });
  }

  test("live call joins the local LiveKit room", async ({ page, request }) => {
    const token = await request.get(`${apiURL}/v1/calls/${callId}/media-token`);
    expect(token.ok()).toBeTruthy();
    const availability = (await token.json()) as {
      voice_agent_status: "READY" | "UNAVAILABLE";
    };
    await page.goto(`/call/${callId}`);
    await expect(page.locator(".call-stage h2")).toContainText("Connected", {
      timeout: 15_000,
    });
    if (availability.voice_agent_status === "READY") {
      await expect(
        page.getByText("No agent is processing microphone audio"),
      ).toHaveCount(0);
      await expect(
        page.getByRole("button", { name: "Start microphone" }),
      ).toBeEnabled();
    } else {
      await expect(page.getByRole("status")).toContainText(
        "No agent is processing microphone audio",
      );
      await expect(
        page.getByRole("button", { name: "Start microphone" }),
      ).toBeDisabled();
    }
  });

  test("media request failure can reconnect the same durable call", async ({
    page,
  }) => {
    await page.route("**/api/backend/v1/calls/*/media-token", (route) =>
      route.abort("failed"),
    );
    await page.goto(`/call/${callId}`);
    await expect(page.locator(".call-stage h2")).toHaveText(
      "Media unavailable",
    );
    await page.unroute("**/api/backend/v1/calls/*/media-token");
    await page.getByRole("button", { name: "Retry" }).click();
    await expect(page.locator(".call-stage h2")).toContainText("Connected", {
      timeout: 15_000,
    });
    await expect(page).toHaveURL(new RegExp(`/call/${callId}$`));
  });

  test("landing consent starts a durable call and ending media keeps recovery honest", async ({
    page,
  }) => {
    await page.goto("/");
    const start = page.getByRole("button", { name: /Start conversation/ });
    await expect(start).toBeDisabled();
    await page.getByRole("checkbox").check();
    await expect(start).toBeEnabled();
    await start.click();
    await expect(page).toHaveURL(/\/call\/[0-9a-f-]{36}$/);
    await expect(page.locator("h1")).toHaveText("Live call");
    await page.getByRole("button", { name: "End call" }).click();
    await expect(page).toHaveURL(/\/summary$/);
    await expect(
      page.getByRole("heading", { name: "Still checking" }),
    ).toBeVisible();
    await expect(page.getByText("Current outcome verified")).toHaveCount(0);
  });

  test("recoverable API failure offers retry", async ({ page }) => {
    await page.route("**/api/backend/v1/dashboard/summary", (route) =>
      route.abort("failed"),
    );
    await page.goto("/dashboard");
    await expect(page.locator(".error-panel")).toContainText(
      "Could not load this view",
      { timeout: 20_000 },
    );
    await page.unroute("**/api/backend/v1/dashboard/summary");
    await page.getByRole("button", { name: "Retry" }).click();
    await expect(page.locator(".error-panel")).toHaveCount(0);
    await expect(page.locator("h1")).toHaveText("Dashboard");
  });
});
