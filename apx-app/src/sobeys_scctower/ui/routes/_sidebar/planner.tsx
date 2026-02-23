import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Send,
  Loader2,
  Bot,
  User,
  Brain,
  Wrench,
  ChevronRight,
} from "lucide-react";
import Markdown from "react-markdown";

export const Route = createFileRoute("/_sidebar/planner")({
  component: () => <PlannerChat />,
});

interface ChatStep {
  type: "thinking" | "tool_call" | "genie_call";
  title: string;
  content: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  steps?: ChatStep[];
  streaming?: boolean;
  elapsed?: number;
}

function StepIcon({ type }: { type: ChatStep["type"] }) {
  switch (type) {
    case "thinking":
      return <Brain className="h-3.5 w-3.5 text-violet-500" />;
    case "genie_call":
    case "tool_call":
      return <Wrench className="h-3.5 w-3.5 text-blue-500" />;
    default:
      return null;
  }
}

function StepLabel({ step }: { step: ChatStep }) {
  switch (step.type) {
    case "thinking":
      return "Reasoning";
    case "genie_call":
      return `Querying ${step.title}`;
    case "tool_call":
      return `Executing ${step.title}`;
    default:
      return step.title;
  }
}

function CollapsibleStep({ step }: { step: ChatStep }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border/50 rounded-md overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-3 py-2 text-xs text-muted-foreground hover:bg-muted/50 transition-colors"
      >
        <ChevronRight
          className={`h-3 w-3 transition-transform ${open ? "rotate-90" : ""}`}
        />
        <StepIcon type={step.type} />
        <span className="font-medium">
          <StepLabel step={step} />
        </span>
      </button>
      {open && (
        <div className="px-3 pb-2 text-xs border-t border-border/30">
          <div className="pt-2 prose prose-xs max-w-none text-muted-foreground [&_p]:my-0.5">
            <Markdown>{step.content}</Markdown>
          </div>
        </div>
      )}
    </div>
  );
}

