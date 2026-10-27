import { api, Artifact } from "./api";

export type CommandContext = {
  invId: string;
  artifacts: Artifact[];
  onRefresh: () => Promise<void>;
  onInspect: (artifactId: string) => void;
};

export type CommandResult = {
  output: string;
  sideEffect?: "clear" | "exit";
};

export async function parseAndRun(
  line: string,
  ctx: CommandContext
): Promise<CommandResult> {
  const trimmed = line.trim();
  if (!trimmed) return { output: "" };

  const [cmd, ...rest] = trimmed.split(/\s+/);
  const arg = rest.join(" ");
  const lower = cmd.toLowerCase();

  switch (lower) {
    case "help":
      return {
        output: `PHANTOM COMMAND INTERFACE
help              — this message
scan              — analyze archive (memory engine)
memories          — list artifact ids
inspect <id>      — show artifact excerpt
connect <clue_id> — ask about a connection (via AI)
question <text>   — ask the ghost
timeline          — list timeline event count
theory            — request competing theories
hint              — investigation hint
clear             — clear terminal view
exit              — end session banner

All horror content is fictional. No real ghost detection.`,
      };
    case "clear":
      return { output: "", sideEffect: "clear" };
    case "exit":
      return {
        output: "SESSION SUSPENDED. LOCAL DATA REMAINS IN YOUR ARCHIVE.",
        sideEffect: "exit",
      };
    case "scan": {
      const r = await api.scan(ctx.invId);
      await ctx.onRefresh();
      return {
        output: `SCAN COMPLETE.
Artifacts processed: ${r.artifacts_processed}
Mode: ${r.is_demonstration ? "DEMONSTRATION (mock)" : "LOCAL MODEL"}
Check EVIDENCE GRAPH and TIMELINE tabs.`,
      };
    }
    case "memories": {
      if (!ctx.artifacts.length) {
        return { output: "MEMORY FRAGMENTS FOUND: 00\nImport files or load sample investigation." };
      }
      const lines = ctx.artifacts.map(
        (a) => `${a.id}  ${a.filename}${a.summary ? ` — ${a.summary.slice(0, 60)}…` : ""}`
      );
      return { output: `MEMORY FRAGMENTS FOUND: ${String(ctx.artifacts.length).padStart(2, "0")}\n${lines.join("\n")}` };
    }
    case "inspect": {
      if (!arg) return { output: "Usage: inspect <artifact_id>" };
      const art = ctx.artifacts.find((a) => a.id === arg || a.id.startsWith(arg));
      if (!art) {
        try {
          const remote = await api.getArtifact(arg);
          ctx.onInspect(remote.id);
          return {
            output: `[${remote.id}] ${remote.filename}\n---\n${remote.content.slice(0, 1200)}`,
          };
        } catch {
          return { output: `Artifact not found: ${arg}` };
        }
      }
      ctx.onInspect(art.id);
      return {
        output: `[${art.id}] ${art.filename}\n---\n${art.content.slice(0, 1200)}`,
      };
    }
    case "connect": {
      if (!arg) return { output: "Usage: connect <clue_id>" };
      const r = await api.chat(
        ctx.invId,
        `Explain the connection for clue ${arg}. Label inference vs document evidence.`
      );
      return { output: r.content };
    }
    case "question": {
      if (!arg) return { output: "Usage: question <your question>" };
      const r = await api.chat(ctx.invId, arg);
      const refs =
        r.source_references?.length > 0
          ? `\n[refs: ${r.source_references.join(", ")}]`
          : "";
      return { output: r.content + refs };
    }
    case "timeline": {
      const events = await api.timeline(ctx.invId);
      if (!events.length) {
        return { output: "Timeline empty. Run scan after importing artifacts." };
      }
      const preview = events
        .slice(0, 8)
        .map(
          (e) =>
            `${e.timestamp || "UNKNOWN"} [${e.evidence_type}] ${e.description.slice(0, 70)}`
        )
        .join("\n");
      return {
        output: `TIMELINE ENTRIES: ${events.length}\n${preview}\n(Open TIMELINE panel for full view.)`,
      };
    }
    case "theory": {
      const r = await api.chat(
        ctx.invId,
        "List competing theories for this investigation. Mark each as speculation."
      );
      return { output: r.content };
    }
    case "hint":
      return {
        output:
          "Try: load sample → scan → inspect an artifact id → check graph for 02:13 links.\nContradictory incident reports are intentional.",
      };
    default:
      if (lower.startsWith("question")) {
        const q = trimmed.slice("question".length).trim();
        if (q) return parseAndRun(`question ${q}`, ctx);
      }
      return {
        output: `Unknown command: ${cmd}. Type help.`,
      };
  }
}
