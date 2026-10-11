"use client";

import { useQuery } from "@tanstack/react-query";
import { Room, RoomEvent, Track } from "livekit-client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import {
  apiGet,
  apiPost,
  rowSchema,
  rows,
  summarySchema,
  text,
} from "@/lib/api";
import { PlaybackReporter } from "@/lib/playback-reporter";
import {
  Identifier,
  LoadingState,
  PageHeading,
  Panel,
  ProblemPanel,
  StatusChip,
} from "./ui";

const mediaTokenSchema = z.object({
  livekit_url: z.string(),
  livekit_token: z.string(),
  voice_agent_status: z.enum(["READY", "UNAVAILABLE"]),
});
const detailSchema = z.object({
  call: rowSchema,
  workflows: z.array(rowSchema),
  operations: z.array(rowSchema),
  repairs: z.array(rowSchema),
});
const timelineSchema = z
  .object({ segments: z.array(rowSchema), utterances: z.array(rowSchema) })
  .passthrough();

export function LiveCall({ callId }: { callId: string }) {
  const router = useRouter();
  const detail = useQuery({
    queryKey: ["call", callId],
    queryFn: () => apiGet(`/v1/calls/${callId}`, detailSchema),
    refetchInterval: 3000,
  });
  const summary = useQuery({
    queryKey: ["summary", callId],
    queryFn: () => apiGet(`/v1/calls/${callId}/summary`, summarySchema),
    refetchInterval: 3000,
  });
  const timeline = useQuery({
    queryKey: ["timeline", callId],
    queryFn: () => apiGet(`/v1/calls/${callId}/timeline`, timelineSchema),
    refetchInterval: 3000,
  });
  const room = useRef<Room | null>(null);
  const remoteAudio = useRef<HTMLDivElement | null>(null);
  const [mediaState, setMediaState] = useState("Connecting to media…");
  const [agentStatus, setAgentStatus] = useState<
    "UNKNOWN" | "READY" | "UNAVAILABLE"
  >("UNKNOWN");
  const [muted, setMuted] = useState(false);
  const [microphoneActive, setMicrophoneActive] = useState(false);
  const [startingMicrophone, setStartingMicrophone] = useState(false);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [mediaRetry, setMediaRetry] = useState(0);
  const endCommand = useRef<string | null>(null);
  const knownSegments = useRef<Set<string> | null>(null);
  const [autoPlayIds, setAutoPlayIds] = useState<string[]>([]);

  const workflow = detail.data?.workflows.at(-1);
  const lastVoiceEvent = rows(timeline.data?.voice_events).at(-1);
  const voiceMessage =
    lastVoiceEvent?.event_type === "ClarificationRequired" ||
    lastVoiceEvent?.event_type === "AgentTurnFailed" ||
    lastVoiceEvent?.event_type === "AgentTurnUnknown"
      ? text(rowSchema.parse(lastVoiceEvent.normalized_json).message)
      : null;
  const callMediaStatus = detail.data?.call.media_status;
  const currentOperation = detail.data?.operations.find(
    (op) =>
      op.applicability === "CURRENT" &&
      op.intent_revision === workflow?.current_revision,
  );

  useEffect(() => {
    if (!timeline.data) return;
    const ids = rows(timeline.data.segments)
      .map((segment) => segment.id)
      .filter((id): id is string => typeof id === "string");
    if (knownSegments.current === null) {
      knownSegments.current = new Set(ids);
      return;
    }
    const fresh = ids.filter((id) => !knownSegments.current?.has(id));
    ids.forEach((id) => knownSegments.current?.add(id));
    if (fresh.length > 0 && microphoneActive)
      setAutoPlayIds((previous) => [...previous, ...fresh]);
  }, [timeline.data, microphoneActive]);

  useEffect(() => {
    if (callMediaStatus === undefined || callMediaStatus === "ENDED") return;
    let active = true;
    const nextRoom = new Room();
    room.current = nextRoom;
    nextRoom.on(
      RoomEvent.Reconnecting,
      () => active && setMediaState("Reconnecting to media…"),
    );
    nextRoom.on(
      RoomEvent.Reconnected,
      () => active && setMediaState("Connected"),
    );
    nextRoom.on(
      RoomEvent.Disconnected,
      () =>
        active && setMediaState("Disconnected — reconnecting may be needed"),
    );
    nextRoom.on(RoomEvent.TrackSubscribed, (track) => {
      if (track.kind === Track.Kind.Audio && remoteAudio.current)
        remoteAudio.current.appendChild(track.attach());
    });
    nextRoom.on(RoomEvent.TrackUnsubscribed, (track) =>
      track.detach().forEach((node) => node.remove()),
    );
    async function connect() {
      try {
        const media = await apiGet(
          `/v1/calls/${callId}/media-token`,
          mediaTokenSchema,
        );
        if (!active) return;
        setAgentStatus(media.voice_agent_status);
        let timeout: ReturnType<typeof setTimeout> | undefined;
        try {
          await Promise.race([
            nextRoom.connect(media.livekit_url, media.livekit_token),
            new Promise<never>((_, reject) => {
              timeout = setTimeout(
                () => reject(new Error("Media connection timed out")),
                10_000,
              );
            }),
          ]);
        } finally {
          if (timeout) clearTimeout(timeout);
        }
        if (!active) return;
        setMediaState("Connected");
      } catch (caught) {
        void nextRoom.disconnect();
        if (active) {
          setError(caught);
          setMediaState("Media unavailable");
        }
      }
    }
    void connect();
    return () => {
      active = false;
      room.current = null;
      void nextRoom.disconnect();
    };
  }, [callId, callMediaStatus, mediaRetry]);

  async function toggleMute() {
    if (!room.current) return;
    setStartingMicrophone(true);
    try {
      await room.current.localParticipant.setMicrophoneEnabled(
        !microphoneActive || muted,
      );
      setMicrophoneActive(true);
      setMuted(microphoneActive && !muted);
    } catch (caught) {
      setError(caught);
    } finally {
      setStartingMicrophone(false);
    }
  }

  async function endCall() {
    if (ending) return;
    setEnding(true);
    setError(null);
    endCommand.current ??= crypto.randomUUID();
    try {
      await apiPost(
        `/v1/calls/${callId}/end`,
        { command_id: endCommand.current },
        rowSchema,
      );
      await room.current?.disconnect();
      router.push(`/call/${callId}/summary`);
    } catch (caught) {
      setError(caught);
      setEnding(false);
    }
  }

  if (detail.isPending)
    return (
      <>
        <PageHeading title="Live call" />
        <LoadingState />
      </>
    );
  if (detail.isError)
    return (
      <ProblemPanel
        error={detail.error}
        onRetry={() => void detail.refetch()}
      />
    );
  return (
    <>
      <PageHeading
        eyebrow="VOICE SESSION"
        title="Live call"
        description="Conversation and durable business state are tracked separately."
        action={
          <Link className="button secondary" href={`/call/${callId}/summary`}>
            View summary
          </Link>
        }
      />
      {error !== null && (
        <ProblemPanel
          error={error}
          onRetry={() => {
            setError(null);
            setMediaState("Connecting to media…");
            setAgentStatus("UNKNOWN");
            setMediaRetry((attempt) => attempt + 1);
            void detail.refetch();
          }}
        />
      )}
      {agentStatus === "UNAVAILABLE" &&
        detail.data.call.media_status !== "ENDED" && (
          <div className="alert error" role="status">
            Voice assistant unavailable. No agent is processing microphone
            audio. Start the local voice model and retry this connection.
            <button
              className="button secondary"
              onClick={() => {
                setAgentStatus("UNKNOWN");
                setMediaState("Connecting to media…");
                setMediaRetry((attempt) => attempt + 1);
              }}
            >
              Retry voice agent
            </button>
          </div>
        )}
      <div className="call-stage">
        <div>
          <div className="call-orb" aria-hidden="true">
            ✦
          </div>
          <h2>
            {detail.data.call.media_status === "ENDED"
              ? "Media ended"
              : mediaState}
          </h2>
          <p>
            Call <Identifier value={callId} /> ·{" "}
            {summary.data?.current_statement ??
              (agentStatus === "READY"
                ? "Listening for a maintenance request."
                : "Waiting for a voice agent.")}
          </p>
          {voiceMessage && <p role="status">{voiceMessage}</p>}
          <div ref={remoteAudio} aria-label="Assistant audio" />
          <div className="call-controls">
            <button
              className="button secondary"
              disabled={
                mediaState !== "Connected" ||
                agentStatus !== "READY" ||
                startingMicrophone
              }
              onClick={() => void toggleMute()}
            >
              {!microphoneActive
                ? "Start microphone"
                : muted
                  ? "Unmute microphone"
                  : "Mute microphone"}
            </button>
            <button
              className="button danger"
              disabled={ending || detail.data.call.media_status === "ENDED"}
              onClick={() => void endCall()}
            >
              {ending ? "Ending…" : "End call"}
            </button>
          </div>
        </div>
      </div>
      <div className="alert info">
        LiveKit carries media. PostgreSQL holds the durable business state and
        controls which outcome claims may be played.
      </div>
      <div className="two-column">
        <Panel title="State dimensions">
          <dl className="key-values">
            <div className="key-value">
              <dt>Conversation</dt>
              <dd>
                <StatusChip value={detail.data.call.conversation_phase} />
              </dd>
            </div>
            <div className="key-value">
              <dt>Accepted revision</dt>
              <dd>{text(workflow?.current_revision, "0")}</dd>
            </div>
            <div className="key-value">
              <dt>Operation phase</dt>
              <dd>
                <StatusChip value={currentOperation?.processing_phase} />
              </dd>
            </div>
            <div className="key-value">
              <dt>Effect knowledge</dt>
              <dd>
                <StatusChip
                  value={currentOperation?.effect_knowledge ?? "UNKNOWN"}
                />
              </dd>
            </div>
            <div className="key-value">
              <dt>Applicability</dt>
              <dd>
                <StatusChip value={currentOperation?.applicability} />
              </dd>
            </div>
            <div className="key-value">
              <dt>Speech eligibility</dt>
              <dd>
                <StatusChip
                  value={currentOperation?.speech_eligibility ?? "BLOCKED"}
                />
              </dd>
            </div>
          </dl>
          {detail.data.repairs.length > 0 && (
            <p className="alert error">
              A correction obligation is recorded. Inspect the trace before
              claiming an outcome.
            </p>
          )}
        </Panel>
        <Panel title="Conversation record">
          {timeline.isPending ? (
            <LoadingState />
          ) : timeline.isError ? (
            <ProblemPanel
              error={timeline.error}
              onRetry={() => void timeline.refetch()}
            />
          ) : rows(timeline.data.utterances).length ? (
            <div className="event-list">
              {rows(timeline.data.utterances).map((item) => (
                <div className="event" key={text(item.id)}>
                  <strong>{text(item.speaker)}</strong>
                  <p>{text(item.transcript)}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="subtle">No transcript has been finalized yet.</p>
          )}
        </Panel>
      </div>
      {timeline.data && (
        <Panel title="Released speech segments">
          {rows(timeline.data.segments)
            .filter(
              (segment) =>
                segment.state === "PUBLISHED" || segment.state === "STARTED",
            )
            .map((segment) => (
              <PlayableSegment
                key={text(segment.id)}
                callId={callId}
                segment={segment}
                autoPlay={autoPlayIds.includes(text(segment.id))}
                onRefresh={() => void timeline.refetch()}
              />
            ))}
          {rows(timeline.data.segments).filter(
            (segment) =>
              segment.state === "PUBLISHED" || segment.state === "STARTED",
          ).length === 0 && (
            <p className="subtle">
              No evidence-authorized audio is ready to play.
            </p>
          )}
        </Panel>
      )}
    </>
  );
}

function PlayableSegment({
  callId,
  segment,
  autoPlay,
  onRefresh,
}: {
  callId: string;
  segment: Record<string, unknown>;
  autoPlay: boolean;
  onRefresh: () => void;
}) {
  const audio = useRef<HTMLAudioElement | null>(null);
  const reporter = useRef<PlaybackReporter | null>(null);
  const autoStarted = useRef(false);
  const [error, setError] = useState<unknown>(null);
  const refreshRef = useRef(onRefresh);
  const segmentId = text(segment.id);
  const durationMs = Number(segment.duration_ms ?? 0);
  const frameCount = Number(segment.frame_count ?? 0);
  const wordTimeline = JSON.stringify(segment.word_timeline_json ?? []);
  useEffect(() => {
    refreshRef.current = onRefresh;
  }, [onRefresh]);
  useEffect(() => {
    const node = audio.current;
    if (!node || !segmentId) return;
    const words = rows(JSON.parse(wordTimeline) as unknown);
    const next = new PlaybackReporter(
      callId,
      {
        segmentId,
        durationMs,
        frameCount,
        wordEndMs: words.map((word) => Number(word.end_ms ?? 0)),
      },
      node,
      (id, event) =>
        apiPost(`/v1/calls/${id}/playback-events`, event, rowSchema).then(
          () => undefined,
        ),
      localStorage,
    );
    reporter.current = next;
    void next.flush().catch(setError);
    if (autoPlay && !autoStarted.current) {
      autoStarted.current = true;
      void next
        .start()
        .then(() => refreshRef.current())
        .catch(setError);
    }
    return () => {
      next.dispose();
      reporter.current = null;
    };
  }, [callId, segmentId, durationMs, frameCount, wordTimeline, autoPlay]);
  return (
    <div className="filter-row">
      <span>
        <StatusChip value={segment.segment_class} />{" "}
        <Identifier value={segment.id} />
      </span>
      <audio
        ref={audio}
        preload="none"
        src={`/api/backend/v1/audio-segments/${text(segment.id)}/audio`}
      />
      <button
        className="button secondary"
        onClick={() =>
          void reporter.current?.start().then(onRefresh).catch(setError)
        }
      >
        Play approved audio
      </button>
      <button
        className="button secondary"
        onClick={() =>
          void reporter.current?.interrupt().then(onRefresh).catch(setError)
        }
      >
        Stop / barge in
      </button>
      {error !== null && <ProblemPanel error={error} />}
    </div>
  );
}
