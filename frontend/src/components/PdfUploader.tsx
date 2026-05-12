import { useRef, useState } from "react";
import { FileUp, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { IngestDocument } from "@/types";

interface PdfUploaderProps {
  onExtracted: (docs: IngestDocument[]) => void;
}

async function extractTextFromPdf(file: File): Promise<string> {
  const pdfjsLib = await import("pdfjs-dist");
  pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.min.mjs",
    import.meta.url
  ).toString();

  const buffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
  const pages: string[] = [];

  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items
      .map((item) => ("str" in item ? item.str : ""))
      .join(" ");
    pages.push(text);
  }

  return pages.join("\n\n").trim();
}

export function PdfUploader({ onExtracted }: PdfUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFiles(picked: FileList | null) {
    if (!picked) return;
    const pdfs = Array.from(picked).filter((f) => f.type === "application/pdf");
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      return [...prev, ...pdfs.filter((f) => !existing.has(f.name))];
    });
  }

  function removeFile(name: string) {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  }

  async function process() {
    if (!files.length) return;
    setLoading(true);
    setError(null);
    try {
      const docs: IngestDocument[] = await Promise.all(
        files.map(async (file) => {
          const text = await extractTextFromPdf(file);
          const name = file.name.replace(/\.pdf$/i, "");
          return {
            id: name.toLowerCase().replace(/\s+/g, "-"),
            title: name,
            source_type: "manual" as const,
            department: "Uploaded",
            text,
          };
        })
      );
      onExtracted(docs);
      setFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF extraction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 hover:bg-accent/30 transition-colors"
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <FileUp className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm font-medium">Drop PDF files here or click to browse</p>
        <p className="text-xs text-muted-foreground mt-1">Text is extracted locally — no file is uploaded directly</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {/* Selected files */}
      {files.length > 0 && (
        <ul className="space-y-1.5">
          {files.map((f) => (
            <li key={f.name} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
              <span className="truncate">{f.name}</span>
              <Button variant="ghost" size="icon" className="h-6 w-6 flex-shrink-0" onClick={() => removeFile(f.name)}>
                <X className="h-3 w-3" />
              </Button>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {files.length > 0 && (
        <Button onClick={process} disabled={loading} className="gap-2 w-full" variant="outline">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
          {loading ? "Extracting text…" : `Extract & Add ${files.length} PDF${files.length !== 1 ? "s" : ""}`}
        </Button>
      )}
    </div>
  );
}
