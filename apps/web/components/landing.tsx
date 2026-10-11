"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, useSyncExternalStore } from "react";
import { apiGet, apiPost, callSessionSchema, configSchema } from "@/lib/api";
import { LoadingState, ProblemPanel } from "./ui";

export function Landing() {
  const router = useRouter();
  const config = useQuery({
    queryKey: ["public-config"],
    queryFn: () => apiGet("/v1/public/config", configSchema),
  });
  const [consent, setConsent] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const command = useRef<string | null>(null);
  const started = useRef(false);
  const mediaSupported = useSyncExternalStore(
    () => () => undefined,
    () => Boolean(navigator.mediaDevices?.getUserMedia),
    () => true,
  );

  async function start() {
    if (started.current || !consent || !config.data?.synthetic_resident_id)
      return;
    started.current = true;
    setPending(true);
    setError(null);
    command.current ??= crypto.randomUUID();
    try {
      const call = await apiPost(
        "/v1/calls",
        { consent: true, resident_id: config.data.synthetic_resident_id },
        callSessionSchema,
        command.current,
      );
      router.push(`/call/${call.call_id}`);
    } catch (caught) {
      setError(caught);
      setPending(false);
      started.current = false;
    }
  }

  return (
    <div className="landing">
      <header className="landing-header">
        <Link className="brand" href="/">
          <span className="brand-mark">✦</span>
          <span>
            indigo<span className="brand-accent"> intelligence</span>
            <small>COMMIT AWARE VOICE</small>
          </span>
        </Link>
        <Link className="button secondary" href="/dashboard">
          Open workspace ↗
        </Link>
      </header>
      <div className="landing-hero">
        <span className="landing-tag">SYNTHETIC RESEARCH PROTOTYPE</span>
        <h1>
          A voice agent that <span>checks before it claims.</span>
        </h1>
        <p>
          Explore maintenance scheduling with an agent that tracks corrections,
          reconciles uncertain actions, and reports consequential outcomes only
          after verification.
        </p>
      </div>
      <div className="landing-cards">
        <div className="landing-card">
          <div className="landing-card-icon">◉</div>
          <h2>Natural conversation</h2>
          <p>
            Speak, pause, and correct a scheduling request while the voice
            transport stays responsive.
          </p>
        </div>
        <div className="landing-card">
          <div className="landing-card-icon">◇</div>
          <h2>Durable operations</h2>
          <p>
            PostgreSQL retains intent revisions, effects, and uncertainty
            through retries and disconnects.
          </p>
        </div>
        <div className="landing-card">
          <div className="landing-card-icon">✓</div>
          <h2>Evidence-bound claims</h2>
          <p>
            Decisive outcome speech needs a current receipt and applicable claim
            permit.
          </p>
        </div>
      </div>
      <section className="consent-card" aria-labelledby="consent-title">
        <h2 id="consent-title">Start a synthetic conversation</h2>
        <p>
          This is a controlled research environment. Your microphone will stream
          to the local LiveKit server; call events and recordings may be
          retained for evaluation.
        </p>
        {config.isPending && <LoadingState />}
        {config.isError && (
          <ProblemPanel
            error={config.error}
            onRetry={() => void config.refetch()}
          />
        )}
        {!mediaSupported && (
          <div className="alert error">
            This browser does not support microphone capture. Use a current
            browser with microphone access.
          </div>
        )}
        {config.data && !config.data.synthetic_resident_id && (
          <div className="alert">
            No synthetic demo resident is available. Apply the Phase 5 migration
            before starting.
          </div>
        )}
        <label className="consent-row">
          <input
            type="checkbox"
            checked={consent}
            onChange={(event) => setConsent(event.target.checked)}
          />
          <span>
            I consent to microphone streaming and research recording for this
            synthetic call.
          </span>
        </label>
        {error !== null && <ProblemPanel error={error} onRetry={start} />}
        <div className="consent-actions">
          <button
            className="button"
            disabled={
              !consent ||
              pending ||
              !config.data?.synthetic_resident_id ||
              !mediaSupported
            }
            onClick={() => void start()}
          >
            {pending ? "Creating durable call…" : "Start conversation →"}
          </button>
          <a href="#how-it-works" className="button secondary">
            How it works
          </a>
        </div>
      </section>
      <section className="consent-card" id="how-it-works">
        <h2>How it works</h2>
        <p>
          A call is created before media joins. Accepted intent revisions,
          operations, verification receipts, and playback exposure are separate
          records. Unknown provider outcomes remain visible until reconciled.
        </p>
      </section>
      <footer className="landing-footer">
        Research demo · PostgreSQL durable truth · Provider-neutral cascaded
        voice path
      </footer>
    </div>
  );
}
