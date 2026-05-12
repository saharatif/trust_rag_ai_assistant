export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  trustScore?: number;
  confidence?: "low" | "medium" | "high";
  answerStatus?: "answered" | "unsupported";
  sourcesUsed?: number;
  needsReview?: boolean;
  reviewReason?: string;
}

export interface IngestDocument {
  id: string;
  title: string;
  source_type: "policy" | "contract" | "manual" | "report" | "faq";
  department: string;
  text: string;
}

export interface IngestResponse {
  documents_received: number;
  chunks_created: number;
  status: string;
}

export interface ChatResponse {
  answer: string;
  confidence: "low" | "medium" | "high";
  answer_status: "answered" | "unsupported";
  trust_score: number;
  sources_used: number;
  needs_review: boolean;
  review_reason?: string;
}

export interface ReviewItem {
  review_id: string;
  response_id: string;
  question: string;
  answer: string;
  confidence: "low" | "medium" | "high";
  trust_score: number;
  review_reason: string;
  created_at: string;
}

export interface ReviewListResponse {
  total: number;
  items: ReviewItem[];
}
