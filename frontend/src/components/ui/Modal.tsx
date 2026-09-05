import type { ReactNode } from "react";
import { X } from "lucide-react";

export default function Modal({
  title,
  micro,
  onClose,
  children,
  wide,
}: {
  title: string;
  micro?: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onClick={onClose}>
      <div
        className={`card bg-card2 w-full ${wide ? "max-w-3xl" : "max-w-lg"} p-8 relative max-h-[85vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="absolute top-5 right-5 text-salmon hover:text-white" onClick={onClose} aria-label="Close">
          <X size={18} />
        </button>
        {micro && <div className="micro flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-accent inline-block" />{micro}</div>}
        <h2 className="text-2xl font-bold mt-2 mb-6">{title}</h2>
        {children}
      </div>
    </div>
  );
}
