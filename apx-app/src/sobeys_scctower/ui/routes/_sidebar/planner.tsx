import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Loader2, Bot, User } from "lucide-react";
import Markdown from "react-markdown";

export const Route = createFileRoute("/_sidebar/planner")({
  component: () => <PlannerChat />,
});

interface Message {
  role: "user" | "assistant";
  content: string;
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

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");

    const userMsg: Message = { role: "user", content: text };
    const allMessages = [...messages, userMsg];
    setMessages([
      ...allMessages,
      {
        role: "assistant",
        content:
          "Thinking... the agent is querying data sources. This may take up to a minute.",
      },
    ]);
    setStreaming(true);

    try {
      // Step 1: Start the task (fast — just kicks off background work)
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

      if (!startRes.ok) {
        throw new Error(`Start failed: ${startRes.status}`);
      }

      const { task_id } = await startRes.json();

      // Step 2: Poll every 3 seconds until done (each poll is a short GET)
      let attempts = 0;
      const maxAttempts = 100; // 5 minutes at 3s intervals
      while (attempts < maxAttempts) {
        await new Promise((r) => setTimeout(r, 3000));
        attempts++;

        // Update thinking message with elapsed time
        const elapsed = attempts * 3;
        setMessages([
          ...allMessages,
          {
            role: "assistant",
            content: `Thinking... (${elapsed}s elapsed — querying supply chain data)`,
          },
        ]);

        const pollRes = await fetch(`/api/chat/poll/${task_id}`);
        if (!pollRes.ok) continue;

        const task = await pollRes.json();

        if (task.status === "done") {
          setMessages([
            ...allMessages,
            { role: "assistant", content: task.response || "No response from agent." },
          ]);
          break;
        }

        if (task.status === "error") {
          setMessages([
            ...allMessages,
            { role: "assistant", content: `Agent error: ${task.response}` },
          ]);
          break;
        }
        // status is "pending" or "running" — keep polling
      }

      if (attempts >= maxAttempts) {
        setMessages([
          ...allMessages,
          {
            role: "assistant",
            content:
              "The agent is taking longer than expected. Please try a simpler question.",
          },
        ]);
      }
    } catch (e) {
      setMessages([
        ...allMessages,
        {
          role: "assistant",
          content: "Sorry, there was an error starting the planning agent. Please try again.",
        },
      ]);
    }
    setStreaming(false);
  };

  const suggestedPrompts = [
    "What is the stockout risk for Organic Tomatoes at DC-East?",
    "Plan a demand rebalance for next week",
    "Which DCs have excess inventory that could be redistributed?",
    "Forecast demand for Organic Bananas considering today's weather",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Demand Forecasting & Planning Agent</h1>
        <p className="text-sm text-muted-foreground">
          Interactive planning powered by Agent Bricks declarative agents
        </p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        {/* Messages */}
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-16">
              <Bot className="h-12 w-12 text-primary/40 mb-4" />
              <h2 className="text-lg font-semibold text-foreground/80">
                Supply Chain Planning Assistant
              </h2>
              <p className="text-sm text-muted-foreground mt-1 max-w-md">
                Ask about demand forecasts, inventory levels, shipping schedules,
                supplier orders, or plan distribution scenarios.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 max-w-lg justify-center">
                {suggestedPrompts.map((p) => (
                  <Badge
                    key={p}
                    variant="outline"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-xs"
                    onClick={() => {
                      setInput(p);
                    }}
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
                      <div className="prose prose-sm max-w-none [&_p]:my-1 [&_ul]:my-1 [&_li]:my-0.5">
                        <Markdown>{msg.content || "..."}</Markdown>
                      </div>
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

        {/* Input */}
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
            <Button onClick={sendMessage} disabled={streaming || !input.trim()} size="icon">
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
