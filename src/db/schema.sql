-- TrustRAG database schema for PostgreSQL / SQLite.
-- Tracks conversations, AI responses, human reviews, and audit trails.

-- Conversations: top-level grouping of related messages
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title TEXT
);

-- Messages: individual turn in a conversation (user or AI)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- AI Responses: detailed tracking of RAG pipeline results
CREATE TABLE IF NOT EXISTS ai_responses (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence TEXT CHECK (confidence IN ('low', 'medium', 'high')),
    answer_status TEXT CHECK (answer_status IN ('answered', 'unsupported')),
    trust_score REAL CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
    sources_used INT,
    retrieved_doc_ids TEXT,  -- JSON array of source document IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- Review Queue: responses flagged for human review
CREATE TABLE IF NOT EXISTS review_queue (
    id TEXT PRIMARY KEY,
    response_id TEXT NOT NULL UNIQUE,
    review_reason TEXT NOT NULL,
    trust_score REAL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'modified')),
    reviewer_id TEXT,
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES ai_responses(id)
);

-- Audit Log: immutable record of all system actions for compliance
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,  -- e.g., 'question_asked', 'answer_generated', 'review_completed'
    resource_type TEXT,    -- e.g., 'response', 'review'
    resource_id TEXT,
    actor_type TEXT,       -- 'user', 'system', 'reviewer'
    actor_id TEXT,
    details TEXT,          -- JSON with contextual info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_ai_responses_message_id ON ai_responses(message_id);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_review_queue_created_at ON review_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