function AssistantMessage({ msg }: { msg: Message }) {
  const steps = msg.steps || [];

  return (
    <div>
      {steps.length > 0 && (
        <div className="flex flex-col gap-1.5 mb-3">
          {steps.map((step, j) => (
            <CollapsibleStep key={j} step={step} />
          ))}
        </div>
      )}
      {msg.streaming && !msg.content && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>
            Agent is thinking...
            {msg.elapsed ? ` (${msg.elapsed}s)` : ""}
          </span>
        </div>
      )}
      {msg.content && (
        <div
          className="prose prose-sm max-w-none dark:prose-invert
            [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-4 [&_h2]:mb-2
            [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-3 [&_h3]:mb-1
            [&_p]:my-2
            [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-6
            [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-6
            [&_li]:my-0.5 [&_li]:pl-1
            [&_ul_ul]:my-0.5 [&_ul_ul]:pl-4
            [&_ol_ul]:my-0.5 [&_ol_ul]:pl-4
            [&_table]:w-full [&_table]:text-xs [&_table]:border-collapse [&_table]:my-3
            [&_th]:border [&_th]:border-border [&_th]:px-2 [&_th]:py-1 [&_th]:bg-muted [&_th]:font-medium [&_th]:text-left
            [&_td]:border [&_td]:border-border [&_td]:px-2 [&_td]:py-1
            [&_hr]:my-4 [&_hr]:border-border
            [&_strong]:font-semibold
            [&_code]:bg-muted [&_code]:px-1 [&_code]:rounded [&_code]:text-xs
            [&_pre]:bg-muted [&_pre]:p-3 [&_pre]:rounded-md [&_pre]:overflow-x-auto
            [&_blockquote]:border-l-2 [&_blockquote]:border-border [&_blockquote]:pl-3 [&_blockquote]:italic
            [&_img]:max-w-full [&_img]:rounded-md"
        >
          <Markdown>{msg.content}</Markdown>
        </div>
      )}
    </div>
  );
}

function PlannerChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");

    const userMsg: Message = { role: "user", content: text };
    const allMessages = [...messages, userMsg];
    const assistantIdx = allMessages.length;

    setMessages([
      ...allMessages,
      { role: "assistant", content: "", steps: [], streaming: true },
    ]);
    setStreaming(true);

    try {
      const startRes = await fetch("/api/chat/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: allMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!startRes.ok) throw new Error(`Start failed: ${startRes.status}`);
      const { task_id } = await startRes.json();

      // Poll frequently — 1s for first 30s, then 2s after
      let attempts = 0;
      const maxAttempts = 250;
      const startTime = Date.now();
      while (attempts < maxAttempts) {
        const delay = attempts < 30 ? 1000 : 2000;
        await new Promise((r) => setTimeout(r, delay));
        attempts++;

        const pollRes = await fetch(`/api/chat/poll/${task_id}?_t=${Date.now()}`, {
          cache: "no-store",
        });
        if (!pollRes.ok) continue;
        const task = await pollRes.json();

        const steps: ChatStep[] = (task.steps || []).filter(
          (s: ChatStep) => s.type === "thinking" || s.type === "tool_call" || s.type === "genie_call",
        );

        if (task.status === "done") {
          setMessages((prev) => {
            const next = [...prev];
            next[assistantIdx] = {
              role: "assistant",
              content: task.response || "No response from agent.",
              steps,
              streaming: false,
            };
            return next;
          });
          break;
        }

        if (task.status === "error") {
          setMessages((prev) => {
            const next = [...prev];
            next[assistantIdx] = {
              role: "assistant",
              content: `Error: ${task.response}`,
              steps,
              streaming: false,
            };
            return next;
          });
          break;
        }

        // Still running — show steps, partial answer, and elapsed time
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        setMessages((prev) => {
          const next = [...prev];
          next[assistantIdx] = {
            role: "assistant",
            content: task.response || "",
            steps,
            streaming: true,
            elapsed,
          };
          return next;
        });
      }

      if (attempts >= maxAttempts) {
        setMessages((prev) => {
          const next = [...prev];
          next[assistantIdx] = {
            role: "assistant",
            content:
              "The agent is taking longer than expected. Please try a simpler question.",
            steps: [],
            streaming: false,
          };
          return next;
        });
      }
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      console.error("Chat error:", e);
      setMessages((prev) => {
        const next = [...prev];
        next[assistantIdx] = {
          role: "assistant",
          content: `Error: ${errMsg}. Please try again.`,
          steps: [],
          streaming: false,
        };
        return next;
      });
    }
    setStreaming(false);
  }, [input, streaming, messages]);

  const suggestedPrompts = [
    "What is the stockout risk for Organic Tomatoes at DC-East?",
    "Plan a demand rebalance for next week",
    "Which DCs have excess inventory that could be redistributed?",
    "Forecast demand for Organic Bananas considering today's weather",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">
          Demand Forecasting & Planning Agent
        </h1>
        <p className="text-sm text-muted-foreground">
          Interactive planning powered by Agent Bricks declarative agents
        </p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-16">
              <Bot className="h-12 w-12 text-primary/40 mb-4" />
              <h2 className="text-lg font-semibold text-foreground/80">
                Supply Chain Planning Assistant
              </h2>
              <p className="text-sm text-muted-foreground mt-1 max-w-md">
                Ask about demand forecasts, inventory levels, shipping
                schedules, supplier orders, or plan distribution scenarios.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 max-w-lg justify-center">
                {suggestedPrompts.map((p) => (
                  <Badge
                    key={p}
                    variant="outline"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-xs"
                    onClick={() => setInput(p)}
                  >
                    {p}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <AssistantMessage msg={msg} />
                    ) : (
                      msg.content
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-7 h-7 rounded-full bg-foreground/10 flex items-center justify-center flex-shrink-0 mt-1">
                      <User className="h-4 w-4 text-foreground/60" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about supply chain planning..."
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={streaming}
              className="flex-1"
            />
            <Button
              onClick={sendMessage}
              disabled={streaming || !input.trim()}
              size="icon"
            >
              {streaming ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
