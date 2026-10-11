import { describe, expect, it } from "vitest";

import {
  PlaybackReporter,
  type PlayableAudio,
  type PlaybackEvent,
} from "./playback-reporter";

class MemoryStore {
  value: string | null = null;
  getItem(): string | null {
    return this.value;
  }
  setItem(_key: string, value: string): void {
    this.value = value;
  }
}

class FakeAudio implements PlayableAudio {
  currentTime = 0;
  ended = false;
  played = false;
  paused = false;
  cleared = false;
  private listeners = new Map<string, () => void>();
  async play(): Promise<void> {
    this.played = true;
  }
  pause(): void {
    this.paused = true;
  }
  removeAttribute(name: string): void {
    if (name === "src") this.cleared = true;
  }
  load(): void {}
  addEventListener(name: string, listener: () => void): void {
    this.listeners.set(name, listener);
  }
  removeEventListener(name: string): void {
    this.listeners.delete(name);
  }
}

const timing = {
  segmentId: "e07303ba-4d28-49d9-896e-49fd19a607ee",
  durationMs: 1000,
  frameCount: 16000,
  wordEndMs: [300, 700, 1000],
};
const callId = "d27d0233-254d-4289-9148-c855b3b7b28b";

describe("playback reporter", () => {
  it("gates play on a server STARTED acknowledgement and records the stopped span", async () => {
    const audio = new FakeAudio();
    const store = new MemoryStore();
    const sent: PlaybackEvent[] = [];
    const reporter = new PlaybackReporter(
      callId,
      timing,
      audio,
      async (_id, event) => {
        if (event.event_type === "STARTED") expect(audio.played).toBe(false);
        sent.push(event);
      },
      store,
    );
    await reporter.start();
    expect(audio.played).toBe(true);
    audio.currentTime = 0.55;
    await reporter.interrupt();
    expect(audio.paused).toBe(true);
    expect(audio.cleared).toBe(true);
    expect(sent.map((event) => event.event_type)).toEqual([
      "STARTED",
      "INTERRUPTED",
    ]);
    expect(sent[1].last_frame).toBe(8800);
    expect(sent[1].last_word_index).toBe(1);
    reporter.dispose();
  });

  it("keeps the same event ID for a retry after a network failure", async () => {
    const audio = new FakeAudio();
    const store = new MemoryStore();
    const attempts: string[] = [];
    const reporter = new PlaybackReporter(
      callId,
      timing,
      audio,
      async (_id, event) => {
        attempts.push(event.event_id);
        throw new Error("offline");
      },
      store,
    );
    await expect(reporter.start()).rejects.toThrow("offline");
    expect(audio.played).toBe(false);
    reporter.dispose();
    const restored = new PlaybackReporter(
      callId,
      timing,
      audio,
      async (_id, event) => {
        attempts.push(event.event_id);
      },
      store,
    );
    await restored.flush();
    expect(attempts).toHaveLength(2);
    expect(attempts[0]).toBe(attempts[1]);
    expect(store.value).toBe("[]");
    restored.dispose();
  });

  it("acknowledges completion only after the media element ends", async () => {
    const audio = new FakeAudio();
    const sent: PlaybackEvent[] = [];
    const reporter = new PlaybackReporter(
      callId,
      timing,
      audio,
      async (_id, event) => {
        sent.push(event);
      },
      new MemoryStore(),
    );
    await reporter.start();
    await expect(reporter.complete()).rejects.toThrow("did not end");
    audio.ended = true;
    await reporter.complete();
    expect(sent.at(-1)?.event_type).toBe("COMPLETED");
    expect(sent.at(-1)?.last_frame).toBe(16000);
    reporter.dispose();
  });
});
