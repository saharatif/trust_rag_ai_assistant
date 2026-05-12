import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { TrustScoreBadge } from "@/components/TrustScoreBadge";
import { api } from "@/lib/api";
import type { ChatMessage } from "@/types";

let msgId = 0;

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setError(null);

    const userMsg: ChatMessage = { id: String(++msgId), role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.chat(question);
      const assistantMsg: ChatMessage = {
        id: String(++msgId),
        role: "assistant",
        content: res.answer,
        trustScore: res.trust_score,
        confidence: res.confidence,
        answerStatus: res.answer_status,
        sourcesUsed: res.sources_used,
        needsReview: res.needs_review,
        reviewReason: res.review_reason,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b">
        <h1 className="text-lg font-semibold">Chat</h1>
        <p className="text-sm text-muted-foreground">Ask questions from your approved documents</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground gap-3">
            <Bot className="h-12 w-12 opacity-20" />
            <p className="text-sm">Ask a question to get started.<br />Answers are grounded in your ingested documents.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
            )}

            <div className={`max-w-[75%] space-y-2 ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
              <div className={`rounded-lg px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              }`}>
                {msg.content}
              </div>

              {/* Answer metadata */}
              {msg.role === "assistant" && msg.trustScore !== undefined && (
                <div className="flex flex-wrap gap-2 items-center">
                  <TrustScoreBadge score={msg.trustScore} />

                  <Badge variant="outline" className="text-xs">
                    {msg.confidence} confidence
                  </Badge>

                  {msg.sourcesUsed !== undefined && (
                    <Badge variant="outline" className="text-xs">
                      {msg.sourcesUsed} source{msg.sourcesUsed !== 1 ? "s" : ""}
                    </Badge>
                  )}

                  {msg.needsReview && (
                    <Badge variant="warning" className="gap-1 text-xs">
                      <AlertTriangle className="h-3 w-3" />
                      Needs Review
                      {msg.reviewReason && ` — ${msg.reviewReason.replace(/_/g, " ")}`}
                    </Badge>
                  )}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
              <Bot className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="bg-muted rounded-lg px-4 py-3 flex gap-1 items-center">
              <span className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" />
            </div>
          </div>
        )}

        {error && (
          <div className="text-sm text-destructive bg-destructive/10 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t">
        <div className="flex gap-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
            rows={2}
            className="resize-none"
            disabled={loading}
          />
          <Button onClick={send} disabled={loading || !input.trim()} size="icon" className="h-auto">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
