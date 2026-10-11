"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { z } from "zod";
import { apiPost } from "@/lib/api";
import { PageHeading, Panel, ProblemPanel } from "./ui";

const resultSchema = z.object({
  run_id: z.uuid(),
  status: z.literal("DRAFT"),
  manifest_hash: z.string(),
});
const arms = ["B0", "B1", "B2", "B3", "P1", "P2"];

export function ExperimentLauncher() {
  const router = useRouter();
  const [name, setName] = useState("Maintenance correction pilot");
  const [fixture, setFixture] = useState("synthetic-maintenance-v1");
  const [intent, setIntent] = useState(
    "Maintenance appointment at the corrected time",
  );
  const [phase, setPhase] = useState("P8");
  const [provider, setProvider] = useState("HIDDEN_COMMIT");
  const [fault, setFault] = useState("RESPONSE_LOSS");
  const [chosenArms, setChosenArms] = useState(["B3"]);
  const [seeds, setSeeds] = useState("1,2,3");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const command = useRef<string | null>(null);
  const parsedSeeds = seeds
    .split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isInteger(value));
  const executionCount = chosenArms.length * parsedSeeds.length;

  async function create() {
    if (pending || chosenArms.length === 0 || parsedSeeds.length === 0) return;
    setPending(true);
    setError(null);
    command.current ??= crypto.randomUUID();
    try {
      const result = await apiPost(
        "/v1/evaluation/runs",
        {
          command_id: command.current,
          name,
          fixture_version: fixture,
          final_intent: intent,
          correction_phase: phase,
          provider_behavior: provider,
          fault_family: fault,
          arms: chosenArms,
          seeds: parsedSeeds,
          oracle_required: true,
          model_profile: "strict-cascade",
        },
        resultSchema,
      );
      router.push(`/evaluation/runs/${result.run_id}`);
    } catch (caught) {
      setError(caught);
      setPending(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="RESEARCH MODE"
        title="New experiment"
        description="Create a draft manifest. The independent runner and oracle are delivered in Phase 6."
      />
      {error !== null && (
        <ProblemPanel
          error={error}
          onRetry={() => {
            setError(null);
          }}
        />
      )}
      <div className="two-column">
        <Panel title="Scenario definition">
          <div className="filter-row">
            <label className="field">
              Run name
              <input
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                  command.current = null;
                }}
              />
            </label>
            <label className="field">
              Fixture version
              <input
                value={fixture}
                onChange={(event) => {
                  setFixture(event.target.value);
                  command.current = null;
                }}
              />
            </label>
          </div>
          <label className="field">
            Externally specified final intent
            <textarea
              value={intent}
              onChange={(event) => {
                setIntent(event.target.value);
                command.current = null;
              }}
            />
          </label>
          <div className="filter-row">
            <label className="field">
              Correction phase
              <select
                value={phase}
                onChange={(event) => {
                  setPhase(event.target.value);
                  command.current = null;
                }}
              >
                {Array.from({ length: 10 }, (_, index) => (
                  <option key={index} value={`P${index}`}>
                    P{index}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Provider behavior
              <select
                value={provider}
                onChange={(event) => {
                  setProvider(event.target.value);
                  command.current = null;
                }}
              >
                {[
                  "VISIBLE_COMMIT",
                  "HIDDEN_COMMIT",
                  "REFUSAL",
                  "UNKNOWN_TIMEOUT",
                ].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <label className="field">
              Fault family
              <select
                value={fault}
                onChange={(event) => {
                  setFault(event.target.value);
                  command.current = null;
                }}
              >
                {[
                  "NONE",
                  "RESPONSE_LOSS",
                  "DELAY",
                  "REDIS_LOSS",
                  "PARTIAL_PLAYBACK",
                ].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
          </div>
        </Panel>
        <Panel title="System arms and execution plan">
          <p>
            Strict research voice path: provider-neutral cascaded STT → LLM →
            TTS. Native audio is an optional comparison adapter.
          </p>
          <div className="filter-row">
            {arms.map((arm) => (
              <label className="consent-row" key={arm}>
                <input
                  type="checkbox"
                  checked={chosenArms.includes(arm)}
                  onChange={(event) => {
                    setChosenArms(
                      event.target.checked
                        ? [...chosenArms, arm]
                        : chosenArms.filter((item) => item !== arm),
                    );
                    command.current = null;
                  }}
                />
                {arm}
              </label>
            ))}
          </div>
          <label className="field">
            Independent seed list (comma separated)
            <input
              value={seeds}
              onChange={(event) => {
                setSeeds(event.target.value);
                command.current = null;
              }}
            />
          </label>
          <p>
            <strong>{executionCount}</strong> proposed executions ·{" "}
            <strong>1</strong> scenario definition ·{" "}
            <strong>{parsedSeeds.length}</strong> repetitions per arm.
            Repetitions do not increase independent scenario count.
          </p>
          <div className="alert">
            This saves a DRAFT only. It cannot execute until the Phase 6 oracle,
            fixture version, fault scheduler, and replay bundle are installed
            and frozen.
          </div>
          <button
            className="button"
            disabled={
              pending ||
              chosenArms.length === 0 ||
              parsedSeeds.length === 0 ||
              !name.trim() ||
              !intent.trim()
            }
            onClick={() => void create()}
          >
            {pending ? "Saving draft…" : "Create draft manifest"}
          </button>
        </Panel>
      </div>
    </>
  );
}
