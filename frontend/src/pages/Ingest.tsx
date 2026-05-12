import { useState } from "react";
import { PlusCircle, Trash2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { IngestDocument } from "@/types";

const SOURCE_TYPES = ["policy", "contract", "manual", "report", "faq"] as const;

function emptyDoc(): IngestDocument {
  return { id: "", title: "", source_type: "policy", department: "", text: "" };
}

export function Ingest() {
  const [docs, setDocs] = useState<IngestDocument[]>([emptyDoc()]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ documents_received: number; chunks_created: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  function updateDoc(index: number, field: keyof IngestDocument, value: string) {
    setDocs((prev) => prev.map((d, i) => (i === index ? { ...d, [field]: value } : d)));
  }

  function addDoc() {
    setDocs((prev) => [...prev, emptyDoc()]);
  }

  function removeDoc(index: number) {
    setDocs((prev) => prev.filter((_, i) => i !== index));
  }

  async function submit() {
    setError(null);
    setResult(null);

    const valid = docs.every((d) => d.id.trim() && d.title.trim() && d.department.trim() && d.text.trim());
    if (!valid) {
      setError("All fields are required for every document.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.ingest(docs);
      setResult({ documents_received: res.documents_received, chunks_created: res.chunks_created });
      setDocs([emptyDoc()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-6 space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Ingest Documents</h1>
        <p className="text-sm text-muted-foreground">Add documents to the knowledge base for retrieval</p>
      </div>

      {result && (
        <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span>
            Ingested <strong>{result.documents_received}</strong> document{result.documents_received !== 1 ? "s" : ""} →{" "}
            <strong>{result.chunks_created}</strong> chunks created
          </span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {docs.map((doc, index) => (
          <Card key={index}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Document {index + 1}</CardTitle>
                {docs.length > 1 && (
                  <Button variant="ghost" size="icon" onClick={() => removeDoc(index)} className="h-8 w-8 text-muted-foreground hover:text-destructive">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Document ID</Label>
                  <Input
                    placeholder="e.g. hr-policy-001"
                    value={doc.id}
                    onChange={(e) => updateDoc(index, "id", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Title</Label>
                  <Input
                    placeholder="e.g. HR Policy Handbook 2026"
                    value={doc.title}
                    onChange={(e) => updateDoc(index, "title", e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Source Type</Label>
                  <select
                    value={doc.source_type}
                    onChange={(e) => updateDoc(index, "source_type", e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    {SOURCE_TYPES.map((t) => (
                      <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label>Department</Label>
                  <Input
                    placeholder="e.g. HR, Finance, IT"
                    value={doc.department}
                    onChange={(e) => updateDoc(index, "department", e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Document Text</Label>
                <Textarea
                  placeholder="Paste the full document content here…"
                  value={doc.text}
                  onChange={(e) => updateDoc(index, "text", e.target.value)}
                  rows={5}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={addDoc} className="gap-2">
          <PlusCircle className="h-4 w-4" />
          Add Another Document
        </Button>
        <Button onClick={submit} disabled={loading}>
          {loading ? "Ingesting…" : `Ingest ${docs.length} Document${docs.length !== 1 ? "s" : ""}`}
        </Button>
      </div>
    </div>
  );
}
