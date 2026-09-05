import type { Node } from "@xyflow/react";
import { NODE_SPEC, NODE_LABELS, NODE_COLORS } from "./nodeSpec";
import type { PersonaNodeData } from "./PersonaNode";

export default function ParamsPanel({
  node,
  onChange,
}: {
  node: Node | null;
  onChange: (key: string, value: string | number) => void;
}) {
  if (!node) {
    return (
      <div className="card p-4 text-xs text-salmon/60">
        Select a node on the canvas to tune its parameters. Drag from a node's bottom handle to another
        node's top handle to wire dependencies. No prompts needed — the bots read these controls.
      </div>
    );
  }
  const data = node.data as PersonaNodeData;
  const spec = NODE_SPEC[data.nodeType] ?? {};
  const color = NODE_COLORS[data.nodeType] ?? "#dc2626";

  return (
    <div className="card p-4 space-y-4">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full" style={{ background: color }} />
        <span className="font-bold text-sm">{NODE_LABELS[data.nodeType]}</span>
        <span className="micro text-salmon/50 ml-auto">{node.id}</span>
      </div>
      {Object.entries(spec).map(([key, s]) => (
        <div key={key}>
          <label className="micro block mb-1.5">{key.replace(/_/g, " ")}</label>
          {s.kind === "enum" ? (
            <select
              className="w-full bg-card2 border border-line rounded px-2 py-1.5 text-xs outline-none focus:border-accent"
              value={String(data.params[key] ?? s.default)}
              onChange={(e) => onChange(key, e.target.value)}
            >
              {s.options!.map((o) => (
                <option key={o} value={o}>{o.replace(/_/g, " ")}</option>
              ))}
            </select>
          ) : (
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={s.min}
                max={s.max}
                value={Number(data.params[key] ?? s.default)}
                onChange={(e) => onChange(key, Number(e.target.value))}
                className="flex-1 accent-[#dc2626]"
              />
              <span className="font-mono text-xs text-salmon w-8 text-right">
                {Number(data.params[key] ?? s.default)}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
