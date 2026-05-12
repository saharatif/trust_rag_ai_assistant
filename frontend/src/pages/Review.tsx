import { useState, useEffect, useCallback } from "react";
import { CheckCircle, XCircle, PenLine, RefreshCw, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrustScoreBadge } from "@/components/TrustScoreBadge";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import type { ReviewItem } from "@/types";

const REVIEWER_ID = "reviewer-ui";

type Action = "approve" | "reject" | "modify" | null;

interface ItemState {
  action: Action;
  notes: string;
  correctedAnswer: string;
  loading: boolean;
  done: boolean;
  error: string | null;
}

function defaultState(): ItemState {
  return { action: null, notes: "", correctedAnswer: "", loading: false, done: false, error: null };
}

export function Review() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [states, setStates] = useState<Record<string, ItemState>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getPendingReviews();
      setItems(res.items);
      setStates(Object.fromEntries(res.items.map((i) => [i.review_id, defaultState()])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function setState(id: string, patch: Partial<ItemState>) {
    setStates((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  }

  async function submit(item: ReviewItem) {
    const s = states[item.review_id];
    setState(item.review_id, { loading: true, error: null });
    try {
      if (s.action === "approve") {
        await api.approveReview(item.review_id, REVIEWER_ID, s.notes);
      } else if (s.action === "reject") {
        await api.rejectReview(item.review_id, REVIEWER_ID, s.notes);
      } else if (s.action === "modify") {
        await api.modifyReview(item.review_id, REVIEWER_ID, s.correctedAnswer, s.notes);
      }
      setState(item.review_id, { done: true, loading: false });
    } catch (err) {
      setState(item.review_id, {
        error: err instanceof Error ? err.message : "Action failed",
        loading: false,
      });
    }
  }

  const pending = items.filter((i) => !states[i.review_id]?.done);

  return (
    <div className="h-full overflow-y-auto px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Review Queue</h1>
          <p className="text-sm text-muted-foreground">
            {loading ? "Loading…" : `${pending.length} pending review${pending.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && pending.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <Inbox className="h-12 w-12 opacity-20" />
          <p className="text-sm">No pending reviews — queue is clear.</p>
        </div>
      )}

      <div className="space-y-4">
        {items.map((item) => {
          const s = states[item.review_id] ?? defaultState();
          if (s.done) return null;

          return (
            <Card key={item.review_id}>
              <CardHeader className="pb-3">
                <div className="flex flex-wrap gap-2 items-center">
                  <TrustScoreBadge score={item.trust_score} />
                  <Badge variant="outline" className="text-xs">{item.confidence} confidence</Badge>
                  <Badge variant="warning" className="text-xs">{item.review_reason.replace(/_/g, " ")}</Badge>
                  <span className="text-xs text-muted-foreground ml-auto">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Question</p>
                  <p className="text-sm">{item.question}</p>
                </div>
                <Separator />
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Answer</p>
                  <p className="text-sm text-muted-foreground">{item.answer}</p>
                </div>

                {/* Action buttons */}
                {!s.action && (
                  <div className="flex gap-2 pt-1">
                    <Button size="sm" variant="outline" className="gap-2 text-green-700 border-green-200 hover:bg-green-50"
                      onClick={() => setState(item.review_id, { action: "approve" })}>
                      <CheckCircle className="h-4 w-4" /> Approve
                    </Button>
                    <Button size="sm" variant="outline" className="gap-2 text-red-700 border-red-200 hover:bg-red-50"
                      onClick={() => setState(item.review_id, { action: "reject" })}>
                      <XCircle className="h-4 w-4" /> Reject
                    </Button>
                    <Button size="sm" variant="outline" className="gap-2"
                      onClick={() => setState(item.review_id, { action: "modify", correctedAnswer: item.answer })}>
                      <PenLine className="h-4 w-4" /> Modify
                    </Button>
                  </div>
                )}

                {/* Action form */}
                {s.action && (
                  <div className="space-y-3 pt-1 border-t">
                    <p className="text-sm font-medium capitalize">{s.action} this response</p>

                    {s.action === "modify" && (
                      <div className="space-y-1.5">
                        <Label>Corrected Answer</Label>
                        <Textarea
                          rows={3}
                          value={s.correctedAnswer}
                          onChange={(e) => setState(item.review_id, { correctedAnswer: e.target.value })}
                        />
                      </div>
                    )}

                    <div className="space-y-1.5">
                      <Label>{s.action === "reject" ? "Reason" : "Notes (optional)"}</Label>
                      <Textarea
                        rows={2}
                        placeholder={s.action === "reject" ? "Why is this being rejected?" : "Any additional notes…"}
                        value={s.notes}
                        onChange={(e) => setState(item.review_id, { notes: e.target.value })}
                      />
                    </div>

                    {s.error && <p className="text-sm text-destructive">{s.error}</p>}

                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => submit(item)} disabled={s.loading}>
                        {s.loading ? "Submitting…" : "Confirm"}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setState(item.review_id, { action: null })}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
