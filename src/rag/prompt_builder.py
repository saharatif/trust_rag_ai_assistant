# Prompt construction for grounded RAG answers.

from src.rag.retriever import RetrievedMatch


def build_rag_prompt(question: str, matches: list[RetrievedMatch]) -> str:
    """Build a compact prompt from retrieved source chunks."""
    context_blocks = [
        (
            f"Source {index}: {match.title} "
            f"({match.document_id}, {match.chunk_id})\n{match.text}"
        )
        for index, match in enumerate(matches, start=1)
    ]
    context = "\n\n".join(context_blocks) or "No relevant document context found."
    return (
        "Answer the question using only the source context. "
        "If the context does not support an answer, say that the documents do not "
        "contain enough information.\n\n"
        f"Question: {question}\n\n"
        f"Source context:\n{context}"
    )
