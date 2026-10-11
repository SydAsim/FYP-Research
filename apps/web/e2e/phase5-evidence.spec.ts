import { createHash, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { expect, test, type APIRequestContext } from "@playwright/test";

const controller = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8004";
const simulator = process.env.PLAYWRIGHT_SIM_URL ?? "http://127.0.0.1:8010";
const worker = process.env.PLAYWRIGHT_WORKER_URL ?? "http://127.0.0.1:8002";

async function post(
  request: APIRequestContext,
  base: string,
  path: string,
  data: Record<string, unknown>,
  status?: number,
): Promise<Record<string, unknown>> {
  const response = await request.post(`${base}${path}`, { data });
  if (status) expect(response.status(), await response.text()).toBe(status);
  else expect(response.ok(), await response.text()).toBeTruthy();
  return response.json() as Promise<Record<string, unknown>>;
}

async function get(
  request: APIRequestContext,
  path: string,
): Promise<Record<string, unknown>> {
  const response = await request.get(`${controller}${path}`);
  expect(response.ok(), await response.text()).toBeTruthy();
  return response.json() as Promise<Record<string, unknown>>;
}

async function fixture(request: APIRequestContext) {
  const value = await post(
    request,
    controller,
    "/internal/phase1/fixtures",
    {
      command_id: randomUUID(),
    },
    201,
  );
  return {
    callId: String(value.call_id),
    workflowId: String(value.workflow_id),
    ticketId: String(value.ticket_id),
    utteranceIds: value.utterance_ids as string[],
  };
}

async function revision(
  request: APIRequestContext,
  item: Awaited<ReturnType<typeof fixture>>,
  number: number,
  hour: number,
  appointmentId?: string,
) {
  return post(
    request,
    controller,
    `/v1/workflows/${item.workflowId}/revisions`,
    {
      command_id: randomUUID(),
      expected_revision: number - 1,
      change_class: number === 1 ? "INITIAL" : "PARAMETER_CORRECTION",
      desired_state: {
        ticket_id: item.ticketId,
        ...(appointmentId ? { appointment_id: appointmentId } : {}),
        requested_start: `2026-11-05T${hour}:00:00+05:00`,
        requested_end: `2026-11-05T${hour + 1}:00:00+05:00`,
        timezone: "Asia/Karachi",
      },
      candidate_source: {
        utterance_id: item.utteranceIds[number - 1],
        model: "phase5-browser-evidence",
        prompt_hash: `phase5-browser-evidence-${number}`,
        transcript_version: 1,
      },
    },
    201,
  );
}

async function step(request: APIRequestContext) {
  return post(request, worker, "/internal/phase2/step", {}, 200);
}

async function drain(request: APIRequestContext) {
  for (let count = 0; count < 40; count += 1) {
    if ((await step(request)).action === "idle") return;
  }
  throw new Error("Durable worker did not become idle within 40 steps");
}

function toneWav(): Buffer {
  const pcm = Buffer.alloc(64_000);
  const output = Buffer.alloc(44 + pcm.length);
  output.write("RIFF", 0);
  output.writeUInt32LE(output.length - 8, 4);
  output.write("WAVEfmt ", 8);
  output.writeUInt32LE(16, 16);
  output.writeUInt16LE(1, 20);
  output.writeUInt16LE(1, 22);
  output.writeUInt32LE(16_000, 24);
  output.writeUInt32LE(32_000, 28);
  output.writeUInt16LE(2, 32);
  output.writeUInt16LE(16, 34);
  output.write("data", 36);
  output.writeUInt32LE(pcm.length, 40);
  pcm.copy(output, 44);
  return output;
}

test.describe("Phase 5 evidence browser journeys", () => {
  test.describe.configure({ mode: "serial" });

  test("normal booking needs a current resource-bound receipt", async ({
    request,
    page,
  }) => {
    const item = await fixture(request);
    await revision(request, item, 1, 15);
    const operation = await post(
      request,
      controller,
      "/v1/operations/appointments",
      {
        command_id: randomUUID(),
        workflow_id: item.workflowId,
        expected_intent_revision: 1,
        expected_resource_version: 0,
        idempotency_key: `phase5-normal:${randomUUID()}`,
      },
      202,
    );
    const committed = await post(
      request,
      controller,
      `/v1/operations/${operation.operation_id}/commit-local`,
      { command_id: randomUUID() },
      200,
    );
    await page.goto(`/call/${item.callId}/summary`);
    await expect(
      page.getByRole("heading", { name: "Still checking" }),
    ).toBeVisible();
    const receipt = await post(
      request,
      controller,
      "/internal/phase3/verifications",
      {
        command_id: randomUUID(),
        operation_id: operation.operation_id,
        expected_intent_revision: 1,
        claim_type: "CURRENT_APPOINTMENT",
      },
      201,
    );
    expect(receipt.result).toBe("SATISFIED");
    await expect(
      page.getByRole("heading", { name: "Current outcome verified" }),
    ).toBeVisible({
      timeout: 15_000,
    });
    await page.goto(`/appointments/${committed.appointment_id}`);
    await expect(
      page
        .getByText(String(receipt.receipt_id).slice(0, 8), { exact: false })
        .first(),
    ).toBeVisible();
    await revision(request, item, 2, 16, String(committed.appointment_id));
    await page.goto(`/call/${item.callId}/summary`);
    await expect(
      page.getByRole("heading", { name: "Still checking" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Current outcome verified" }),
    ).toHaveCount(0);
  });

  test("hidden commit correction remains auditable and never retries blindly", async ({
    request,
    page,
  }) => {
    const scenario = await post(
      request,
      simulator,
      "/internal/scenarios",
      {
        supports_reschedule: false,
        faults: [
          {
            request_index: 1,
            stage: "AFTER_COMMIT_BEFORE_RESPONSE",
            kind: "DROP_RESPONSE",
          },
        ],
      },
      201,
    );
    const item = await fixture(request);
    await revision(request, item, 1, 15);
    const operation = await post(
      request,
      controller,
      "/internal/phase2/operations",
      {
        command_id: randomUUID(),
        workflow_id: item.workflowId,
        scenario_id: scenario.scenario_id,
        expected_intent_revision: 1,
        expected_resource_version: 0,
        idempotency_key: `phase5-hidden:${randomUUID()}`,
      },
      202,
    );
    let ambiguous: Record<string, unknown> | undefined;
    for (let count = 0; count < 40; count += 1) {
      await step(request);
      ambiguous = await get(
        request,
        `/v1/operations/${operation.operation_id}`,
      );
      if (
        (ambiguous.operation as Record<string, unknown>).effect_knowledge ===
        "UNKNOWN"
      )
        break;
    }
    expect(
      (ambiguous?.operation as Record<string, unknown>).effect_knowledge,
    ).toBe("UNKNOWN");
    await page.goto(`/call/${item.callId}/summary`);
    await expect(
      page.getByRole("heading", { name: "Still checking" }),
    ).toBeVisible();
    await revision(request, item, 2, 16);
    await drain(request);
    const truthResponse = await request.get(
      `${simulator}/internal/scenarios/${scenario.scenario_id}/truth`,
    );
    expect(truthResponse.ok()).toBeTruthy();
    const commits = (await truthResponse.json()).commits as {
      action: string;
    }[];
    expect(commits.map((entry) => entry.action)).toEqual([
      "CREATE",
      "CANCEL",
      "CREATE",
    ]);
    const old = await get(request, `/v1/operations/${operation.operation_id}`);
    expect(
      (old.attempts as { attempt_type: string }[]).filter(
        (entry) => entry.attempt_type === "WRITE",
      ),
    ).toHaveLength(1);
    await page.goto(`/calls/${item.callId}/trace`);
    await expect(page.getByText("SUPERSEDED").first()).toBeVisible();
    await expect(page.getByText("PRESENT").first()).toBeVisible();
  });

  test("partly played stale outcome creates visible durable repair", async ({
    request,
    page,
  }) => {
    const scenario = await post(
      request,
      simulator,
      "/internal/scenarios",
      {},
      201,
    );
    const item = await fixture(request);
    await revision(request, item, 1, 15);
    const operation = await post(
      request,
      controller,
      "/internal/phase2/operations",
      {
        command_id: randomUUID(),
        workflow_id: item.workflowId,
        scenario_id: scenario.scenario_id,
        expected_intent_revision: 1,
        expected_resource_version: 0,
        idempotency_key: `phase5-playback:${randomUUID()}`,
      },
      202,
    );
    await drain(request);
    const receipt = await post(
      request,
      controller,
      "/internal/phase3/verifications",
      {
        command_id: randomUUID(),
        operation_id: operation.operation_id,
        expected_intent_revision: 1,
        claim_type: "CURRENT_APPOINTMENT",
      },
      201,
    );
    expect(receipt.result).toBe("SATISFIED");
    const permit = await post(
      request,
      controller,
      "/internal/phase3/claims",
      {
        command_id: randomUUID(),
        receipt_id: receipt.receipt_id,
        expected_intent_revision: 1,
      },
      201,
    );
    await post(
      request,
      controller,
      `/internal/phase3/permits/${permit.permit_id}/queue`,
      {
        command_id: randomUUID(),
        expected_intent_revision: 1,
      },
      200,
    );
    const synthesis = await get(
      request,
      `/internal/phase4/permits/${permit.permit_id}/synthesis-input`,
    );
    const audio = toneWav();
    const segment = await post(
      request,
      controller,
      "/internal/phase4/audio-segments",
      {
        command_id: randomUUID(),
        permit_id: permit.permit_id,
        expected_intent_revision: 1,
        audio_base64: audio.toString("base64"),
        audio_hash: createHash("sha256").update(audio).digest("hex"),
        text_hash: synthesis.text_hash,
        tts_model_id: "phase5-browser-tone",
        tts_config_hash: createHash("sha256")
          .update("phase5-browser-tone")
          .digest("hex"),
      },
      201,
    );
    await post(
      request,
      controller,
      `/internal/phase4/audio-segments/${segment.segment_id}/queue`,
      {
        command_id: randomUUID(),
        expected_intent_revision: 1,
      },
      200,
    );
    await post(
      request,
      controller,
      `/internal/phase4/audio-segments/${segment.segment_id}/release`,
      {
        command_id: randomUUID(),
        expected_intent_revision: 1,
      },
      200,
    );
    await page.goto(`/call/${item.callId}`);
    await page.getByRole("button", { name: "Play approved audio" }).click();
    await expect
      .poll(
        async () => {
          const timeline = await get(
            request,
            `/v1/calls/${item.callId}/timeline`,
          );
          return (
            timeline.playback_events as {
              event_type: string;
              played_ms: number;
            }[]
          ).some(
            (entry) => entry.event_type === "PROGRESS" && entry.played_ms > 0,
          );
        },
        { timeout: 12_000 },
      )
      .toBe(true);
    await revision(request, item, 2, 16);
    await expect(
      page.getByText("A correction obligation is recorded."),
    ).toBeVisible({ timeout: 12_000 });
    const summary = await get(request, `/v1/calls/${item.callId}/summary`);
    expect(summary.business_resolution).toBe("REPAIR_PENDING");
  });

  test("Redis loss leaves PostgreSQL browser reads available", async ({
    request,
    page,
  }) => {
    test.skip(
      process.env.PLAYWRIGHT_REDIS_FAULT !== "1",
      "Opt in to stopping the project Redis container",
    );
    const item = await fixture(request);
    execFileSync("docker", ["compose", "stop", "redis"], {
      cwd: process.cwd() + "/../..",
    });
    try {
      await page.goto(`/call/${item.callId}/summary`);
      await expect(
        page.getByRole("heading", { name: "Still checking" }),
      ).toBeVisible();
      const summary = await get(request, `/v1/calls/${item.callId}/summary`);
      expect(summary.business_resolution).toBe("UNRESOLVED_RECOVERING");
    } finally {
      execFileSync("docker", ["compose", "start", "redis"], {
        cwd: process.cwd() + "/../..",
      });
    }
  });
});
