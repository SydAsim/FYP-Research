import { describe, expect, it } from "vitest";
import { healthSchema } from "./health-schema";

describe("health contract", () => {
  it("accepts a service liveness response", () => {
    expect(healthSchema.parse({ status: "ok", service: "web" }).service).toBe(
      "web",
    );
  });
});
