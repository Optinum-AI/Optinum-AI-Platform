import type { ReactNode } from "react";

export default function StatCard({ label, value, delta, deltaGood, icon }: {
  label: string;
  value: string;
  delta: string;
  deltaGood?: boolean;
  icon?: ReactNode;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <span className="micro">{label}</span>
        {icon && <span className="text-salmon/70">{icon}</span>}
      </div>
      <div className="text-3xl font-extrabold mt-3">{value}</div>
      <div className={`font-mono text-[11px] mt-2 ${deltaGood === false ? "text-accent2" : "text-pos"}`}>{delta}</div>
    </div>
  );
}
