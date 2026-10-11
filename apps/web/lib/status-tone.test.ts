import { describe, expect, it } from "vitest";
import { statusTone } from "./status-tone";

describe("evidence status colors", () => {
  it("reserves green for evidence-backed outcomes", () => {
    expect(statusTone("SATISFIED")).toBe("good");
    expect(statusTone("RESOLVED_VERIFIED")).toBe("good");
    expect(statusTone("CONFIRMED")).toBe("neutral");
    expect(statusTone("UNVERIFIED")).toBe("neutral");
    expect(statusTone("CLAIM_PERMITTED")).toBe("neutral");
  });

  it("keeps unknown separate from failure", () => {
    expect(statusTone("UNKNOWN")).toBe("warn");
    expect(statusTone("VIOLATED")).toBe("bad");
    expect(statusTone("REPAIR_PENDING")).toBe("bad");
  });
});
