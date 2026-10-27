"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { StatusBar } from "@/components/StatusBar";
import { Terminal } from "@/components/Terminal";
import {
  api,
  Artifact,
  GraphEdge,
  GraphNode,
  Health,
  Investigation,
  ReconstructReport,
  TimelineEvent,
} from "@/lib/api";

const EvidenceGraph = dynamic(
  () => import("@/components/EvidenceGraph").then((m) => m.EvidenceGraph),
  { ssr: false, loading: () => <PanelSkeleton title="Evidence Graph" /> }
);

type Tab = "terminal" | "archive" | "graph" | "timeline" | "settings";

const TABS: { id: Tab; label: string }[] = [
  { id: "terminal", label: "Terminal" },
  { id: "archive", label: "Archive" },
  { id: "graph", label: "Evidence Graph" },
  { id: "timeline", label: "Timeline" },
  { id: "settings", label: "Settings" },
];

export default function HomePage() {
  const [tab, setTab] = useState<Tab>("terminal");
  const [health, setHealth] = useState<Health | null>(null);
  const [inv, setInv] = useState<Investigation | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [selectedArt, setSelectedArt] = useState<Artifact | null>(null);
  const [graphNode, setGraphNode] = useState<GraphNode | null>(null);
  const [graphEdge, setGraphEdge] = useState<GraphEdge | null>(null);
  const [graphTick, setGraphTick] = useState(0);
  const [semanticSearch, setSemanticSearch] = useState(false);
  const [report, setReport] = useState<ReconstructReport | null>(null);
  const [firstRun, setFirstRun] = useState(true);
  const [muted, setMuted] = useState(false);
  const [graphFilter, setGraphFilter] = useState("all");
  const [provider, setProvider] = useState("mock");
  const [customPersonality, setCustomPersonality] = useState("");
  const [offline, setOffline] = useState(true);

  const reducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const refreshInv = useCallback(async (id: string) => {
    const list = await api.listInvestigations();
    const current = list.find((i) => i.id === id) || list[0];
    if (current) setInv(current);
    const arts = await api.getArtifacts(id);
    setArtifacts(arts);
    setTimeline(await api.timeline(id));
  }, []);

  const boot = useCallback(async (sample: boolean) => {
    const h = await api.health();
    setHealth(h);
    setProvider(h.model_provider);
    const created = await api.createInvestigation({
      load_sample: sample,
      active_personality: "phantom",
      title: sample ? undefined : "New Investigation",
    });
    setInv(created);
    await refreshInv(created.id);
    setFirstRun(false);
    localStorage.setItem("phantom_onboarded", "1");
  }, [refreshInv]);

  useEffect(() => {
    setOffline(typeof navigator !== "undefined" ? !navigator.onLine : true);
    const on = () => setOffline(!navigator.onLine);
    window.addEventListener("online", on);
    window.addEventListener("offline", on);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", on);
    };
  }, []);

  useEffect(() => {
    void (async () => {
      const h = await api.health();
      setHealth(h);
      const onboarded = localStorage.getItem("phantom_onboarded");
      const list = await api.listInvestigations();
      if (list.length) {
        setInv(list[0]);
        await refreshInv(list[0].id);
        setFirstRun(!onboarded);
      }
    })().catch(console.error);
  }, [refreshInv]);

  const onRefresh = useCallback(async () => {
    if (inv) await refreshInv(inv.id);
    setGraphTick((t) => t + 1);
  }, [inv, refreshInv]);

  const onInspect = useCallback(
    (id: string) => {
      const a = artifacts.find((x) => x.id === id);
      if (a) {
        setSelectedArt(a);
        setTab("archive");
      }
    },
    [artifacts]
  );

  if (firstRun && !inv) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-6">
        <div className="max-w-lg space-y-6 rounded-xl border border-phantom-violet/30 bg-phantom-panel p-8">
          <h1 className="font-mono text-2xl text-phantom-green">PHANTOM</h1>
          <p className="text-sm text-phantom-muted leading-relaxed">
            Investigate a fictional digital haunting using local artifacts. Files stay on
            your machine. Horror content is entertainment only — no real ghost detection.
          </p>
          <ul className="list-disc pl-5 text-sm space-y-1 text-gray-300">
            <li>Try the sample case without downloading an AI model.</li>
            <li>Configure Ollama later for full local inference.</li>
          </ul>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="rounded bg-phantom-violet px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              onClick={() => void boot(true)}
            >
              Sample: THE LAST PROCESS
            </button>
            <button
              type="button"
              className="rounded border border-phantom-green/40 px-4 py-2 text-sm text-phantom-green"
              onClick={() => void boot(false)}
            >
              Empty investigation
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col">
      <StatusBar health={health} investigation={inv} offline={offline} />
      <nav className="flex flex-wrap gap-1 border-b border-phantom-violet/10 bg-phantom-panel/50 px-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm ${
              tab === t.id
                ? "border-b-2 border-phantom-green text-phantom-green"
                : "text-phantom-muted hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 p-2">
          <button
            type="button"
            className="text-xs text-phantom-muted hover:text-white"
            onClick={() => void boot(true)}
          >
            Sample investigation
          </button>
          <button
            type="button"
            className="text-xs text-phantom-muted hover:text-white"
            onClick={() => void boot(false)}
          >
            New investigation
          </button>
          <button
            type="button"
            aria-pressed={muted}
            className="text-xs text-phantom-muted"
            onClick={() => setMuted((m) => !m)}
          >
            {muted ? "Unmute" : "Mute"} SFX
          </button>
        </div>
      </nav>

      <div className="flex flex-1 flex-col gap-4 p-4 lg:flex-row">
        <section className="flex flex-1 flex-col min-h-[420px]">
          {tab === "terminal" && inv && (
            <Terminal
              invId={inv.id}
              artifacts={artifacts}
              onRefresh={onRefresh}
              onInspect={onInspect}
              muted={muted}
              reducedMotion={reducedMotion}
            />
          )}
          {tab === "archive" && (
            <ArchivePanel
              invId={inv?.id}
              artifacts={artifacts}
              selected={selectedArt}
              onSelect={setSelectedArt}
              onUploaded={onRefresh}
            />
          )}
          {tab === "graph" && inv && (
            <div className="flex h-full flex-col gap-2">
              <select
                className="w-fit rounded border border-phantom-violet/30 bg-black px-2 py-1 text-xs"
                value={graphFilter}
                onChange={(e) => setGraphFilter(e.target.value)}
                aria-label="Graph filter"
              >
                <option value="all">All nodes</option>
                <option value="artifact">Artifacts</option>
                <option value="clue">Clues</option>
                <option value="entity">Entities</option>
                <option value="event">Events</option>
                <option value="inference">Inferences</option>
              </select>
              <EvidenceGraph
                invId={inv.id}
                filter={graphFilter}
                refreshKey={graphTick}
                onSelectNode={setGraphNode}
                onSelectEdge={setGraphEdge}
              />
              {graphNode && (
                <GraphInspector
                  invId={inv.id}
                  node={graphNode}
                  onRefresh={onRefresh}
                />
              )}
              {graphEdge && (
                <EdgeInspector edge={graphEdge} onRefresh={onRefresh} />
              )}
            </div>
          )}
          {tab === "timeline" && (
            <TimelinePanel events={timeline} onOpenArtifact={onInspect} />
          )}
          {tab === "settings" && inv && (
            <SettingsPanel
              invId={inv.id}
              provider={provider}
              setProvider={setProvider}
              customPersonality={customPersonality}
              setCustomPersonality={setCustomPersonality}
              semanticSearch={semanticSearch}
              setSemanticSearch={setSemanticSearch}
              onExport={async (fmt) => {
                const data = await api.export(inv.id, fmt);
                downloadText(`phantom-export.${fmt === "json" ? "json" : "md"}`, data);
              }}
              onReconstruct={async () => {
                setReport(await api.reconstruct(inv.id));
              }}
              onDelete={async () => {
                await api.deleteInvestigation(inv.id);
                setInv(null);
                setFirstRun(true);
              }}
              report={report}
            />
          )}
        </section>
      </div>
      {firstRun && inv && (
        <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/70 p-4">
          <div className="max-w-md rounded-lg border border-phantom-green/30 bg-phantom-panel p-4 text-sm">
            <p className="text-phantom-green font-mono">FIRST RUN</p>
            <p className="mt-2 text-phantom-muted">
              Use the terminal: <code className="text-phantom-green">scan</code>, then{" "}
              <code className="text-phantom-green">memories</code> and{" "}
              <code className="text-phantom-green">inspect &lt;id&gt;</code>.
            </p>
            <button
              type="button"
              className="mt-3 text-phantom-violet underline"
              onClick={() => setFirstRun(false)}
            >
              Enter the archive
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

function PanelSkeleton({ title }: { title: string }) {
  return (
    <div className="flex h-64 items-center justify-center rounded-lg border border-phantom-violet/20 text-phantom-muted">
      Loading {title}…
    </div>
  );
}

function ArchivePanel({
  invId,
  artifacts,
  selected,
  onSelect,
  onUploaded,
}: {
  invId?: string;
  artifacts: Artifact[];
  selected: Artifact | null;
  onSelect: (a: Artifact) => void;
  onUploaded: () => Promise<void>;
}) {
  return (
    <div className="grid h-full gap-4 md:grid-cols-2">
      <div className="overflow-y-auto rounded-lg border border-phantom-violet/20 bg-phantom-panel p-3">
        <label className="mb-3 block text-xs uppercase text-phantom-muted">
          Import artifact (explicit selection only)
          <input
            type="file"
            accept=".txt,.md,.markdown,.json,.csv,.log"
            className="mt-1 block w-full text-sm"
            disabled={!invId}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f && invId) {
                void api.uploadArtifact(invId, f).then(() => onUploaded());
              }
              e.target.value = "";
            }}
          />
        </label>
        <ul className="space-y-2">
          {artifacts.map((a) => (
            <li key={a.id}>
              <button
                type="button"
                onClick={() => onSelect(a)}
                className="w-full rounded border border-transparent px-2 py-2 text-left text-sm hover:border-phantom-violet/40"
              >
                <span className="text-phantom-green">{a.filename}</span>
                <span className="block text-xs text-phantom-muted">{a.id}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="overflow-y-auto rounded-lg border border-phantom-violet/20 bg-black/50 p-4 font-mono text-xs whitespace-pre-wrap">
        {selected ? (
          <>
            <p className="mb-2 text-phantom-violet">{selected.filename}</p>
            {selected.summary && (
              <p className="mb-3 text-phantom-muted">{selected.summary}</p>
            )}
            {selected.content}
          </>
        ) : (
          <p className="text-phantom-muted">Select an artifact to inspect.</p>
        )}
      </div>
    </div>
  );
}

function TimelinePanel({
  events,
  onOpenArtifact,
}: {
  events: TimelineEvent[];
  onOpenArtifact: (id: string) => void;
}) {
  const dated = events.filter((e) => e.timestamp);
  const unknown = events.filter((e) => !e.timestamp);
  return (
    <div className="space-y-4 overflow-y-auto rounded-lg border border-phantom-violet/20 bg-phantom-panel p-4">
      <Section title="Dated events" items={dated} onOpen={onOpenArtifact} />
      <Section title="Unknown date" items={unknown} onOpen={onOpenArtifact} />
    </div>
  );
}

function Section({
  title,
  items,
  onOpen,
}: {
  title: string;
  items: TimelineEvent[];
  onOpen: (id: string) => void;
}) {
  if (!items.length) return null;
  return (
    <div>
      <h3 className="mb-2 text-xs uppercase tracking-wide text-phantom-muted">{title}</h3>
      <ul className="space-y-3">
        {items.map((e) => (
          <li key={e.id} className="rounded border border-phantom-violet/10 p-3 text-sm">
            <div className="flex justify-between gap-2">
              <span className="text-phantom-green">{e.timestamp || "UNKNOWN"}</span>
              <span className="text-xs uppercase text-phantom-violet">{e.evidence_type}</span>
            </div>
            <p className="mt-1">{e.description}</p>
            {e.source_references?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {e.source_references.map((ref) => (
                  <button
                    key={ref}
                    type="button"
                    className="text-xs text-phantom-green underline"
                    onClick={() => onOpen(ref)}
                  >
                    {ref}
                  </button>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SettingsPanel({
  invId,
  provider,
  setProvider,
  customPersonality,
  setCustomPersonality,
  semanticSearch,
  setSemanticSearch,
  onExport,
  onReconstruct,
  onDelete,
  report,
}: {
  invId: string;
  provider: string;
  setProvider: (p: string) => void;
  customPersonality: string;
  setCustomPersonality: (s: string) => void;
  semanticSearch: boolean;
  setSemanticSearch: (v: boolean) => void;
  onExport: (fmt: "markdown" | "json") => Promise<void>;
  onReconstruct: () => Promise<void>;
  onDelete: () => Promise<void>;
  report: ReconstructReport | null;
}) {
  return (
    <div className="space-y-6 overflow-y-auto rounded-lg border border-phantom-violet/20 bg-phantom-panel p-4 text-sm">
      <section>
        <h2 className="text-phantom-green font-mono">Model</h2>
        <p className="mt-1 text-phantom-muted text-xs">
          Mock mode works offline with no download. Ollama: install from ollama.com, pull e.g.{" "}
          <code>qwen2.5:3b</code> (~2GB+) — check model license before use.
        </p>
        <select
          className="mt-2 rounded border border-phantom-violet/30 bg-black px-2 py-1"
          value={provider}
          onChange={(e) => {
            const v = e.target.value;
            setProvider(v);
            void api.updateModel({ provider: v });
          }}
        >
          <option value="mock">Demonstration (Mock)</option>
          <option value="ollama">Ollama (Local)</option>
        </select>
        <label className="mt-3 flex items-center gap-2 text-xs text-phantom-muted">
          <input
            type="checkbox"
            checked={semanticSearch}
            onChange={(e) => {
              setSemanticSearch(e.target.checked);
              void api.updateModel({
                provider,
                semantic_search_enabled: e.target.checked,
              });
            }}
          />
          Semantic retrieval (Ollama embeddings — requires{" "}
          <code>nomic-embed-text</code> or compatible model)
        </label>
      </section>
      <section>
        <h2 className="text-phantom-green font-mono">Personality</h2>
        <select
          className="mt-2 rounded border border-phantom-violet/30 bg-black px-2 py-1 text-xs"
          defaultValue="phantom"
          onChange={(e) => {
            void api.updateInvestigationSettings(invId, {
              active_personality: e.target.value,
            });
          }}
        >
          <option value="witness">The Witness</option>
          <option value="archivist">The Archivist</option>
          <option value="phantom">The Phantom</option>
          <option value="echo">The Echo</option>
        </select>
        <textarea
          className="mt-2 w-full rounded border border-phantom-violet/30 bg-black p-2 text-xs"
          rows={3}
          placeholder="Optional custom instructions..."
          value={customPersonality}
          onChange={(e) => setCustomPersonality(e.target.value)}
          onBlur={() => {
            void api.updateInvestigationSettings(invId, {
              custom_personality: customPersonality,
            });
          }}
        />
      </section>
      <section>
        <h2 className="text-phantom-green font-mono">Privacy</h2>
        <p className="text-xs text-phantom-muted">
          Data stored locally in backend/data/phantom.db. Deleting an investigation removes
          associated records from the app database (OS backups may retain copies).
        </p>
        <button
          type="button"
          className="mt-2 rounded border border-phantom-red/50 px-3 py-1 text-phantom-red text-xs"
          onClick={() => void onDelete()}
        >
          Delete this investigation
        </button>
      </section>
      <section className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded bg-phantom-violet px-3 py-1 text-xs"
          onClick={() => void onReconstruct()}
        >
          Final reconstruction
        </button>
        <button
          type="button"
          className="rounded border border-phantom-green/40 px-3 py-1 text-xs text-phantom-green"
          onClick={() => void onExport("markdown")}
        >
          Export Markdown
        </button>
        <button
          type="button"
          className="rounded border border-phantom-green/40 px-3 py-1 text-xs text-phantom-green"
          onClick={() => void onExport("json")}
        >
          Export JSON
        </button>
      </section>
      {report && (
        <article className="rounded border border-phantom-green/20 bg-black/40 p-3 text-xs space-y-2 max-h-96 overflow-y-auto">
          <h3 className="text-phantom-green">Final Reconstruction</h3>
          <p>{report.case_summary}</p>
          <p className="text-phantom-muted">{report.disclaimer}</p>
          <p className="italic">{report.final_story}</p>
        </article>
      )}
    </div>
  );
}

function GraphInspector({
  invId,
  node,
  onRefresh,
}: {
  invId: string;
  node: GraphNode;
  onRefresh: () => Promise<void>;
}) {
  const [target, setTarget] = useState("");
  return (
    <aside className="rounded border border-phantom-violet/20 bg-black/40 p-3 text-xs space-y-2">
      <div>
        <strong>{node.label}</strong> ({node.type}) — {node.evidence_type}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded border border-phantom-violet/30 bg-black px-2 py-1"
          placeholder="Connect to node id..."
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        />
        <button
          type="button"
          className="rounded border border-phantom-green/40 px-2 text-phantom-green"
          onClick={() => {
            if (!target.trim()) return;
            void api
              .addRelationship(invId, {
                source_id: node.id,
                target_id: target.trim(),
                explanation: "Manual investigator link",
              })
              .then(() => onRefresh());
          }}
        >
          Link
        </button>
      </div>
    </aside>
  );
}

function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
