import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  ReactFlow, Background, Controls, BackgroundVariant, MarkerType,
  useNodesState, useEdgesState, addEdge,
} from "@xyflow/react";
import type { Node, Edge, Connection, ReactFlowInstance } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Play, Save, Plus, Trash2 } from "lucide-react";
import PersonaNode from "../components/strategy/PersonaNode";
import ParamsPanel from "../components/strategy/ParamsPanel";
import RunLogPanel from "../components/strategy/RunLogPanel";
import { NODE_SPEC, NODE_LABELS, defaultParams } from "../components/strategy/nodeSpec";
import { get, put, post } from "../api/client";
import { useFetch } from "../hooks/useFetch";
import type { Strategy, Execution, Post, Graph } from "../api/types";

const nodeTypes = { persona: PersonaNode };

function toNodes(graph: Graph): Node[] {
  return graph.nodes.map((n) => ({
    id: n.id,
    type: "persona",
    position: n.position,
    data: { nodeType: n.type, params: n.params },
  }));
}

function toEdges(graph: Graph): Edge[] {
  return graph.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    style: { stroke: "#fca5a5", strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#fca5a5" },
  }));
}

export default function StrategyStudioPage() {
  const { id } = useParams();
  const { data: strategy } = useFetch(() => get<Strategy>(`/strategies/${id}`), [id]);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<string | null>(null);
  const [execution, setExecution] = useState<Execution | null>(null);
  const [running, setRunning] = useState(false);
  const [tab, setTab] = useState<"log" | "calendar" | "posts">("log");
  const pollRef = useRef<number | null>(null);
  const rfRef = useRef<ReactFlowInstance | null>(null);

  const { data: posts, refetch: refetchPosts } = useFetch(
    () => get<Post[]>(`/strategies/${id}/posts`),
    [id, execution?.status],
  );

  useEffect(() => {
    if (strategy?.graph) {
      setNodes(toNodes(strategy.graph));
      setEdges(toEdges(strategy.graph));
      setTimeout(() => rfRef.current?.fitView(), 50);
    }
  }, [strategy, setNodes, setEdges]);

  useEffect(() => () => { if (pollRef.current) window.clearInterval(pollRef.current); }, []);

  const onConnect = useCallback(
    (c: Connection) => setEdges((eds) => addEdge({ ...c, style: { stroke: "#fca5a5", strokeWidth: 1.5 } }, eds)),
    [setEdges],
  );

  const selectedNode = useMemo(() => nodes.find((n) => n.id === selectedId) ?? null, [nodes, selectedId]);

  const updateParam = (key: string, value: string | number) => {
    if (!selectedId) return;
    setNodes((ns) => ns.map((n) => (n.id === selectedId ? { ...n, data: { ...n.data, params: { ...(n.data.params as object), [key]: value } } } : n)));
  };

  const addNode = (type: string) => {
    const nid = `n_${type}_${Math.floor(Math.random() * 9000 + 1000)}`;
    setNodes((ns) => [
      ...ns,
      { id: nid, type: "persona", position: { x: 60 + (ns.length % 5) * 60, y: 60 + (ns.length % 5) * 60 }, data: { nodeType: type, params: defaultParams(type) } },
    ]);
  };

  const deleteSelected = () => {
    if (!selectedId) return;
    setNodes((ns) => ns.filter((n) => n.id !== selectedId));
    setEdges((es) => es.filter((e) => e.source !== selectedId && e.target !== selectedId));
    setSelectedId(null);
  };

  const buildGraph = (): Graph => ({
    version: 1,
    nodes: nodes.map((n) => ({
      id: n.id,
      type: (n.data.nodeType as string) ?? "goal",
      position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
      params: (n.data.params as Record<string, string | number>) ?? {},
    })),
    edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
  });

  const save = async () => {
    setSaveState("saving");
    try {
      await put(`/strategies/${id}`, { graph: buildGraph() });
      setSaveState("saved");
    } catch (e) {
      setSaveState(e instanceof Error ? e.message : "invalid graph");
    }
  };

  const run = async () => {
    await save();
    setRunning(true);
    setTab("log");
    const { execution_id } = await post<{ execution_id: string }>(`/strategies/${id}/run`);
    pollRef.current = window.setInterval(async () => {
      const exec = await get<Execution>(`/executions/${execution_id}`);
      setExecution(exec);
      if (exec.status !== "running") {
        if (pollRef.current) window.clearInterval(pollRef.current);
        setRunning(false);
        refetchPosts();
      }
    }, 2500);
  };

  const byDay = useMemo(() => {
    const map = new Map<string, Post[]>();
    for (const p of posts ?? []) {
      const day = p.scheduled_at.slice(0, 10);
      map.set(day, [...(map.get(day) ?? []), p]);
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [posts]);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="micro flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent" /> Strategy Studio • Pictorial Command Graph
          </div>
          <h1 className="text-3xl font-extrabold mt-2">{strategy?.product?.name ?? "Loading..."}</h1>
          <p className="text-salmon/70 text-sm mt-1">
            The Strategist bot drafted this pipeline. Rewire nodes and tune dials — the fleet reads the graph, not prompts.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {saveState && <span className="font-mono text-[10px] text-salmon/70">{saveState}</span>}
          <button className="btn-ghost flex items-center gap-2" onClick={save}><Save size={13} /> Save</button>
          <button className="btn-accent flex items-center gap-2" onClick={run} disabled={running}>
            <Play size={13} /> {running ? "Fleet running..." : "Run Strategy"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <div className="xl:col-span-3 card overflow-hidden" style={{ height: 520 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onInit={(inst) => { rfRef.current = inst; inst.fitView(); }}
            onSelectionChange={({ nodes: sel }) => setSelectedId(sel[0]?.id ?? null)}
            fitView
            proOptions={{ hideAttribution: true }}
            className="bg-ink"
          >
            <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="#262626" />
            <Controls position="bottom-right" />
          </ReactFlow>
        </div>

        <div className="space-y-4">
          <div className="card p-4">
            <div className="micro mb-3 flex items-center gap-2"><Plus size={12} /> Add Node</div>
            <div className="grid grid-cols-2 gap-2">
              {Object.keys(NODE_SPEC).map((t) => (
                <button key={t} className="btn-ghost" onClick={() => addNode(t)}>{NODE_LABELS[t]}</button>
              ))}
            </div>
            <button className="btn-ghost w-full mt-2 border-accent/50 text-accent2 flex items-center justify-center gap-2" onClick={deleteSelected} disabled={!selectedId}>
              <Trash2 size={12} /> Delete Selected
            </button>
          </div>
          <ParamsPanel node={selectedNode} onChange={updateParam} />
        </div>
      </div>

      <div>
        <div className="flex gap-2 mb-3">
          {(["log", "calendar", "posts"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-wider border transition-colors ${
                tab === t ? "border-accent bg-accent/15 text-white" : "border-line text-salmon/70 hover:text-white"
              }`}>
              {t === "log" ? "Run Log" : t === "calendar" ? "Content Calendar" : `Posts (${posts?.length ?? 0})`}
            </button>
          ))}
        </div>
        {tab === "log" && <RunLogPanel logs={execution?.logs ?? []} status={execution?.status ?? "idle"} />}
        {tab === "calendar" && (
          <div className="grid grid-cols-4 gap-3">
            {byDay.length === 0 && <div className="card p-6 text-sm text-salmon/60 col-span-4">Run the strategy to populate the calendar.</div>}
            {byDay.map(([day, dayPosts]) => (
              <div key={day} className="card p-4 space-y-2">
                <div className="micro">{day}</div>
                {dayPosts.map((p) => (
                  <div key={p.id} className="card bg-card2 p-2.5">
                    <div className="font-mono text-[9px] uppercase text-pos">{p.platform} • {p.scheduled_at.slice(11, 16)} UTC</div>
                    <div className="text-[11px] text-salmon/90 mt-1 line-clamp-3">{p.content_text}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
        {tab === "posts" && (
          <div className="grid grid-cols-2 gap-3">
            {(posts ?? []).map((p) => (
              <div key={p.id} className="card p-4">
                <div className="flex justify-between font-mono text-[10px] uppercase">
                  <span className="text-pos">{p.platform}</span>
                  <span className="text-salmon/50">{p.impressions ?? 0} imp • {p.likes ?? 0} likes</span>
                </div>
                <p className="text-sm mt-2">{p.content_text}</p>
                <p className="text-[11px] text-salmon/60 mt-2 italic">Creative note: {p.asset_notes}</p>
              </div>
            ))}
            {(posts ?? []).length === 0 && <div className="card p-6 text-sm text-salmon/60 col-span-2">No posts yet.</div>}
          </div>
        )}
      </div>
    </div>
  );
}
