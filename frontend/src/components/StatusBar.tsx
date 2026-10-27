import { Health, Investigation } from "@/lib/api";

type Props = {
  health: Health | null;
  investigation: Investigation | null;
  offline: boolean;
};

export function StatusBar({ health, investigation, offline }: Props) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-2 border-b border-phantom-violet/20 bg-phantom-panel/80 px-4 py-2 text-xs uppercase tracking-wider">
      <div className="flex flex-wrap gap-4">
        <span className="text-phantom-green">PHANTOM</span>
        <span>
          Investigation:{" "}
          <span className="text-white normal-case">{investigation?.title ?? "—"}</span>
        </span>
        <span>Evidence: {investigation?.artifact_count ?? 0}</span>
        <span className="text-phantom-red">
          Unresolved: {investigation?.unresolved_questions ?? 0}
        </span>
      </div>
      <div className="flex flex-wrap gap-4 text-phantom-muted">
        <span>
          Model: {health?.model_provider ?? "…"}{" "}
          {health?.model_available ? (
            <span className="text-phantom-green">online</span>
          ) : health?.model_provider === "mock" ? (
            <span className="text-phantom-violet">demo</span>
          ) : (
            <span className="text-phantom-red">unavailable</span>
          )}
        </span>
        <span>{offline ? "OFFLINE OK" : "NETWORK"}</span>
      </div>
    </header>
  );
}
