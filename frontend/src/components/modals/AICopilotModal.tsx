import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { post } from "../../api/client";
import Modal from "../ui/Modal";

interface Message {
  role: "user" | "assistant";
  content: string;
  provider?: string;
  time: string;
}

const QUICK_PROMPTS = [
  "How does Browser Connect automate posting without API limits?",
  "How are CAPTCHAs and 2FA handled securely?",
  "Suggest a 7-day multi-channel posting strategy for SaaS",
  "Write an attention-grabbing product launch post for LinkedIn",
];

export default function AICopilotModal({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello. I am the Optinum AI Social & Automation Copilot. I can assist you with channel connections, automated browser workflows, content strategy, and multi-platform distribution. How can I help today?",
      time: "Just now",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const send = async (text: string) => {
    const q = text.trim();
    if (!q || busy) return;

    const userMsg: Message = {
      role: "user",
      content: q,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const res = await post<{ reply: string; provider: string }>("/social-hub/ai-chat", {
        message: q,
      });

      const aiMsg: Message = {
        role: "assistant",
        content: res.reply || "No response received.",
        provider: res.provider,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: unknown) {
      const errorMsg: Message = {
        role: "assistant",
        content:
          err instanceof Error
            ? `Error: ${err.message}`
            : "Failed to generate AI response. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      title="Optinum AI Copilot"
      micro="Autonomous Social & Growth Intelligence"
      onClose={onClose}
    >
      <div className="flex flex-col h-[480px] max-h-[75vh]">
        {/* Messages scroll area */}
        <div className="flex-1 overflow-y-auto space-y-3.5 pr-2 -mr-2">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex gap-3 text-xs ${
                m.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <div
                className={`w-7 h-7 rounded flex items-center justify-center shrink-0 ${
                  m.role === "user"
                    ? "bg-accent/20 border border-accent text-accent2"
                    : "bg-cyan-950 border border-cyan-700/50 text-cyan-400"
                }`}
              >
                {m.role === "user" ? <User size={13} /> : <Bot size={14} />}
              </div>

              <div
                className={`max-w-[82%] rounded-lg p-3 leading-relaxed ${
                  m.role === "user"
                    ? "bg-accent text-white"
                    : "bg-card2 border border-line text-salmon/90"
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>
                <div className="flex items-center justify-between gap-2 mt-1.5 pt-1 border-t border-line/30 text-[10px] text-salmon/50 font-mono">
                  <span>{m.time}</span>
                  {m.provider && <span>Engine: {m.provider}</span>}
                </div>
              </div>
            </div>
          ))}

          {busy && (
            <div className="flex gap-3 text-xs">
              <div className="w-7 h-7 rounded bg-cyan-950 border border-cyan-700/50 text-cyan-400 flex items-center justify-center shrink-0">
                <Bot size={14} />
              </div>
              <div className="p-3 rounded-lg bg-card2 border border-line flex items-center gap-2 text-salmon/70 text-xs">
                <Loader2 size={13} className="animate-spin text-cyan-400" />
                <span>Analyzing request & generating response...</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Quick prompt chips */}
        {messages.length <= 2 && (
          <div className="pt-3 pb-2 border-t border-line/50 mt-2 flex flex-wrap gap-1.5">
            {QUICK_PROMPTS.map((qp, idx) => (
              <button
                key={idx}
                className="text-[10px] font-mono px-2 py-1 rounded bg-card hover:bg-card2 border border-line text-salmon/80 hover:text-white transition text-left"
                onClick={() => send(qp)}
              >
                {qp}
              </button>
            ))}
          </div>
        )}

        {/* Input box */}
        <form
          className="pt-3 border-t border-line flex items-center gap-2 mt-auto"
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
        >
          <input
            className="input text-xs flex-1"
            placeholder="Ask AI Copilot about channels, automation, strategy..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
          />
          <button
            type="submit"
            className="btn-accent px-3 py-2 text-xs flex items-center gap-1.5"
            disabled={!input.trim() || busy}
          >
            {busy ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
            <span>Send</span>
          </button>
        </form>
      </div>
    </Modal>
  );
}
