import { z } from "zod";

const playbackEventSchema = z.object({
  event_id: z.uuid(),
  segment_id: z.uuid(),
  event_type: z.enum([
    "RECEIVED",
    "QUEUED",
    "STARTED",
    "PROGRESS",
    "INTERRUPTED",
    "COMPLETED",
  ]),
  client_time: z.iso.datetime({ offset: true }),
  played_ms: z.number().int().nonnegative(),
  last_frame: z.number().int().nonnegative(),
  last_word_index: z.number().int().nonnegative(),
});

export type PlaybackEvent = z.infer<typeof playbackEventSchema>;
export type PlaybackEventType = PlaybackEvent["event_type"];

export interface SegmentTiming {
  segmentId: string;
  durationMs: number;
  frameCount: number;
  wordEndMs: number[];
}

export interface PlayableAudio {
  currentTime: number;
  ended: boolean;
  play(): Promise<void>;
  pause(): void;
  removeAttribute(name: string): void;
  load(): void;
  addEventListener(name: string, listener: () => void): void;
  removeEventListener(name: string, listener: () => void): void;
}

export interface PendingStore {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export type SendPlayback = (
  callId: string,
  event: PlaybackEvent,
) => Promise<void>;

export class PlaybackReporter {
  private readonly key: string;
  private readonly pending: PlaybackEvent[];
  private lastProgressMs = 0;
  private chain: Promise<void> = Promise.resolve();
  private readonly onTimeUpdate = () => {
    const progress = this.progress();
    if (progress.played_ms - this.lastProgressMs >= 200) {
      this.lastProgressMs = progress.played_ms;
      void this.record("PROGRESS", progress).catch(() => this.audio.pause());
    }
  };
  private readonly onEnded = () => {
    void this.complete().catch(() => this.audio.pause());
  };

  constructor(
    private readonly callId: string,
    private readonly timing: SegmentTiming,
    private readonly audio: PlayableAudio,
    private readonly send: SendPlayback,
    private readonly store: PendingStore,
  ) {
    this.key = `phase4-playback:${callId}`;
    const saved: unknown = JSON.parse(this.store.getItem(this.key) ?? "[]");
    this.pending = z.array(playbackEventSchema).parse(saved);
    this.audio.addEventListener("timeupdate", this.onTimeUpdate);
    this.audio.addEventListener("ended", this.onEnded);
  }

  private progress(): Pick<
    PlaybackEvent,
    "played_ms" | "last_frame" | "last_word_index"
  > {
    const played_ms = Math.max(
      0,
      Math.min(
        this.timing.durationMs,
        Math.floor(this.audio.currentTime * 1000),
      ),
    );
    return {
      played_ms,
      last_frame: Math.min(
        this.timing.frameCount,
        Math.floor((played_ms * 16000) / 1000),
      ),
      last_word_index: this.timing.wordEndMs.filter((end) => end <= played_ms)
        .length,
    };
  }

  private save(): void {
    this.store.setItem(this.key, JSON.stringify(this.pending));
  }

  async flush(): Promise<void> {
    while (this.pending.length > 0) {
      const event = this.pending[0];
      await this.send(this.callId, event);
      this.pending.shift();
      this.save();
    }
  }

  record(
    event_type: PlaybackEventType,
    progress = this.progress(),
  ): Promise<void> {
    const event: PlaybackEvent = {
      event_id: crypto.randomUUID(),
      segment_id: this.timing.segmentId,
      event_type,
      client_time: new Date().toISOString(),
      ...progress,
    };
    playbackEventSchema.parse(event);
    this.pending.push(event);
    this.save();
    this.chain = this.chain.catch(() => undefined).then(() => this.flush());
    return this.chain;
  }

  async start(): Promise<void> {
    await this.chain.catch(() => undefined);
    await this.flush();
    await this.record("STARTED");
    await this.audio.play();
  }

  async interrupt(): Promise<void> {
    const progress = this.progress();
    this.audio.pause();
    this.audio.removeAttribute("src");
    this.audio.load();
    await this.record("INTERRUPTED", progress);
  }

  async complete(): Promise<void> {
    if (!this.audio.ended)
      throw new Error("Cannot acknowledge audio that did not end");
    await this.record("COMPLETED", {
      played_ms: this.timing.durationMs,
      last_frame: this.timing.frameCount,
      last_word_index: this.timing.wordEndMs.length,
    });
  }

  dispose(): void {
    this.audio.removeEventListener("timeupdate", this.onTimeUpdate);
    this.audio.removeEventListener("ended", this.onEnded);
  }
}
