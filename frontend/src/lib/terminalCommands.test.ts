import { describe, expect, it, vi } from "vitest";
import { parseAndRun } from "./terminalCommands";

vi.mock("./api", () => ({
  api: {
    scan: vi.fn(),
    chat: vi.fn(),
    timeline: vi.fn(),
    getArtifact: vi.fn(),
  },
}));

describe("terminal command parser", () => {
  it("parses help", async () => {
    const r = await parseAndRun("help", {
      invId: "x",
      artifacts: [],
      onRefresh: async () => {},
      onInspect: () => {},
    });
    expect(r.output).toContain("scan");
  });

  it("parses clear", async () => {
    const r = await parseAndRun("clear", {
      invId: "x",
      artifacts: [],
      onRefresh: async () => {},
      onInspect: () => {},
    });
    expect(r.sideEffect).toBe("clear");
  });
});
