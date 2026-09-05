import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";
import { NODE_LABELS, NODE_COLORS } from "./nodeSpec";

export interface PersonaNodeData {
  nodeType: string;
  params: Record<string, string | number>;
  [key: string]: unknown;
}

function PersonaNode({ data, selected }: NodeProps) {
  const d = data as PersonaNodeData;
  const color = NODE_COLORS[d.nodeType] ?? "#dc2626";
  const summary = Object.entries(d.params ?? {})
    .slice(0, 2)
    .map(([k, v]) => `${k.split("_")[0]}:${v}`)
    .join(" ");
  return (
    <div
      className={`rounded-md border bg-card2 px-3 py-2 min-w-36 shadow-lg ${selected ? "border-accent" : "border-line"}`}
      style={{ boxShadow: selected ? `0 0 0 2px ${color}55` : undefined }}
    >
      <Handle type="target" position={Position.Top} className="!bg-salmon !w-2 !h-2 !border-0" />
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full" style={{ background: color }} />
        <span className="micro" style={{ color }}>{NODE_LABELS[d.nodeType] ?? d.nodeType}</span>
      </div>
      <div className="font-mono text-[10px] text-salmon/80 mt-1 truncate max-w-44">{summary}</div>
      <Handle type="source" position={Position.Bottom} className="!bg-salmon !w-2 !h-2 !border-0" />
    </div>
  );
}

export default memo(PersonaNode);
