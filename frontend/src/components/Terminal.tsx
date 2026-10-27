"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Artifact } from "@/lib/api";
import { parseAndRun } from "@/lib/terminalCommands";

type Props = {
  invId: string;
  artifacts: Artifact[];
  onRefresh: () => Promise<void>;
  onInspect: (id: string) => void;
  muted: boolean;
  reducedMotion: boolean;
};

type Line = { text: string; type: "system" | "out" | "in" | "error" };

const BOOT_LINES = [
  "PHANTOM KERNEL v1.0",
  "Initializing memory bus........ OK",
  "Mounting local archive......... OK",
  "SESSION RESTORED.",
  "MEMORY FRAGMENTS FOUND: --",
  "LAST KNOWN ACTIVITY: UNKNOWN",
  "THERE IS SOMETHING IN THE ARCHIVE.",
];

export function Terminal({
  invId,
  artifacts,
  onRefresh,
  onInspect,
  muted,
  reducedMotion,
}: Props) {
  const [lines, setLines] = useState<Line[]>([]);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [histIdx, setHistIdx] = useState(-1);
  const [booted, setBooted] = useState(false);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const audioCtx = useRef<AudioContext | null>(null);

  const playKey = useCallback(() => {
    if (muted) return;
    try {
      if (!audioCtx.current) audioCtx.current = new AudioContext();
      const ctx = audioCtx.current;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.frequency.value = 880;
      g.gain.value = 0.02;
      o.connect(g);
      g.connect(ctx.destination);
      o.start();
      o.stop(ctx.currentTime + 0.03);
    } catch {
      /* ignore */
    }
  }, [muted]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  useEffect(() => {
    if (booted || reducedMotion) {
      setLines([
        { text: "SESSION RESTORED.", type: "system" },
        {
          text: `MEMORY FRAGMENTS FOUND: ${String(artifacts.length).padStart(2, "0")}`,
          type: "system",
        },
        { text: "Type help for commands.", type: "system" },
      ]);
      setBooted(true);
      return;
    }
    let i = 0;
    const id = setInterval(() => {
      if (i >= BOOT_LINES.length) {
        clearInterval(id);
        setBooted(true);
        return;
      }
      const t = BOOT_LINES[i];
      setLines((prev) => [
        ...prev,
        {
          text:
            t === "MEMORY FRAGMENTS FOUND: --"
              ? `MEMORY FRAGMENTS FOUND: ${String(artifacts.length).padStart(2, "0")}`
              : t,
          type: "system",
        },
      ]);
      i++;
    }, 420);
    return () => clearInterval(id);
  }, [booted, reducedMotion, artifacts.length]);

  const runCommand = async (cmd: string) => {
    setLines((p) => [...p, { text: `> ${cmd}`, type: "in" }]);
    setBusy(true);
    try {
      const result = await parseAndRun(cmd, {
        invId,
        artifacts,
        onRefresh,
        onInspect,
      });
      if (result.sideEffect === "clear") {
        setLines([]);
      } else if (result.output) {
        setLines((p) => [...p, { text: result.output, type: "out" }]);
      }
    } catch (e) {
      setLines((p) => [
        ...p,
        { text: e instanceof Error ? e.message : "Command failed", type: "error" },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = input.trim();
    if (!v || busy) return;
    setHistory((h) => [...h, v]);
    setHistIdx(-1);
    setInput("");
    playKey();
    void runCommand(v);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!history.length) return;
      const next = histIdx < 0 ? history.length - 1 : Math.max(0, histIdx - 1);
      setHistIdx(next);
      setInput(history[next]);
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (histIdx < 0) return;
      const next = histIdx + 1;
      if (next >= history.length) {
        setHistIdx(-1);
        setInput("");
      } else {
        setHistIdx(next);
        setInput(history[next]);
      }
    }
  };

  return (
    <div className="flex h-full flex-col rounded-lg border border-phantom-violet/30 bg-black/60 bg-scanlines font-mono text-sm shadow-lg shadow-phantom-violet/10">
      <div className="flex-1 overflow-y-auto p-4 space-y-1">
        {lines.map((ln, idx) => (
          <motion.div
            key={idx}
            initial={reducedMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            className={
              ln.type === "system"
                ? "text-phantom-green/90"
                : ln.type === "in"
                  ? "text-white"
                  : ln.type === "error"
                    ? "text-phantom-red"
                    : "text-phantom-green"
            }
          >
            <Typewriter text={ln.text} enabled={!reducedMotion && ln.type === "system"} />
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-phantom-violet/20 p-3">
        <span className="text-phantom-green animate-pulse" aria-hidden>
          ▮
        </span>
        <input
          className="flex-1 bg-transparent text-phantom-green outline-none placeholder:text-phantom-muted"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy || !booted}
          placeholder="enter command..."
          aria-label="Terminal command input"
          autoComplete="off"
          spellCheck={false}
        />
      </form>
    </div>
  );
}

function Typewriter({ text, enabled }: { text: string; enabled: boolean }) {
  const [shown, setShown] = useState(enabled ? "" : text);
  useEffect(() => {
    if (!enabled) {
      setShown(text);
      return;
    }
    setShown("");
    let i = 0;
    const t = setInterval(() => {
      i++;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(t);
    }, 12);
    return () => clearInterval(t);
  }, [text, enabled]);
  return <span>{shown}</span>;
}
